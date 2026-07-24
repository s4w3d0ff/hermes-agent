# Scryfall API — Quirks & Patterns

## Bulk Data Download

- Endpoint: `https://api.scryfall.com/bulk-data`
- Response is a JSON list of objects. The field is **`download_uri`** (not `download_url`).
- "Default Cards" name is exact match — case sensitive: `"Default Cards"` not `"Default cards"`.
- **Format: JSON array** (not NDJSON/line-delimited). `json.load()` not `for line in f`.
- File may be `.json.gz` but Scryfall returns plain `.json` despite the extension. Check magic bytes (`\x1f\x8b` = gzip) before decompressing.

```python
# Detect format before parsing
with open(path, "rb") as f:
    magic = f.read(2)
if magic == b"\x1f\x8b":
    # gzip NDJSON or JSON array
else:
    # plain JSON array
```

## Rate Limiting

- **10 requests/second max**. Scryfall enforces aggressively.
- Use `time.sleep(1.1)` between API calls to stay safe.
- 429 errors include `details` field with retry advice.
- Bulk download uses `curl -L` (follow redirects).

## Card Object Fields

| Field | Notes |
|---|---|
| `lang` | Language code (`"en"`, `"es"`, `"ja"` etc.) — **not** `language` |
| `image_uris` | Keys: `small`, `normal`, `large`, `png`, `art_crop`, `border_crop` |
| frame | 1993, 1997, 2003, 2015, future — from bulk data only |
| border_color | white, black, gold, silver, yellow, borderless — not border_mode |
| `card_types` | List: `"creature"`, `"sorcery"` etc. Also has `"token"` and `"deal"` |
| `layout` | `"normal"`, `"split"`, `"modal_dfc"`, `"token"`, `"deal"` etc. |

## Language Mismatch Pitfall

Scryfall's `image_uris` point to the card's image which may be in a different language than the DB entry. When downloading test/training data:

1. Fetch card by ID: `GET /cards/{id}`
2. **Always check `lang` field** in API response
3. Skip if `lang != "en"` (or target language)
4. The bulk DB has `language` column but maps to Scryfall's `lang` field

## Card Search

- `/cards/search?where=id:{id}` does not work reliably.
- Use `/cards/{scryfall_id}` directly.

## MTG Frame Region Coordinates

| Region | Fraction of frame height |
|---|---|
| Header (name/cost) | ~2% - 22% |
| Body (text/illustration) | ~22% - 74% |
| Footer (rules/PT) | ~74% - 87% (NOT full bottom) |

Footer is ~13% of frame, not 26%. Old config used `y_end=1.00` which was wrong.

## Common Set Codes

`8ED`, `7ED`, `5DN`, `MRD`, `M10`-`M24`, `CMR`, `STB`, `AFC`, `ELD`, `ZNR`, `WAR`, `THB`, `DOM`, `RNA`, `GRN`, `RIX`, `M22`, `M23`, `M24`, `KHM`, `LIN`, `NEO`, `SNC`, `STX`, `ONE`, `WOE`, `MKM`, `MLD`, `AER`, `AFR`, `SIH`
