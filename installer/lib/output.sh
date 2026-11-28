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

