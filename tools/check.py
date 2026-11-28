#!/usr/bin/env python3
"""Everything a change should pass before it is committed: `make check`."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failed = False


def step(name, ok, detail=""):
    global failed
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f"\n{detail}" if detail and not ok else ""))
    failed |= not ok


def run(*cmd):
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return done.returncode == 0, (done.stdout + done.stderr).strip()


ok, out = run(sys.executable, "tools/build.py", "--check")
step("built files are up to date", ok, out)

for part in sorted(list((ROOT / "app").rglob("*.py")) + list((ROOT / "helper").rglob("*.py"))
                   + list((ROOT / "plugins/rgb/parts").rglob("*.py"))):
    try:
        compile(part.read_text(encoding="utf-8"), str(part), "exec")
        step(f"syntax {part.relative_to(ROOT)}", True)
    except SyntaxError as err:
        step(f"syntax {part.relative_to(ROOT)}", False, str(err))

for script in ("loq_controller_install.sh", "loq_rgb.sh"):
    ok, out = run("bash", "-n", script)
    step(f"bash -n {script}", ok, out)

ok, out = run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
step("unit tests", ok, out)

sys.exit(1 if failed else 0)
