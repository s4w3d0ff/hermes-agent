# Scryfall Bulk Data - Download & Parsing Quirks

## download_uri (NOT downloads_uri)

The bulk data response object from `GET /bulk-data/{type}` uses **singular** `download_uri`, not `downloads_uri`:

```python
# WRONG
url = data["downloads_uri"]  # KeyError

# CORRECT
url = data["download_uri"]
```

## File Format: Check Magic Bytes

Scryfall bulk data may be plain JSON or gzip-compressed. Check before decompressing:

```python
import urllib.request, gzip

with urllib.request.urlopen(url, timeout=300) as resp:
    raw = resp.read()
    if raw[:2] == b'\x1f\x8b':  # gzip magic bytes
        json_data = gzip.decompress(raw).decode("utf-8")
    else:
        json_data = raw.decode("utf-8")
```

## `set` Field: String, Not Object

In bulk data, `card["set"]` is the set code as a **string**, not a nested object:

```python
# Bulk data structure:
# {"set": "2ed", "set_name": "Classic Sixth Edition", ...}

# WRONG - assumes object:
set_code = card.get("set", {}).get("code", "")  # Returns "" for bulk data

# CORRECT - handle both forms:
set_code = (card["set"] if isinstance(card["set"], str) 
            else card["set"].get("code", ""))
```

## Boolean Fields Return None

Many boolean fields on individual cards are `null` in bulk data, not `False`:

```python
# WRONG - None doesn't cast to int:
int(card.get("token", False))  # Works but confusing

# CORRECT - explicit truthiness:
1 if card.get("token") else 0
```

## updated_at Is Null

Bulk data cards have `"updated_at": null`. Do not use for freshness checks:

```python
# WRONG - None breaks datetime parsing
updated = datetime.fromisoformat(card["updated_at"])

# Use file modification time instead
import os
mtime = os.path.getmtime("bulk-data.json")
```

## Card Name Search: SQL LIKE Is Insufficient

`LIKE "%lightning%"` won't match typos like "Lightnin Bolt". Use Levenshtein fallback:

```python
# Step 1: Fast SQL LIKE for prefix/substring
# Step 2: Levenshtein.ratio on LIKE results (threshold >= 0.7)
# Step 3: If LIKE returns nothing, search by first word + Levenshtein
```

## frame vs frame_status - Frame Era Classification

Bulk data has **`frame`** (e.g., "2015", "2003", "1993", "1997", "future") but **`frame_status`** is always empty in bulk downloads. Use `frame` for card frame era classification.

```python
# WRONG - frame_status is always "" in bulk data:
card["frame_status"]  # Always empty

# CORRECT - use frame field:
card["frame"]  # "2015", "2003", "1993", "1997", "future", "custom"

# For DB schema, store both but rely on frame:
# frame_status = obj.get("frame_status", "")  # Always ""
# frame = obj.get("frame", "")  # Actual value
```

**Common frame values in bulk data:**
- `"1993"` - Alpha through Urza's Saga (pre-8th ed)
- `"1997"` - 4th Edition through 7th Edition
- `"2003"` - Mirrodin through 8th Edition (8th ed frame)
- `"2015"` - M10 through M15 (Beleren frame)
- `"future"` - Future-bordered (1997–2002)

**Migration tip**: If your DB schema already has `frame_status` but no `frame` column, add `frame` and backfill from bulk data by matching `scryfall_id`. Use batched `UPDATE ... WHERE scryfall_id = ?` in groups of ~10K.
