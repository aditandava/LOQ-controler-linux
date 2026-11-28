remove_hooks() {
  if [ -f "$LUA_MAIN" ] && grep -qF -- "$BEGIN" "$LUA_MAIN" && grep -qF -- "$END" "$LUA_MAIN"; then
    sed -i --follow-symlinks "/^$BEGIN\$/,/^$END\$/d" "$LUA_MAIN"
  fi
  if [ -f "$CONF" ]; then
    sed -i --follow-symlinks '/# loq-center$/d' "$CONF"
  fi
  rm -f "$LUA_OWN"
}

