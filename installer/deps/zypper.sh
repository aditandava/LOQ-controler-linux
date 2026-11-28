deps_zypper() {
  local need=()
  command -v python3 >/dev/null || need+=(python3)
  python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
    || need+=(python3-gobject-Gdk typelib-1_0-Gtk-3_0)
  command -v pkexec >/dev/null || need+=(polkit)
  command -v brightnessctl >/dev/null || need+=(brightnessctl)
  if [ "${#need[@]}" -gt 0 ]; then
    say "Installing: ${need[*]}"
    sudo zypper install -y "${need[@]}" || die "zypper install failed."
  fi
}

