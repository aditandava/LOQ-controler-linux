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

say "Installing the app (sudo is needed for the root helper)"
sudo install -Dm755 -o root -g root "$work/loq-center-helper" "$HELPER"
sudo install -Dm644 -o root -g root "$work/dev.loqcenter.policy" "$POLICY"
pkill -u "$(id -u)" -f 'loq-center --daemon' >/dev/null 2>&1 || true  # so the new version runs
install -Dm755 "$work/loq-center" "$BIN/loq-center"

# Download the icon. If GitHub cannot be reached the app still works with a stock icon.
icon_ref="computer-laptop"
install_icon() {
  local tmp="$work/$ICON_FILE" url got=0 urls=()
  if [ -n "${LOQ_ICON_URL:-}" ]; then
    urls=("$LOQ_ICON_URL")
  else
    urls=("$ICON_BASE/main/icon/$ICON_FILE" "$ICON_BASE/master/icon/$ICON_FILE")
  fi
  for url in "${urls[@]}"; do
    if fetch "$url" "$tmp" && [ -s "$tmp" ] && grep -q '<svg' "$tmp"; then
      got=1
      break
    fi
  done
  if [ "$got" -eq 1 ]; then
    install -Dm644 "$tmp" "$ICON"
    refresh_icons
    icon_ref="loq-center"
    say "Icon installed"
  elif [ -f "$ICON" ]; then
    icon_ref="loq-center"
    say "Could not download the icon, so the one already installed was kept."
  else
    say "Could not download the icon from GitHub, so a stock icon is used. Run the installer again once the icon is uploaded."
  fi
}
install_icon

mkdir -p "$(dirname "$DESKTOP")" "$CONFIG/loq-center"
cat > "$DESKTOP" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=LOQ Center
Comment=Battery, performance, display and GPU controls
Exec="$BIN/loq-center"
Icon=$icon_ref
Terminal=false
Categories=Settings;HardwareSettings;
StartupWMClass=loq-center
DESKTOP_EOF

