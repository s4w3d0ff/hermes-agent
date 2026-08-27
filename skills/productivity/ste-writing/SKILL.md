---
name: ste-writing
description: Write or check text against ASD-STE100 technical English.
version: 0.0.1
author: [s4w3d0ff, hermes]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ste, simplified technical english, writing, technical writing, docs]
---
---

# STE Writing (ASD-STE100 Simplified Technical English, Issue 9)

Source of truth: `~/Projects/asd-ste100-issue9/ASD-STE100 Simplified Technical English - ASD-STE100_ISSUE9.pdf`. This skill distills Part 1 (writing rules) into the files below; the JSONL dictionaries from that folder ship in `dictionaries/` and drive the linter.

## Files
- SKILL.md - this rule cheat-sheet + linter usage
- references/rules.md - full rule texts of all 9 sections, with PDF examples
- references/examples.md - real Non-STE -> STE replacements (dictionary pairs + section examples)
- references/dictionary-format.md - JSONL schema for the four dictionary files
- scripts/lint.py - Python linter (stdlib only), checks text against the dictionaries
- dictionaries/ - asdste100_issue9_base.jsonl, _base_names_lower.jsonl, _base_v0.5.1.jsonl, _technical_words.jsonl

## Linter (run first when checking prose)

    python3 scripts/lint.py file.md                     # errors + warnings
    python3 scripts/lint.py - < worksteps.txt           # stdin; line numbers restart at 1 per input
    python3 scripts/lint.py --procedural worksteps.md   # stricter 20-word limit
    python3 scripts/lint.py --json out.json docs/*.md   # machine-readable, exit 0/1

Options: `--dicts-dir DIR` (default: this skill's dictionaries/), `--max-words N` (overrides the type default; use `--procedural` for the STE 20-word work-step limit), `--allow R101,R402,...`, `--exempt-file FILE` (`RULEID LINE` per line suppresses that rule on one line of its file).

## Core rules (condensed) - full text in references/rules.md

**Section 1 Words.** 1.1 Use only: dictionary-approved words, technical nouns, technical verbs. 1.2 An approved word is valid ONLY in its specified part of speech ("test" noun yes / verb no -> "Do a test of..."). 1.3 Only the approved meaning ("follow" = come/go after; obey instructions). 1.4 Only dictionary-listed verb/adjective forms. 1.5-1.10 Technical nouns: allowed if they fit one of the 22 categories (parts, vehicles/machines & locations on them, materials, dimensions, fluids/gases, electrical terms...); short, unambiguous, no slang/jargon/regionals; ONE name per item. 1.12-1.13 Technical verbs allowed but never as nouns. 1.14 American spelling.

**Section 2 Multi-word nouns.** Max THREE words (head noun last; >3 words is ambiguous). Longer: write in full once, then give a shorter form or hyphenate the unit; or restructure with prepositions ("Install the terminal tags on the forward overheat thermocouple of the turbine." not "...overheat thermocouple terminal tags.").

**Section 3 Verbs.** Only these forms/tenses: infinitive, imperative, simple present, simple past, simple future (+ past participle ONLY as an adjective). No auxiliaries (no be/have/can/must + -ed/-ing): "The seat is to be installed" -> "Install the seat."; "has adjusted" -> "adjusted"; "can be adjusted" -> "You can adjust...". The "-ing" form only inside technical nouns ("the door operating rod"), never as a verb. Active voice; passive in descriptive text only when agent unknown. Prefer a direct approved verb over nominalization: not "gives an indication of 450 ohms", WRITE "shows 450 ohms".

**Section 4 Sentences.** Short, clear. No contractions, no omitted words (no "don't"; keep the full form). Vertical lists for complex text; connecting words/phrases between related sentences; article (the/a/an) or demonstrative (this/these) before a noun when applicable.

**Section 5 Procedural writing.** Max 20 WORDS per sentence, ONE instruction per sentence, imperative ("Remove the bolt."). If a condition must be known first: descriptive statement + comma + command. Notes give information, not instructions.

**Section 6 Descriptive writing.** Max 25 words/sentence; one subject per sentence, one topic per paragraph, max six sentences/paragraph; key terms for structure. No imperative here (except quoted text).

**Section 7 Safety.** Label the risk level: WARNING = injury or death; CAUTION = damage to objects. Open with a clear command or condition, then give the explanation of risk/result ("CAUTION: DO NOT TOUCH THE FAN BLADE. YOU CAN BE BURNED BY THE HOT SURFACE.").

**Section 8 Punctuation & word count.** No semicolons - write two sentences instead. Parentheses for references, item numbers, step ids, abbreviations, singular+plural forms, explanations, alternatives. Word counting: text in parentheses = 1 word; hyphenated words = 1 word; numbers, number+unit (2 mm), abbreviations, alphanumeric identifiers, quoted text, titles/labels/proper nouns each count as ONE word.

**Section 9 + General recommendations.** When a dictionary alternative changes part of speech you MUST rebuild the sentence ("operable" -> "can operate"), not just swap words. Use approved words with their exact meanings; no phrasal verbs; consistent style throughout. GRs: keep the conjunction "that" after make sure/show/recommend etc.; use "with" carefully (instrument vs togetherness ambiguity); pronouns only when reference is unambiguous (rewrite if not); avoid Latin abbreviations (e.g., i.e., etc.); gender-neutral language (no he/she); possessive -'s allowed but rewrite when unsure; watch false friends.

## Dictionary semantics (what the linter encodes)
- `base.jsonl`: 2200 entries, status approved/rejected, type_ v/adj/n/adv/prep/conj/pron/art/prefix, meanings[] with STE examples, spellings[] = approved inflected verb forms, alternatives[] = approved substitutes (each with own ste/non-ste examples).
- `technical_words.jsonl`: approved TECHNICAL nouns (TN) and verbs (TV), including multi-word phrases - these bypass the base check.
- Conflicts are normal: many words are approved in one part of speech but rejected in another ("test": noun ok, verb no; "use": both). The linter flags wrong-POS use as R102.

## Writing STE quickly (top patterns)
- make sure that ... (not verify/ensure/check-as-verb); MAKE SURE + full clause
- increase / decrease; STOP ("turn off" rejected as a unit - "STOP THE COMPUTER.")
- install / remove; ATTACH with TO ("attach the bolt to the flange")
- IF ... , DO/STOP/REPLACE ... ; two-sentence splits instead of semicolons
- Safety: CAUTION:/WARNING: + imperative + result explanation

## Verify after writing
1. Run `scripts/lint.py` on the file; fix every R-code (use --json for detail).
2. Re-check anything the linter can't judge (meaning-level rule 1.3, phrasal nuance): compare against references/rules.md examples and the PDF section cited there.
