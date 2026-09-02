---
name: twitch-token-tooling
description: "Issue and validate Twitch tokens via twitch-cli."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [twitch, oauth, token, twitch-cli, scopes, bot-testing]
---
# Twitch Token Tooling

Issue user/app access tokens for local bot development (twitch-cli or the project's own TokenHandler flow), derive the exact scope list from what a test exercises, and validate any issued token before injection.

**The agent host is the same machine as the user's GUI.** The user has physical access to the browser AND the entire agent environment — one OS, one hardware. Do not describe the host as headless or hand off commands for 'the laptop terminal' when you can execute them yourself; verify what you claim to run.

## When to Use

- A local bot (smoke test, debug run) needs a fresh Twitch user or app access token.
- User asks "what scopes do I need for the test token?" — derive from the calls the test makes, hand over the exact `twitch token` command.
- Validating an existing token before injection: zero-scope tokens validate as 200 yet are useless.

Don't use for: production credential management, or EventSub/webhook architecture (that lives in the twitch-api reference skill).

## Prerequisites

- twitch-cli installed on the user's GUI machine (`twitch` on PATH; Homebrew installs to a ~/linuxbrew/.linuxbrew/bin/twitch style path — check `which twitch`).
- App registered at dev.twitch.tv/console/apps; client id + secret reachable by the agent (usually a gitignored project `.env`).
- The app's OAuth Redirect URLs include `http://localhost:3000` as the FIRST entry, no trailing slash. twitch-cli hard-codes port 3000 and requires it first in the list.

## Issuing tokens (user runs these on the GUI machine)

```
twitch token                                # app access token
twitch token -u -s "scope1 scope2 ..."      # user token, space-separated quoted scopes
```

- Re-running overwrites the saved token. A login issued without `-s` leaves a valid-but-zero-scope token (env `TOKENSCOPES=[]`, validate returns `"scopes": null`) — re-run with the `-s` list to get usable scopes.
- Config file: `~/.config/twitch-cli/.twitch-cli.env` with keys `CLIENTID`, `CLIENTSECRET`, `ACCESSTOKEN`, `REFRESHTOKEN`, `TOKENSCOPES`, `TOKENEXPIRATION`. `twitch configure` fills the client pair; token commands fill the rest.
- Public-client refresh tokens are one-time-use with a 30-day TTL — capture `REFRESHTOKEN` at issue time if the test may need re-auth later.

## Running the project's own OAuth flow (pool-guy pattern)

Prefer this over twitch-cli when the bot project ships its own token handler: it exercises production code paths, and the token lands directly in the app's storage — no file injection needed. Verified working 2026-09 for pool-guy (`tools/oauth_login.py`, committed on `fix/audit-remediation`).

```python
from poolguy.core.oauth import TokenHandler          # project's own handler, not a reimplementation
from poolguy.core.storage import SQLiteStorage       # default db/twitch.db is gitignored (/db/)

handler = TokenHandler(
    client_id=env["TWITCH_CLIENT_ID"],
    client_secret=env.get("TWITCH_CLIENT_SECRET"),
    redirect_uri="http://localhost:5000/callback",   # must match a URL registered in the dev console for this app
    scopes=["user:read:chat", "user:write:chat", "moderator:read:followers"],
    storage=SQLiteStorage(str(ROOT / "db" / "twitch.db")),
    browser={"librewolf": "/usr/bin/librewolf"},      # explicit path = deterministic GUI browser, no xdg guesswork
)
token = await handler.get_token()                     # saved token valid  -> validate/refresh; invalid -> interactive auth
```

- **DISPLAY fallback**: the agent's shell may run on a tty session with no DISPLAY while the user's GUI runs on `:1`. Before launching any browser from your own shell, fall back to `os.environ.setdefault("DISPLAY", ":1")` when `/tmp/.X11-unix/X1` exists. The user's own terminal needs nothing.
- **Keep the registered redirect port** (pool-guy: 5000) rather than picking a 'nicer' one like 8080 — it is already in the dev-console app registration, so zero console changes. A new port means updating OAuth Redirect URLs first.
- **Test-run before handing off**: run the command yourself with `timeout ~20s` and confirm the browser process actually launches (pgrep the binary), then kill that test instance and verify the callback port is free again — only after that hand the user the SAME exact command. Same machine, so no 'run this on your laptop' framing.
- The saved token in `db/twitch.db` IS the semi-permanent login: every later run validates/refreshes it instead of re-authing. Public-client refresh tokens are one-time-use with a 30-day TTL, so re-login is at most once per ~30 days via this same flow.

## Testing without real API calls (development default)

User directive: during development, do NOT make live Twitch API calls casually (risk of tripping limits or invalidating credentials by mistake). Use twitch-cli's offline tooling as the default dev loop:

- `twitch mock-api` — generates mock data and runs a local mock server; point the bot at it to exercise REST paths with zero real traffic.
- `twitch event` / `websocket event` — trigger fake EventSub notifications locally against your own handler/client, no live subscription needed.

Real user tokens are reserved for explicit live smoke/regression runs (the one-shot live test), not routine development. Full CLI docs: twitch-api skill `references/cli/` (`mock-api-command.md`, `event-command.md`, `websocket-event-command.md`).

## Semi-permanent dev token (agreed pattern)

User wants a reusable test token so re-login isn't needed per test run. Pattern:
1. Issue ONE user token with the FULL scope set any pool-guy test might need (`user:read:chat user:write:chat moderator:read:followers`), account must mod the target channel (GOTTEM, id 108284496).
2. Persist `ACCESSTOKEN` + `REFRESHTOKEN` in a gitignored file OUTSIDE the repo (never commit); inject via the project's token-file env var.
3. Let the app auto-refresh: public-client refresh tokens are one-time-use with 30-day TTL, so "semi-permanent" really means ~30 days of automated refresh from one login, then re-run `twitch token -u -s ...` and update the stored file.

## Deriving scopes from what the test exercises

Map each live call in the smoke/regression script to its scope before asking the user for anything:

| Test action | Scope | Extra requirement |
|---|---|---|
| EventSub WS subscribe `channel.chat.message` | `user:read:chat` | granted from the chatting user's token |
| Send Chat Message API (`/helix/chat/messages`) | `user:write:chat` | account may post in target channel (mod or open chat) |
| Get Channel Followers, paginated | `moderator:read:followers` | token owner must be a MOD of the broadcaster being queried, else 403 |
| Hourly validate + refresh cycle | none extra | just keep the refresh token |

Then hand the user one exact command, e.g.:
`twitch token -u -s "user:read:chat user:write:chat moderator:read:followers"`

Cross-check against a working sibling bot's stored token (e.g. its SQLite `tokens` table) — its granted scopes are ground truth for what that account can do.

## Validating a token before use (agent-side, headless)

```
GET https://id.twitch.tv/oauth2/validate
Authorization: OAuth <token>
```

- 200 → `{ client_id, scopes, expires_in, login, user_id }`. Check BOTH: `scopes` non-null and covering the test's needs, AND `client_id` equals the app under test. A token from another app validates fine but is useless for this project.
- 401 → invalid/expired.
- Zero-scope tokens return 200 with `"scopes": null`. Never trust the env file's `TOKENSCOPES` key or file mtime — hit the endpoint.

## Injecting into a headless bot test

Write the token as JSON matching what the project's storage layer expects (check its `save_token` shape) to a file outside the repo, and point the script at it via env var (pool-guy convention: `SMOKE_TOKEN_FILE`). Keep `.env` and any token files gitignored; never commit tokens. Redact values in logs/chat — show only first/last few chars.

## Pitfalls

- Redirect URL missing or not FIRST with a trailing slash → twitch-cli hangs on the localhost:3000 callback that never arrives. Fix in dev console (add `http://localhost:3000` as entry 1, no trailing `/`), then re-run.
- Zero-scope login masquerading as success: terminal prints a token but `TOKENSCOPES=[]`; validate shows `scopes:null`. Re-run with the `-s` list.
- Borrowing tokens from sibling projects/apps (e.g. another bot's stored token): may be valid yet wrong app, missing scopes, or the account lacks mod status on the target channel → 403/insufficient-scope on specific endpoints even though validate passes. Match app + account role before suspecting code.
- One-time-use public refresh tokens: if a long-lived test re-auths, the original refresh token is dead after first use; keep a copy of `REFRESHTOKEN` from issue time.
- twitch-cli failing interactively on the user's GUI (root cause unknown to you) → do NOT go down a debugging rabbit hole in their GUI session. The project's own OAuth flow (section above) is an equally valid token source that exercises production code — pivot there instead of making the user chase CLI errors.
- Never frame work as 'run this on your laptop/GUI machine': same system. You can and should execute it, verify the side effects (browser process spawned, port bound/freed), and hand back the exact command you verified.

## Verification

- Validate endpoint returns 200 with the expected scopes list and matching `client_id`.
- The bot reaches logged-in state on the injected token without triggering interactive re-auth, and each live API step (subscribe/send/followers) returns success.
