#!/usr/bin/env python3
"""Regenerate the horus skin's banner_hero from ascii-image-converter output.

Usage:
  python3 hero_from_ansi.py [ANSI_FILE] [--skin SKIN_YAML]

Pipeline (default values in parens):
  1. Generate colored art, e.g.:
       ascii-image-converter images/YuuBooty.png -C -W 40 --braille > /tmp/hero-ansi.txt
     Note: --save-txt writes PLAIN text; colors only exist on stdout, so redirect it.
  2. Run this script (stdlib-only) to convert the xterm-256 ANSI codes into
     Rich markup ([#RRGGBB]...[/]) and rewrite the banner_hero block in the
     skin YAML (~/.hermes/skins/horus.yaml).

The embedded palette is rich.color.Color.from_ansi(i)'s exact truecolor for i in
0..255 (generated with the installed rich), so `[#hex]` round-trips to the same
truecolor the CLI/TUI renderer will produce. Regenerate if rich upgrades:
  from rich.color import Color; print(" ".join("{:02X}{:02X}{:02X}".format(*Color.from_ansi(i).get_truecolor()) for i in range(256)))
"""
import argparse
import re
from pathlib import Path

# Exact rich truecolors for xterm-256 indices 0..255 (space-separated, row-major).
_PALETTE = """
000000 800000 008000 808000 000080 800080 008080 C0C0C0 808080 FF0000 00FF00 FFFF00 0000FF FF00FF 00FFFF FFFFFF
000000 00005F 000087 0000AF 0000D7 0000FF 005F00 005F5F 005F87 005FAF 005FD7 005FFF 008700 00875F 008787 0087AF
0087D7 0087FF 00AF00 00AF5F 00AF87 00AFAF 00AFD7 00AFFF 00D700 00D75F 00D787 00D7AF 00D7D7 00D7FF 00FF00 00FF5F
00FF87 00FFAF 00FFD7 00FFFF 5F0000 5F005F 5F0087 5F00AF 5F00D7 5F00FF 5F5F00 5F5F5F 5F5F87 5F5FAF 5F5FD7 5F5FFF
5F8700 5F875F 5F8787 5F87AF 5F87D7 5F87FF 5FAF00 5FAF5F 5FAF87 5FAFAF 5FAFD7 5FAFFF 5FD700 5FD75F 5FD787 5FD7AF
5FD7D7 5FD7FF 5FFF00 5FFF5F 5FFF87 5FFFAF 5FFFD7 5FFFFF 870000 87005F 870087 8700AF 8700D7 8700FF 875F00 875F5F
875F87 875FAF 875FD7 875FFF 878700 87875F 878787 8787AF 8787D7 8787FF 87AF00 87AF5F 87AF87 87AFAF 87AFD7 87AFFF
87D700 87D75F 87D787 87D7AF 87D7D7 87D7FF 87FF00 87FF5F 87FF87 87FFAF 87FFD7 87FFFF AF0000 AF005F AF0087 AF00AF
AF00D7 AF00FF AF5F00 AF5F5F AF5F87 AF5FAF AF5FD7 AF5FFF AF8700 AF875F AF8787 AF87AF AF87D7 AF87FF AFAF00 AFAF5F
AFAF87 AFAFAF AFAFD7 AFAFFF AFD700 AFD75F AFD787 AFD7AF AFD7D7 AFD7FF AFFF00 AFFF5F AFFF87 AFFFAF AFFFD7 AFFFFF
D70000 D7005F D70087 D700AF D700D7 D700FF D75F00 D75F5F D75F87 D75FAF D75FD7 D75FFF D78700 D7875F D78787 D787AF
D787D7 D787FF D7AF00 D7AF5F D7AF87 D7AFAF D7AFD7 D7AFFF D7D700 D7D75F D7D787 D7D7AF D7D7D7 D7D7FF D7FF00 D7FF5F
D7FF87 D7FFAF D7FFD7 D7FFFF FF0000 FF005F FF0087 FF00AF FF00D7 FF00FF FF5F00 FF5F5F FF5F87 FF5FAF FF5FD7 FF5FFF
FF8700 FF875F FF8787 FF87AF FF87D7 FF87FF FFAF00 FFAF5F FFAF87 FFAFAF FFAFD7 FFAFFF FFD700 FFD75F FFD787 FFD7AF
FFD7D7 FFD7FF FFFF00 FFFF5F FFFF87 FFFFAF FFFFD7 FFFFFF 080808 121212 1C1C1C 262626 303030 3A3A3A 444444 4E4E4E
585858 626262 6C6C6C 767676 808080 8A8A8A 949494 9E9E9E A8A8A8 B2B2B2 BCBCBC C6C6C6 D0D0D0 DADADA E4E4E4 EEEEEE
"""

PALETTE = _PALETTE.split()
assert len(PALETTE) == 256, f"palette must have 256 entries, got {len(PALETTE)}"

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
            hexc = "#" + PALETTE[idx]
            if runs and runs[-1][0] == hexc:
                runs[-1][1].append(ch)
            else:
                runs.append([hexc, [ch]])
        rows.append("".join(f"[{h}]{''.join(cs)}[/]" for h, cs in runs))
    return rows


def rewrite_hero(skin_yaml, art_rows):
    """Replace the banner_hero block (and nothing else) in the skin YAML."""
    text = Path(skin_yaml).read_text(encoding="utf-8")
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if re.match(r"^banner_hero:\s*\|", l))
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j] and not lines[j].startswith(" "):
            end = j
            break
    new_block = [lines[start]] + ["  " + row for row in art_rows]
    Path(skin_yaml).write_text("\n".join(lines[:start] + new_block + lines[end:]), encoding="utf-8")
    print(f"rewrote banner_hero in {skin_yaml}: {len(art_rows)} rows x {len(art_rows[0])} chars markup")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ansi_file", nargs="?", default="/tmp/hero-ansi.txt",
                    help="ANSI file from: ascii-image-converter IMG -C -W 40 --braille > FILE")
    ap.add_argument("--skin", default=str(Path.home() / ".hermes/skins/horus.yaml"))
    args = ap.parse_args()
    rows = convert_file(args.ansi_file)
    if not rows:
        raise SystemExit(f"no braille cells found in {args.ansi_file} (did you pass -C --braille?)")
    rewrite_hero(args.skin, rows)


if __name__ == "__main__":
    main()
