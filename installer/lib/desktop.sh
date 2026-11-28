# Only an icon cache that already exists needs a refresh; without one, GTK reads the folder directly.
refresh_icons() {
  if [ -f "$DATA/icons/hicolor/icon-theme.cache" ] && command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -qft "$DATA/icons/hicolor" >/dev/null 2>&1 || true
  fi
}

reload_hypr() {
  if command -v hyprctl >/dev/null && [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]; then
    hyprctl reload >/dev/null 2>&1 || true
  fi
}

