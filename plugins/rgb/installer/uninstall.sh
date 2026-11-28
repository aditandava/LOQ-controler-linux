# ------------------------------------------------------------------ uninstall
if [ "${1:-}" = "--uninstall" ]; then
  say "Removing LOQ RGB plugin and udev rules"
  rm -f "$PLUGIN" "$CONFIG/rgb-enabled"
  rmdir "$PLUGIN_DIR" 2>/dev/null || true
  sudo rm -f "$RULES"
  sudo udevadm control --reload-rules 2>/dev/null || true
  sudo udevadm trigger --subsystem-match=usb --subsystem-match=hidraw 2>/dev/null || true
  say "Done. The LOQ RGB tab disappears next time LOQ Center opens."
  exit 0
fi

[ -z "${1:-}" ] || die "Unknown option: $1"

