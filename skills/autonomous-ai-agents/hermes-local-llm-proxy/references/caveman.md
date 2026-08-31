# Caveman — concrete instance of the local LLM proxy shim

Caveman (github.com/JuliusBrussee/caveman) has two installable halves:
1. **Skill pack** ("save output") — terse-reply skills. `node bin/install.js --only hermes` copies 7 skill dirs into `~/.hermes/skills/productivity/`. No proxy involved; works standalone. Say "caveman mode" or `/caveman` in a new session.
2. **Proxy** ("save input") — local OpenAI-compatible compression layer on loopback; shrinks context before the provider call. This is what this skill wires into Hermes.

## State on this box (as of 2026-08-30)

The proxy was detached and its systemd user unit removed at user request: caveman input-side compression did not work for hermes (it refused to compress streamed requests). Current state:
- No `caveman-proxy` process, no service. Do NOT assume ports 8787/8790 exist or that `systemctl --user ... caveman-proxy` works.
- Hermes talks directly: `model.base_url http://192.168.1.232:1234/v1` (see `~/.hermes/config.yaml`).
- The skill pack and the native MCP plugin (`caveman_native`, tools `mcp__caveman_native__*`) remain active — output-side compression still works without depending on the proxy.
- `~/.caveman/` data dir (binaries, ccr.db, caveman.yaml) was left in place; re-wiring means recreating the unit below + repointing `model.base_url`, nothing more.

## Key paths (this box)
- Binaries: `~/.caveman/bin/caveman-proxy` (+ engine, mcp, shrink, browse, cavemem). Manifest: `~/.caveman/bin/.bin-manifest.json`.
- **Proxy config:** `~/.caveman/caveman.yaml` (override path via `$CAVEMAN_CONFIG`). Absent file = shim forwards to hosted default.
- **Feature/telemetry config:** `~/.caveman-cloud/config.json` → `"telemetry": {"enabled": bool}`. User wants it OFF; keep it that way. Do not re-enable.
- Run state: `~/.caveman/run/<port>.json`, `native.sock`. Logs: `~/.caveman/proxy.log`. Usage DB (local only): `~/.caveman/caveman.db` (`requests`, `usage_events` tables).
- Hermes plugin/MCP wiring the vendor installer may add lives in `~/.hermes/plugins/` and fenced blocks in `config.yaml` (markers like `# >>> caveman:native-hermes-*`). Vendor keeps backups under `~/.caveman/integrations/backups/<agent>/`.

## Proxy config schema (`~/.caveman/caveman.yaml`)
```yaml
label: local-lmstudio
mode: compress          # record | compress | pixel (operator-facing)
listen: 127.0.0.1:8787
providers:
  openai:
    base_url: http://<model-host>:<port>   # NO trailing /v1 — adapter appends it
compat: {}
```
- `providers.<name>.base_url` pins the upstream for that provider's route. The `/w/hermes/...` Hermes route maps to the **openai** provider upstream, so pin `providers.openai.base_url`.
- Named OpenAI-compatible mounts use `compat.<name>: {base_url, api_key_env}` and mount at `/compat/<name>/...`.

## SSRF allowlist (required for LAN/self-hosted)
Proxy blocks private/link-local/loopback outbound by default. Add the exact host to the service unit env:
```ini
Environment=CAVE_SSRF_ALLOWLIST=<model-ip>        # e.g. 192.168.1.232 — no :port, no ranges
```

## Durable systemd user service (`~/.config/systemd/user/caveman-proxy.service`)
```ini
[Unit]
Description=Caveman local compression proxy (routes Hermes LLM traffic, forwards to LM Studio)
After=network.target

[Service]
Type=simple
WorkingDirectory=%h
Environment=CAVE_SSRF_ALLOWLIST=<model-ip>
ExecStart=/home/<user>/.caveman/bin/caveman-proxy
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
```
Apply: `systemctl --user daemon-reload && systemctl --user enable --now caveman-proxy.service`. Check: `systemctl --user status caveman-proxy` (want `active`). If it crash-loops "port in use", an orphaned unmanaged proxy holds the port — find via `ss -tlnp | grep 8787`, kill that pid, restart.

## Wiring Hermes
- `hermes config set model.base_url http://127.0.0.1:8787/w/hermes/v1`
- Provider stays whatever the user runs (e.g. `lmstudio`). Auth (`LM_API_KEY` from `~/.hermes/.env`) is sent as Bearer and forwarded verbatim by the proxy to upstream — the proxy never stores it. Rotate token = edit `.env` only.

## Telemetry off
Edit `~/.caveman-cloud/config.json`: `"telemetry": { "enabled": false, ... }`. Verify after any CLI run that might flip consent: read back `d['telemetry']['enabled'] is False`.

## Rollback / re-wiring on this box (no uninstall)
- Bypass (already in place since 2026-08-30): `model.base_url` points directly at `http://192.168.1.232:1234/v1`; the caveman-proxy unit no longer exists. Re-wiring means recreating it per the template above + repointing base_url.
- Pre-change config backup lives at `~/.hermes/backups/config.yaml.pre-caveman-<ts>.yaml`.

## Install (from a clone; avoids npm 12 arg-parsing quirks with the npx one-liner)
```bash
git clone --depth 1 https://github.com/JuliusBrussee/caveman.git /tmp/caveman
cd /tmp/caveman && node bin/install.js --only hermes --dry-run   # preview: only touches ~/.hermes/skills/productivity/
node bin/install.js --only hermes                                 # install skill pack
```
`caveman setup --install` (npm CLI) only verifies/downloads binaries; it does NOT wire Hermes. The persistent config wiring is what `~/.caveman/caveman.yaml` + `model.base_url` do here.
