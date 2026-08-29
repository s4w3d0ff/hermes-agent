# Skin spinner-key rendering paths (traced 2026-08-28)

Verified against the hermes-agent checkout at `~/.hermes/hermes-agent` on this
install. Line numbers go stale after updates — re-grep before relying on them,
and treat the *consumer topology* below as the durable part:

## Who consumes what (spinner section)

| Skin key | Consumer(s) | Renders where |
|---|---|---|
| `waiting_faces` / `thinking_faces` / `thinking_verbs` | `KawaiiSpinner.get_waiting_faces/get_thinking_faces/get_thinking_verbs` → composed into spinner *messages* at `agent/tool_executor.py` (per-tool lines) and `agent/conversation_loop.py` (thinking line) | Everywhere the CLI prints tool/thinking progress, incl. interactive REPL — via `_spinner_text` TUI widget AND plain-TTY KawaiiSpinner frames |
| `wings` (list of [left,right] pairs) | **exactly one consumer**: `KawaiiSpinner._animate()` in `agent/display.py`, which reads `skin.get_spinner_wings()` and wraps each `\r`-animated frame as `<2sp>{left} {frame} {message} {right} ({elapsed}s)` | Only plain-TTY contexts where `_animate` runs on raw stdout (e.g. one-shot / non-prompt_toolkit surfaces) |

## Why `spinner.wings` never shows in the interactive REPL (code gap, not config)

1. The whole interactive main loop runs inside prompt_toolkit's `patch_stdout()`
   (`cli.py`, search for `with patch_stdout():`).
2. Under that context `sys.stdout` is a `StdoutProxy`. `KawaiiSpinner._animate()`
   detects this (`_is_patch_stdout_proxy()`) and returns early in an idle loop —
   *before* it ever reaches the wings code. Comment there says the TUI widget
   takes over spinner display, so the `\r` animation is deliberately suppressed.
3. The thing that actually draws the visible spinner line in the REPL is
   `HermesCLI._render_spinner_text()` in `cli.py` — it reads only `_spinner_text`,
   elapsed time, and token flow. It **never consults `spinner.wings`**.

Therefore no valid config format makes wings appear in the interactive REPL; a
patch to `_render_spinner_text()` (or KawaiiSpinner) upstream is required. When
this surfaces again: verify with `git status --short` that the checkout is clean,
and report the gap instead of patching.

## Where wings DO render today
Any bare-TTY context where `KawaiiSpinner._animate` runs without a StdoutProxy —
e.g. one-shot mode (`hermes chat -q ...`) from a real terminal. On this install
the user's approvals.deny blocks agent-run `hermes *chat*`, so ask the user to run
it once as ground-truth verification: wings should appear as brackets around the
spinner line (e.g. `𓁜 … 𓁝`).

## "Wings show without my skin" — a known misread, not a second consumer
Users report that with NO custom skin, bracket-like decorations DO frame the
spinner in the same REPL. That is NOT `wings` rendering: it is the built-in
parentheses/ear glyphs inside the fallback kawaii face strings —
`KAWAII_WAITING` / `KAWAII_THINKING` in agent/display.py (entries like
`(｡◕‿◕｡)` and `٩(◕‿◕｡)۶`). Without a skin, `get_waiting_faces()` falls back to
those wrapped strings, so the face itself looks bracketed. Custom skins whose
faces are bare glyphs (no parens in the string) lose that framing entirely —
which reads as "my wings don't show but default does". Never treat this report
as evidence of a second wing consumer; the single-consumer topology stands.
Config-only approximation if the user wants framing anyway: bake wrap glyphs
into each face string (e.g. `⟪𓅓⟫`) — brackets hug the glyph per frame, not the
whole line like true wings do; it is an aesthetic change to their skin art, so
offer it rather than applying silently.

## Config format reference (canonical, per official docs "Skins & Themes")
```yaml
spinner:
  waiting_faces: ["(⚔)", "(⛨)"]     # list of strings
  thinking_faces: ["(⚔)", "(<>)"]   # list of strings
  thinking_verbs: ["forging"]       # list of strings
  wings:                            # list of [left, right] string pairs
    - ["⟪⚔", "⚔⟫"]
    - ["⟪▲", "▲⟫"]
```
Parser: `SkinConfig.get_spinner_wings()` in `hermes_cli/skin_engine.py` — keeps an
entry only if it is a 2-element list/tuple, stringifies both sides. Entries with
other shapes are silently dropped (a likely cause of "some wings missing" if the
user hand-wrote malformed pairs).

## Verification one-liner (run from the checkout)
```bash
cd <hermes-agent checkout> && ./venv/bin/python - <<'EOF'
import yaml, hermes_cli.config as H  # or however this install loads its main config
from hermes_cli.skin_engine import load_skin, get_active_skin_name, init_skin_from_config
cfg = <loaded config dict from step 1>   # e.g. the loaded YAML of the active profile's main config file
init_skin_from_config(cfg)   # REQUIRED: active skin is a module global set only at CLI startup
print("active:", get_active_skin_name())
s = load_skin(get_active_skin_name())
w = s.get_spinner_wings()
print(f"{len(w)} wing pairs; first: {w[:3]}")
EOF
```

Pitfall: `get_active_skin_name()` in a bare script returns "default" unless you
first call `init_skin_from_config(cfg)` with the loaded config — it is a module
global populated only during CLI startup. Without init, an empty-looking result
is a probe artifact, not evidence that no skin is active (the YAML's own
`spinner:` block still parses fine via `load_skin(name)`).
