deps_apt() {
  local need=()
  command -v python3 >/dev/null || need+=(python3)
  python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
    || need+=(python3-gi gir1.2-gtk-3.0)
  python3 -c 'import cairo, gi._gi_cairo' >/dev/null 2>&1 || need+=(python3-cairo python3-gi-cairo)
  command -v pkexec >/dev/null || need+=(pkexec)
  dpkg -s librsvg2-common >/dev/null 2>&1 || need+=(librsvg2-common)
  command -v brightnessctl >/dev/null || need+=(brightnessctl)
  if [ "${#need[@]}" -gt 0 ]; then
    say "Installing: ${need[*]}"
    sudo apt-get update && sudo apt-get install -y "${need[@]}" || die "apt-get install failed."
  fi
}

