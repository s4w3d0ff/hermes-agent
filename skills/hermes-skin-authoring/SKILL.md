---
name: hermes-skin-authoring
description: "Author Hermes skins: banner art, palettes, image-to-hero."
version: 1.0.0
author: s4w3d0ff
license: MIT
metadata:
  hermes:
    tags: [hermes, skins, theming, ascii-art]
    related_skills: [hermes-agent]
---

# Hermes Skin Authoring

## When to Use

- Creating or editing a user skin in `~/.hermes/skins/` (colors, branding, spinner, tool_emojis).
- Making `banner_logo` / `banner_hero` art from an image (ascii-image-converter braille output), including converting its ANSI 256-color tags into the Rich hex markup the skin parser requires.

Creating or editing user skins for the Hermes CLI/TUI/desktop. Complements the bundled `hermes-agent` skill (general config); this one covers the skin YAML and its banner art fields specifically.

## Layout & invariants

- User skins live at `~/.hermes/skins/<name>.yaml`. The engine globs **only** `*.yaml` — any other file co-located there is inert, so helper scripts may sit next to the skin without affecting `list_skins()`.
- Missing YAML fields fall back to the built-in `default` skin; partial files are fine.
- `banner_logo` / `banner_hero`: block scalars with one art row per line, each line Rich markup: `[#RRGGBB]text[/][#hex2]more[/]`. Rendered via `Text.from_markup` in `hermes_cli/banner.py`; pushed verbatim to TUI/desktop through tui_gateway (`resolve_skin`).
- Hex tags are fixed — they do NOT adapt to `light_colors`/`dark_colors`. Built-in skins behave the same; don't "fix" it.
- Full schema reference: the docstring at the top of `hermes_cli/skin_engine.py` in `~/.hermes/hermes-agent/` is the source of truth, not this skill.

## Image → hero pipeline (braille art)

User preference for hero art: use `--braille`. Width 40 fits the banner column; drop lower if it wraps on narrow terminals.

1. Generate colored ANSI to a file — colors only exist on **stdout** (`--save-txt` writes plain text):
   ```bash
   ascii-image-converter images/YuuBooty.png -C -W 40 --braille > /tmp/hero-ansi.txt
   ```
2. Back up the skin, convert, rewrite (script resolves colors via `rich.color.Color.from_ansi` at runtime), then diff:
   ```bash
   PY=~/.hermes/hermes-agent/.venv/bin/python
   cp ~/.hermes/skins/horus.yaml /tmp/horus.yaml.bak
   $PY <this-skill>/scripts/ansi_to_rich.py /tmp/hero-ansi.txt --skin ~/.hermes/skins/horus.yaml
   diff /tmp/horus.yaml.bak ~/.hermes/skins/horus.yaml   # only the banner_hero block may change
   ```
3. Verify round-trip (cell-by-cell char+color against the original ANSI, through the real skin loader):
   ```bash
   $PY <this-skill>/scripts/verify_hero.py --skin ~/.hermes/skins/horus.yaml --ansi /tmp/hero-ansi.txt
   # expect: mismatches=0 and "plain art identical: True"; exit 0
   ```

## Pitfalls (learned the hard way)

- **Never hand-write an xterm-256 palette table.** rich's `Color.from_ansi` mapping deviates from classic xterm in places (e.g. index 16 maps to white, not black). A hand-built table produced wrong hex tags and a broken token count; deriving colors at runtime via `rich.color.Color.from_ansi` is always correct by construction.
- **System python3 has no rich.** Run the scripts with the repo venv: `~/.hermes/hermes-agent/.venv/bin/python`.
- **Rich span indexing:** after `Text.from_markup`, spans' start/end index into `t.plain`, NOT the markup source string; and `span.style` may be a raw str — normalize via `Style.parse(str(...))` before reading `.color`. (verify_hero.py encodes both.)
- **`--save-txt` strips color** in ascii-image-converter; only stdout carries ANSI, even when redirected.
- Keep hero width modest (~40) and eyeball the rendered banner under a narrow terminal for wrapping: `Console().print(skin.banner_hero)` via the venv python.

## Support files

- `scripts/ansi_to_rich.py` — ANSI file → Rich markup; rewrites only the target `field: |` block in the skin YAML. Flags: `[ANSI_FILE] [--skin PATH] [--field banner_hero|banner_logo] [--dry-run]`.
- `scripts/verify_hero.py` — round-trip verifier (real skin loader + from_markup vs original ANSI); non-zero exit on any char/color mismatch or plain-art drift.
