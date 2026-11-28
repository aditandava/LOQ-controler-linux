install_deps() {
  if command -v pacman >/dev/null; then
    local missing=()
    for pkg in python python-gobject gtk3 polkit brightnessctl librsvg; do
      pacman -Q "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
    done
    if [ "${#missing[@]}" -gt 0 ]; then
      say "Installing: ${missing[*]}"
      sudo pacman -S --needed "${missing[@]}" || die "Package install failed. Run 'sudo pacman -Syu', then try again."
    fi
    if ! command -v envycontrol >/dev/null; then
      for aur_helper in yay paru; do
        if command -v "$aur_helper" >/dev/null; then
          say "Installing envycontrol via $aur_helper (optional, for GPU mode switching)"
          "$aur_helper" -S --needed --noconfirm envycontrol || true
          break
        fi
      done
      command -v envycontrol >/dev/null \
        || say "envycontrol not found — Integrated button hidden (install from AUR later if needed)."
    fi
  elif command -v apt-get >/dev/null; then
    local need=()
    command -v python3 >/dev/null || need+=(python3)
    python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
      || need+=(python3-gi gir1.2-gtk-3.0)
    command -v pkexec >/dev/null || need+=(pkexec)
    dpkg -s librsvg2-common >/dev/null 2>&1 || need+=(librsvg2-common)
    command -v brightnessctl >/dev/null || need+=(brightnessctl)
    if [ "${#need[@]}" -gt 0 ]; then
      say "Installing: ${need[*]}"
      sudo apt-get update && sudo apt-get install -y "${need[@]}" || die "apt-get install failed."
    fi
  elif command -v dnf >/dev/null; then
    local need=()
    command -v python3 >/dev/null || need+=(python3)
    python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
      || need+=(python3-gobject gtk3)
    command -v pkexec >/dev/null || need+=(polkit)
    command -v brightnessctl >/dev/null || need+=(brightnessctl)
    if [ "${#need[@]}" -gt 0 ]; then
      say "Installing: ${need[*]}"
      sudo dnf install -y "${need[@]}" || die "dnf install failed."
    fi
  elif command -v zypper >/dev/null; then
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
  else
    command -v python3 >/dev/null || die "python3 is required."
    command -v pkexec >/dev/null || die "polkit (pkexec) is required."
  fi
}

install_deps

# Fan full speed on many LOQ models goes through the acpi_call kernel module.
install_fan_module() {
  command -v pacman >/dev/null || return 0
  modinfo acpi_call >/dev/null 2>&1 && return 0
  local pkgs=(acpi_call-dkms) base
  for base in /usr/lib/modules/*/pkgbase; do
    [ -r "$base" ] && pkgs+=("$(cat "$base")-headers")
  done
  say "Installing ${pkgs[*]} (needed for fan full speed and dGPU only)"
  sudo pacman -S --needed "${pkgs[@]}" \
    || say "acpi_call was not installed. Cooling may not reach full fan speed."
}

install_fan_module
sudo modprobe acpi_call 2>/dev/null || say "acpi_call did not load (reboot, or check Secure Boot)."

