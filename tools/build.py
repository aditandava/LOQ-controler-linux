#!/usr/bin/env python3
"""Build the shipped files from the section files.

    python3 tools/build.py           # write every output
    python3 tools/build.py --check   # fail if an output is stale (used by `make check`)

Each target is a folder with a manifest.txt that lists its section files in order.
The sections are joined as they are (no rewriting), so what you edit is what ships.
"""
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXEC = 0o755


def scenes_part():
    """Python code holding the built-in tab wallpapers (assets/wallpapers/<tab>.svg)."""
    files = sorted((ROOT / "assets/wallpapers").glob("*.svg"))
    lines = ["# ------------------------------------------------ built-in wallpapers (generated)",
             "# Made by tools/build.py from assets/wallpapers/*.svg. Edit the .svg files, not this.",
             "SCENE_SVG = {"]
    for f in files:
        lines.append(f"    {f.stem!r}: {f.read_text(encoding='utf-8')!r},")
    lines += ["}", "", ""]
    return "\n".join(lines)


GENERATED = {"@generated:wallpapers": scenes_part}


def join_parts(folder):
    base = ROOT / folder
    names = [ln.strip() for ln in (base / "manifest.txt").read_text().splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    generated = [n for n in names if n in GENERATED]
    names = [n for n in names if n not in GENERATED]
    missing = [n for n in names if not (base / n).is_file()]
    if missing:
        sys.exit(f"{folder}/manifest.txt lists missing files: {', '.join(missing)}")
    on_disk = {p.relative_to(base).as_posix() for p in base.rglob("*")
               if p.is_file() and p.name != "manifest.txt"}
    unlisted = sorted(on_disk - set(names))  # generated entries are not files
    if unlisted:
        sys.exit(f"{folder}: files not in manifest.txt (they would not ship): {', '.join(unlisted)}")
    order = [ln.strip() for ln in (base / "manifest.txt").read_text().splitlines()
             if ln.strip() and not ln.lstrip().startswith("#")]
    return "".join(GENERATED[n]() if n in GENERATED else (base / n).read_text(encoding="utf-8")
                   for n in order)


def rgb_installer():
    template = (ROOT / "plugins/rgb/loq_rgb.sh.in").read_text()
    rules = (ROOT / "plugins/rgb/99-ite-kbd.rules").read_text()
    plugin = (ROOT / "plugins/rgb/rgb.py").read_text()
    return template.replace("@@RULES@@\n", rules).replace("@@PLUGIN@@\n", plugin)


def targets():
    """(output path, text producer, file mode). Order matters: rgb.py before loq_rgb.sh."""
    return [
        ("src/loq-center", lambda: join_parts("app"), EXEC),
        ("src/loq-center-helper", lambda: join_parts("helper"), EXEC),
        ("src/dev.loqcenter.policy", lambda: (ROOT / "assets/dev.loqcenter.policy").read_text(), 0o644),
        ("src/loq-center.dcol", lambda: (ROOT / "assets/loq-center.dcol").read_text(), 0o644),
        ("plugins/rgb/rgb.py", lambda: join_parts("plugins/rgb/parts"), 0o644),
        ("loq_controller_install.sh", lambda: join_parts("installer"), EXEC),
        ("loq_rgb.sh", rgb_installer, EXEC),
    ]


def main(argv):
    check = argv[1:] == ["--check"]
    stale = []
    for rel, produce, mode in targets():
        out = ROOT / rel
        text = produce()
        if check:
            if not out.exists() or out.read_text(encoding="utf-8") != text:
                stale.append(rel)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        out.chmod(mode)
        print(f"built {rel}")
    if stale:
        print("Out of date (run: make build): " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
