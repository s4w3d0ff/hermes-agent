#!/usr/bin/env python3
"""Verify a skin banner field round-trips exactly against its source ANSI art.

Loads the skin through the real loader (load_skin), parses each art row with
Text.from_markup, and compares every cell's character AND color against the
original ascii-image-converter ANSI file. Also asserts the plain-text art is
byte-identical (no lost/added chars). Exit 0 = perfect round-trip.

Pitfalls encoded here (do not regress):
  * span.start/span.end index into t.plain, NOT the markup source string.
  * span.style may be a raw str; normalize with Style.parse before .color.

Usage:
    python3 verify_hero.py --skin ~/.hermes/skins/horus.yaml \
        [--field banner_hero] [--ansi /tmp/hero-ansi.txt]

Requires rich (use the repo venv). Resolves hermes_cli from ~/.hermes/hermes-agent.
"""
import argparse
import re
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skin", default=str(Path.home() / ".hermes/skins/horus.yaml"))
    ap.add_argument("--field", choices=["banner_hero", "banner_logo"], default="banner_hero")
    ap.add_argument("--ansi", default="/tmp/hero-ansi.txt")
    args = ap.parse_args()

    sys.path.insert(0, str(Path.home() / ".hermes/hermes-agent"))
    from hermes_cli.skin_engine import load_skin
    from rich.color import Color
    from rich.style import Style
    from rich.text import Text

    # Resolve skin by the YAML file's stem (matches how load_skin finds user skins).
    name = Path(args.skin).stem
    art = getattr(load_skin(name), args.field)
    assert art, f"{args.field} is empty on skin '{name}'"

    CELL_RE = re.compile(r"\x1b\[38;5;(\d+)m(.*?)\x1b\[0m")
    orig_lines = []
    for line in Path(args.ansi).read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        cells = [(m.group(2), Color.from_ansi(int(m.group(1))).get_truecolor())
                 for m in CELL_RE.finditer(line)]
        orig_lines.append(cells)

    hero_rows = [l for l in art.split("\n") if l.strip()]
    assert len(hero_rows) == len(orig_lines), \
        f"row count {len(hero_rows)} != ANSI rows {len(orig_lines)}"

    mismatches = 0
    for i, (row, cells) in enumerate(zip(hero_rows, orig_lines)):
        t = Text.from_markup(row)  # raises on malformed markup
        rendered = []
        for span in t.spans:
            s = span.style if isinstance(span.style, Style) else Style.parse(str(span.style))
            rgb = s.color.get_truecolor() if s and s.color else None
            seg = t.plain[span.start:span.end]  # spans index into PLAIN text
            rendered.extend((c, rgb) for c in seg)
        assert len(rendered) == len(cells), \
            f"row {i}: {len(rendered)} cells != {len(cells)} (markup lost/added chars)"
        for j, ((och, orgb), (nch, nrgb)) in enumerate(zip(cells, rendered)):
            if och != nch:
                mismatches += 1
                print(f"MISMATCH row{i} col{j} char: {och!r} vs {nch!r}")
                break
            if orgb != nrgb:
                mismatches += 1
                print(f"MISMATCH row{i} col{j} color: ansi={orgb} rendered={nrgb}")

    plain_ok = Text.from_markup("\n".join(hero_rows)).plain.replace("\n", "") == \
        "".join(ch for cells in orig_lines for ch, _ in cells)

    print(f"rows: {len(hero_rows)}  cells/row: {len(orig_lines[0])}  "
          f"mismatches: {mismatches}  plain art identical: {plain_ok}")
    sys.exit(1 if (mismatches or not plain_ok) else 0)


if __name__ == "__main__":
    main()
