#!/usr/bin/env python3
"""STE lint — check technical text against ASD-STE100 Simplified Technical English (Issue 9).

Data-driven: loads the base controlled vocabulary and the technical-word list from
this skill's dictionaries/ (or --dicts-dir) and applies the mechanical subset of
the Part-1 writing rules. Lexical checks are reliable; syntactic ones are best-effort
and reported as warnings so a human still makes the final call on meaning-level
rules (Rule 1.3, phrasal nuance).

Rules implemented:
  R101 error    word rejected in the base dictionary            (suggests approved alternatives)   [Rule 1.1/9.2]
  R102 warning  spelling is approved for one part of speech and
                rejected for another — check its POS in context                              [Rule 1.2]
  R104 info     word not in the base dictionary and not a technical term — allowed only as
                a qualifying technical noun/verb                                              [Rules 1.5, 1.6]
  R903 error    multi-word unit rejected in the dictionary (phrasal verbs etc.)               [Rule 9.3]
  R402 error    contraction / pronoun + 's contraction                                           [Rule 4.2]
  R801 error    semicolon — write two sentences instead                                          [Rule 8.1]
  R305 warning  -ing form after a be-verb — check Rule 3.5 usage                                 [Rule 3.5]
  R501/R601 err sentence longer than the word-count limit for its type
                (procedural = 20 words with --procedural, descriptive = 25 otherwise)          [Rules 5.1/6.3]

Word counting follows Rule 8: parenthetical text counts as one word; number + unit
counts as one word; hyphenated words count as one word (they tokenize as one token).

Usage:
    python3 lint.py [--procedural] [--max-words N] [--dicts-dir DIR]
                    [--allow R801,R903] [--exempt-file FILE] [--json OUT] TARGET [TARGET...]
TARGET is a file (or '-' for stdin, read as one logical document). Exemption file:
one 'RULEID LINE' or 'RULEID ALL' per line. Exit 0 when no errors remain, 1 otherwise.
Stdlib only; Python 3.8+.
"""

import argparse
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__)) + "/.."
DEFAULT_DICTS = os.path.join(SKILL_DIR, "dictionaries")

# ---------------------------------------------------------------- dictionaries

def load_dicts(dicts_dir):
    base_path = os.path.join(dicts_dir, "asdste100_issue9_base.jsonl")
    tech_path = os.path.join(dicts_dir, "asdste100_issue9_technical_words.jsonl")
    if not (os.path.exists(base_path) and os.path.exists(tech_path)):
        sys.exit("dictionaries not found in %s — pass --dicts-dir" % dicts_dir)

    by_word = {}   # lowercased headword or unit -> list of base entries
    with open(base_path, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            by_word.setdefault(e["name"].lower(), []).append(e)

    tech_names = set()          # single-token technical terms (TN/TV)
    with open(tech_path, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            n = e["name"].lower()
            if " " not in n:
                tech_names.add(n)

    rejected_units = {w for w in by_word if " " in w and by_word[w][0]["status"] == "rejected"}

    return by_word, tech_names, rejected_units


def entry_info(entries):
    """Summarize a word's entries: approved POS set and unique alternative labels."""
    approved_types = {e["type_"] for e in entries if e["status"] == "approved"}
    alternatives = []
    for e in entries:
        if e["status"] != "rejected":
            continue
        for alt in e.get("alternatives", []):
            exs = alt.get("ste_example") or []
            label = "%s (%s)" % (alt["name"], alt.get("type_", "?"))
            if exs:
                label += ' — e.g. "%s"' % exs[0]
            if label not in alternatives:
                alternatives.append(label)
    return approved_types, alternatives


# ------------------------------------------------------------------- line prep

CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")
LIST_MARKER_RE = re.compile(r"^(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def preprocess_line(raw):
    """Strip markdown scaffolding, inline code and URLs; return cleaned prose."""
    t = LINK_RE.sub(r"\1", raw)
    t = URL_RE.sub(" ", t)
    t = CODE_RE.sub(" ", t)
    t = LIST_MARKER_RE.sub("", t.strip())
    return re.sub(r"\|", " ", t).strip()


def is_code_fence(line):
    return bool(re.match(r"^\s*(```|~~~)", line))

# ----------------------------------------------------------------- word count

PAREN_RE = re.compile(r"\(([^()]*)\)")

UNITS = {
    "mm", "cm", "m", "km", "in", "ft", "mi", "nm", "v", "a", "w", "kw", "mw",
    "nv", "ma", "kn", "rpm", "deg", "c", "f", "khz", "mhz", "ghz",
    "pa", "kpa", "mpa", "bar", "psi", "oz", "lb", "lbf", "kg", "g", "mg",
    "ml", "l", "h", "min", "s", "ohm", "ohms", "volt", "volts",
    "amp", "amps", "watt", "watts", "second", "seconds", "minute", "minutes",
}


def ste_word_count(sentence):
    """Count words per STE Rule 8: parenthetical text = 1 word, number + unit = 1 word."""
    s = sentence.strip()
    if not s or set(s) <= {":", ",", ".", "!", "?", " ", ";"}:
        return 0
    n_parens = len(PAREN_RE.findall(s))
    tokens = [t for t in re.split(r"\s+", PAREN_RE.sub(" ", s)) if t]

    count, i = 0, 0
    while i < len(tokens):
        bare = tokens[i].strip(",.;:!?\"'")
        # number (+optionally a following unit word) counts as ONE (Rule 8.6)
        if re.fullmatch(r"\d[\d,.]*", bare) and i + 1 < len(tokens):
            nxt = tokens[i + 1].strip(",.;:!?\"'").lower()
            if nxt in UNITS:
                count += 1
                i += 2
                continue
        count += 1
        i += 1
    return count + n_parens


def split_sentences(text):
    """Split on . ! ? and : (Rule 8.4 — a colon ends the sentence in vertical lists)."""
    parts = re.split(r"(?<=[.:!?])\s+", text.strip())
    return [p for p in parts if p.strip()]

# ----------------------------------------------------------------------- lint

ING_AFTER_BE_RE = re.compile(r"\b(?:is|are|was|were|be)\s+([A-Za-z]+)ing\b")
CONTRACTION_END_RE = re.compile(r"\b([A-Za-z]+)='(t|m|re|ve|ll)\b")
PRONOUN_S_WORDS = {"it", "that", "there", "he", "she"}


def check_line(line, by_word, tech_names, rejected_units, max_words):
    """Return a list of issue dicts for one preprocessed line."""

    def add(rule, level, word, message):
        issues.append({"rule": rule, "level": level, "word": word, "message": message})

    issues = []

    if ";" in line:
        add("R801", "error", ";", "semicolon — write two sentences instead (Rule 8.1)")

    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", line)
    lower_seq = [w.lower() for w in words]
    n = len(lower_seq)

    # R903 rejected multi-word units — longest match first, mark consumed tokens
    consumed = set()
    if rejected_units:
        for i in range(n):
            if i in consumed:
                continue
            best = None
            for L in (4, 3, 2):
                if i + L <= n:
                    phrase = " ".join(lower_seq[i:i + L])
                    if phrase in rejected_units:
                        best = phrase
                        break
            if best:
                entry = by_word[best][0]
                alt_names = [a["name"] for a in entry.get("alternatives", [])][:4]
                add(
                    "R903", "error", best,
                    "rejected unit '%s' (Rule 9.3: no phrasal verbs) — use %s"
                    % (best, ", ".join(alt_names) if alt_names else "a single approved verb"),
                )
                consumed.update(range(i, i + len(best.split())))

    # per-word dictionary checks
    for idx, w in enumerate(lower_seq):
        if idx in consumed:
            continue
        key = w.strip("'")
        entries = by_word.get(key)
        if not entries:
            if key not in tech_names and re.fullmatch(r"[a-z]{4,}", key):
                add(
                    "R104", "info", w,
                    "not in the STE dictionary — allowed only as a qualifying technical noun/verb "
                    "(Rules 1.5/1.6); check your glossary",
                )
            continue

        statuses = {e["status"] for e in entries}
        if "approved" not in statuses:
            _, alternatives = entry_info(entries)
            add(
                "R101", "error", w,
                "rejected word (Rule 1.1). Approved alternative(s): %s"
                % ("; ".join(alternatives[:3]) if alternatives else "see the dictionary"),
            )
        elif "rejected" in statuses:
            approved_types, _ = entry_info(entries)
            all_types = {e["type_"] for e in entries}
            rejected_types = sorted(all_types - approved_types)
            add(
                "R102", "warning", w,
                "'%s' is approved only as %s — check the part of speech here (Rule 1.2); "
                "rejected as: %s" % (w, ",".join(sorted(approved_types)), ",".join(rejected_types) or "-"),
            )

    # R402 contractions and pronoun + 's
    for m in CONTRACTION_END_RE.finditer(line):
        add("R402", "error", m.group(0), "'%s' is a contraction — write it out (Rule 4.2)" % m.group(0))
    for m in re.finditer(r"\b([A-Za-z]+)='s\b", line):
        if m.group(1).lower() in PRONOUN_S_WORDS:
            add("R402", "error", m.group(0), "'%s' is a contraction — write it out (Rule 4.2)" % m.group(0))

    # R305 -ing after be-verbs (Rule 3.5)
    for m in ING_AFTER_BE_RE.finditer(line):
        add("R305", "warning", m.group(1) + "ing",
            "'%s' — check the -ing form usage (Rule 3.5); prefer a simple tense" % m.group(0))

    # sentence length (Rules 5.1 / 6.3)
    for sent in split_sentences(line):
        cnt = ste_word_count(sent)
        if cnt > max_words:
            add(
                "R501" if max_words <= 20 else "R601", "error", "",
                "sentence has %d words, limit is %d (Rule %s)" % (
                    cnt, max_words, "5.1" if max_words <= 20 else "6.3"),
            )

    return issues


def lint_text(text, by_word, tech_names, rejected_units, max_words):
    out = []
    in_fence = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if is_code_fence(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        processed = preprocess_line(raw)
        if not processed:
            continue
        for issue in check_line(processed, by_word, tech_names, rejected_units, max_words):
            out.append({"line": lineno, **issue})
    return out


def load_exemptions(path):
    exemptions = set()  # (rule, line-number-string) or (rule, "ALL")
    with open(path, encoding="utf-8") as f:
        for ln in f:
            parts = ln.split()
            if len(parts) >= 2 and re.fullmatch(r"R\d+", parts[0]):
                exemptions.add((parts[0], parts[1].upper()))
    return exemptions

# ----------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="files to check, or '-' for stdin")
    ap.add_argument("--procedural", action="store_true",
                    help="treat text as work steps: 20-word sentence limit (Rule 5.1)")
    ap.add_argument("--max-words", type=int, default=None,
                    help="override the per-sentence word-count limit")
    ap.add_argument("--dicts-dir", default=DEFAULT_DICTS)
    ap.add_argument("--allow", default="", help="comma-separated rule ids to suppress (e.g. R801,R903)")
    ap.add_argument("--exempt-file", default=None, help="file with 'RULEID LINE' or 'RULEID ALL' entries")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="also write a machine-readable report to this path")
    args = ap.parse_args(argv)

    by_word, tech_names, rejected_units = load_dicts(args.dicts_dir)
    max_words = args.max_words if args.max_words is not None else (20 if args.procedural else 25)
    allowed = {a.strip().upper() for a in args.allow.split(",") if a.strip()}
    exemptions = load_exemptions(args.exempt_file) if args.exempt_file else set()

    label_order = []
    all_issues = {}   # file -> [issue rows]
    counts = {"error": 0, "warning": 0, "info": 0}

    for target in args.targets:
        if target == "-":
            text = sys.stdin.read()
            label = "<stdin>"
        else:
            with open(target, encoding="utf-8") as f:
                text = f.read()
            label = target
        label_order.append(label)
        kept = []
        for it in lint_text(text, by_word, tech_names, rejected_units, max_words):
            if it["rule"] in allowed:
                continue
            if (it["rule"], str(it["line"])) in exemptions or (it["rule"], "ALL") in exemptions:
                continue
            row = dict({"file": label}, **it)
            counts[row["level"]] += 1
            kept.append(row)
        all_issues[label] = kept

    # human-readable report, grouped per file, sorted by line then rule
    printed = set()
    for fname in label_order:
        if fname in printed:
            continue
        printed.add(fname)
        rows = all_issues.get(fname, [])
        if not rows:
            continue
        print("== %s ==" % fname)
        for r in sorted(rows, key=lambda x: (x["line"], x["rule"])):
            tag = {"error": "ERR", "warning": "WRN", "info": "inf"}[r["level"]]
            word = (" '%s'" % r["word"]) if r.get("word") else ""
            print("  L%-4d [%s] %-5s%s %s" % (r["line"], tag, r["rule"], word, r["message"]))

    # machine-readable report
    flat = []
    for fname in label_order:
        if fname not in all_issues:
            continue
        for r in sorted(all_issues[fname], key=lambda x: (x["line"], x["rule"])):
            flat.append({"file": r["file"], "line": r["line"], "rule": r["rule"],
                         "level": r["level"], "word": r.get("word", ""),
                         "message": r["message"]})
    report = {
        "source": "ASD-STE100 Issue 9 (2025-01-15)",
        "dicts_dir": os.path.abspath(args.dicts_dir),
        "procedural": bool(args.procedural),
        "max_words_per_sentence": max_words,
        "allowed_rules": sorted(allowed),
        "counts": {"errors": counts["error"], "warnings": counts["warning"], "infos": counts["info"]},
        "issues": flat,
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    total = len(flat)
    print()
    if total == 0:
        print("STE check passed — no issues found.")
    else:
        print("Done: %d error(s), %d warning(s), %d info" % (counts["error"], counts["warning"], counts["info"]))
    return 1 if counts["error"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
