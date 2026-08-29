---
name: hermes-skin-troubleshooting
description: "Diagnose Hermes skin keys not rendering on any surface."
version: 1.0.0
author: Hermes Agent (autonomous review)
license: MIT
metadata:
  hermes:
    tags: [hermes, skins, themes, debugging, tui, display]
    related_skills: [hermes-agent]
---

# Hermes Skin Troubleshooting

Diagnose "my custom skin's <feature> isn't displaying" for the Hermes CLI / TUI / desktop. The fix lives in a user skin YAML (skins dir under the active profile home, e.g. `horus.yaml`) — or nowhere at all (an upstream code gap). It never lives in application source.

## When to Use
- User reports a custom skin feature missing: "wings not showing", spinner faces/verbs ignored, colors or branding not applied on CLI/TUI/desktop.
- Before editing any `~/.hermes/skins/*.yaml` after such a report — this skill separates format bugs from surface-rendering gaps so you don't churn the YAML for nothing.

## Hard rules
- **NEVER edit installed app/service codebases** (the hermes-agent checkout, LM Studio, caveman proxy, etc.). They are update-managed checkouts; edits get clobbered on the next update and destroy local truth. Fix via user config files only: skin YAMLs and safe config writers.
- When a code-level gap is found, report it to the user with file/function pointers for an upstream issue — do not patch.
- If you ever DO accidentally edit installed source: revert exactly (reverse patches), then prove clean state with `git status --short` in that checkout before reporting done.

## Workflow
1. **Confirm active skin + surface.** Open the active profile's main YAML config and check `display.skin` / `display.interface`. Many `hermes` subcommands may be blocked by the user's approval deny list (this install denies e.g. `hermes *config*`, `hermes *chat*`) — reading files directly is always fine; check that list before running any hermes CLI verb.
2. **Validate the skin file with the app's own engine** — ground truth, not eyeballed YAML:
   ```bash
   cd <hermes-agent checkout> && ./venv/bin/python - <<'EOF'
   from hermes_cli.skin_engine import load_skin
   s = load_skin("NAME")
   print(s.get_spinner_wings())          # or any getter for the key in question
   print(len(s.spinner.get("waiting_faces", [])))
   EOF
   ```
   Always use the checkout venv's interpreter (`./venv/bin/python`) — system `python3` lacks deps. If the loader parses the values correctly, the config format is already right and "fixing" it changes nothing. Say so explicitly instead of inventing a change.
3. **Find every consumer of that key** to learn which surface actually renders it:
   ```bash
   grep -rn "<key>" --include="*.py" <hermes-agent checkout> | grep -vE "tests/|node_modules"
   grep -rn "<key>" ui-tui/src apps/desktop web/src 2>/dev/null   # TS surfaces
   ```
   If the renderer on the user's active surface never reads the key, NO config format will make it appear — that is an upstream code gap. Stop there; report with pointers (see references/skin-rendering-paths.md for the already-traced map).
4. **Check canonical formats in official docs** before touching YAML: `curl -s https://hermes-agent.nousresearch.com/docs/llms-full.txt` → "Skins & Themes" section (full template + per-key type tables, e.g. `wings:` = list of `[left, right]` pairs).
5. **Only then** edit the user skin YAML — and only if the format genuinely deviates from the documented schema.

## Pitfalls
- "YAML looks right" ≠ "will render". Format validity (step 2) and surface consumption (step 3) are two independent checks; most false leads skip step 3.
- Don't run engine verification with bare `python3` — missing deps; use the checkout venv interpreter.
- Line numbers in references go stale after hermes updates — re-grep, don't trust remembered offsets.
- Exotic glyphs (hieroglyphs U+130xx etc.): if faces render but wings show as tofu boxes on the one surface that does support them, suspect terminal font coverage before config.

## References
- `references/skin-rendering-paths.md` — verified consumer map for spinner keys: which surfaces render what, why `spinner.wings` never appears in the interactive REPL regardless of config, and where it CAN render. Consult BEFORE promising any config fix can make a feature appear; re-verify claims after hermes updates.
