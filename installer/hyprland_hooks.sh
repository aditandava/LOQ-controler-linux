key_taken() {
  command -v hyprctl >/dev/null || return 1
  hyprctl -j binds 2>/dev/null | /usr/bin/python3 -I -c 'import json, sys
try: binds = json.load(sys.stdin)
except ValueError: sys.exit(1)
hit = any(b.get("modmask") == 65 and str(b.get("key", "")).upper() == "L"
          and "LOQ Center" not in str(b.get("description", ""))
          and "loq-center" not in str(b.get("arg", "")) for b in binds)
sys.exit(0 if hit else 1)'
}

remove_hooks
bind_key=1
if key_taken; then
  bind_key=0
  say "SUPER+SHIFT+L is already in use, so no shortcut was added."
fi

if [ -f "$LUA_MAIN" ] && [ -f "$DATA/hypr/hyde.lua" ]; then
  if grep -qE '^return([^A-Za-z0-9_]|$)' "$LUA_MAIN"; then
    say "hyprland.lua ends with 'return', so it was not edited. Open LOQ Center from the app launcher."
  else
    cp "$LUA_MAIN" "$LUA_MAIN.before-loq-center"
    {
      if [ "$bind_key" -eq 1 ]; then
        echo 'hl.bind("SUPER + SHIFT + L", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.local/bin/loq-center"), { description = "[Utilities] LOQ Center" })'
      fi
      echo 'hl.window_rule({ name = "loq-center", match = { class = "^(loq-center|dev[.]loqcenter[.]App)$" }, float = true, center = true })'
      # Starts the plug-in / unplug watcher at login. Wrapped so a Hyprland without this call cannot break the config.
      echo 'pcall(function() hl.on("hyprland.start", function() pcall(hl.exec_cmd, os.getenv("HOME") .. "/.local/bin/loq-center --daemon") end) end)'
    } > "$LUA_OWN"
    [ -z "$(tail -c1 "$LUA_MAIN")" ] || echo >> "$LUA_MAIN"
    {
      echo "$BEGIN"
      echo "pcall(dofile, [[$LUA_OWN]])"
      echo "$END"
    } >> "$LUA_MAIN"
    reload_hypr
    say "Hyprland rule added (backup: $LUA_MAIN.before-loq-center)"
  fi
elif [ -f "$CONF" ] && [ ! -f "$DATA/hypr/hyde.lua" ]; then
  [ -z "$(tail -c1 "$CONF")" ] || echo >> "$CONF"
  echo 'exec-once = $HOME/.local/bin/loq-center --daemon # loq-center' >> "$CONF"
  if [ "$bind_key" -eq 1 ]; then
    echo 'bind = SUPER SHIFT, L, exec, $HOME/.local/bin/loq-center # loq-center' >> "$CONF"
    say "Shortcut added to userprefs.conf"
  fi
  reload_hypr
else
  say "No HyDE config recognised. Open LOQ Center from the app launcher."
fi

