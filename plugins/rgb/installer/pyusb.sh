# ------------------------------------------------------------------ pyusb dep
if python3 -c "import usb.core" 2>/dev/null; then
  say "python-pyusb is already installed."
else
  say "Installing PyUSB (fallback USB backend)"
  if command -v pacman > /dev/null; then
    sudo pacman -S --needed python-pyusb || die "pacman install failed."
  elif command -v apt-get > /dev/null; then
    sudo apt-get update && sudo apt-get install -y python3-usb || die "apt-get install failed."
  elif command -v dnf > /dev/null; then
    sudo dnf install -y python3-pyusb || die "dnf install failed."
  elif command -v zypper > /dev/null; then
    sudo zypper install -y python3-pyusb || die "zypper install failed."
  else
    say "Unknown package manager — install PyUSB if hidraw permissions alone are not used."
  fi
fi

