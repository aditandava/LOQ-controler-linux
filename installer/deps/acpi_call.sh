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

