# Download the icon. If GitHub cannot be reached the app still works with a stock icon.
icon_ref="computer-laptop"
install_icon() {
  local tmp="$work/$ICON_FILE" url got=0 urls=()
  if [ -n "${LOQ_ICON_URL:-}" ]; then
    urls=("$LOQ_ICON_URL")
  else
    urls=("$ICON_BASE/main/icon/$ICON_FILE" "$ICON_BASE/master/icon/$ICON_FILE")
  fi
  for url in "${urls[@]}"; do
    if fetch "$url" "$tmp" && [ -s "$tmp" ] && grep -q '<svg' "$tmp"; then
      got=1
      break
    fi
  done
  if [ "$got" -eq 1 ]; then
    install -Dm644 "$tmp" "$ICON"
    refresh_icons
    icon_ref="loq-center"
    say "Icon installed"
  elif [ -f "$ICON" ]; then
    icon_ref="loq-center"
    say "Could not download the icon, so the one already installed was kept."
  else
    say "Could not download the icon from GitHub, so a stock icon is used. Run the installer again once the icon is uploaded."
  fi
}
install_icon

