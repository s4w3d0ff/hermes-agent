# MTG Card OCR - Preprocessing (Working Config)

## Core Principle

**DO NOT use Otsu binary thresholding on MTG card text.** Colored card names on colored backgrounds get destroyed - the binary threshold maps subtle contrast to pure black/white, losing the text entirely.

**DO NOT use CLAHE or gamma correction on small crops.** They distort local contrast in a way that Tesseract cannot recover from.

## Working Pipeline

```
1. Pad image with white border (before any other processing)
2. Grayscale
3. Denoise (fastNlMeansDenoising, h=10)
4. Scale 2x (INTER_LINEAR)
5. OCR with PSM 7
```

### Why padding matters

The white border gives Tesseract clean context and prevents edge artifacts from degrading OCR. A 75px header crop padded to 375px, then denoised + 2x = 750px, gives Tesseract enough resolution to read card names reliably.

**Padding must come BEFORE grayscale conversion** - pad the BGR image, then convert.

## Profile Defaults (Working)

```python
header_standard:  pad=150, denoise=10, scale=2x, PSM=7
header_aggressive: pad=200, denoise=15, scale=2x, PSM=7
footer_standard:   pad=150, denoise=10, scale=2x, PSM=7
footer_aggressive: pad=200, denoise=15, scale=2x, PSM=4
```

### Implementation in `apply_profile()`

```python
def apply_profile(image, profile):
    out = image.copy()
    
    # Pad FIRST (before any processing)
    pad = profile.get("border_pad_px", 0)
    if pad > 0:
        out = cv2.copyMakeBorder(out, pad, pad, pad, pad,
                                  cv2.BORDER_CONSTANT, value=[255,255,255])
    
    # Grayscale
    if profile.get("grayscale") and len(out.shape) == 3:
        out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    strength = profile.get("denoise_strength", 0)
    if strength > 0:
        out = cv2.fastNlMeansDenoising(out, h=strength)
    
    # ... NO CLAHE, NO gamma, NO Otsu for small crops ...
    
    # Scale
    scale_factor = profile.get("scale_factor", None)
    if scale_factor:
        out = cv2.resize(out, (0,0), fx=scale_factor, fy=scale_factor,
                         interpolation=cv2.INTER_LINEAR)
    
    return out
```

## Crop Sizing

- Header: top 11% of card height (11.1% for integer rounding)
- Footer: bottom 11% of card height (11.1% from bottom)
- Do NOT increase crop size - the card name bar sits in the top ~11% by design

## Failed Approaches (Don't Revert To These)

| Approach | Why it fails |
|----------|-------------|
| Otsu threshold | Destroys colored text on colored backgrounds |
| CLAHE | Over-amplifies noise in small crops |
| Gamma correction | Shifts contrast in ways Tesseract can't parse |
| Deskew on small crops | Adds artifacts, no skew to correct |
| Increasing crop size | User explicitly says no - 11% is correct |
| PSM 6/8 for name bar | PSM 7 (single text line) is best for card names |

## Debugging Checklist

1. **Full card baseline**: Run Tesseract on full card first. If it works but cropped regions don't → preprocessing or crop height issue.
2. **Check raw OCR**: Empty strings in `raw_ocr` fields mean segmentation/OCR failure before scrubbing even runs.
3. **Verify crop height**: 680px card → 11.1% = 75px header. After padding (150px) = 375px. After 2x scale = 750px. Tesseract needs ~200px minimum; 750px is fine.
4. **Verify padding is white**: Non-white borders (black, gray) confuse Tesseract about image boundaries.

## Source: magidex OCR pipeline fix 2026-06-27
