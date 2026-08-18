# MTG Card OCR - Architecture Reference

## Overview

Best practices for OCR-based extraction of MTG card data from images. Combines image preprocessing, frame-type-aware segmentation, Tesseract 5 OCR, and fuzzy matching against a local Scryfall oracle-cards database.

## Card Layout - Key Regions

Cards have consistent text regions that vary by frame type. Extract these regions BEFORE OCR to reduce noise.

### Region Names (standard)
| Region | Description | Typical PSM |
|--------|-------------|-------------|
| `name` | Card name (top, above art box) | 10 - single line |
| `artist` | Artist credit (bottom-left of art box) | 7 - single line |
| `collector` | Collector number + set code (bottom) | 7 - single line |
| `copyright` | Copyright text (bottom) | 7 - single line |

### Region Coordinate Fractions (M15 frame, 200x300 ratio)

These are fractional coordinates `(x1, y1, x2, y2)` relative to the card image dimensions.

```python
# M15 frame
name =        (0.08, 0.02, 0.92, 0.12)   # narrow band at top
artist =      (0.05, 0.82, 0.50, 0.88)   # bottom-left quadrant
collector =   (0.05, 0.88, 0.50, 0.94)   # below artist
copyright =   (0.05, 0.94, 0.95, 0.98)   # very bottom strip
```

### Frame Type Adjustments

| Frame | Name Region | Notes |
|-------|-------------|-------|
| `M15` (2015) | `(0.08, 0.02, 0.92, 0.12)` | Standard name band |
| `MODERN` | Same as M15 | Identical layout to M15 |
| `BORDERLESS` | `(0.02, 0.01, 0.98, 0.10)` | Wider name band, extends into art |
| `EXTENDED_ART` | Same as borderless | Art bleeds to edges |
| `OLD` (pre-M10) | `(0.10, 0.05, 0.90, 0.15)` | Wider name band, lower position |
| `SILVER` | `(0.08, 0.02, 0.92, 0.12)` | Same as M15 |
| `GOLD` | `(0.08, 0.02, 0.92, 0.12)` | Same as M15 |
| `DOUBLE_FACED` | `(0.08, 0.02, 0.92, 0.12)` | Same as M15 |
| `UNKNOWN` | `(0.08, 0.02, 0.92, 0.12)` | Fallback to M15 |

## Frame Type Detection

Detect frame type by analyzing image features:

1. **Art bleed detection**: Check top 15% of image for high pixel variance (>5000). If high variance, likely `BORDERLESS` or `EXTENDED_ART`.
2. **Border detection**: Canny edge detection on grayscale. Low dark pixel percentage (<5%) indicates borderless.
3. **Fuzzy match to known**: If detection is ambiguous, use OCR'd name to search Scryfall database, then check `frame` and `border_color` fields.

### Detection Algorithm
```python
def detect_frame_type(image):
    h, w = image.shape[:2]
    # Check art bleed in top region
    top_15 = image[:int(h * 0.15), :]
    variance = np.var(top_15)
    if variance > 5000:
        return FrameType.BORDERLESS
    # Check border darkness
    edges = cv2.Canny(grayscale(image), 50, 150)
    dark_pct = np.sum(edges == 0) / edges.size
    if dark_pct < 0.05:
        return FrameType.BORDERLESS
    return FrameType.M15  # default
```

## OCR Engine Configuration

### Tesseract 5 PSM Settings by Region
| Region | PSM | Rationale |
|--------|-----|-----------|
| `name` | 10 | Single line of text |
| `artist` | 7 | Single line |
| `collector` | 7 | Single line with digits |
| `copyright` | 7 | Single line |
| Full card | 6 | Uniform block of text |

### Whitelist by Region
| Region | Whitelist | Rationale |
|--------|-----------|-----------|
| `collector` | `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-` | Collector numbers |
| `name` | None | Full Unicode for card names |
| `artist` | None | Full Unicode for names |

### Beleren Font
- M15+ cards use the **Beleren** typeface for card names and rules text.
- Beleren is not free (Wizards owns it). For OCR training, generate sample images using system fonts that closely match Beleren's character shapes.
- Training target: `tessdata_best/beleren.traineddata`
- Generate .box files from Scryfall oracle-cards names, render at 300 DPI, run Tesseract box generation.

## Matching Strategy

### Name Matching
- Use `fuzz.token_set_ratio` (NOT `partial_ratio`) for card names.
- `token_set_ratio` handles extra/missing OCR words (e.g. "Zoe" appended), ignores word order.
- `partial_ratio` is wrong for names - "Hero" vs "Vizier of Many Faces" scores 75% via substring match.
- Threshold: 15.0 for `FuzzyMatcher.match_field()`, 60.0 for strategy-based matching.
- Combine all header tokens into one query string, not individual token matching.

### Collector Number Matching
- Use `fuzz.partial_ratio` for collector_number, set_code, artist.
- Expand slash-split tokens before matching (e.g. "074/269" → ["074", "269"]).
- Strip leading zeros after split (e.g. "074" → "74").
- Regex for parsing: `([A-Za-z]{2,6})\s*(\d+[a-z]?)`

### Combined Scoring - How It Works
`combined_confidence` and `combined_similarity` must be computed PER-ROW, not globally:

1. **Strategy fields** (e.g. name+artist): Compare combo value against DB row's actual value for that field. Weight confidence by similarity: `conf * sim / 100`.
2. **Non-strategy OCR datapoints**: Score against ALL DB columns in the row to break ties when strategy fields are identical.
3. **Never compare OCR datapoints against each other** - that produces identical scores for all matching rows.

Key: `StrategyMatcher._query_strategy()` must compare combo values against DB row values, not OCR tokens against other OCR tokens.

### Cross-Field Validation
| Name Match | Collector Match | Set Match | Confidence |
|------------|-----------------|-----------|------------|
| Yes | Yes | Yes | 95-100% |
| Yes | No | Yes | 75-85% |
| Yes | No | No | 60-70% |
| No | Yes | Yes | 70-80% |
| No | Yes | No | 50-60% |
| No | No | No | 0% |

## Preprocessing Chain

Recommended OpenCV preprocessing before OCR:
1. Grayscale conversion
2. Gaussian blur (5x5 kernel)
3. Adaptive threshold (block size=15, C=2)
4. Unsharp mask sharpening (radius=2, amount=1.5)
5. Morphological cleanup (open then close, 3x3 kernel)

## Database Schema (SQLite)

```sql
CREATE TABLE cards (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_lower TEXT NOT NULL,
    set_code TEXT NOT NULL,
    collector_number TEXT NOT NULL,
    rarity TEXT,
    frame TEXT,
    border_color TEXT,
    layout TEXT,
    full_art INTEGER,
    token INTEGER,
    promo INTEGER,
    textless INTEGER
);

CREATE INDEX idx_name_lower ON cards(name_lower);
CREATE INDEX idx_set_code ON cards(set_code);
CREATE INDEX idx_collector_full ON cards(set_code, collector_number);
```

## Pitfalls & Gotchas

1. **Set codes are case-insensitive** - always normalize to uppercase before querying.
2. **pytesseract `image_to_data` returns lists** - `data["conf"]` is a Python list, not numpy array. Use `float(np.mean([float(c) for c in data["conf"] if c > 0]))`.
3. **sqlite3 Row objects** - set `row_factory = sqlite3.Row` to use `dict(row)`.
4. **FrameType as Enum** - must use `from enum import Enum` and `class FrameType(Enum):` for `isinstance()` checks to work.
5. **CardPipeline must call `create_schema()`** - in-memory SQLite databases don't auto-create tables.
6. **CLI subprocess tests** - use `sys.executable` for subprocess python, not bare `"python"`, to stay in venv.
7. **Tesseract may not be installed** - wrap OCR calls in try/except, raise `OCRError` with helpful message if tesseract binary is missing.
8. **Borderless cards have art bleeding into text regions** - use frame detection to select correct coordinate map.

## Reference Data Sources

- Scryfall bulk data: `https://scryfall.com/docs/api/bulk-data`
- Scryfall catalogs: `https://scryfall.com/docs/api/catalogs`
- Oracle cards JSON: `{bulk_data_url}/oracle-cards.json`
- Card frame reference: `https://mtg.wiki/page/Card_frame`
- Collector number reference: `https://mtg.wiki/page/Collector_number`

## OCR Pipeline - Debugging Lessons (2026-06)

- **Header 11% crop too small**: 74px on 680px tall card yields empty Tesseract output. MTG name bar starts ~2-3px from top and occupies ~8-10% of height. Use 2%-13% crop with PSM 6 for better results.
- **PSM 7 fails on tiny regions**: Try PSM 6 (uniform block) or PSM 11 (wide line) when PSM 7 returns empty.
- **Full card baseline test**: Always run Tesseract on the full card first as a baseline. If full card OCR works but cropped regions don't, the issue is region height or PSM mismatch.
- **Color-based mask extraction**: White text on colored background can be extracted via HSV range mask (`lower=[0,0,150], upper=[180,50,255]`), then scaled 3-4x before OCR.
- **Footer OCR quality**: Garbled footer text (e.g., "7 uti Da x y" for a 75px region) means the footer crop is too small. MTG footer region is ~13% of card height but starts at ~88% (not 89%), so actual text area is ~8%-9% of height.
- **Benchmark pattern**: Run `benchmark.py --count N` to validate pipeline changes. Check `raw_ocr` fields in output JSON - empty strings indicate segmentation/OCR failures before scrubbing even runs.
