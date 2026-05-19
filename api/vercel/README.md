# Vercel — DataDiggers Chat Proxy

This Vercel serverless function proxies chat requests from the DataDiggers website to Anthropic's Claude API.

## Deploy in 3 commands

```bash
cd api/vercel
npx vercel                                  # follow prompts, creates a Vercel project
npx vercel env add ANTHROPIC_API_KEY        # paste your sk-ant-... key when prompted
npx vercel --prod
```

After `vercel --prod`, you'll get a URL like:
```
https://datadiggers-chat-xxxxx.vercel.app
```

The chat endpoint is at `/api/chat` on that domain.

## Wire the website
Either edit `js/chat.js` and change `apiEndpoint`, **or** add this line to your HTML:

```html
<script>window.DD_CHAT_ENDPOINT = "https://datadiggers-chat-xxxxx.vercel.app/api/chat";</script>
```

## Same-origin option (recommended)
If you also host the static site on Vercel (as a static project), `/api/chat` is same-origin and CORS isn't needed.

## Free tier
Vercel hobby tier: 100GB-hours of function compute and 100GB bandwidth/month. Plenty for a corporate site.

## System prompt
The topic-scoping system prompt lives at the top of `api/chat.js`. Edit and redeploy to change behavior.
