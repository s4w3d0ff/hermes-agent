---
name: twitch-cli-mock-testing
description: Use when testing Twitch against twitch-cli mock servers.
tags: [twitch, testing, pytest, mocks]
related_skills: []
---

# Twitch CLI Mock Testing

Offline test-suite pattern: drive the code under test's real HTTP/WS/OAuth request paths against `twitch-cli`'s local mock servers so wire-format responses are exercised instead of hand-rolled fakes. Proven in pool-guy (115-test suite, fully offline except one manual live smoke).

## When to use
- Writing or extending tests for code that talks to api.twitch.tv / id.twitch.tv / EventSub WSS.
- You need wire-format fidelity (pagination shapes, close codes, CLI-signed webhook traffic) without real credentials or network access.
- NOT the home for: rate-limit backoff logic (mocks send no `Ratelimit-*` headers), `/oauth2/validate`, chat-send token auth — those stay unit-level. See references/cli-quirks-v1.1.24.md for the full cannot-serve list.

## Server lifecycle fixture (session-scoped)
1. Ports: API mock **8000**, EventSub WS mock **8090**. Never bind 8080 — that is the OAuth callback port in this deployment. Use ephemeral local ports only when a second WS instance is needed (e.g. `-S` deadline mode).
2. Pre-check: `ss -ltnp` both ports; kill only your own stale listeners matched on exact twitch cmdlines, never by bare port ownership. If still occupied after self-clean, fail loudly and stop.
3. Data first: `twitch mock-api generate -c 20`. Ids are random per run — **never hardcode mock ids**; discover at runtime from `/units/clients` and `/units/users?first=100`, and pick fixture users by a runtime property (e.g. max follower total) rather than an id.
4. Start via `subprocess.Popen` with logs to session tmp files: `twitch mock-api start -p 8000`, `twitch event websocket start-server -p 8090`. Health-poll: GET `/units/clients` until 200; WS server via TCP connect. 30s budget, clear failure message.
5. Teardown: terminate + bounded wait + kill fallback; re-check ports are free afterwards.

## No-real-network guard (non-negotiable)
Session autouse fixture monkeypatches `aiohttp.ClientSession._request` and `websockets.connect`; any URL whose host is not 127.0.0.1/localhost raises immediately. The suite proves itself offline by construction; a regression that calls production fails in seconds instead of at rate limits.

## Driving the CLI from async tests — pitfalls
- **Never use blocking `subprocess.run()` inside an async test while your own aiohttp server shares the event loop.** The CLI holds its HTTP request open waiting for YOUR handler, but blocking run() stalls the very loop that must answer it. Symptom: Go-side "context deadline exceeded" and zero bytes arriving at your listener — verify with a raw asyncio TCP probe before blaming routing or signatures. Use `asyncio.create_subprocess_exec` + `communicate()` under `wait_for`.
- **aiohttp routes are exact path matches**: the CLI posts to `/eventsub/` (trailing slash) while handlers usually register `/eventsub` — 404s that look like auth failures. Register both variants in test wiring; production registers its own paths.
- Manual token refresh: persist the response immediately, Twitch rotates refresh tokens on use — a crash between request and save forces full re-login. `scope` arrives as a LIST in refresh responses but a string for authorization_code exchanges; normalize before storing.

## What v1.1.24 mocks cannot do (keep unit-level)
- Push a WS frame for `twitch event websocket subscription --status=user_removed` — the command only rewrites stored status, zero frames reach connected clients (probe-verified). Test revocation handling at injection level: feed a spec-shaped revocation frame into your real handler, using the CLI-created revoked record as fixture. Re-validate on version bump.
- Serve the user_token grant from form bodies (`/auth/authorize` is query-params-only; 400 otherwise) — production request code cannot drive it offline. `client_credentials` via `/auth/token` works through real request code.
- No Ratelimit-* headers, no /oauth2/validate route, beta scope catalog rejects chat scopes (chat send not token-authable offline).

## Pointers
- references/cli-quirks-v1.1.24.md — full versioned quirks bank (empirical; re-probe on upgrade). Command syntax reference: default profile's twitch-api skill `references/cli/*.md` (read-only from this profile).
