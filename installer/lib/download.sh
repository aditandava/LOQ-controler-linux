fetch() {  # fetch <url> <destination>
  if command -v curl >/dev/null; then
    curl -fsL --connect-timeout 10 --max-time 60 -o "$2" "$1"
  elif command -v wget >/dev/null; then
    wget -q -T 60 -O "$2" "$1"
  else
    return 1
  fi
}

# get_source <path in the project> <destination>: the copy next to this script, else from GitHub.
get_source() {
  local rel="$1" dest="$2" branch
  if [ -n "$SELF_DIR" ] && [ -f "$SELF_DIR/$rel" ]; then
    cp "$SELF_DIR/$rel" "$dest"
    return 0
  fi
  for branch in main master; do
    if fetch "$REPO_RAW/$branch/$rel" "$dest" && [ -s "$dest" ]; then
      return 0
    fi
  done
  return 1
}

