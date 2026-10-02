# Rampage History Server

Servidor autoritativo do modo **History** usando Cloudflare Workers + Durable Objects + WebSocket.

## Deploy

No Cloudflare Workers Builds, conecte o repositório `islandzombieslz/Rampage` e use:

- Path: `/history-server`
- Build command: vazio
- Deploy command: `npx wrangler deploy`
- Preview command: `npx wrangler preview`

Depois do primeiro deploy, copie a URL `https://rampage-history.<subdominio>.workers.dev`.

Endpoints:
- `GET /health`
- `GET /servers`
- `WS /ws?server=history-1&uid=<uid>&name=<nick>`

Cada ID de servidor é roteado para um Durable Object independente, que é a autoridade da partida. Nenhum jogador vira host.
