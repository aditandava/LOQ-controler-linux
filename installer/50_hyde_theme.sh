if [ -d "$CONFIG/hyde" ]; then
  say "Adding the HyDE wallbash theme"
  install -Dm644 "$work/loq-center.dcol" "$DCOL"
  if command -v hyde-shell >/dev/null; then
    hyde-shell reload >/dev/null 2>&1 || say "Change your wallpaper once to apply the colours."
  else
    say "Change your wallpaper once to apply the colours."
  fi
else
  say "HyDE config folder not found; the built-in colours will be used."
fi

