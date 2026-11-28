deps_pacman() {
  local missing=()
  for pkg in python python-gobject python-cairo gtk3 polkit brightnessctl librsvg; do
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
}

