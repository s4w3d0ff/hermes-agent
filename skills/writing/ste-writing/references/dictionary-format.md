# Dictionary file formats (JSONL, one entry per line)

Source folder: `~/Projects/asd-ste100-issue9/`. Copies are shipped in this skill's `dictionaries/` so the linter is self-contained. The PDF is the source of truth; these files encode its Part 2 dictionary.

## asdste100_issue9_base.jsonl — primary controlled vocabulary (2,200 entries)
Schema (field -> meaning):
- `name`: headword or multi-word unit, UPPERCASE when approved, lowercase when rejected (multi-word units like "according to", "turn off" exist).
- `status`: `approved` | `rejected`. 881 approved / 1319 rejected.
- `type_`: part of speech — v (verb), adj, n, adv, prep, conj, pron, art, prefix. Conflicts are normal: the same spelling may appear in both statuses under different types (e.g. "test": approved as n, its verb use is what's flagged).
- `meanings`: list of `{value (approved meaning text), ste_example [strings], nonste_example [strings], note}` — empty for rejected entries whose alternatives carry the examples.
- `spellings`: UPPERCASE inflected forms approved for verbs (REMOVES, REMOVED) and comparative/superlative adjectives (SLOWER, SLOWEST). The linter treats these as permitted surface forms of the headword.
- `alternatives`: list of replacement entries with the SAME schema shape `{name, status, type_, meanings, spellings, alternatives, ste_example, nonste_example, note}` — approved substitutes for rejected words; multi-word alternatives (e.g. "MAKE SURE") appear here too.
- `source`, `category`: provenance tags ("STE100:9").

## asdste100_issue9_base_names_lower.jsonl — same 2,200 entries, names lower-cased. Convenient for direct token lookups (case-folded).

## asdste100_issue9_base_v0.5.1.jsonl — earlier export of the base dictionary (832K vs 1.2M): fewer fields per entry (`name`, `type_`, `status`, `meanings` with ste_example only, no spellings/alternatives). Kept for diffing; prefer `_base.jsonl`.

## asdste100_issue9_technical_words.jsonl — technical noun/verb allowance (779 entries)
Fields: `{name (may be multi-word, case-mixed), status: approved, type_: TN | TV, source, category (TN2/TN3.../TV2... pointing at PDF TN/TV categories), note}`. These are the technical-noun / technical-verb classes of Rule 1.5–1.6 — words NOT in the base dictionary that ARE allowed when used as a noun or verb respectively. Includes multi-word phrases ("abort button", "Acceptance Test").

## Precedence the linter uses
1. Token matches a `technical_words` name (case-insensitive, incl. whole phrase) -> allowed.
2. Else token in base dictionary: status approved AND type fits usage context -> OK; rejected -> flag with its alternatives listed as suggestions.
3. Approved surface forms (`spellings`) are OK for their headword.
4. Unknown word -> "possible technical noun/verb?" review note (Rules 1.5/1.6), not an error, unless flagged by --strict-unknown.

POS heuristics (approximate — the linter is lexical, see caveats in scripts/lint.py):
- verb slot: sentence start (imperative), after modals/auxiliaries, "-s" third-person suffix at clause end; flag if word approved only as non-verb and used there.
- adjective slot: before a noun or after a linking verb.
- Errors are reported with rule id (R1xx) so `--allow` can suppress known noise.
