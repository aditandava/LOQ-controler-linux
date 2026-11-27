#!/usr/bin/env bash
# LOQ Center installer for EndeavourOS / Arch with Hyprland and HyDE.
# Install:   bash loq_controller_install.sh
# Remove:    bash loq_controller_install.sh --uninstall
set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN="$HOME/.local/bin"
HELPER=/usr/local/libexec/loq-center-helper
POLICY=/usr/share/polkit-1/actions/dev.loqcenter.policy
DCOL="$CONFIG/hyde/wallbash/always/loq-center.dcol"
DESKTOP="$DATA/applications/loq-center.desktop"
# Where the project files are downloaded from (a fork can set LOQ_REPO_RAW to its own address).
REPO_RAW="${LOQ_REPO_RAW:-https://github.com/aditandava/LOQ-controler-linux/raw}"
# App icon: downloaded from the icon folder of the project.
# To use a different file, run:  LOQ_ICON_URL=https://example.com/my-icon.svg bash loq_controller_install.sh
ICON_FILE="loq-center.svg"
ICON_BASE="$REPO_RAW"
ICON="$DATA/icons/hicolor/scalable/apps/$ICON_FILE"
LUA_MAIN="$CONFIG/hypr/hyprland.lua"
LUA_OWN="$CONFIG/hypr/loq-center.lua"
CONF="$CONFIG/hypr/userprefs.conf"
BEGIN="-- >>> loq-center >>>"
END="-- <<< loq-center <<<"

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

install_deps() {
  if command -v pacman >/dev/null; then
    local missing=()
    for pkg in python python-gobject gtk3 polkit brightnessctl librsvg; do
      pacman -Q "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
    done
    if [ "${#missing[@]}" -gt 0 ]; then
      say "Installing: ${missing[*]}"
      sudo pacman -S --needed "${missing[@]}" || die "Package install failed. Run 'sudo pacman -Syu', then try again."
    fi
    if ! command -v envycontrol >/dev/null; then
      for aur_helper in yay paru; do
        if command -v "$aur_helper" >/dev/null; then
          say "Installing envycontrol via $aur_helper (optional, for GPU mode switching)"
          "$aur_helper" -S --needed --noconfirm envycontrol || true
          break
        fi
      done
      command -v envycontrol >/dev/null \
        || say "envycontrol not found — Integrated button hidden (install from AUR later if needed)."
    fi
  elif command -v apt-get >/dev/null; then
    local need=()
    command -v python3 >/dev/null || need+=(python3)
    python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
      || need+=(python3-gi gir1.2-gtk-3.0)
    command -v pkexec >/dev/null || need+=(pkexec)
    dpkg -s librsvg2-common >/dev/null 2>&1 || need+=(librsvg2-common)
    command -v brightnessctl >/dev/null || need+=(brightnessctl)
    if [ "${#need[@]}" -gt 0 ]; then
      say "Installing: ${need[*]}"
      sudo apt-get update && sudo apt-get install -y "${need[@]}" || die "apt-get install failed."
    fi
  elif command -v dnf >/dev/null; then
    local need=()
    command -v python3 >/dev/null || need+=(python3)
    python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
      || need+=(python3-gobject gtk3)
    command -v pkexec >/dev/null || need+=(polkit)
    command -v brightnessctl >/dev/null || need+=(brightnessctl)
    if [ "${#need[@]}" -gt 0 ]; then
      say "Installing: ${need[*]}"
      sudo dnf install -y "${need[@]}" || die "dnf install failed."
    fi
  elif command -v zypper >/dev/null; then
    local need=()
    command -v python3 >/dev/null || need+=(python3)
    python3 -c 'import gi; gi.require_version("Gtk","3.0"); from gi.repository import Gtk' >/dev/null 2>&1 \
      || need+=(python3-gobject-Gdk typelib-1_0-Gtk-3_0)
    command -v pkexec >/dev/null || need+=(polkit)
    command -v brightnessctl >/dev/null || need+=(brightnessctl)
    if [ "${#need[@]}" -gt 0 ]; then
      say "Installing: ${need[*]}"
      sudo zypper install -y "${need[@]}" || die "zypper install failed."
    fi
  else
    command -v python3 >/dev/null || die "python3 is required."
    command -v pkexec >/dev/null || die "polkit (pkexec) is required."
  fi
}

install_deps

# Fan full speed on many LOQ models goes through the acpi_call kernel module.
install_fan_module() {
  command -v pacman >/dev/null || return 0
  modinfo acpi_call >/dev/null 2>&1 && return 0
  local pkgs=(acpi_call-dkms) base
  for base in /usr/lib/modules/*/pkgbase; do
    [ -r "$base" ] && pkgs+=("$(cat "$base")-headers")
  done
  say "Installing ${pkgs[*]} (needed for fan full speed and dGPU only)"
  sudo pacman -S --needed "${pkgs[@]}" \
    || say "acpi_call was not installed. Cooling may not reach full fan speed."
}

install_fan_module
sudo modprobe acpi_call 2>/dev/null || say "acpi_call did not load (reboot, or check Secure Boot)."

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# The program files live in the src folder of the project. Use them from next to this script
# when it was cloned, otherwise download them.
for part in loq-center loq-center-helper dev.loqcenter.policy loq-center.dcol; do
  get_source "src/$part" "$work/$part" \
    || die "Could not get src/$part. Check your internet connection and that the file is in the src folder of the GitHub project."
done

say "Checking the files"
/usr/bin/python3 -I -c 'import sys
for f in sys.argv[1:]: compile(open(f, encoding="utf-8").read(), f, "exec")' \
  "$work/loq-center" "$work/loq-center-helper" || die "A file is damaged. Download the installer again."
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' \
  >/dev/null 2>&1 || die "Python GTK3 does not load. Install python-gobject/gtk3 (or python3-gi) and try again."

say "Installing the app (sudo is needed for the root helper)"
sudo install -Dm755 -o root -g root "$work/loq-center-helper" "$HELPER"
sudo install -Dm644 -o root -g root "$work/dev.loqcenter.policy" "$POLICY"
pkill -u "$(id -u)" -f 'loq-center --daemon' >/dev/null 2>&1 || true  # so the new version runs
install -Dm755 "$work/loq-center" "$BIN/loq-center"

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

mkdir -p "$(dirname "$DESKTOP")" "$CONFIG/loq-center"
cat > "$DESKTOP" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=LOQ Center
Comment=Battery, performance, display and GPU controls
Exec="$BIN/loq-center"
Icon=$icon_ref
Terminal=false
Categories=Settings;HardwareSettings;
StartupWMClass=loq-center
DESKTOP_EOF

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