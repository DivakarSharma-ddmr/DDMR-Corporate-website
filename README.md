# DataDiggers Website

A static rebuild of [www.datadiggers-mr.com](https://www.datadiggers-mr.com) for GitHub Pages, with an integrated AI chat assistant powered by Claude.

The chat agent is **scoped strictly to DataDiggers topics and the market research industry** — off-topic questions are politely declined and the user is redirected to the sales team.

---

## What's inside

```
datadiggers-site/
├── index.html                    Homepage
├── pages/                        22 sub-pages (company, solutions, contact, legal…)
├── css/
│   ├── style.css                 Main design system (green palette, Fraunces + Manrope)
│   └── chat.css                  Chat widget styles
├── js/
│   ├── partials.js               Shared header & footer (auto-injected)
│   ├── main.js                   Mobile menu, form handling, scroll reveal
│   └── chat.js                   The chat widget — connects to your backend
├── api/
│   ├── cloudflare-worker/        Option A: Cloudflare Worker backend
│   └── vercel/                   Option B: Vercel serverless function
├── .github/workflows/deploy.yml  Auto-deploys to GitHub Pages on push to main
└── .gitignore
```

---

## How it all fits together

1. **Static site** (HTML/CSS/JS) is hosted on GitHub Pages — free.
2. **Chat widget** (`js/chat.js`) sits at the bottom-right of every page.
3. When a visitor sends a message, the widget POSTs to a **backend proxy** (Cloudflare Worker *or* Vercel function — your choice).
4. The proxy holds your **Anthropic API key** as a secret and forwards the request to Claude with a topic-scoping system prompt.
5. The reply comes back; the widget renders it.

GitHub Pages alone can't safely hold the API key (the code is public). That's why a small backend proxy is needed — both options below are free for normal traffic levels.

---

## Quick-start: get the site live (3 steps)

### Step 1 — Push to GitHub

```bash
cd datadiggers-site
git init
git add .
git commit -m "Initial DataDiggers website rebuild"
git branch -M main
git remote add origin https://github.com/<your-org>/<your-repo>.git
git push -u origin main
```

### Step 2 — Enable GitHub Pages

In your repo: **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**.

Push any change to `main` and the workflow in `.github/workflows/deploy.yml` will publish your site to `https://<your-org>.github.io/<your-repo>/`.

### Step 3 — Pick a chat backend

You get both options pre-configured. Pick one:

| | **Cloudflare Worker** | **Vercel** |
|---|---|---|
| Free tier | 100k requests/day | 100GB-hours/month |
| Cold start | None (always warm) | Slight on first request |
| Setup time | ~5 minutes | ~5 minutes |
| Custom domain | Free | Free |

Both work great. Pick whichever ecosystem you're more comfortable with. Detailed deploy instructions are in:
- [`api/cloudflare-worker/README.md`](api/cloudflare-worker/README.md)
- [`api/vercel/README.md`](api/vercel/README.md)

### Step 4 — Connect the website to your backend

Once your backend is deployed, you'll have a URL like `https://datadiggers-chat.your-subdomain.workers.dev/api/chat`.

Open `index.html` (and ideally include it once in `js/chat.js`, but the cleanest way is via a global variable). Add this line just **before** `<script src="js/chat.js"></script>` on every page:

```html
<script>window.DD_CHAT_ENDPOINT = "https://YOUR-BACKEND-URL/api/chat";</script>
```

Or — simpler — edit `js/chat.js` directly at the top:
```js
apiEndpoint: window.DD_CHAT_ENDPOINT || 'https://YOUR-BACKEND-URL/api/chat',
```

That's it. The chat widget will now talk to your deployed backend.

---

## You need an Anthropic API key

Both backend options need one. Get one here: **https://console.anthropic.com/settings/keys**

- Create an Anthropic account
- Add a payment method (pay-as-you-go; no monthly minimum)
- Generate a key starting with `sk-ant-...`
- Paste it when prompted by `wrangler secret put` or `vercel env add`

**Never commit this key to your repo.** Both backends store it as an environment secret, not in code.

### Expected cost
The chat uses **Claude Haiku 4.5** — fast and cheap. Typical exchange (5–10 messages) costs around **$0.001–$0.005**. A site getting 100 chats/day will cost roughly **$1–$5/month**.

---

## Customising the chat assistant

### Change what it knows or how it behaves
Open the `SYSTEM_PROMPT` constant at the top of:
- `api/cloudflare-worker/worker.js` (if using Cloudflare), or
- `api/vercel/api/chat.js` (if using Vercel)

Edit, then redeploy (`wrangler deploy` or `vercel --prod`).

The system prompt currently:
- Establishes the assistant's identity as the DataDiggers website assistant
- Lists company facts, products, panels, certifications, and contact info
- **Restricts scope** to: (1) DataDiggers itself, (2) DataDiggers products, (3) market research in general
- **Refuses everything else** and redirects to `rfq@datadiggers-mr.com` / `+40 770 794 874`
- Sets tone: warm, professional, concise

### Change the welcome message and quick replies
Open `js/chat.js` and edit the `CONFIG` block at the top:
```js
const CONFIG = {
  welcomeMessage: "…",
  quickReplies: ["…", "…"],
  …
};
```

### Change the visual styling
Open `css/chat.css`. Colors, sizes, animation timings — all there.

---

## Local testing

The static site needs no build step. Just open `index.html` in a browser — *but* relative paths and the partials script work best when served. The easiest way:

```bash
cd datadiggers-site
python3 -m http.server 8080
# visit http://localhost:8080
```

To test the chat locally:
```bash
cd api/cloudflare-worker
npx wrangler dev          # runs on http://localhost:8787
```
Then set `window.DD_CHAT_ENDPOINT = "http://localhost:8787/api/chat"` in your browser console.

---

## Production checklist before going live

- [ ] Repo pushed; GitHub Pages enabled
- [ ] Backend deployed; `ANTHROPIC_API_KEY` set as a secret
- [ ] `window.DD_CHAT_ENDPOINT` pointed at the deployed backend
- [ ] CORS locked down: in `worker.js` / `chat.js`, replace `"Access-Control-Allow-Origin": "*"` with your actual Pages URL (e.g. `https://your-org.github.io`)
- [ ] Tested chat from a deployed page (not localhost)
- [ ] Tested an off-topic question (should refuse and offer sales contact)
- [ ] Privacy policy, terms, cookie policy reviewed (placeholders provided — replace with finalized text)
- [ ] Contact form handler wired up (currently shows a success message but doesn't deliver — point it at Formspree / Netlify Forms / your own endpoint)
- [ ] Custom domain configured (optional — both GitHub Pages and CF/Vercel support custom domains)

---

## Things that are placeholders / to do later

These are intentionally left for you because they're business decisions, not technical ones:

- **Contact / quote / demo forms** — they show a success animation but don't actually deliver. Easiest fix: sign up for [Formspree](https://formspree.io) (free tier), get an endpoint URL, change each `<form data-dd-form>` to `<form action="https://formspree.io/f/XXXX" method="POST">` and remove the `data-dd-form` attribute (so the demo handler doesn't intercept).
- **Legal pages** — `privacy-policy.html`, `terms-and-conditions.html`, `cookie-policy.html` contain placeholder copy. Replace with your finalized legal text.
- **Team photos** — the Meet-the-Team page uses initial-letter avatars; swap to real photos when you have them.
- **Blog** — currently a static index of card teasers. Wire to a real CMS (or just write static blog pages) when ready.
- **Analytics** — no tracking is included. Add Google Analytics, Plausible, or whatever you prefer in `js/partials.js` if needed.
- **Image assets** — the original site uses several hero images and decorative graphics on CDN URLs we can't redistribute. The rebuild uses CSS-only visuals (gradients, animated globe, geometric backgrounds). Swap in your own imagery when desired.

---

## Why this architecture?

- **No build step.** Plain HTML/CSS/JS — easy to read, edit, and audit. No webpack, no node_modules in the site itself.
- **No framework lock-in.** You can keep this for years without dependency rot.
- **Tiny.** The whole site is under 200KB. Loads fast everywhere.
- **Resilient.** If the chat backend ever goes down, the rest of the site keeps working.
- **Secure.** Your API key never touches the browser.
- **Cheap.** GitHub Pages (free) + Cloudflare Workers or Vercel (free tier) + Anthropic ($1–5/month at modest traffic).

---

## Need help?
- Questions about the code → check inline comments in each file
- Questions about Anthropic API → https://docs.claude.com
- Questions about Cloudflare Workers → https://developers.cloudflare.com/workers
- Questions about Vercel → https://vercel.com/docs

Good luck — you're 95% of the way to a modern, AI-powered corporate website. 🚀
