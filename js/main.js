/* DataDiggers — site behaviors */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu toggle
  const toggle = document.querySelector('.menu-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    // Close menu when a link is clicked
    links.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        if (window.innerWidth <= 720) links.classList.remove('open');
      });
    });
  }

  // Year in footer
  const year = document.getElementById('current-year');
  if (year) year.textContent = new Date().getFullYear();

  // Forms → POST to the Cloudflare Worker /api/contact endpoint
  const CONTACT_ENDPOINT =
    window.DD_CONTACT_ENDPOINT ||
    'https://datadiggers-chat.divakar-sharma.workers.dev/api/contact';

  document.querySelectorAll('form[data-dd-form]').forEach((form) => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"]');
      const success = form.querySelector('.form-success');
      const error = form.querySelector('.form-error');
      const formType = form.dataset.formType || 'contact';

      const originalLabel = submitBtn ? submitBtn.textContent : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending…';
      }
      if (error) error.classList.remove('show');

      const fields = Object.fromEntries(new FormData(form).entries());

      try {
        const response = await fetch(CONTACT_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ formType, fields })
        });

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.error || `Request failed (${response.status})`);
        }

        if (success) success.classList.add('show');
        form.reset();
        setTimeout(() => success && success.classList.remove('show'), 8000);
      } catch (err) {
        console.error('[DD Form] Submission failed:', err);
        if (error) {
          error.textContent = 'Sorry — we couldn\'t send your message. Please try again, or email rfq@datadiggers-mr.com directly.';
          error.classList.add('show');
        } else {
          alert('Sorry — we couldn\'t send your message. Please try again, or email rfq@datadiggers-mr.com directly.');
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalLabel;
        }
      }
    });
  });

  // Reveal on scroll for elements with [data-reveal]
  const reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = 1;
          entry.target.style.transform = 'translateY(0)';
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach((el) => {
      el.style.opacity = 0;
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
      io.observe(el);
    });
  }
});
