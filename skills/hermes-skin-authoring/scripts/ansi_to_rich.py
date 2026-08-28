#!/usr/bin/env python3
"""Convert ascii-image-converter ANSI output into a skin banner field.

Reads an ANSI file of `ESC[38;5;<n>m<char>ESC[0m` cells (one art row per line,
produced by:  ascii-image-converter IMG -C -W 40 --braille > FILE) and rewrites
the target `field: |` block in a skin YAML with Rich markup rows
(`[#RRGGBB]run[/][#hex2]...[/]`, adjacent same-color runs merged). Only that
block is touched; the rest of the file is byte-preserved.

Colors are resolved at runtime via rich.color.Color.from_ansi — do NOT embed a
hand-written xterm-256 table (rich's mapping deviates from classic xterm, e.g.
index 16 -> white).

Usage:
    python3 ansi_to_rich.py [ANSI_FILE] [--skin ~/.hermes/skins/horus.yaml] \
        [--field banner_hero|banner_logo] [--dry-run]

Requires rich (use the repo venv: ~/.hermes/hermes-agent/.venv/bin/python).
"""
import argparse
import re
from pathlib import Path

from rich.color import Color

CELL_RE = re.compile(r"\x1b\[38;5;(\d+)m(.*?)\x1b\[0m")


def convert_file(path):
    """ANSI file -> list of Rich-markup rows (consecutive same-color runs merged)."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").split("\n"):
        cells = [(int(m.group(1)), m.group(2)) for m in CELL_RE.finditer(line)]
        if not cells:
            continue
        runs = []  # [[hex, [chars]], ...]
        for idx, ch in cells:
            rgb = Color.from_ansi(idx).get_truecolor() or (0, 0, 0)
            hexc = "#{:02X}{:02X}{:02X}".format(*rgb)
            if runs and runs[-1][0] == hexc:
                runs[-1][1].append(ch)
            else:
                runs.append([hexc, [ch]])
        rows.append("".join(f"[{h}]{''.join(cs)}[/]" for h, cs in runs))
    return rows


def rewrite_field(skin_yaml, field, art_rows):
    """Replace only the `field: |` block in the skin YAML; rest byte-preserved."""
    lines = Path(skin_yaml).read_text(encoding="utf-8").split("\n")
    start = next(i for i, l in enumerate(lines) if re.match(rf"^{re.escape(field)}:\s*\|", l))
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j] and not lines[j].startswith(" "):
            end = j
            break
    new_block = [lines[start]] + ["  " + row for row in art_rows]
    return "\n".join(lines[:start] + new_block + lines[end:]), start, len(art_rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ansi_file", nargs="?", default="/tmp/hero-ansi.txt")
    ap.add_argument("--skin", default=str(Path.home() / ".hermes/skins/horus.yaml"))
    ap.add_argument("--field", choices=["banner_hero", "banner_logo"], default="banner_hero")
    ap.add_argument("--dry-run", action="store_true", help="print converted rows, write nothing")
    args = ap.parse_args()

    rows = convert_file(args.ansi_file)
    if not rows:
        raise SystemExit(f"no 256-color cells found in {args.ansi_file} (did you pass -C --braille?)")
    for row in rows[:3]:
        print(row[:72], "...", sep="")

    text, start, n = rewrite_field(args.skin, args.field, rows)
    if args.dry_run:
        print(f"[dry-run] would replace lines {start + 1}.. of the {args.field} block "
              f"({n} rows) in {args.skin}")
        return
    Path(args.skin).write_text(text, encoding="utf-8")
    print(f"rewrote {args.field} in {args.skin}: {n} rows x {len(rows[0])} markup chars")


if __name__ == "__main__":
    main()
