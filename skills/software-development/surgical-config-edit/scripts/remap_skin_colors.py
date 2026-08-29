import difflib
import re
import shutil
import sys
from pathlib import Path

import yaml


def hex_channels(value):
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def squared_rgb(a, b):
    return sum((x - y) ** 2 for x, y in zip(hex_channels(a), hex_channels(b)))


def art_palette(*arts):
    text = "\n".join(art or "" for art in arts)
    return {c.upper() for c in re.findall(r"\[#([0-9A-Fa-f]{6})\]", text)}


def nearest(value, palette):
    return min(palette, key=lambda c: squared_rgb(value, c))


def main(argv):
    dry_run = "--dry-run" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(f"usage: {argv[0]} <skin.yaml> [--dry-run]")
        return 2

    path = Path(args[0])
    original_text = path.read_text()
    doc = yaml.safe_load(original_text)
    colors_old = {k: v.upper() for k, v in doc["colors"].items()}
    palette = art_palette(doc.get("banner_logo"), doc.get("banner_hero"))
    if not palette:
        print("no banner hex tags found; nothing to map against")
        return 1

    mapping = {k: "#" + nearest(v, palette) for k, v in colors_old.items()}

    updated_text = original_text
    for key in colors_old:
        old_fragment = f'{key}: "{colors_old[key]}"'
        if updated_text.count(old_fragment) != 1:
            print(f"fragment not unique or missing: {old_fragment}")
            return 1
        updated_text = updated_text.replace(old_fragment, f'{key}: "#{mapping[key]}"')

    changed_keys = [k for k in colors_old if mapping[k] != colors_old[k]]
    diff_lines = difflib.unified_diff(
        original_text.splitlines(), updated_text.splitlines(), lineterm="")
    removed = [l[1:] for l in diff_lines if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
    line_pattern = re.compile(r'\s*[a-z_]+: "#[0-9A-F]{6}"')
    if len(removed) != len(changed_keys) or len(added) != len(changed_keys):
        print(f"diff size mismatch: {len(removed)} removed, {len(added)} added, "
              f"{len(changed_keys)} keys changed")
        return 1
    for line in removed + added:
        if not line_pattern.fullmatch(line):
            print(f"unexpected diff line: {line!r}")
            return 1

    updated_doc = yaml.safe_load(updated_text)
    for key, value in doc.items():
        if key == "colors":
            continue
        if updated_doc.get(key) != value:
            print(f"untouched section changed: {key}")
            return 1
    palette_set = {"#" + c for c in palette}
    for key, value in updated_doc["colors"].items():
        if value.upper() not in palette_set:
            print(f"value outside banner palette: {key} = {value}")
            return 1

    if dry_run:
        print("\n".join(diff_lines))
        return 0

    shutil.copyfile(path, str(path) + ".bak")
    path.write_text(updated_text)
    diff_path = Path(str(path) + ".diff")
    diff_path.write_text("\n".join(diff_lines))
    print(f"{len(changed_keys)} keys retuned; backup at {path}.bak; diff at {diff_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
