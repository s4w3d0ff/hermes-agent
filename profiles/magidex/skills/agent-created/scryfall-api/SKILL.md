---
name: scryfall-api
description: >-
  Scryfall MTG API patterns, quirks, and reference data. Covers bulk data download,
  rate limiting, card object fields, and language validation. Essential for building
  card databases and test datasets.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mtg, scryfall, api, card-database, bulk-data]
---

# Scryfall API Skill

## Overview

Patterns and quirks for interacting with the Scryfall MTG API. Covers bulk data
download, rate limiting, field mapping, and language validation pitfalls.

## Quick Reference

- **Bulk data**: `https://api.scryfall.com/bulk-data` → field is `download_uri`
- **Single card**: `GET /cards/{id}` — use `/cards/search` is unreliable
- **Rate limit**: 10 req/s max, use `sleep(1.1)` between calls
- **Language field**: `lang` in API, stored as `language` in DB
- **Bulk format**: JSON array (not NDJSON), check magic bytes before gzip
- **Frame field**: Use `frame` from bulk data for card frame era (not `frame_status` — always empty)

## Pitfalls

1. **Language mismatch**: `image_uris` may point to non-English images even when DB says `language='en'`. Always validate `card_data.get("lang")` in API response.
2. **Bulk format**: Scryfall bulk data is a JSON array, not line-delimited. Check magic bytes for gzip before decompressing.
3. **Rate limiting**: Enforced aggressively. 429 errors include retry advice. Use curl for downloads.
4. **frame vs frame_status**: Scryfall bulk data has `frame` (e.g., "2015", "2003", "1993", "1997", "future") but `frame_status` is always empty. Use `frame` for card frame era classification. `frame_status` is only populated via the individual card API endpoint, not in bulk data.
5. **Individual API doesn't return `frame`**: `GET /cards/{id}` does NOT include the `frame` field. Must use the value stored in the local DB from bulk data when saving card metadata.
6. **border_color naming**: Scryfall uses `border_color` (not `border_mode`). DB columns, JSON metadata, and API queries must all use `border_color` to match.

## Support Files
- references/sqlite-database-quirks.md — DB schema quirks (rowid vs id TEXT), FTS5 triggers (use new.rowid, not new.id), rapidfuzz unpacking (value, score, _), ijson binary mode, FTS5 special char escaping, INSERT OR REPLACE semantics
- references/mtg-ocr-architecture.md — Card layout, frame types, Tesseract PSM settings, matching strategy
- references/mtg-ocr-preprocessing.md — **Working preprocessing pipeline**: white padding + denoise + scale 2x. DO NOT use Otsu/CLAHE/gamma on small crops.
- references/schema-unification.md — DB schema alignment pattern: detect legacy columns, drop/rename to match API names, verify no remaining references.

## OCR Pipeline — Preprocessing

**DO NOT use Otsu binary thresholding on MTG card text.** Colored card names on colored backgrounds get destroyed — the binary threshold maps subtle contrast to pure black/white, losing the text entirely.

**DO NOT use CLAHE or gamma correction on small crops.** They distort local contrast in a way that Tesseract cannot recover from.

**Working pipeline:**
```
1. Pad image with white border (150px header, 200px aggressive)
2. Grayscale
3. Denoise (fastNlMeansDenoising, h=10)
4. Scale 2x (INTER_LINEAR)
5. OCR with PSM 7
```

Key insight: **padding must come BEFORE grayscale conversion.** A 75px header crop padded to 375px, denoised + 2x = 750px, gives Tesseract enough resolution.

**Profile defaults (working):**
```
header_standard:  pad=150, denoise=10, scale=2x, PSM=7
header_aggressive: pad=200, denoise=15, scale=2x, PSM=7
footer_standard:   pad=150, denoise=10, scale=2x, PSM=7
footer_aggressive: pad=200, denoise=15, scale=2x, PSM=4
```

Crop size: 11% from top for header, 11% from bottom for footer. This is correct — do not increase.

## OCR Pipeline — Fuzzy Matching Scorer Selection

**Choose scorer by field type — wrong scorer causes false positives.**

| Field | Scorer | Threshold | Why |
|-------|--------|-----------|-----|
| `name` | `fuzz.token_set_ratio` | — | Handles extra/missing OCR words ("Vizier of Many Faces Zoe" → DB "Vizier of Many Faces" = 100%). Ignores word order. |
| `collector_number` | `_cn_similarity()` | ≥ min_score | Structural: exact match (100%) or prefix match (80%). NO fuzzy fallback. Only use first segment of slash-split CNs ("074/269" → "074" only, not "269" which is total count). Strip leading zeros. |
| `set_code` | `fuzz.token_set_ratio` | ≥ 80% | Short codes — `token_set_ratio` prevents "akh" matching "akm" at 67%. Classifier in `match_all()` uses `token_set_ratio` ≥ 80% to classify tokens into set_code. |
| `artist` | `fuzz.token_set_ratio` | — | Avoids substring false positives — "ryan" matching "ryan pancoast" at 100% with `partial_ratio`. `token_set_ratio` excludes unshared terms. |

**Classifier (match_all):** Footer tokens classified by fuzzy-matching against actual DB values, NOT regex patterns. Regex `^[A-Z]{2,4}$` classifies "EN" and "YEE" as set_codes when they aren't. Use `token_set_ratio` against DB set_codes with threshold ≥ 80%.

**Key pitfalls:**
- `partial_ratio` on card names → false positives ("Hero" vs "Vizier of Many Faces" = 75%). Use `token_set_ratio`.
- `partial_ratio` on artist names → "ryan" matches "ryan pancoast" at 100%. Use `token_set_ratio`.
- `_cn_similarity` must NOT fall back to `partial_ratio` — it turns "074" into a substring match of "0" at 100%. Use exact/prefix only.
- Slash-split CNs: only first segment is the collector position. "074/269" → "074", discard "269" (total count).

**Benchmark wiring:** `matching_strategies_used` = `{strategy_name: actual_DB_row_count}` — count unique rows returned by each strategy's query, NOT the number of query parameter combos. Count via:
```python
matched_rows = set()
for m in matches:
    matched_rows.add(f"{m['name']}|{m['set_code']}|{m['collector_number']}")
strategies_used[strategy_name] = len(matched_rows)
```
Multi-field AND strategies return fewer rows than single-field strategies — this is correct. Wire it: `matches, strategies_used = matcher.match_with_counts(...)` → return in `process_card()`. Never hardcode `{}`.

## Benchmark Output Format — Known Drifts

- `scrubbed_ocr` = `{"header": list[str], "footer": list[str]}` — the cleaned token arrays from `scrub_tokens()`, NOT fuzzy match results.
- `top_scrubs` = `{"field": [{"value": str, "similarity": float, "confidence": float}]}` — fuzzy match results per field, truncated to top_k.
- `matching_strategies_used` = `{strategy_name: actual_unique_DB_rows_matched}` — count of distinct DB rows returned by each strategy's query. NOT the number of query parameter combos. Count via unique (name|set_code|collector_number) tuples. Multi-field AND strategies return fewer rows than single-field — this is correct behavior. Wire: `matches, strategies_used = matcher.match_with_counts(...)` → return in `process_card()`. Never hardcode `{}`.
- Benchmark `card` field = `jpeg_path.name` (e.g., "card1.jpeg"), NOT the card name. Card name is in `ground_truth.card_name`.
- `total_generated_fuzz` accumulates across ALL cards. A bug that resets it inside the card loop reports only the last card's count.
- Field names must be consistent: `set_code` (DB column) not `set`. Mismatch between `results["set"]` and `STRATEGIES` referencing `set_code` causes zero strategies to match → empty `matching_strategies_used`.
- FTS5 query terms must strip ALL non-alphanumeric characters. Minimal escape (removing only `:`, `"`, `(`, `)`, `&`) leaves chars like `/`, `,`, `'` that cause FTS5 syntax errors. Use `re.sub(r'[^a-zA-Z0-9]', '', text)`.

## Cross-Reference

For DB schema, bulk data parsing, and test card generation — use **`scryfall-data`** skill instead.
