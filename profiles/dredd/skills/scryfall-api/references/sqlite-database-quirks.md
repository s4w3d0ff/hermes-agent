# SQLite Database - MTG OCR Quirks

## Schema: id TEXT vs rowid INTEGER

When an FTS5 virtual table exists with triggers referencing `new.id`, using `id TEXT PRIMARY KEY` fails because the PRIMARY KEY becomes a rowid alias (TEXT), but FTS5 rowid expects INTEGER.

**Fix**: Use explicit `rowid INTEGER PRIMARY KEY AUTOINCREMENT` + `id TEXT NOT NULL UNIQUE`:

```sql
CREATE TABLE cards (
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    -- ...
);
```

## FTS5 Trigger Syntax

FTS5 triggers must use `new.rowid` / `old.rowid` - NOT `new.id` / `old.id`:

```sql
CREATE TRIGGER cards_fts_insert AFTER INSERT ON cards BEGIN
    INSERT INTO cards_fts(rowid, name, artist, collector_number, set_code)
    VALUES (new.rowid, new.name, new.artist, new.collector_number, new.set_code);
END;
```

Using `new.id` (TEXT) causes `datatype mismatch` on INSERT.

## SQL Reserved Keyword: `set`

SQLite treats `set` as a reserved keyword. In FTS5 column lists, use `set_code` or quote with double-quotes `"set"` (NOT brackets `[set]`):

```sql
-- WRONG
CREATE VIRTUAL TABLE cards_fts USING fts5(name, artist, collector_number, [set]);

-- CORRECT
CREATE VIRTUAL TABLE cards_fts USING fts5(name, artist, collector_number, set_code);
```

In triggers, column references use plain `new.set_code` / `old.set_code`.

## Bulk Data: Boolean Fields

Scryfall bulk data returns booleans (`true`/`false`) for fields like `highres_image`, `digital`, `full_art`, `promo`, `textless`, `reprint`, `variation`. These must be cast to `str()` or `int()` before DB insertion.

```python
def _int(v):
    return int(v) if v is not None else None
def _text(v):
    return str(v) if v is not None else None
```

## ijson: Binary Mode Required

The `ijson` C backend requires a binary file handle. If the file is opened in text mode, re-open in binary:

```python
if hasattr(fh, 'mode') and 'b' not in fh.mode:
    fh = open(file_handle.name, 'rb')
```

## rapidfuzz: process.extract Return Format

`process.extract()` returns `(value, score, match_info)` tuples - NOT `(score, value)`. The score is a float string (e.g., `'100.0'`), not an int. Always unpack as `(value, score, _)` and cast to `float()`.

```python
# WRONG
for score, value in matches:  # ValueError: too many values to unpack

# CORRECT
for value, score, _ in matches:
    if float(score) >= min_score:
        ...
```

## FTS5 Query Special Characters

FTS5 `MATCH` queries break on special characters: `&`, `"`, `(`, `)`, `OR`, `AND`, `:`. Escape or strip them:

```python
escaped = value.replace('&', '').replace('"', '').replace('(', '').replace(')', '')
escaped = re.sub(r'\b(OR|AND)\b', '', escaped, flags=re.IGNORECASE)
```

## INSERT OR REPLACE vs INSERT OR IGNORE

With `rowid INTEGER PRIMARY KEY AUTOINCREMENT` + `id TEXT UNIQUE`, use `INSERT OR REPLACE` (not `IGNORE`) to allow upserts on duplicate `id` values.

## Trigger Semicolon Splitting

Triggers contain semicolons inside `BEGIN...END` blocks. Do NOT split trigger SQL by `;`. Parse by `BEGIN`/`END` blocks instead.

## Bulk Insert Error Handling

Batch-level `executemany` failures swallow individual row errors. Use row-level `try/except` inside the batch loop for proper error isolation:

```python
for row in batch:
    try:
        cur.execute(INSERT, row)
    except Exception:
        # skip bad row, continue
        pass
```
