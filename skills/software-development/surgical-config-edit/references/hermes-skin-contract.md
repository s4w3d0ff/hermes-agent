# Hermes skin contract (verified 2026-08)

Source-of-truth locations for `~/.hermes/skins/<name>.yaml` edits.

## Canonical color token set
- **44 tokens**, defined in `apps/shared/src/skin.ts` as `SKIN_COLOR_TOKENS`. This is the ONE shape TUI/desktop consume over JSON-RPC; treat it as the enum of valid keys.
- The `skin_engine.py` module docstring lists only ~30 of them — do NOT use prose docs for coverage checks. Extract from skin.ts: `set(re.findall(r"'([a-z_]+)'", m.group(1)))`.
- Python CLI reads a 28-key subset via `get_color("key")` / `_skin_color("key")` in `hermes_cli/` (grep those two patterns for the live set).

## Merge semantics (`skin_engine._build_skin_config`)
- User skin colors **merge over built-in `default`** — missing keys silently fall back to default-skin values, never error. So a "missing key" is invisible unless you audit coverage explicitly.
- `light_colors` / `dark_colors` are NOT merged over defaults: an absent block means "no hand-tuned polarity variant", and the TUI auto-adapts `colors` (contrast-clamped foregrounds). Leave them omitted unless the user asks for a tuned light/dark pair.

## Fallback chain example
- `ui_primary`: read only by `hermes_cli/journey.py:37` as `skin.get_color("ui_primary", "") or skin.get_color("banner_title", "#FFD700")`. One of the 44 canonical tokens that no built-in skin defines — safe to add with a value equal to banner_title (runtime output unchanged, contract closed).

## Banner art invariants
- `banner_logo` / `banner_hero` are Rich-markup block scalars (`|`). Their actual color vocabulary = union of all `[#RRGGBB]` tags in both arts (horus: 50 unique colors, 24-bit — not the xterm-256 palette).
- To retune only the `colors:` block against that vocabulary, use `scripts/remap_skin_colors.py`. Never touch the art itself; verify via parsed equivalence (`ndoc["banner_hero"] == doc["banner_hero"]`), not raw-text regex (block-scalar indentation makes raw extraction brittle — a real session lost a debug cycle to exactly this).

## Verification one-liner
```python
import re, pathlib, yaml
h = yaml.safe_load(pathlib.Path("~/.hermes/skins/horus.yaml").expanduser().read_text())
art = h["banner_logo"] + "\n" + h["banner_hero"]
palette = {c.upper() for c in re.findall(r"\[#([0-9A-Fa-f]{6})\]", art)}
assert all(v.lstrip("#").upper() in palette for v in h["colors"].values())
```
Note the `lstrip("#")` — hex values in YAML carry a leading `#`, extracted tags do not; mismatched normalization false-flags every value (real bug this session).
