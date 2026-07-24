# Schema Unification — Aligning Local DB with API Naming

## Problem

Local databases often accumulate legacy column names that diverge from the external API's field names. Common in MTG projects:
- `frame_status` (legacy) vs `frame` (Scryfall API)
- `border_mode` (legacy) vs `border_color` (Scryfall API)

Legacy columns are often empty or inconsistent, causing silent data loss.

## Detection

```python
import sqlite3
conn = sqlite3.connect("data/card_db.sqlite")

# 1. Find ALL columns
cols = [r[1] for r in conn.execute("PRAGMA table_info(cards)").fetchall()]

# 2. Check for both old and new names
has_old = any(k in cols for k in ["frame_status", "border_mode"])
has_new = any(k in cols for k in ["frame", "border_color"])

# 3. Verify data is populated in new columns, not old
empty_old = conn.execute("SELECT COUNT(*) FROM cards WHERE frame_status IS NOT NULL AND frame_status != ''").fetchone()[0]
filled_new = conn.execute("SELECT COUNT(*) FROM cards WHERE frame IS NOT NULL AND frame != ''").fetchone()[0]

print(f"Legacy column populated: {empty_old}, New column populated: {filled_new}")
# If legacy=0 and new>0 → safe to drop legacy
```

## Fix Steps

1. **Drop empty legacy columns:**
   ```sql
   ALTER TABLE cards DROP COLUMN frame_status;
   ```

2. **Rename columns to match API:**
   ```sql
   ALTER TABLE cards RENAME COLUMN border_mode TO border_color;
   ```

3. **Update all code references** (search-and-replace across entire codebase):
   - SQL queries: `border_mode` → `border_color`, `frame_status` → `frame`
   - Dict keys in metadata JSON
   - Column lists in SELECT/INSERT statements

4. **Verify no remaining references:**
   ```bash
   grep -r "frame_status\|border_mode" --include="*.py" --include="*.json" .
   ```

## Prevention

Always use Scryfall API field names directly in local schema:
- `frame` (not `frame_status`)
- `border_color` (not `border_mode`)
- `lang` → store as `language` in DB (add note about mapping)
- `set` → store as `set_code` in DB (more descriptive)

## Bulk Data vs Individual API

| Field | Bulk Data | Individual API | Notes |
|---|---|---|---|
| `frame` | YES | NO | Must store in DB from bulk data |
| `frame_status` | Always empty | Populated | Legacy, ignore |
| `border_color` | YES | YES | Use directly |
| `lang` | YES | YES | Map to `language` in DB |
| `set` | YES | YES | Map to `set_code` in DB |

The individual card API (`GET /cards/{id}`) does NOT return `frame`. Always use the DB-stored value when generating metadata.