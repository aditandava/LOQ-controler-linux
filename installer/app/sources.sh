work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# The program files live in the src folder of the project. Use them from next to this script
# when it was cloned, otherwise download them.
for part in loq-center loq-center-helper dev.loqcenter.policy loq-center.dcol; do
  get_source "src/$part" "$work/$part" \
    || die "Could not get src/$part. Check your internet connection and that the file is in the src folder of the GitHub project."
done

say "Checking the files"
/usr/bin/python3 -I -c 'import sys
for f in sys.argv[1:]: compile(open(f, encoding="utf-8").read(), f, "exec")' \
  "$work/loq-center" "$work/loq-center-helper" || die "A file is damaged. Download the installer again."
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' \
  >/dev/null 2>&1 || die "Python GTK3 does not load. Install python-gobject/gtk3 (or python3-gi) and try again."

