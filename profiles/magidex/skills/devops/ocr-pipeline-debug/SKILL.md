---
name: ocr-pipeline-debug
description: >
  Debugging and fixing issues in OCR-based text recognition pipelines.
  Covers similarity scoring pitfalls, tokenization bugs, benchmark analysis,
  and performance tuning for Tesseract-based card/text recognition systems.
version: 1.0.0
author: Centaur
license: MIT
platforms: [linux, macos, windows]
tags: [OCR, Debugging, Similarity Scoring, Tokenization, Benchmarking]
---

# OCR Pipeline Debug

Debug and fix issues in OCR pipelines — Tesseract-based text recognition,
scoring anomalies, tokenization bugs, benchmark regressions.

## When to Use

- Datapoint similarity scores are uniformly high (all 100%) when they should differ
- Fuzzy matching returns wrong candidates ranked first
- Benchmark accuracy dropped after a scoring change
- Pipeline performance exceeds target (>2s per card)
- OCR results produce false positives that drown correct matches

## Scoring Pitfalls

### SUBSTRING MATCHING GIVES FALSE 100% SCORES

```python
# BAD: t in val.lower() — "ill" in "Illustrator" = 100%
if t in val.lower():  # substring check
    score = 100.0
```

Any token contained as a substring of a DB value gets 100%. Fix: use `rfuzz.ratio()` which penalizes when the search string is a subset of a longer value:

```python
ratio = rfuzz.ratio(search_lower, val.lower())
# "knight" vs "Attended Knight" → 57% (not 100%)
# "hill giant" vs "Hill Giant" → 100% (exact match)
# "dan frazier" vs "Dan Frazier" → 100% (exact match)
```

`ratio()` requires proportional overlap. Single-token matches in long values score low. Exact or near-exact multi-token matches score high.

### partial_ratio ALSO GIVES FALSE 100%

```python
rfuzz.partial_ratio("knight", "Attended Knight")  # 100%!
rfuzz.partial_ratio("ill", "Illustrator")  # 100%!
```

`partial_ratio` returns 100% whenever the shorter string is entirely contained in the longer one. Same bug as substring matching. DO NOT USE for scoring.

### token_set_ratio IGNORES EXTRA WORDS

```python
rfuzz.token_set_ratio("knight", "Attended Knight")  # 100%!
```

Token-based variants ignore extra tokens entirely. BAD for OCR where the DB value has many words but search only captures one.

### BEST SCORING: rapidfuzz.ratio()

```python
def _score_matches(rows: list, search: str) -> dict:
    search_lower = search.lower()
    results = {}
    for row in rows:
        val = row[0]
        ratio = rfuzz.ratio(search_lower, val.lower())
        if ratio >= 45:
            results[val] = round(ratio, 1)
    return results
```

ratio() is the correct default. Penalizes subsets naturally. Garbled OCR still matches via shared character n-grams.

### MAX-SCORE MERGING INSTEAD OF UPDATE()

When consolidating results from multiple profiles/OCR tokens, do NOT use `dict.update()` — it overwrites higher scores with lower ones:

```python
# BAD: later entry (58.3) overwrites earlier (100.0)
all_results.update({"Dan Frazier": 58.3})  # was 100.0

# GOOD: keep max
if match_val not in all_results or match_score > all_results[match_val]:
    all_results[match_val] = match_score
```

This applies at two levels: consolidate_datapoints() and match_cards global_candidates().

### CONSOLIDATE DEDUP BY MATCH_VALUE, NOT OCR_TOKEN

Consolidate by (dp_type, match_value) across all OCR tokens — not by (dp_type, ocr_token). Different OCR tokens from different profiles may find the same DB value. They should merge into ONE entry with merged profiles and max score:

```python
# Phase 1: merge by (dp_type, ocr_token) across profiles
merged[dp_type, ocr_token] = {profiles, results}

# Phase 2: deduplicate by (dp_type, match_value) across OCR tokens
value_map[dp_type, match_val] = merged_profiles + max_scores

# Phase 3: output grouped by dp_type
output[dp_type].append(entry)
```

### REMOVE SCORE THRESHOLDS BEFORE DB QUERY

DO NOT apply min_score_threshold or min_score filters before building database queries. These truncate valid datapoints that would find correct matches. Let the combined_similarity sort order handle ranking:

```python
# BAD: truncates all candidates below 40
qualified = [(v, s) for v, s in sorted_results if s >= 40]

# GOOD: keep ALL, sort later by combined_similarity
global_candidates[dp_type] = [{"value": v, "score": s} for v, s in sorted_results]

# BAD: discards combos below 45
if min_score >= 45:
    combos.append(best_per_field)

# GOOD: accept all combos, let DB + combined_similarity sort decide
combos.append(best_per_field)
```

### NO HARD CAPS ON CANDIDATES BEFORE COMBO BUILDING

DO NOT cap candidate counts before building search combos. SQLite handles massive batched OR queries fine within performance targets. Remove `[:n_top]` slices on global_candidates and `[:10]` slices on candidate_lists for combos.

## Debug Workflow

1. **Read** the full pipeline code — every file that touches scoring
2. **Check** benchmark output for uniform high scores (all 100%)
3. **Trace** one failing card through: raw OCR → scrubbed tokens → search string → DB query → score
4. **Verify** the similarity function is comparing apples to apples
5. **Commit** before benchmarking — each commit is a checkpoint
6. **Count false 100%** scores across all failed cards — if >0, scoring still wrong

## Performance Targets

- Average time per card: <2s (95% accuracy across test cards)
- Never scale images above 10x — serious performance impact
- Batch DB queries in chunks of 50-100 to avoid SQLite parameter limits
- Use ThreadPoolExecutor for parallel OCR profiles

## Benchmark Analysis

When benchmarking, check:
- `avg_time_per_card` stays under 2s
- `found` count matches expected accuracy target
- `top_potential_datapoints` similarity scores actually differentiate candidates
- Matching results sorted by combined_similarity descending
- Zero false 100% scores in failed cards (search token matches unrelated card name at 100%)