# Bring the plug-in / unplug watcher back if it was switched on before this update.
if grep -qs '"enabled": true' "$CONFIG/loq-center/auto.json" && [ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; then
  setsid -f "$BIN/loq-center" --daemon >/dev/null 2>&1 < /dev/null || true
fi

say "Done."
say "Open with SUPER+SHIFT+L (if added) or run: ~/.local/bin/loq-center"
if pgrep -u "$(id -u)" -f "$BIN/loq-center" >/dev/null 2>&1; then
  say "Close the currently open LOQ Center window and reopen it to apply the update."
fi
command -v envycontrol >/dev/null || say "The Integrated button stays hidden: envycontrol is not installed (optional)."