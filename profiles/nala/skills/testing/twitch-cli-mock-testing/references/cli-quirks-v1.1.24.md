# twitch-cli v1.1.24 quirks (empirical, 2026-09)

Observed against installed twitch-cli v1.1.24 while building the pool-guy offline suite. Re-validate on version bump — treat every row as a hypothesis until re-probed.

## mock-api (`twitch mock-api start -p 8000`)
- Helix routes under `http://127.0.0.1:8000/mock/...` (drop-in for https://api.twitch.tv/helix).
- `/units/*` unauthenticated: generated clients (`ID`, `Secret`), users with follower graphs, partner users (~11 followers each at `-c 20`). Data is random per `generate` run — discover ids at runtime.
- Pagination real (cursor + `total`); **terminal pages omit the `pagination` key entirely** (production sends `{}`).
- No `Ratelimit-*` headers on any response → proactive rate-limit backoff stays unit-level.
- Deprecated routes return real 410 (`/users/follows`); unknown routes 404 with JSON body — good for error-surfacing regression tests.
- Cross-user reads: one partner's user token can read ANY channel's followers (walk all follower totals with a single auth call).

## Auth endpoints
- `POST /auth/token?grant_type=client_credentials&client_id&client_secret` → app token; works from real form-body request code. 24h TTL, no refresh flow.
- `POST /auth/authorize?grant_type=user_token&...` — **query params only**, and the string must be urlencoded (raw spaces silently 400 with a misleading message). Form body returns 400 `missing required parameter` even when all fields are present → production form-body code cannot drive the user_token grant offline.
- `authorization_code` grant against `/auth/token`: 400 offline.
- Beta scope catalog rejects `user:read:chat`, `user:write:chat`; accepts e.g. `moderator:read:followers`, `user:read:email`. Chat send therefore cannot be token-authed offline (payload construction stays unit-level + one live smoke).

## EventSub WS (`twitch event websocket start-server -p 8090`)
- Serves `ws://127.0.0.1:PORT/ws` plus a subscription API at `http://127.0.0.1:PORT/eventsub/subscriptions` (POST/GET/DELETE) — out-of-band verification of what the client actually subscribed to.
- Welcome carries per-client session id; observed `keepalive_timeout_seconds: 10` (production differs).
- GET on the subscriptions endpoint can return an empty body on some paths → clients must tolerate a missing body.
- `twitch event websocket reconnect`: sends `session_reconnect`, stands up the replacement server at the SAME url/port (original pid persists), 30s grace window then close. Client follows `reconnect_url`; verify out-of-band that subscription ids are preserved under the new session_id, and that a post-reconnect trigger (`--session=<new sid>`) dispatches.
- `twitch event trigger <event> --transport=websocket [--session=X]`: ~50 supported events; **`channel.chat.message` is NOT in the v1.1.24 list** → chat-message WS dispatch stays injection-level + live smoke.
- `twitch event websocket subscription --status=<s> --subscription=<id>`: rewrites stored status ONLY — **no WS frame is pushed to connected clients** (probe: rc=0, zero frames received). Revocation handling must be tested by injecting a spec-shaped revocation frame into the real handler. CLI rejects status changes mid-reconnect.
- `twitch event websocket close --session=X --reason=<code>`: arbitrary close codes.
- `-S/--require-subscription`: enforces the 10s subscribe deadline ("Connection unused" close). Offline analog of spec code 4003; exact production semantics differ — document the divergence in the test commit. Run it on an ephemeral port as a second server instance, assert the run loop cycles through deadline closes without crash-looping.

## Webhook transport (`-F http://127.0.0.1:<port>/eventsub/`)
- `twitch event verify-subscription <event> -b <broadcaster>`: real signed challenge POST; CLI reports valid response + 2xx only when the handler echoes the challenge as text/plain.
- `twitch event trigger <event> -T webhook -s <secret>`: forwards a genuinely HMAC-SHA256-signed notification (`Twitch-Eventsub-Msgsignature`); secret must be 10–100 ASCII chars.
- Both are Go HTTP clients that hold their request open until you answer — drive them with async subprocesses, never blocking ones, when the target server lives in your event loop.

## Cross-checks
- Command syntax reference: default profile's twitch-api skill `references/cli/*.md` (scraped docs; read-only from this profile). This file records where behavior diverges from or exceeds those docs.
- Working implementation of the full pattern: pool-guy branch `test/offline-mock-suite`, `tests/conftest.py` + `tests/test_events_ws.py` / `test_webhook.py` / `test_tokens.py`.
