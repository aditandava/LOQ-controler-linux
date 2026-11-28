if [ "${1:-}" = "--uninstall" ]; then
  say "Removing LOQ Center"
  pkill -u "$(id -u)" -f 'loq-center --daemon' >/dev/null 2>&1 || true
  remove_hooks
  rm -f "$BIN/loq-center" "$DESKTOP" "$DCOL" "$CONFIG/loq-center/theme.css" "$ICON"
  refresh_icons
  rmdir "$CONFIG/loq-center/plugins" 2>/dev/null || true
  rmdir "$CONFIG/loq-center" 2>/dev/null || true
  sudo rm -f "$HELPER" "$POLICY"
  reload_hypr
  say "Removed. Battery and performance settings stay as you last set them."
  exit 0
fi
[ -z "${1:-}" ] || die "Unknown option: $1"

