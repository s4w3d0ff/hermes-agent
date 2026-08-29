---
name: surgical-config-edit
description: Use when patching one section of a config file in place.
---

# Surgical Config Edits with Invariant Proof

Class task: change one section / key-set of a structured file — often under a value constraint ("only use values from set X") — while everything else stays untouched. Instances: retuning the `colors:` block of a Hermes skin to its banner art's palette, editing one key group in config.yaml, patching a generated manifest.

## When to use
- User asks for "change ONLY section X" / "keep everything else identical".
- Values are constrained to an existing set (color palettes, enums, allowlists).
- The file has large verbatim regions that must not be touched (YAML block scalars `|`, embedded ASCII art/markup).

## Procedure
1. **Parse first; never regex raw text.** Load with `yaml.safe_load` / `tomllib`. Do NOT extract block scalars from the raw YAML string — indentation and `|` headers make it brittle. Compare PARSED values before/after for regions you must not touch.
2. **Derive the source of truth deterministically.** Example: palette = union of all hex tags in referenced art, `set(re.findall(r'\[#([0-9A-Fa-f]{6})\]', art))`.
3. **Compute the mapping with no unrequested heuristics.** If the user gave a strict constraint ("only values from set S"), use plain nearest-match (squared RGB distance for colors). Do NOT inject overrides, contrast guards, or aesthetic fixes the user didn't ask for — if an exception seems warranted, say so in your reply instead of silently applying it.
4. **Apply via unique-fragment replacement.** For each key: `frag = f'{key}: "{old}"'`; assert `text.count(frag) == 1`, then single `.replace()`. This preserves every other byte — no full-file rewrite and NEVER a YAML re-dump (a dump would reorder keys, change quoting style, and destroy block-scalar formatting).
5. **Keep rollback artifacts.** `shutil.copyfile(path, path + '.bak')` before writing; save the diff to `<stem>.diff`.

## Verification (run it — do not skip)
- Every new value is in the source set: `assert v.upper() in palette_set` for every mapped key. A broken distance function silently produces wrong mappings; membership is the cheap catch.
- Diff audit with `difflib.unified_diff`: exactly N changed lines == number of keys touched, and each removed/added line matches the expected key-line pattern (e.g. `\s*[a-z_]+: "#[0-9A-F]{6}"`). Any extra line = collateral edit; abort BEFORE writing.
- Parsed equivalence for untouched sections: `ndoc[key] == doc[key]` for every top-level section you did not touch (banner art, spinner lists, ...).
- All assertions pass before the file is written; on failure restore from `.bak` and fix.

## Schema completeness check (after value edits)
Value-constrained edits often carry a second invariant: the block must cover the schema's full canonical key set. Missing keys rarely error — they silently inherit fallbacks — so audit coverage after editing, not just values:
- Find the authoritative contract where it lives, not in prose docs. For Hermes skins: `SKIN_COLOR_TOKENS` in `apps/shared/src/skin.ts` (44 tokens) is canonical; the `skin_engine.py` docstring lists only a subset. User colors merge over the built-in `default` skin, so absent keys fall back silently instead of failing.
- Cross-check with actual reader call sites (`grep -rhoE 'get_color\("[a-z_]+"|_skin_color\("[a-z_]+"' hermes_cli/`) to see which keys are really consumed and what their fallbacks resolve to before deciding a missing key matters.
- Leave genuinely optional blocks omitted (e.g. skin `light_colors`/`dark_colors` — the TUI auto-adapts polarity) unless hand-tuning; adding them means inventing values that were not requested.

Hermes-skin specifics: `references/hermes-skin-contract.md`.

## Pitfalls
- **yaml.dump to "apply" edits** — destroys key order, quoting style, block scalars. Never for surgical edits.
- **Regexing `key: value` lines across the whole file** when a fragment could appear in multiple sections. The count==1 assertion catches it; if count>1, scope the replacement to that section's line range instead.
- **Stalling on research.** If the spec is mechanical ("remap X under constraint Y"), go straight to an asserting script and run it. Do not add judgment calls — user frustration with overthinking is a known signal in this class of task (a real session here ended with "DO I NEED TO SPELL IT OUT ANY FURTHER?").
- Python hex parsing: `int(h[i:i+2], 16)` per channel; validate input format before lookup (a malformed token must fail loudly, not map to a wrong color).

## Reference implementation
`scripts/remap_skin_colors.py` — retunes any Hermes skin's `colors:` block to the union palette of its `banner_logo` + `banner_hero` art, with all invariants above baked in. Run: `python3 remap_skin_colors.py <skin.yaml> [--dry-run]`. Keeps `.bak` and `.diff` artifacts next to the file.
