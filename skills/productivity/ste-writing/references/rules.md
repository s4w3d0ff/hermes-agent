# ASD-STE100 Issue 9 - Writing Rules (Part 1, condensed)

All nine sections. Rule texts follow the standard; examples are verbatim from the PDF (2025-01-15). Page refs like (1-3-4) point into `~/Projects/asd-ste100-issue9/ASD-STE100 Simplified Technical English - ASD-STE100_ISSUE9.pdf`.

## Section 1 - Words (pages 1-1-1 ... 1-1-25)

**Rule 1.1** Use words that are: approved in the dictionary, technical nouns, or technical verbs.
The controlled dictionary is Part 2 of the standard. Words not in it may be used only if they qualify as a technical noun/verb (a term referring to a specified concept applicable to a subject field). Examples from the PDF: "use" is an approved verb; "engine" is a technical noun; "ream" is a technical verb.

**Rule 1.2** Use approved words ONLY as their specified part of speech.
- "Test" = approved noun, not verb: STE `Do a test for leaks in the system.` / non-STE `Test the system for leaks.`
- "Dim" = approved adjective, not verb: STE `Set the lights to the dim position.` / non-STE `Dim the lights.`
- A word can be approved as several POSes ("clean": verb and adjective); sentence position disambiguates.
- Same-POS alternatives allow word-for-word replacement: "acceptable" -> `A value of 2 mm is permitted.`
- Different-POS alternatives force a new construction: "operable" (adj) -> operate (v): STE `Make sure that the valve can operate.`

**Rule 1.3** Use approved words only with their approved meanings.
"follow" = come after / go after only: STE `Do the procedures that follow:` / non-STE `Follow the safety instructions.` -> STE `Obey the safety instructions.` (obey = "to do that which the procedures or instructions tell you").

**Rule 1.4** Use only approved forms of verbs and adjectives.
Dictionary lists e.g. REMOVE, REMOVES, REMOVED, REMOVED (infinitive/imperative, simple present, past, participle). Adjectives give base + comparative/superlative where formed with -er/-est: SLOW (SLOWER, SLOWEST); "more/most" forms are fine because more and most are approved words.

**Rules 1.5-1.10 Technical nouns.** Allowed if they fit one of the twenty-two categories (exact list, PDF pages 1-1-2...1-1-6):
1 Official parts information; 2 Vehicles or machines, and locations on them; 3 Tools and support equipment, their parts, and locations on them; 4 Materials, consumables, and unwanted material; 5 Facilities, infrastructure, and logistic procedures; 6 Systems, components and circuits, their functions, configurations, and parts; 7 Mathematical, scientific, engineering terms, and formulas; 8 Navigation and geographic terms; 9 Numbers, units of measurement and time (and their symbols); 10 Quoted text; 11 Professional roles, individuals, groups, organizations, and geopolitical entities; 12 Parts of the body; 13 Common personal effects, food, and beverages; 14 Medical terms; 15 Official documents, parts of documentation, standards, and guidelines; 16 Environmental and operational conditions; 17 Colors; 18 Damage terms; 19 Computer science, information and communication technology; 20 Civil and military operations; 21 Law and regulations; 22 Animals, plants, and other life forms.
When selecting: short and easy to understand; no regional/slang/jargon words (1.10); ONE technical noun per item - do not use different nouns for the same item (1.11).

**Rules 1.12-1.13 Technical verbs.** Verbs may be used if they refer to a specified concept or process in your subject field; never use a technical verb as a noun (and by mirror image of 1.7, not a technical noun as verb).

**Rule 1.14** American English spelling unless an official directive says otherwise.

## Section 2 - Multi-word nouns (pages 1-2-1 ...)

**Rule 2.1** Write multi-word nouns of no more than THREE words. The head noun is the LAST word; >3 modifiers makes relations ambiguous, especially for readers whose first language puts the main noun first.
PDF examples:
- `Runway light connection` (3 words, clear - main noun "connection")
- 5-word: `Runway light connection resistance calibration` -> STE `Calibration of the resistance of the runway light connection.`
- Non-STE `Install the forward turbine overheat thermocouple terminal tags.` -> STE `Install the terminal tags on the forward overheat thermocouple of the turbine.`
- Non-STE `Remove the engine transmission housing attachment bolts.` -> STE `Remove the bolts that attach the transmission housing to the engine.`

**Rule 2.2** When a technical noun has more than three words, write it in full once, then either give a shorter form or hyphenate words used as one unit.

## Section 3 - Verbs (pages 1-3-1 ... 1-3-9)

**Rule 3.1** Use only the verb forms given in the dictionary (see `spellings` field, e.g. REMOVE/REMOVES/REMOVED/REMOVED; GIVE/GIVES/GAVE/GIVEN).

**Rule 3.2** Only these tenses/forms: infinitive, imperative, simple present, simple past, simple future; past participle as adjective (see 3.3). NO auxiliaries for complex constructions:
- Non-STE `The operator has adjusted the linkage.` -> STE `The operator adjusted the linkage.` (present perfect is not approved)
- Non-STE `The seat is to be installed before you install the cushion` -> STE `Before you install the cushion, install the seat.`
- Non-STE `The volume control can be adjusted.` -> STE `You can adjust the volume control.`
- Non-STE `The temperature must be adjusted.` -> STE `Adjust the temperature.`
- Non-STE `The sleeve will be adjusted by the robot.` -> STE `The robot will adjust the sleeve.`

**Rule 3.3** Use the past participle as an adjective (not with "have").

**Rule 3.5** The "-ing" form only as a technical noun or modifier inside one:
- OK: `Be careful while the door is opening.` (permitted present progressive usage as listed) - but generally avoid: Non-STE `When you are doing this procedure, obey all the safety precautions.` -> restructure to simple tenses.

**Rule 3.6 Active voice.** In descriptive writing, passive only when the agent is unknown.
PDF pattern table (1-3-8...9):
| Non-STE | STE |
|---|---|
| The seat is to be installed before you install the cushion | Before you install the cushion, install the seat. |
| The volume control can be adjusted. | You can adjust the volume control. |
| The temperature must be adjusted. | Adjust the temperature. |
| The sleeve will be adjusted by the robot. | The robot will adjust the sleeve. |

**Rule 3.7 Use an approved verb to describe an action, not a noun.**
- Do: `The ohmmeter gives an indication of 450 ohms.` -> Write: `The ohmmeter shows 450 ohms.`
- Do: `Before the removal of the unit, make sure that the power supply is OFF.` -> Write: `Before you remove the unit, make sure that the power supply is OFF.`
- If no approved verb exists for the action: Non-STE `Check the laptop battery.` -> STE `Do a check of the laptop battery.` (here "check" as bare verb without object class is not the approved usage).

## Section 4 - Sentences (pages 1-4-1 ...)

**Rule 4.1** Short, clear sentences giving accurate instructions/information. Long sentence split across two; no omitted words; keep "that": Non-STE `Make sure it is locked.` style ellipses are avoided - full form with the conjunction.
PDF anti-pattern: `To remove the cover assembly (9), first remove the four screws (10) that attach the cover assembly to the bulkhead and then open the hatch.` -> split into numbered short steps.

**Rule 4.2** Do not omit words or use contractions. No "don't", "it's"; write it is / do not in full.

**Rule 4.3** Use a vertical list for complex texts (numbered work steps, bullet items). One item = one instruction; keep items parallel in form.

**Rule 4.4** Connect related sentences with approved connecting words/phrases: and, or, but, then, next, finally, before you / after you (+ verb), when + clause, because of (approved phrase), therefore (see dictionary). Do not start every sentence with "and".

**Rule 4.5 (Issue 9 addition)** Use an article (the/a/an) or demonstrative adjective (this/these) before a noun or multi-word noun where applicable - e.g. `The flight compartment` not bare uncountable-in-context omissions; `a safe area`.

## Section 5 - Procedural writing (pages 1-5-1 ...)

Work steps / procedures give instructions, so:
**Rule 5.1** Maximum **20 words** per sentence in procedures.
**Rule 5.2** One instruction per sentence, unless two or more actions occur at the same time (`Hold the panel and press the latch.`).
**Rule 5.3** Imperative form for instructions: `Remove the bolt.`, `Install the clip on the bracket.`, `Make sure that ...`.
**Rule 5.4** Condition first, then command, separated by a comma:
`IF THE LIGHT IS ON, OPEN THE HATCH.` / descriptive statement + comma + command: `The panel is heavy, use two persons to lift it.`
**Rule 5.5** Notes give information only - no instructions in notes (`Note: The seal is reusable for one flight hour.`); instructions live in the numbered steps.

## Section 6 - Descriptive writing (pages 1-6-1 ...)

Descriptive texts = descriptions of items/systems/components, reports, brochures, and notes inside procedures. Imperative not permitted (except quoted text).
**Rule 6.1** Give information gradually; each sentence has ONE subject. Too much at once forces rereading.
**Rule 6.2** Key words / key phrases give logical structure (consistent headings, lead terms in definitions: `The fuel pump supplies pressurized fuel to the engine.`).
**Rule 6.3** Maximum **25 words** per sentence.
**Rule 6.4** Paragraphs group related information; one topic per paragraph (6.5); max six sentences per paragraph (6.6).

## Section 7 - Safety instructions (pages 1-7-1 ...)

**Rule 7.1** Mark the risk level: WARNING = risk of injury or death to a person; CAUTION = risk of damage to objects/equipment. (Other industries may use danger/attention/notice per ANSI Z535 / ISO 45001 / ISO 3864 - content must still follow 7.1-7.3.)
**Rule 7.2** Start with a clear, accurate command or condition. All examples in the standard are uppercase (style convention, not an STE rule): `WARNING: WEAR SAFETY GLASSES.` / `CAUTION: THE ENGINE CAN START SUDDENLY.`
**Rule 7.3** Give the explanation showing risk/result after the command/condition:
`CAUTION: DO NOT TOUCH THE FAN BLADE. YOU CAN BE BURNED BY THE HOT SURFACE.`

## Section 8 - Punctuation and word count (pages 1-8-1 ...)

**Rule 8.1** All standard punctuation EXCEPT the semicolon (`;`). Two sentences instead of one long compound: non-STE `The bolt is installed; it must be torqued.` -> `Install the bolt. Then, torque the bolt to 25 Nm.`
**Rule 8.2** Hyphens connect directly related words (one unit): pop-out indicator, re-entry port, two-person lift.
**Rule 8.3** Parentheses only for: references to illustrations/text; letters/numbers identifying items on an illustration or in text; work-step identifiers; abbreviations; singular AND plural forms together (`bolt(s)`); explaining a word/part of the sentence; alternatives (`the red (or blue) switch`).
**Rule 8.4** In a vertical list, a colon ends the sentence like a period for word-count purposes: `The fasteners must be:` + list items each counted separately.
**Rule 8.5** Parenthesized text counts as ONE word in that sentence's count.
**Rule 8.6** Each of these counts as one word: numbers; number+unit (`2 mm`, `400 ohms`); abbreviations; alphanumeric identifiers; quoted text; titles/headings/placards/labels; proper nouns (individuals, groups, organizations, geopolitical entities).
**Rule 8.7** Hyphenated words count as one word (`pop-out indicator` = 2 words: pop-out + indicator).

## Section 9 - Writing practices + General recommendations (pages 1-9-1 ...)

**Rule 9.1** If a word-for-word replacement is not sufficient (alternative has a different part of speech), use a DIFFERENT sentence construction. Non-STE `Make sure that the valve is operable.` -> STE `Make sure that the valve can operate.`
**Rule 9.2** Use each approved word correctly - its dictionary meaning, POS, and form.
**Rule 9.3** Do not build phrasal verbs from two words: e.g. "look up" rejected -> use an approved single verb (FIND). The dictionary marks multi-word units like `turn off`, `carry out`, `account for` as rejected with single-verb alternatives.
**Rule 9.4** Consistent style when selecting terminology/wording - same term throughout a text, same construction patterns repeated.

### General recommendations GR-1 ... GR-8 (advisory)
- **GR-1 "that":** keep the conjunction after make sure / show / recommend etc.: `Make sure that the door is locked.` Prevents clause-boundary ambiguity.
- **GR-2 "with":** three approved senses - association, help/sharing, instrument/means. Watch: `Install the panel with the green fasteners` = ambiguous (using them vs belonging to it). Prefer: `Attach the panel to the bulkhead using the green fasteners.` or `The green fasteners attach the panel to the bulkhead.`
- **GR-3 Pronouns:** use only approved pronouns from the dictionary; never he/she; if "it/they" could refer to more than one noun, replace the pronoun with the noun.
- **GR-4 "this":** make sure the reader knows what "this" refers to; repeat the context: Non-STE `Make sure that the cover is not locked (this can cause damage to the probe).` -> STE `Make sure that the cover is not locked. If the cover is locked, this can cause damage to the probe.`
- **GR-5 False friends:** verify a word's ENGLISH meaning, not its native-language look-alike (`disposition` ≠ Spanish *disposición*).
- **GR-6 Latin abbreviations:** avoid e.g., i.e., etc. - write "for example", "and so on". Non-STE `Discard the standard parts (e.g., washers, screws, bolts) ...` -> STE `... (for example, washers, bolts).`
- **GR-7 Inclusive language:** gender-neutral; no he/she as generic person.
- **GR-8 Possessive form:** -'s is permitted but if unsure of correctness, rewrite without it: Non-STE `the manufacturer's instructions` -> STE `THE INSTRUCTIONS FOR THE MANUFACTURER` (or "refer to the instruction manual").
