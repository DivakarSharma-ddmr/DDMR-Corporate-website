/* ============================================================
   DataDiggers AI Chat Widget
   Connects to /api/chat backend proxy (Cloudflare Worker or Vercel)
   ============================================================ */

(function () {
  'use strict';

  // ─────────────────────────────────────────────
  // CONFIGURATION
  // ─────────────────────────────────────────────
  const CONFIG = {
    // Endpoint of your backend proxy. Edit when deployed.
    //   - Cloudflare Worker:  https://<your-worker>.workers.dev/api/chat
    //   - Vercel:             https://<your-app>.vercel.app/api/chat
    //   - Same-origin Vercel: /api/chat
    apiEndpoint: window.DD_CHAT_ENDPOINT || 'https://datadiggers-chat.divakar-sharma.workers.dev/api/chat',

    welcomeMessage:
      "👋 Hi! I'm the DataDiggers assistant. I can answer questions about our company, our 2M+ panelist network, our solutions (Brainactive, Syntheo, Modeliq, Correlix, NeoPulse, Omnibus), or the market research industry in general. What can I help you with?",

    quickReplies: [
      'Tell me about your panels',
      'What is Brainactive?',
      'Data quality standards',
      'How do I get a quote?'
    ],

    placeholder: 'Ask about DataDiggers, our panels, or market research…',

    salesContact: {
      email: 'rfq@datadiggers-mr.com',
      phone: '+40 770 794 874'
    }
  };

  // ─────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────
  const state = {
    open: false,
    messages: [],            // [{role: 'user'|'assistant', content: string}]
    sending: false,
    panel: null,
    launcher: null,
    messagesEl: null,
    inputEl: null,
    sendBtn: null,
    badgeEl: null
  };

  // ─────────────────────────────────────────────
  // UI CONSTRUCTION
  // ─────────────────────────────────────────────
  function buildWidget() {
    // Launcher
    const launcher = document.createElement('button');
    launcher.className = 'dd-chat-launcher';
    launcher.setAttribute('aria-label', 'Open DataDiggers chat');
    launcher.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span class="badge" style="display:none">1</span>
    `;
    document.body.appendChild(launcher);
    state.launcher = launcher;
    state.badgeEl = launcher.querySelector('.badge');

    // Panel
    const panel = document.createElement('div');
    panel.className = 'dd-chat-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'DataDiggers chat');
    panel.innerHTML = `
      <div class="dd-chat-header">
        <div class="agent-avatar">DD</div>
        <div class="agent-info">
          <h4>DataDiggers Assistant</h4>
          <span class="status">Online</span>
        </div>
        <button class="close-btn" aria-label="Close chat">✕</button>
      </div>
      <div class="dd-chat-messages" role="log" aria-live="polite"></div>
      <div class="dd-quick-replies"></div>
      <div class="dd-chat-input-bar">
        <textarea rows="1" placeholder="${CONFIG.placeholder}" aria-label="Type your message"></textarea>
        <button class="send-btn" aria-label="Send message" disabled>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
      <div class="dd-chat-footer">Powered by <strong>Claude</strong> · Topics: DataDiggers & market research</div>
    `;
    document.body.appendChild(panel);
    state.panel = panel;
    state.messagesEl = panel.querySelector('.dd-chat-messages');
    state.inputEl = panel.querySelector('textarea');
    state.sendBtn = panel.querySelector('.send-btn');

    wireEvents(panel);
    renderQuickReplies();

    // Show a small unread badge on first page load
    if (!sessionStorage.getItem('dd-chat-greeted')) {
      state.badgeEl.style.display = 'grid';
    }
  }

  function wireEvents(panel) {
    state.launcher.addEventListener('click', toggleOpen);
    panel.querySelector('.close-btn').addEventListener('click', toggleOpen);

    // Input: auto-grow, enable/disable send, Enter to send
    state.inputEl.addEventListener('input', () => {
      autoGrow(state.inputEl);
      state.sendBtn.disabled = !state.inputEl.value.trim() || state.sending;
    });
    state.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
      }
    });
    state.sendBtn.addEventListener('click', send);
  }

  function autoGrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 90) + 'px';
  }

  function toggleOpen() {
    state.open = !state.open;
    state.panel.classList.toggle('open', state.open);
    if (state.open) {
      state.badgeEl.style.display = 'none';
      sessionStorage.setItem('dd-chat-greeted', '1');
      if (state.messages.length === 0) showWelcome();
      setTimeout(() => state.inputEl.focus(), 250);
    }
  }

  function showWelcome() {
    appendMessage('assistant', CONFIG.welcomeMessage);
  }

  function renderQuickReplies() {
    const wrap = state.panel.querySelector('.dd-quick-replies');
    wrap.innerHTML = '';
    CONFIG.quickReplies.forEach((q) => {
      const btn = document.createElement('button');
      btn.textContent = q;
      btn.addEventListener('click', () => {
        state.inputEl.value = q;
        send();
      });
      wrap.appendChild(btn);
    });
  }

  function hideQuickReplies() {
    const wrap = state.panel.querySelector('.dd-quick-replies');
    wrap.style.display = 'none';
  }

  // ─────────────────────────────────────────────
  // MESSAGES
  // ─────────────────────────────────────────────
  function appendMessage(role, content) {
    const div = document.createElement('div');
    div.className = 'dd-msg ' + (role === 'user' ? 'user' : 'bot');
    div.innerHTML = formatContent(content);
    state.messagesEl.appendChild(div);
    state.messagesEl.scrollTop = state.messagesEl.scrollHeight;

    // Track in state (not the welcome — only real exchanges)
    if (role !== 'assistant' || state.messages.length > 0) {
      state.messages.push({ role, content });
    } else {
      // First assistant message (welcome) — don't include in API history
    }
  }

  function formatContent(text) {
    // Minimal safe formatting: escape HTML, then handle **bold**, links, newlines.
    let safe = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold **text**
    safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Markdown links [text](url)
    safe = safe.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    // Bare URLs
    safe = safe.replace(/(^|\s)(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
    // Emails
    safe = safe.replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1">$1</a>');
    // Paragraph breaks
    safe = safe.split(/\n\n+/).map((p) => '<p>' + p.replace(/\n/g, '<br>') + '</p>').join('');
    return safe;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.className = 'dd-msg bot typing';
    div.id = 'dd-typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    state.messagesEl.appendChild(div);
    state.messagesEl.scrollTop = state.messagesEl.scrollHeight;
  }

  function hideTyping() {
    const el = document.getElementById('dd-typing-indicator');
    if (el) el.remove();
  }

  // ─────────────────────────────────────────────
  // SEND
  // ─────────────────────────────────────────────
  async function send() {
    const text = state.inputEl.value.trim();
    if (!text || state.sending) return;

    hideQuickReplies();

    appendMessage('user', text);
    state.inputEl.value = '';
    autoGrow(state.inputEl);
    state.sendBtn.disabled = true;
    state.sending = true;
    showTyping();

    try {
      const response = await fetch(CONFIG.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: state.messages.map((m) => ({ role: m.role, content: m.content }))
        })
      });

      hideTyping();

      if (!response.ok) {
        const errBody = await response.text().catch(() => '');
        throw new Error(`Server returned ${response.status}: ${errBody.slice(0, 200)}`);
      }

      const data = await response.json();
      const reply = (data && data.reply) || "I'm sorry — I couldn't generate a response just now.";
      appendMessage('assistant', reply);
    } catch (err) {
      hideTyping();
      console.error('[DD Chat] Error:', err);
      appendMessage(
        'assistant',
        `I'm having trouble connecting right now. Please try again in a moment, or contact our sales team directly at **${CONFIG.salesContact.email}** or **${CONFIG.salesContact.phone}**.`
      );
    } finally {
      state.sending = false;
      state.sendBtn.disabled = !state.inputEl.value.trim();
      state.inputEl.focus();
    }
  }

  // ─────────────────────────────────────────────
  // BOOT
  // ─────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildWidget);
  } else {
    buildWidget();
  }
})();
