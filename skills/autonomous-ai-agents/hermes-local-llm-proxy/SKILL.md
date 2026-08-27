---
name: hermes-local-llm-proxy
description: Route Hermes LLM traffic through local proxy shim (Caveman).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, proxy, llm-routing, compression, lmstudio, self-hosted, systemd]
    related_skills: [hermes-agent]
---

# Route Hermes LLM Traffic Through a Local OpenAI-Compatible Proxy

Puts a local shim (compression/rewriting/routing) between Hermes and the real model server. The concrete, fully-verified instance in this skill is **Caveman** — see `references/caveman.md` for its exact file layout, install commands, and rollback. This SKILL.md holds the provider-class pattern that applies to ANY such shim.

## When to use
- User wants a local compression/token-saving or routing layer in front of their model (e.g. Caveman's "save input tokens" proxy).
- A third-party tool installed a loopback proxy and expects Hermes to talk to it instead of the upstream directly.
- Debugging why new Hermes sessions suddenly can't reach the model after a shim was added/removed.

## Core architecture
```
Hermes  --base_url-->  http://127.0.0.1:<port>/<route>/v1   (local shim)
                                              |
                                    pinned upstream in shim config
                                              v
                                 real model server (LAN / local / cloud)
```
- Hermes is pointed at the **shim's** base_url via `model.base_url`. Hermes appends its own endpoint suffix (e.g. `/chat/completions`) to that base_url.
- The shim inspects/transforms the request, then forwards it to a **pinned upstream**. Auth headers are forwarded verbatim — the shim does not store your key.

## Wiring steps (provider-class)
1. **Back up first.** Copy `~/.hermes/config.yaml` → `~/.hermes/backups/config.yaml.pre-<change>-<ts>.yaml`. Never hand-edit config; use `hermes config set model.base_url <shim-route>`.
2. **Pin the shim's upstream** in its own config file (for Caveman: `providers.<name>.base_url` in `~/.caveman/caveman.yaml`). An un-pinned shim forwards to a hosted default (OpenAI) — your self-hosted key then gets rejected by the wrong provider.
3. **Allowlist private/LAN upstreams.** Shims block private/link-local/loopback outbound ranges by default (SSRF guard). For a LAN/self-hosted model server, add an exact-host allowlist env var to the service unit (Caveman: `CAVE_SSRF_ALLOWLIST=<ip>`). Use only the specific host; no broad ranges.
4. **Make it durable.** Shims are daemons that idle-exit or die on crash. Wrap in a systemd user service with `Restart=on-failure` and `[Install] WantedBy=default.target`, then `systemctl --user enable --now <svc>`. See durability gotcha below about orphaned port holders.
5. **Point Hermes at it.** `hermes config set model.base_url http://127.0.0.1:<port>/<route>/v1`. This takes effect for every NEW session (and gateway restart), not the live one.

## Gotchas (apply to any OpenAI-compatible shim)
- **base_url path doubling.** Many adapters append `/v1/{chat/completions,...}` themselves. Do NOT include a trailing `/v1` in the pinned upstream base_url or you get `POST /v1/v1/chat/completions` → 404 "Unexpected endpoint". Pin to host:port (e.g. `http://host:port`), not `.../v1`.
- **Un-pinned default upstream.** If the shim's config file is absent, it forwards to a hosted provider. Symptom: your valid self-hosted key returns an *OpenAI-style* 401 "Incorrect API key ... platform.openai.com". Fix = pin base_url + SSRF allowlist.
- **Auth is forwarded verbatim.** The shim does not store the key. Rotating the token upstream means updating only the agent's env (e.g. `LM_API_KEY` in `~/.hermes/.env`) — nothing on the shim side changes.
- **Orphaned port holder blocks the managed unit.** If a previous unmanaged daemon still owns the port, the systemd unit will crash-loop ("port in use"). Identify with `ss -tlnp | grep <port>`, kill that pid, then restart the service so it can bind.

## Verification (do this before declaring done)
1. **E2E through the shim** with the real key, in an isolated subshell so the secret never lands in shell history:
   ```bash
   bash -c 'set -a; source ~/.hermes/.env >/dev/null 2>&1; set +a; \
     curl -sS -m 90 <shim-route>/chat/completions -H "Content-Type: application/json" \
       -H "Authorization: Bearer $LM_API_KEY" -d "{...minimal chat payload...}"' | head -c 800
   ```
   Expect a genuine completion from the real upstream model.
2. **Real Hermes round-trip** (does not touch your live session): `hermes chat -q "Reply with exactly the two words: OK now"` — expect terse `OK now` and exit 0.
3. Confirm telemetry/telemetry-off state if the shim has one, and that the service is `active`.

## Rollback (no uninstall needed)
- Bypass: `hermes config set model.base_url <direct-upstream>` then `systemctl --user stop <svc>`.
- Restore full prior config from the backup in step 1.
