# Cloudflare Worker — DataDiggers Chat Proxy

This Cloudflare Worker proxies chat requests from the DataDiggers website to Anthropic's Claude API, keeping your API key secret on the server side.

## Prerequisites
- A free Cloudflare account: https://dash.cloudflare.com/sign-up
- An Anthropic API key: https://console.anthropic.com/settings/keys
- Node.js 18+ installed locally

## Deploy in 4 commands

```bash
cd api/cloudflare-worker
npm install
npx wrangler login                                # opens browser, log in to Cloudflare
npx wrangler secret put ANTHROPIC_API_KEY         # paste your sk-ant-... key when prompted
npx wrangler deploy                               # deploys the worker
```

After `wrangler deploy` succeeds, you'll see a URL like:
```
https://datadiggers-chat.your-subdomain.workers.dev
```

## Wire the website to your worker
Either edit `js/chat.js` and change `apiEndpoint`, **or** add this line to your HTML before `js/chat.js`:

```html
<script>window.DD_CHAT_ENDPOINT = "https://datadiggers-chat.your-subdomain.workers.dev/api/chat";</script>
```

## Lock CORS to your domain (recommended for production)
In `worker.js`, replace `"Access-Control-Allow-Origin": "*"` with your GitHub Pages domain:
```js
"Access-Control-Allow-Origin": "https://datadiggers.github.io"
```
or your custom domain.

## Free tier
Cloudflare Workers free tier: 100,000 requests/day. More than enough for a corporate site.

## Updating the system prompt
The system prompt that scopes the assistant to DataDiggers topics is at the top of `worker.js` in the `SYSTEM_PROMPT` constant. Edit, then redeploy.
