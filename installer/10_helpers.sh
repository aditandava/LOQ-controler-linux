say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run as your normal user, without sudo."

# Folder of this script when it is a real file (a clone of the project). Empty when it was
# started with: bash <(curl ...)
SELF_DIR=""
SELF="${BASH_SOURCE[0]:-$0}"
if [ -f "$SELF" ] && [ "${SELF#/dev/}" = "$SELF" ] && [ "${SELF#/proc/}" = "$SELF" ]; then
  SELF_DIR="$(cd "$(dirname "$SELF")" && pwd)"
fi

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

remove_hooks() {
  if [ -f "$LUA_MAIN" ] && grep -qF -- "$BEGIN" "$LUA_MAIN" && grep -qF -- "$END" "$LUA_MAIN"; then
    sed -i --follow-symlinks "/^$BEGIN\$/,/^$END\$/d" "$LUA_MAIN"
  fi
  if [ -f "$CONF" ]; then
    sed -i --follow-symlinks '/# loq-center$/d' "$CONF"
  fi
  rm -f "$LUA_OWN"
}

