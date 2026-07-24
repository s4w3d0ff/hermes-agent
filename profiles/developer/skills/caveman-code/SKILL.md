---
name: caveman-code
description: Systematic caveman compression of code docstrings and comments — strip Args/Returns sections, remove articles, abbreviate terms while preserving functional intent.
version: 1.0
created: 2026-06-20
related_skills: [caveman]
---

# Caveman Code — Compress Code Documentation

Apply "caveman ultra" compression to docstrings, comments, and non-computational text across a codebase. Strips verbosity while preserving functional intent.

## Trigger

User asks to compress code comments, docstrings, or documentation to caveman style. Keywords: "caveman", "compress docs", "shrink comments", "ultra brevity", "remove Args/Returns".

## Method

### 1. Count baseline verbosity
Use `execute_code` to scan files for verbose items:
```python
# Count docstrings >60 chars and comments >80 chars
# File: ~/.hermes/<project>/**/*.py
# Threshold: docstring >60 chars, comment >80 chars
```
Save counts for before/after comparison.

### 2. Read files sequentially
Read each file fully (use `read_file` with pagination if large). Track which files need changes.

### 3. Patch systematically by module layer
Group by architectural layer (database → scanner → scripts → main) to maintain context. Use `patch` tool — never `write_file` for targeted changes.

### 4. Compression patterns

**Docstrings:**
- Strip `Args:`, `Returns:`, `Raises:`, `Example:`, `Note:` sections entirely
- Merge remaining description into 1-2 lines
- Remove filler: "The", "A", "An" → drop entirely
- Replace full sentences with phrases: "This function takes X and returns Y" → "Takes X, returns Y"
- Use `→` for arrows, `+` for conjunctions, `#` for number

**Comments:**
- Remove articles: "the image", "a batch", "the database" → "image", "batch", "DB"
- Abbreviate: initialize→init, timestamp→ts, management→mgmt, database→DB
- Drop trailing explanation: "# Set a default last_bulk_update timestamp if not already set" → "# Set default last_bulk_update ts if missing"
- Keep technical precision: don't abbreviate acronyms, variable names, or API terms

**Section headers:**
- Leave untouched unless already caveman — headers are structural, not verbose

### 2b. Large-file pagination
Files over ~10k chars require `limit`/`offset` reads via `read_file`. When the tool reports a partial view (warning about pagination), **re-read the full file** before patching. Patching from a partial view silently corrupts context — `patch` may match text you didn't actually see in its entirety.

### 2c. Exclude SQL DDL from compression
Module-level docstrings containing CREATE TABLE, INSERT, SELECT, or other SQL statements (e.g., `database/models.py`) are code, not documentation. **Never compress these** — they are executable SQL embedded as strings. Compressing them produces broken SQL.

### 5. Verify syntax after every batch
After patching multi-line docstrings, run:
```bash
cd ~/.hermes/<project>
python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ['database/crud.py', 'scanner/matcher.py']]"
```
If syntax error → read the broken file, fix with patch.
Always verify the linter output after each batch — it catches structural corruption before it compounds.

### 6. Count post-compression
Re-run the verbosity count. Target: >50% reduction in verbose docstrings.

## Pitfalls

### Docstring-overwrite breaking function signatures
When replacing multi-line docstrings, never remove the closing `"""` that follows the function signature. Example of what NOT to do:

```python
# BROKEN — removed closing of docstring, breaking the def line
def foo():
    """Compressed docstring."""
    pass  # This is fine

def bar(x, y) -> int:
    """Compressed docstring."""  # ← This is fine

def baz(x, y) -> Optional[dict]:
    """Broken — this docstring replaced the closing line of def baz()"""  # ← BAD
```

If you accidentally delete the `) -> ReturnType:` or close the paren, fix immediately:
```python
# Fix: restore the function signature line
def baz(x, y) -> Optional[dict]:
    """Good docstring."""
```

### Already-concise strings
`patch` returns `"old_string and new_string are identical"` when:
- The string is already caveman-concise
- You already patched it in this session
Safe to skip — not a blocker.

### Duplicate matches
`patch` returns `"Found N matches for old_string"` when the same text appears multiple times. Use more context lines or `replace_all=True`.

### Python syntax validation
After any multi-line docstring replacement, always verify:
```bash
cd ~/.hermes/<project>
python -m py_compile scanner/matcher.py  # or whichever file you just edited
```
If it fails, read the affected file around the error line and patch the broken docstring.

## Reference counts
Track verbosity before/after:
- Before: count verbose docstrings (docstrings >60 chars) and verbose comments (comments >80 chars)
- After: re-count, report reduction percentage
- Target: >50% docstring reduction, >30% comment reduction
