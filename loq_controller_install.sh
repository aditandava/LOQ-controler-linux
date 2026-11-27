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
# App icon: downloaded from the icon folder of the project on GitHub.
# To use a different file, run:  LOQ_ICON_URL=https://example.com/my-icon.svg bash loq_controller_install.sh
ICON_FILE="loq-center.svg"
ICON_BASE="https://github.com/aditandava/LOQ-controler-linux/raw"
ICON="$DATA/icons/hicolor/scalable/apps/$ICON_FILE"
LUA_MAIN="$CONFIG/hypr/hyprland.lua"
LUA_OWN="$CONFIG/hypr/loq-center.lua"
CONF="$CONFIG/hypr/userprefs.conf"
BEGIN="-- >>> loq-center >>>"
END="-- <<< loq-center <<<"

say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run as your normal user, without sudo."

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
    for pkg in python python-gobject gtk3 polkit brightnessctl; do
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

cat > "$work/loq-center" <<'LOQ_FILE_LOQ_CENTER'
#!/usr/bin/python3
"""LOQ Center: a control panel for Lenovo LOQ and Legion laptops on Linux.

Everything shown is detected at runtime. A control only appears when the kernel
or a tool on this machine really provides it.
"""
import fcntl
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

VERSION = "1.10"
SYS = Path("/sys")
PROC = Path("/proc")
HELPER = "/usr/local/libexec/loq-center-helper"
COOLING_STATE = Path("/run/loq-center-cooling.json")
MUX_PENDING = Path("/run/loq-center-mux")  # written by the helper until the next reboot
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
PLUGIN_DIR = CONFIG_DIR / "loq-center" / "plugins"
THEME_FILE = CONFIG_DIR / "loq-center" / "theme.css"
HYPRIDLE_CONF = CONFIG_DIR / "hypr" / "hypridle.conf"
HYPRIDLE_SHARE = DATA_DIR / "hypr" / "hypridle.conf"

CHARGE_LABELS = {"Long_Life": "Battery care", "Standard": "Full charge", "Fast": "Rapid charge"}
PROFILE_LABELS = {
    "low-power": "Quiet", "quiet": "Quiet", "cool": "Cool", "balanced": "Balanced",
    "balanced-performance": "Balanced+", "performance": "Performance", "max-power": "Max power",
    "cooling": "Cooling", "custom": "Custom",
}
PPD_NAMES = {"low-power": "power-saver", "balanced": "balanced", "performance": "performance"}
TOGGLE_LABELS = {"fn_lock": "Fn lock", "camera_power": "Camera"}

# Sleep presets in minutes: (label, dim_sec, lock_sec, dpms_sec, suspend_sec)
IDLE_PRESETS = {
    5:  ("5 min",  120,  180,  240,  300),
    10: ("10 min", 300,  480,  540,  600),
    30: ("30 min", 600, 1200, 1500, 1800),
    0:  ("Never",    0,    0,    0,    0),
}

DEFAULT_HYPRIDLE_TEMPLATE = """$LOCKSCREEN = hyprlock

general {
    lock_cmd = $LOCKSCREEN
    unlock_cmd =
    before_sleep_cmd = loginctl lock-session
    after_sleep_cmd = hyprctl dispatch dpms on
    ignore_dbus_inhibit = false
}

listener {
    timeout = 120
    on-timeout = brightnessctl -s && brightnessctl s 1%
    on-resume = brightnessctl -r
}

listener {
    timeout = 180
    on-timeout = loginctl lock-session
}

listener {
    timeout = 240
    on-timeout = hyprctl dispatch dpms off
    on-resume = hyprctl dispatch dpms on
}

listener {
    timeout = 300
    on-timeout = systemctl suspend
}
"""


class ActionError(Exception):
    """A user-facing failure message."""


# ---------------------------------------------------------------- basic helpers

def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def read_int(path):
    try:
        return int(read(path))
    except (TypeError, ValueError):
        return None


def run(cmd, timeout=15):
    """Run a command and never raise. Returns (code, stdout, stderr)."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
        return done.returncode, done.stdout.strip(), done.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"{cmd[0]} is not installed"
    except subprocess.TimeoutExpired:
        return 124, "", f"{cmd[0]} did not answer in time"
    except OSError as err:
        return 126, "", str(err)


def have(tool):
    return shutil.which(tool) is not None


def helper(*args, timeout=120):
    """Run the root helper through polkit. timeout=None means never interrupt it."""
    if not os.path.exists(HELPER):
        raise ActionError("Root helper is missing. Run the installer again.")
    code, out, err = run(["pkexec", HELPER, *args], timeout=timeout)
    if code == 0:
        return out
    if code == 126:
        raise ActionError("Authentication was cancelled.")
    if code == 127:
        raise ActionError(err or "Not authorised. Is a polkit agent running?")
    raise ActionError(err or out or f"Helper failed with code {code}.")


# ---------------------------------------------------------------------- battery

def batteries():
    found = []
    for dev in sorted((SYS / "class/power_supply").glob("*")):
        if read(dev / "type") == "Battery" and dev.name.startswith("BAT"):
            found.append(dev)
    return found


def battery_info():
    bats = batteries()
    if not bats:
        return None
    bat = bats[0]
    watts = None
    power = read_int(bat / "power_now")
    if power is None:
        current, volts = read_int(bat / "current_now"), read_int(bat / "voltage_now")
        if current is not None and volts is not None:
            power = abs(current) * volts / 1_000_000
    if power is not None:
        watts = abs(power) / 1_000_000
    health = None
    for kind in ("energy", "charge"):
        full, design = read_int(bat / f"{kind}_full"), read_int(bat / f"{kind}_full_design")
        if full and design:
            health = min(100.0, full * 100 / design)
            break
    cycles = read_int(bat / "cycle_count")
    return {
        "capacity": read_int(bat / "capacity"),
        "status": read(bat / "status") or "Unknown",
        "watts": watts,
        "health": health,
        "cycles": cycles if cycles else None,
    }


def on_ac():
    for dev in (SYS / "class/power_supply").glob("*"):
        if read(dev / "type") == "Mains":
            return read(dev / "online") == "1"
    return None


def ideapad_dir():
    found = sorted((SYS / "bus/platform/drivers/ideapad_acpi").glob("VPC2004:*"))
    return found[0] if found else None


def charge_info():
    """Returns {"options": [...], "active": name or None, "note": str} or None."""
    for bat in batteries():
        node = bat / "charge_types"
        if not node.exists():
            continue
        text = read(node)
        if text is None:
            return {"options": ["Long_Life", "Standard", "Fast"], "active": None,
                    "note": "The firmware reports conflicting charge modes (seen after hibernate). "
                            "Choose a mode to repair it."}
        active = re.search(r"\[([^\]]+)\]", text)
        options = [o for o in text.replace("[", "").replace("]", "").split() if o in CHARGE_LABELS]
        if options:
            return {"options": options, "active": active.group(1) if active else None, "note": ""}
    dev = ideapad_dir()
    if dev and (dev / "conservation_mode").exists():
        value = read(dev / "conservation_mode")
        active = {"1": "Long_Life", "0": "Standard"}.get(value)
        return {"options": ["Long_Life", "Standard"], "active": active, "note": ""}
    return None


def charge_note(charge, battery, ac):
    """Explains the selected mode and what the battery is really doing."""
    if charge["note"]:
        return charge["note"]
    active = charge["active"]
    if active is None:
        return "The current charging mode could not be read."
    level = battery["capacity"] if battery else None
    if active == "Long_Life":
        text = "Battery care: stops at a Lenovo firmware limit (about 80% on many LOQ models)."
    else:
        text = ("Rapid charge: goes to 100%, faster mainly at lower levels." if active == "Fast"
                else "Full charge: goes to 100%.")
        if ac is False:
            text += " Plug in the charger."
        elif level is not None and level < 95 and battery["status"] != "Charging":
            text += " Not charging: unplug the charger for 10 seconds, then plug it in again."
    if level is not None:
        text += f"\nNow: {level}% · {battery['status']}"
    return text


def set_charge(mode):
    helper("set", "charge", mode)
    return f"Charging mode: {CHARGE_LABELS.get(mode, mode)}"


# ----------------------------------------------------------- hypridle sleep timer

def hypridle_running():
    code, _, _ = run(["pgrep", "-x", "hypridle"], timeout=3)
    return code == 0


def ensure_hypridle_conf():
    if HYPRIDLE_CONF.exists():
        return HYPRIDLE_CONF.read_text(errors="replace")
    HYPRIDLE_CONF.parent.mkdir(parents=True, exist_ok=True)
    if HYPRIDLE_SHARE.exists():
        text = HYPRIDLE_SHARE.read_text(errors="replace")
    else:
        text = DEFAULT_HYPRIDLE_TEMPLATE
    HYPRIDLE_CONF.write_text(text)
    return text


def classify_listener(block):
    low = block.lower()
    if "suspend" in low:
        return "suspend"
    if "dpms" in low:
        return "dpms"
    if "lock" in low:
        return "lock"
    if "brightnessctl" in low:
        return "dim"
    return "other"


def idle_info():
    """Detects current sleep timeout in minutes (5, 10, 30, or 0 for Never)."""
    if not have("hypridle"):
        return None
    if not hypridle_running():
        return {"active": 0, "note": "Idle timer is off (hypridle stopped). Screen will not lock or sleep automatically."}
    conf_path = HYPRIDLE_CONF if HYPRIDLE_CONF.exists() else HYPRIDLE_SHARE
    text = read(conf_path) or ""
    listeners = re.findall(r"listener\s*\{[^}]*\}", text, re.S)
    suspend_sec = None
    max_sec = 0
    for block in listeners:
        m = re.search(r"timeout\s*=\s*(\d+)", block)
        if not m:
            continue
        sec = int(m.group(1))
        max_sec = max(max_sec, sec)
        if classify_listener(block) == "suspend":
            suspend_sec = sec
    target_sec = suspend_sec if suspend_sec is not None else max_sec
    mins = round(target_sec / 60) if target_sec else 0
    active = mins if mins in (5, 10, 30) else None
    detail = f"Sleep after {mins} min of inactivity." if mins else "Custom hypridle timer active."
    return {"active": active, "note": f"{detail} Stages: dim → lock (hyprlock) → screen off → sleep."}


def restart_hypridle():
    code, _, _ = run(["systemctl", "--user", "list-unit-files", "hypridle.service"], timeout=4)
    if code == 0:
        r_code, _, _ = run(["systemctl", "--user", "restart", "hypridle.service"], timeout=5)
        if r_code == 0 and hypridle_running():
            return
    run(["pkill", "-x", "hypridle"], timeout=3)
    time.sleep(0.15)
    subprocess.Popen(["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def stop_hypridle():
    run(["systemctl", "--user", "stop", "hypridle.service"], timeout=4)
    run(["pkill", "-x", "hypridle"], timeout=3)


def set_idle(minutes):
    if not have("hypridle"):
        raise ActionError("hypridle is not installed.")
    minutes = int(minutes)
    if minutes not in IDLE_PRESETS:
        raise ActionError("Unsupported sleep timer value.")
    if minutes == 0:
        stop_hypridle()
        return "Sleep timer: Never (hypridle stopped)"

    _, dim_s, lock_s, dpms_s, susp_s = IDLE_PRESETS[minutes]
    stage_map = {"dim": dim_s, "lock": lock_s, "dpms": dpms_s, "suspend": susp_s}
    fallback_order = [dim_s, lock_s, dpms_s, susp_s]

    text = ensure_hypridle_conf()
    idx = 0

    def repl(match):
        nonlocal idx
        block = match.group(0)
        kind = classify_listener(block)
        new_timeout = stage_map.get(kind, fallback_order[min(idx, len(fallback_order) - 1)])
        idx += 1
        return re.sub(r"(timeout\s*=\s*)\d+", rf"\g<1>{new_timeout}", block, count=1)

    updated, count = re.subn(r"listener\s*\{[^}]*\}", repl, text, flags=re.S)
    if count == 0:
        updated = DEFAULT_HYPRIDLE_TEMPLATE
        updated = re.sub(r"listener\s*\{[^}]*\}", repl, updated, flags=re.S)
    elif "suspend" not in updated.lower():
        updated = updated.rstrip() + f"\n\nlistener {{\n    timeout = {susp_s}\n    on-timeout = systemctl suspend\n}}\n"

    try:
        HYPRIDLE_CONF.write_text(updated)
    except OSError as err:
        raise ActionError(f"Could not write {HYPRIDLE_CONF}: {err}")

    restart_hypridle()
    return f"Sleep timer set to {minutes} min (dim {dim_s // 60}m, lock {lock_s // 60}m, sleep {minutes}m)"


# ------------------------------------------------------------------ performance

def platform_profile_nodes():
    """(profile_path, choices_path). The Lenovo class device comes first, then the legacy ACPI file."""
    found = []
    for d in (SYS / "class/platform-profile").glob("platform-profile-*"):
        p, c = d / "profile", d / "choices"
        if p.exists() and c.exists():
            name = (read(d / "name") or "").lower()
            other = not any(k in name for k in ("lenovo", "ideapad", "legion"))
            found.append((other, "custom" not in (read(c) or "").split(), d.name, p, c))
    found.sort()
    if found and not found[0][0]:
        return found[0][3], found[0][4]
    legacy_p = SYS / "firmware/acpi/platform_profile"
    legacy_c = SYS / "firmware/acpi/platform_profile_choices"
    if legacy_p.exists() and legacy_c.exists():
        return legacy_p, legacy_c
    return (found[0][3], found[0][4]) if found else (None, None)


def cooling_available():
    node, _ = platform_profile_nodes()
    if node is not None or have("powerprofilesctl"):
        return True
    if any((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        return True
    if any((SYS / "class/powercap").glob("intel-rapl*")):
        return True
    dev = ideapad_dir()
    return bool(dev and (dev / "fan_mode").exists())


def override_state(sys_profile=None):
    """The helper's record of an active Cooling (or substitute Max power) mode, else None."""
    try:
        data = json.loads(read(COOLING_STATE) or "")
    except ValueError:
        return None
    applied = data.get("applied_profile")
    if sys_profile is not None and applied is not None and sys_profile != applied:
        return None
    return data


def mode_row(choices):
    """Always the same order: Quiet, Balanced, Performance, Max power, Cooling."""
    quiet = next((c for c in ("low-power", "quiet") if c in choices), None)
    row = [quiet] if quiet else []
    row += [c for c in ("balanced", "performance") if c in choices]
    if "max-power" in choices or "performance" in choices:
        row.append("max-power")
    return row + ["cooling"]


def _profile_result(choices, current):
    state = override_state(current)
    row = mode_row(choices)
    active = state.get("mode", "cooling") if state else current
    if active in ("low-power", "quiet"):
        active = row[0]
    return {"options": row, "active": active,
            "fans_direct": bool(state and state.get("fans_direct"))}


def profile_info():
    node, choices_node = platform_profile_nodes()
    if node is not None:
        current = read(node)
        choices = (read(choices_node) or "").split()
        if current and choices:
            return _profile_result(choices, current)
    if have("powerprofilesctl"):
        code, out, _ = run(["powerprofilesctl", "list"], timeout=5)
        choices = [k for k, v in PPD_NAMES.items() if re.search(rf"^\*?\s*{v}:", out, re.M)]
        if code == 0 and choices:
            _, now, _ = run(["powerprofilesctl", "get"], timeout=5)
            active = next((k for k, v in PPD_NAMES.items() if v == now), None)
            info = _profile_result(choices, None)
            if not override_state():
                info["active"] = active
            return info
    if cooling_available():
        return _profile_result([], None)
    return None


def set_profile(name):
    if name == "max-power" and on_ac() is False:
        raise ActionError("Plug in the charger before using Max power.")
    if name in ("cooling", "max-power") or COOLING_STATE.exists():
        out = helper("set", "profile", name)
        return out or f"Performance mode: {PROFILE_LABELS.get(name, name)}"
    node, _ = platform_profile_nodes()
    if name in PPD_NAMES and have("powerprofilesctl"):
        code, _, err = run(["powerprofilesctl", "set", PPD_NAMES[name]])
        if code == 0 and (node is None or read(node) == name):
            return f"Performance mode: {PROFILE_LABELS.get(name, name)}"
        if node is None:
            raise ActionError(err or "power-profiles-daemon refused the change.")
    out = helper("set", "profile", name)
    return out or f"Performance mode: {PROFILE_LABELS.get(name, name)}"


# ---------------------------------------------------------------- device toggles

def toggle_info():
    dev = ideapad_dir()
    found = {}
    if dev:
        for name in TOGGLE_LABELS:
            value = read(dev / name)
            if value in ("0", "1"):
                found[name] = value
    return found


def set_toggle(name, value):
    helper("set", "toggle", name, value)
    return f"{TOGGLE_LABELS[name]}: {'on' if value == '1' else 'off'}"


# ------------------------------------------------------------------- brightness

def led_info(path):
    value, top = read_int(path / "brightness"), read_int(path / "max_brightness")
    if value is None or not top:
        return None
    return {"name": path.name, "value": value, "max": top}


def backlight_info():
    if not have("brightnessctl"):
        return None
    devices = sorted((SYS / "class/backlight").glob("*"),
                     key=lambda p: (not p.name.startswith("intel"), p.name))
    for dev in devices:
        info = led_info(dev)
        if info:
            return info
    return None


def keyboard_info():
    if not have("brightnessctl"):
        return None
    for dev in sorted((SYS / "class/leds").glob("*kbd_backlight*")):
        info = led_info(dev)
        if info and info["max"] <= 10:
            return info
    return None


def set_led(device, value):
    code, _, err = run(["brightnessctl", "-q", "-d", device, "set", str(value)])
    if code != 0:
        raise ActionError(err or "brightnessctl failed.")


def set_brightness(percent):
    info = backlight_info()
    if not info:
        raise ActionError("No screen backlight found.")
    percent = max(5, min(100, int(percent)))
    set_led(info["name"], f"{percent}%")
    return f"Brightness: {percent}%"


def set_keyboard(level):
    info = keyboard_info()
    if not info:
        raise ActionError("No keyboard backlight found.")
    set_led(info["name"], int(level))
    return f"Keyboard light: {level}"


# ---------------------------------------------------------------------- display

def monitors():
    code, out, _ = run(["hyprctl", "-j", "monitors"], timeout=5)
    if code != 0:
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def internal_monitor():
    return next((m for m in monitors() if str(m.get("name", "")).startswith("eDP")), None)


def refresh_options(monitor):
    """Maps a rounded refresh rate to a Hyprland mode string at the current resolution."""
    found = {}
    for mode in monitor.get("availableModes", []):
        match = re.fullmatch(r"(\d+)x(\d+)@(\d+(?:\.\d+)?)Hz", str(mode))
        if not match:
            continue
        width, height, rate = int(match[1]), int(match[2]), float(match[3])
        if width == monitor.get("width") and height == monitor.get("height"):
            found.setdefault(round(rate), f"{width}x{height}@{match[3]}")
    return dict(sorted(found.items()))


def display_info():
    mon = internal_monitor()
    if not mon:
        return None
    return {"name": mon["name"], "options": refresh_options(mon),
            "active": round(float(mon.get("refreshRate", 0)))}


def set_refresh(rate):
    mon = internal_monitor()
    if not mon:
        raise ActionError("Built-in screen not found in Hyprland.")
    mode = refresh_options(mon).get(int(rate))
    name = str(mon["name"])
    if not mode or not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise ActionError(f"{rate} Hz is not available.")
    position = f"{int(mon.get('x', 0))}x{int(mon.get('y', 0))}"
    scale = f"{float(mon.get('scale', 1)):g}"
    turn = int(mon.get("transform", 0))
    lua = (f'hl.monitor({{ output = "{name}", mode = "{mode}", position = "{position}", '
           f"scale = {scale}, transform = {turn} }})")
    legacy = f"{name},{mode},{position},{scale},transform,{turn}"
    errors = []
    for cmd in (["hyprctl", "eval", lua], ["hyprctl", "keyword", "monitor", legacy]):
        code, out, err = run(cmd)
        errors.append(err or out)
        for _ in range(10):
            now = internal_monitor()
            if now and abs(float(now.get("refreshRate", 0)) - float(rate)) < 1.5:
                return f"Refresh rate: {rate} Hz (until Hyprland reloads)"
            if code != 0 or "can't" in out or "error" in out.lower():
                break
            time.sleep(0.2)
    raise ActionError("Hyprland did not change the refresh rate. " + " | ".join(filter(None, errors)))


# --------------------------------------------------------------------- graphics

def nvidia_state():
    """Reads sysfs only, so it never wakes a sleeping GPU."""
    for dev in (SYS / "bus/pci/devices").glob("*"):
        if read(dev / "vendor") == "0x10de" and (read(dev / "class") or "").startswith("0x03"):
            return read(dev / "power/runtime_status") or "unknown"
    return "off"


def panel_on_nvidia():
    drm = SYS / "class/drm"
    for connector in drm.glob("card*-eDP-*"):
        if read(connector / "status") == "connected":
            if read(drm / connector.name.split("-")[0] / "device/vendor") == "0x10de":
                return True
    return False


def gpu_mode():
    if not have("envycontrol"):
        return None
    code, out, _ = run(["envycontrol", "--query"])
    return out if code == 0 and out in ("integrated", "hybrid", "nvidia") else "unknown"


def gpu_stats():
    """Asks nvidia-smi. This wakes the GPU, so it only runs when the user asks."""
    fields = "temperature.gpu,power.draw,utilization.gpu,memory.used,memory.total"
    code, out, err = run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"])
    if code != 0 or not out:
        raise ActionError(err or out or "nvidia-smi failed.")
    values = [v.strip() for v in out.splitlines()[0].split(",")]
    if len(values) != 5:
        raise ActionError("Unexpected nvidia-smi output.")
    temp, watts, use, used, total = values
    return f"{temp} °C   {watts} W   {use}% load   {used} / {total} MiB"


def set_gpu(mode):
    return helper("gpu", mode, timeout=None)


def set_mux(mode):
    return helper("gpu", "mux", mode, timeout=None)


GPU_LABELS = {"integrated": "Integrated", "hybrid": "Hybrid", "dgpu": "dGPU only"}


def graphics_state():
    pending = read(MUX_PENDING)
    return {"config": gpu_mode(), "dgpu": panel_on_nvidia(),
            "pending": pending if pending in ("hybrid", "dgpu") else None}


def selected_gpu(state):
    # No envycontrol and a screen that is not on NVIDIA means plain hybrid
    return state["pending"] or ("dgpu" if state["dgpu"] else state["config"] or "hybrid")


def gpu_action(pick, state):
    """What a GPU button does: ("none" | "blocked" | "mux" | "envy", message)."""
    if pick == selected_gpu(state):
        return "none", f"Already set to {GPU_LABELS[pick]}."
    if pick == "integrated" and (state["dgpu"] or state["pending"] == "dgpu"):
        return "blocked", "The screen needs NVIDIA right now. Pick Hybrid and reboot first."
    if pick == "dgpu":
        if state["config"] == "integrated" and not state["dgpu"]:
            return "blocked", "Pick Hybrid and reboot first, then pick dGPU only."
        return "mux", ""
    if pick == "hybrid" and (state["dgpu"] or state["pending"]):
        return "mux", ""
    return "envy", ""


# ----------------------------------------------------------------------- sensors

def cpu_temperature():
    for hw in (SYS / "class/hwmon").glob("hwmon*"):
        if read(hw / "name") in ("coretemp", "k10temp"):
            value = read_int(hw / "temp1_input")
            if value is not None:
                return value / 1000
    return None


def fan_speeds():
    speeds = []
    for node in sorted((SYS / "class/hwmon").glob("hwmon*/fan*_input")):
        value = read_int(node)
        if value is not None:
            speeds.append(value)
    return speeds


class FanWatcher:
    """Fan RPM through the root helper (acpi_call). One helper process serves the whole session."""

    def __init__(self):
        self.process = None
        self.latest, self.stamp = [], 0.0

    def speeds(self):
        if self.process is None:
            if not os.path.exists(HELPER):
                return []
            try:
                self.process = subprocess.Popen(
                    ["pkexec", HELPER, "watch", "fans"], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            except OSError:
                return []
            threading.Thread(target=self._listen, daemon=True).start()
        # An old reading is worse than none
        return self.latest if time.monotonic() - self.stamp < 7 else []

    def _listen(self):
        for line in self.process.stdout:
            try:
                values = json.loads(line)
            except ValueError:
                continue
            if isinstance(values, list) and all(isinstance(v, int) for v in values):
                self.latest, self.stamp = values, time.monotonic()
        self.process.wait()  # never restarted, so a refusal cannot cause repeated prompts


class CpuMeter:
    def __init__(self):
        self.last = None

    def percent(self):
        text = read(PROC / "stat")
        if not text:
            return None
        values = [int(v) for v in text.splitlines()[0].split()[1:9]]
        idle, total = values[3] + values[4], sum(values)
        previous, self.last = self.last, (idle, total)
        if not previous or total <= previous[1]:
            return None
        busy = 1 - (idle - previous[0]) / (total - previous[1])
        return max(0.0, min(100.0, busy * 100))


def memory_info():
    values = {}
    for line in (read(PROC / "meminfo") or "").splitlines():
        key, _, rest = line.partition(":")
        if key in ("MemTotal", "MemAvailable"):
            values[key] = int(rest.split()[0]) / 1_048_576
    if len(values) != 2:
        return None
    return values["MemTotal"] - values["MemAvailable"], values["MemTotal"]


def snapshot(meter, watcher=None):
    return {
        "cpu_temp": cpu_temperature(), "cpu_use": meter.percent(), "memory": memory_info(),
        "fans": fan_speeds() or (watcher.speeds() if watcher else []), "battery": battery_info(), "ac": on_ac(), "charge": charge_info(),
        "profile": profile_info(), "idle": idle_info(),
        "toggles": toggle_info(), "backlight": backlight_info(), "keyboard": keyboard_info(),
        "display": display_info(), "nvidia": nvidia_state(),
    }


# ----------------------------------------------------------------------- presets

PRESETS = {
    "saver": ("Battery saver", ["low-power", "quiet"], min, 40),
    "daily": ("Daily", ["balanced"], max, 70),
    "boost": ("Performance", ["performance", "balanced-performance"], max, None),
}


def apply_preset(key):
    title, wanted, pick_rate, brightness = PRESETS[key]
    done, failed = [], []
    steps = []
    profile = profile_info()
    if profile:
        name = next((p for p in wanted if p in profile["options"]), None)
        if name:
            steps.append(lambda: set_profile(name))
    screen = display_info()
    if screen and screen["options"]:
        rate = pick_rate(screen["options"])
        if rate != screen["active"]:
            steps.append(lambda: set_refresh(rate))
    if brightness and backlight_info():
        steps.append(lambda: set_brightness(brightness))
    for step in steps:
        try:
            done.append(step())
        except ActionError as err:
            failed.append(str(err))
    if failed:
        raise ActionError(f"{title} partly applied. " + " ".join(failed))
    return f"{title} applied" if done else f"{title}: nothing to change"


# --------------------------------------------- settings per power source (auto switch)

AUTO_FILE = CONFIG_DIR / "loq-center" / "auto.json"
AUTO_SOURCES = {"ac": "On charger", "battery": "On battery"}
AUTO_KEYS = ("profile", "refresh", "idle", "brightness")
AUTO_BRIGHTNESS = (30, 50, 70, 100)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def clean_auto_value(key, value):
    """A saved value that makes sense, or None, which means 'leave this setting alone'."""
    if key == "profile":
        return value if isinstance(value, str) and re.fullmatch(r"[a-z-]{2,30}", value) else None
    if key == "refresh":
        return value if _is_int(value) and 24 <= value <= 500 else None
    if key == "idle":
        return value if _is_int(value) and value in IDLE_PRESETS else None
    if key == "brightness":
        return value if _is_int(value) and 5 <= value <= 100 else None
    return None


def load_auto():
    config = {"enabled": False, **{s: dict.fromkeys(AUTO_KEYS) for s in AUTO_SOURCES}}
    try:
        data = json.loads(AUTO_FILE.read_text())
    except (OSError, ValueError):
        return config
    if not isinstance(data, dict):
        return config
    config["enabled"] = data.get("enabled") is True
    for source in AUTO_SOURCES:
        saved = data.get(source)
        if isinstance(saved, dict):
            for key in AUTO_KEYS:
                config[source][key] = clean_auto_value(key, saved.get(key))
    return config


def save_auto(config):
    try:
        AUTO_FILE.parent.mkdir(parents=True, exist_ok=True)
        part = AUTO_FILE.with_suffix(".tmp")
        part.write_text(json.dumps(config, indent=2))
        part.replace(AUTO_FILE)
    except OSError as err:
        raise ActionError(f"Could not save {AUTO_FILE}: {err}")


def power_source():
    ac = on_ac()
    return None if ac is None else ("ac" if ac else "battery")


def apply_auto(source):
    """Applies the saved settings for "ac" or "battery". Only changes what is different."""
    entry = load_auto()[source]
    title = AUTO_SOURCES[source]
    steps = []

    want = entry["profile"]
    if want:
        now = profile_info()
        if now and want in now["options"] and now["active"] != want:
            steps.append(lambda: set_profile(want))
    rate = entry["refresh"]
    if rate:
        screen = display_info()
        if screen and rate in screen["options"] and screen["active"] != rate:
            steps.append(lambda: set_refresh(rate))
    minutes = entry["idle"]
    if minutes is not None:
        idle = idle_info()
        if idle is not None and idle["active"] != minutes:
            steps.append(lambda: set_idle(minutes))
    level = entry["brightness"]
    light = backlight_info()
    if level and light and round(light["value"] * 100 / light["max"]) != level:
        steps.append(lambda: set_brightness(level))

    done, failed = [], []
    for step in steps:
        try:
            done.append(step())
        except ActionError as err:
            failed.append(str(err))
    if failed:
        raise ActionError(f"{title}: " + " ".join(failed))
    return f"{title}: settings applied" if done else f"{title}: already set"


def daemon_lock_path():
    return Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "loq-center-auto.lock"


def daemon_running():
    try:
        with open(daemon_lock_path(), "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    except OSError:
        return False


def start_daemon():
    """Starts the background watcher unless it is already running."""
    if daemon_running():
        return
    try:
        subprocess.Popen([sys.executable, os.path.realpath(sys.argv[0]), "--daemon"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def _mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return 0


def ensure_session_env():
    """A process started early may lack the variables hyprctl and hypridle need. Find them.

    Returns True when a Hyprland session was found."""
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    os.environ["XDG_RUNTIME_DIR"] = runtime
    base = Path(runtime)
    signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if not signature or not (base / "hypr" / signature / ".socket.sock").exists():
        found = sorted((base / "hypr").glob("*/.socket.sock"), key=_mtime)
        if found:
            os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = found[-1].parent.name
        else:
            os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
    if not os.environ.get("WAYLAND_DISPLAY"):
        sockets = sorted(p.name for p in base.glob("wayland-[0-9]") if p.is_socket())
        if sockets:
            os.environ["WAYLAND_DISPLAY"] = sockets[0]
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def run_daemon(stop=lambda: False, interval=3.0, wait=90.0):
    """Applies the saved settings whenever the charger is plugged in or unplugged."""
    last, pending = None, None
    started = time.monotonic()
    while not stop():
        ready = ensure_session_env() or not have("hyprctl")
        source = power_source()
        if source is not None and source != last:
            last, pending = source, source
        if pending:
            if not load_auto()["enabled"]:
                pending = None
            elif ready or time.monotonic() - started > wait:
                try:
                    print(apply_auto(pending), flush=True)
                except ActionError as err:
                    print(f"Auto switch: {err}", file=sys.stderr, flush=True)
                pending = None
        time.sleep(interval)
    return 0


def daemon_main():
    try:
        handle = open(daemon_lock_path(), "w")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("The background service is already running.")
        return 0
    except OSError as err:
        print(f"Cannot start the background service: {err}", file=sys.stderr)
        return 1
    try:
        return run_daemon()
    except KeyboardInterrupt:
        return 0
    finally:
        handle.close()


# ------------------------------------------------------------------------ theme

BASE_COLORS = {
    "loq_bg": "#1e1e2e", "loq_surface": "#2a2b3d", "loq_border": "#45475a",
    "loq_fg": "#f5e9e4", "loq_muted": "#b4b7d1", "loq_accent": "#c79bf0", "loq_accent2": "#ebbcba",
    "loq_on_accent": "#1e1e2e",
}

RULES = """
window.loq { background-color: @loq_bg; color: @loq_fg; }
window.loq label { color: @loq_fg; text-shadow: none; }
window.loq label.title { font-size: 20px; font-weight: bold; color: @loq_accent; }
window.loq label.muted { color: @loq_muted; }
window.loq label.heading { font-weight: bold; color: @loq_accent2; }
window.loq label.value { font-size: 22px; font-weight: bold; }
window.loq label.error { color: #ff8f8f; }
window.loq .card { background-color: @loq_surface; border: 1px solid @loq_border;
  border-radius: 14px; padding: 12px; }
window.loq button { background-image: none; background-color: @loq_surface; color: @loq_fg;
  border: 1px solid @loq_border; border-radius: 10px; padding: 8px 12px;
  box-shadow: none; text-shadow: none; }
window.loq button:hover { border-color: @loq_accent; }
window.loq button:focus { border-color: @loq_accent2; }
window.loq button.active, window.loq button:checked { background-color: @loq_accent;
  border-color: @loq_accent; }
window.loq button.active label, window.loq button:checked label { color: @loq_on_accent;
  font-weight: bold; }
window.loq button:disabled { opacity: 0.55; }
window.loq progressbar trough { background-image: none; background-color: @loq_border;
  border: none; border-radius: 4px; min-height: 6px; }
window.loq progressbar progress { background-image: none; background-color: @loq_accent;
  border: none; border-radius: 4px; min-height: 6px; }
window.loq scale trough { background-color: @loq_border; min-height: 6px; }
window.loq scale highlight { background-color: @loq_accent; }
window.loq scale slider { background-image: none; background-color: @loq_accent2;
  min-width: 18px; min-height: 18px; }
"""


def build_css(theme_text):
    """Defaults, overridden only by well-formed colour lines from the wallbash theme."""
    colors = dict(BASE_COLORS)
    for name, value in re.findall(r"@define-color\s+(loq_\w+)\s+(#[0-9A-Fa-f]{6})\s*;", theme_text or ""):
        if name in colors:
            colors[name] = value
    return "".join(f"@define-color {k} {v};\n" for k, v in colors.items()) + RULES


# -------------------------------------------------------------------------- GUI

def start_gui():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as err:
        print(f"GTK is not available: {err}\nInstall python-gobject and gtk3 (or python3-gi).",
              file=sys.stderr)
        return 1
    if Gdk.Display.get_default() is None:
        print("No graphical session detected.", file=sys.stderr)
        return 1
    GLib.set_prgname("loq-center")
    Gtk.Window.set_default_icon_name("loq-center")
    app = Gtk.Application(application_id="dev.loqcenter.App")
    state = {}

    def activate(_app):
        if "ui" not in state:
            state["ui"] = Window(app, Gtk, Gdk, GLib)
        state["ui"].window.present()

    app.connect("activate", activate)
    return app.run([])


class Choice:
    """A row of buttons where the active one is highlighted."""

    def __init__(self, ui, on_pick):
        self.ui, self.on_pick = ui, on_pick
        self.box = ui.Gtk.Box(spacing=8)
        self.box.set_homogeneous(True)
        self.options, self.buttons = None, {}

    def update(self, options, active):
        options = list(options)
        if options != self.options:
            for child in self.box.get_children():
                child.destroy()
            self.options, self.buttons = options, {}
            for value, label in options:
                button = self.ui.Gtk.Button(label=label)
                button.connect("clicked", lambda _w, v=value: self.on_pick(v))
                button.set_sensitive(not self.ui.busy)
                self.box.pack_start(button, True, True, 0)
                self.buttons[value] = button
                self.ui.actions.append(button)
            self.box.show_all()
        for value, button in self.buttons.items():
            context = button.get_style_context()
            if value == active:
                context.add_class("active")
            else:
                context.remove_class("active")


def spin_rate(rpm):
    """Turns per second shown on screen for a fan speed. A stopped fan does not turn.

    The real speed is far too fast to draw, so this only has to look faster when the fan is
    faster. It is capped so the blades never seem to turn backwards on screen."""
    if not rpm or rpm <= 0:
        return 0.0
    return min(2.4, 0.25 + rpm / 2600.0)


def draw_fan(cr, width, height, angle, colors, active=True, blades=5):
    """Draws a small fan with its blades turned by `angle` radians."""
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 2
    cr.set_line_width(2)
    cr.set_source_rgba(*colors["ring"])
    cr.new_path()
    cr.arc(cx, cy, radius, 0, 2 * math.pi)
    cr.stroke()
    blade = colors["blade"] if active else (*colors["idle"][:3], 0.45)
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(angle)
    for _ in range(blades):
        cr.new_path()
        cr.move_to(radius * 0.16, -radius * 0.04)
        cr.curve_to(radius * 0.28, -radius * 0.70, radius * 0.80, -radius * 0.62,
                    radius * 0.90, -radius * 0.14)
        cr.curve_to(radius * 0.62, -radius * 0.02, radius * 0.40, radius * 0.10,
                    radius * 0.16, radius * 0.08)
        cr.close_path()
        cr.set_source_rgba(*blade)
        cr.fill()
        cr.rotate(2 * math.pi / blades)
    cr.restore()
    cr.new_path()
    cr.set_source_rgba(*(colors["hub"] if active else (*colors["idle"][:3], 0.6)))
    cr.arc(cx, cy, radius * 0.17, 0, 2 * math.pi)
    cr.fill()


class FanWheel:
    """A small fan on the Dashboard. It turns faster when the fan really runs faster."""

    def __init__(self, ui, size=60):
        self.ui = ui
        self.area = ui.Gtk.DrawingArea()
        self.area.set_size_request(size, size)
        self.area.connect("draw", self.on_draw)
        self.angle = 0.0
        self.speed = 0.0   # turns per second drawn right now; eases towards the target
        self.target = 0.0
        self.rpm = None    # None: no reading

    def set_rpm(self, rpm):
        changed = (rpm is None) != (self.rpm is None)
        self.rpm = rpm
        self.target = spin_rate(rpm)
        if changed:
            self.area.queue_draw()

    def step(self, dt):
        """Moves the blades for dt seconds. Speeding up and slowing down is gradual."""
        self.speed += (self.target - self.speed) * min(1.0, dt * 3.0)
        if abs(self.speed - self.target) < 0.01:
            self.speed = self.target
        if self.speed <= 0:
            return False
        self.angle = (self.angle + self.speed * 2 * math.pi * dt) % (2 * math.pi)
        self.area.queue_draw()
        return True

    def on_draw(self, area, cr):
        context = area.get_style_context()

        def pick(name, fallback):
            found, color = context.lookup_color(name)
            return (color.red, color.green, color.blue, 1.0) if found else fallback

        colors = {"ring": pick("loq_border", (0.27, 0.28, 0.35, 1.0)),
                  "blade": pick("loq_accent", (0.78, 0.61, 0.94, 1.0)),
                  "hub": pick("loq_accent2", (0.92, 0.74, 0.73, 1.0)),
                  "idle": pick("loq_muted", (0.70, 0.72, 0.82, 1.0))}
        draw_fan(cr, area.get_allocated_width(), area.get_allocated_height(),
                 self.angle, colors, self.rpm is not None)
        return False


class Window:
    def __init__(self, app, Gtk, Gdk, GLib):
        self.Gtk, self.Gdk, self.GLib = Gtk, Gdk, GLib
        self.busy = False
        self.reading = False
        self.gpu_current = None  # graphics_state() once it is read
        self.actions = []
        self.meter = CpuMeter()
        self.fan_watcher = FanWatcher()
        self.theme_stamp = None
        self.fan_wheels = []
        self.spin_last = time.monotonic()
        self.auto_last = None  # power source seen on the previous refresh
        self.auto_options = {"profile": [], "refresh": [], "idle": False, "brightness": False}
        self.Choice = Choice
        self.ActionError = ActionError
        self.CONFIG_DIR = CONFIG_DIR
        self.DATA_DIR = DATA_DIR
        self.THEME_FILE = THEME_FILE
        self.read = read
        self.plugin_providers = []
        self.provider = Gtk.CssProvider()
        self.load_theme()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)

        self.window = Gtk.ApplicationWindow(application=app, title="LOQ Center")
        self.window.set_default_size(760, 580)
        self.window.get_style_context().add_class("loq")
        self.window.connect("key-press-event", self.on_key)
        self.window.connect("delete-event", self.on_close)

        root = self.vbox(12)
        root.set_border_width(18)
        self.window.add(root)
        root.pack_start(self.label("LOQ Center", "title"), False, False, 0)
        self.subtitle = self.label("Reading hardware…", "muted")
        root.pack_start(self.subtitle, False, False, 0)

        self.stack = Gtk.Stack()
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_homogeneous(True)
        root.pack_start(switcher, False, False, 0)
        root.pack_start(self.stack, True, True, 0)
        self.build_dashboard()
        self.build_power()
        self.build_auto()
        self.build_display()
        self.build_graphics()
        self.load_plugins()

        self.status = self.label("Ready", "muted")
        root.pack_end(self.status, False, False, 0)
        self.window.show_all()
        self.refresh()
        self.refresh_gpu_mode()
        GLib.timeout_add_seconds(2, self.tick)
        GLib.timeout_add(33, self.spin)
        if load_auto()["enabled"]:
            start_daemon()  # keeps switching after this window is closed

    # ---- widgets
    def vbox(self, spacing):
        return self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=spacing)

    def label(self, text, style=None):
        widget = self.Gtk.Label(label=text)
        widget.set_xalign(0)
        widget.set_line_wrap(True)
        widget.set_max_width_chars(60)
        if style:
            widget.get_style_context().add_class(style)
        return widget

    def page(self, name, title):
        scroller = self.Gtk.ScrolledWindow()
        box = self.vbox(12)
        scroller.add(box)
        self.stack.add_titled(scroller, name, title)
        return box

    def card(self, parent, heading):
        box = self.vbox(8)
        box.get_style_context().add_class("card")
        box.pack_start(self.label(heading, "heading"), False, False, 0)
        parent.pack_start(box, False, False, 0)
        return box

    def button(self, text, callback):
        widget = self.Gtk.Button(label=text)
        widget.connect("clicked", lambda _w: callback())
        self.actions.append(widget)
        return widget

    def add(self, parent, widget):
        parent.pack_start(widget, False, False, 0)
        return widget

    def add_css(self, css_text):
        prov = self.Gtk.CssProvider()
        prov.load_from_data(css_text.encode())
        self.Gtk.StyleContext.add_provider_for_screen(
            self.Gdk.Screen.get_default(), prov, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 2)
        self.plugin_providers.append(prov)
        return prov

    def load_plugins(self):
        if not PLUGIN_DIR.is_dir():
            return
        for path in sorted(PLUGIN_DIR.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f"loq_plugin_{path.stem}", path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if callable(getattr(mod, "register", None)):
                        mod.register(self)
            except Exception as err:
                print(f"Plugin {path.name} failed: {err}", file=sys.stderr)

    # ---- pages
    def build_dashboard(self):
        page = self.page("dashboard", "Dashboard")
        grid = self.Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        page.pack_start(grid, False, False, 0)
        self.stats = {}
        items = [("cpu_temp", "CPU temperature"), ("cpu_use", "CPU load"), ("memory", "Memory"),
                 ("battery", "Battery"), ("watts", "Battery power"), ("fans", "Fans")]
        for index, (key, title) in enumerate(items):
            box = self.vbox(6)
            box.get_style_context().add_class("card")
            self.add(box, self.label(title, "muted"))
            value = self.add(box, self.label("…", "value"))
            bar = None
            if key in ("cpu_temp", "cpu_use", "memory", "battery"):
                bar = self.add(box, self.Gtk.ProgressBar())
            if key == "fans":
                wheels = self.Gtk.Box(spacing=10)
                for _ in range(2):
                    wheel = FanWheel(self)
                    wheels.pack_start(wheel.area, False, False, 0)
                    self.fan_wheels.append(wheel)
                self.add(box, wheels)
            self.stats[key] = (value, bar)
            grid.attach(box, index % 3, index // 3, 1, 1)
        card = self.card(page, "One-click presets")
        row = self.Gtk.Box(spacing=8)
        row.set_homogeneous(True)
        for key, preset in PRESETS.items():
            row.pack_start(self.button(preset[0], lambda k=key: self.act(lambda: apply_preset(k))),
                           True, True, 0)
        self.add(card, row)

    def build_power(self):
        page = self.page("power", "Power")
        card = self.card(page, "Performance mode")
        self.profile_row = Choice(self, lambda v: self.act(lambda: set_profile(v)))
        self.add(card, self.profile_row.box)
        self.profile_note = self.add(card, self.label("", "muted"))
        card = self.card(page, "Battery charging")
        self.charge_row = Choice(self, lambda v: self.act(lambda: set_charge(v)))
        self.add(card, self.charge_row.box)
        self.charge_note = self.add(card, self.label("", "muted"))
        self.idle_card = self.card(page, "Sleep & idle timer (hypridle)")
        self.idle_row = Choice(self, lambda v: self.act(lambda: set_idle(v)))
        self.add(self.idle_card, self.idle_row.box)
        self.idle_note = self.add(self.idle_card, self.label("", "muted"))
        card = self.card(page, "Battery health")
        self.health = self.add(card, self.label("…"))

    def build_auto(self):
        page = self.page("auto", "Auto")
        card = self.card(page, "Switch settings when the charger changes")
        self.auto_enable = Choice(self, lambda v: self.pick_auto_enabled(v == "on"))
        self.add(card, self.auto_enable.box)
        self.auto_note = self.add(card, self.label("", "muted"))
        self.auto_rows = {}
        for source, title in AUTO_SOURCES.items():
            card = self.card(page, title)
            rows = {}
            for key, heading in (("profile", "Performance mode"), ("refresh", "Refresh rate"),
                                 ("idle", "Sleep timer"), ("brightness", "Brightness")):
                box = self.vbox(4)
                self.add(box, self.label(heading, "muted"))
                row = Choice(self, lambda v, s=source, k=key: self.pick_auto(s, k, v))
                self.add(box, row.box)
                self.add(card, box)
                rows[key] = (box, row)
            self.auto_rows[source] = rows
        card = self.card(page, "Try it")
        self.add(card, self.button("Apply the settings for the current power source",
                                   self.apply_auto_now))
        self.add(card, self.label("Keep means that setting is left as it is.", "muted"))

    def auto_view(self, config=None):
        config = config or load_auto()
        self.auto_enable.update([("on", "On"), ("off", "Off")], "on" if config["enabled"] else "off")
        if not config["enabled"]:
            self.auto_note.set_text("Off. Choose the settings below, then turn it on.")
        elif daemon_running():
            self.auto_note.set_text("On. A background service applies these settings when you plug in "
                                    "or unplug the charger, even with this window closed.")
        else:
            self.auto_note.set_text("On, but the background service is not running yet. "
                                    "It starts when you log in or open this window.")
        options = self.auto_options
        for source, rows in self.auto_rows.items():
            entry = config[source]
            profiles = [p for p in options["profile"] if not (source == "battery" and p == "max-power")]
            choices = {
                "profile": [(p, PROFILE_LABELS.get(p, p)) for p in profiles],
                "refresh": [(r, f"{r} Hz") for r in options["refresh"]],
                "idle": [(k, v[0]) for k, v in IDLE_PRESETS.items()] if options["idle"] else [],
                "brightness": [(b, f"{b}%") for b in AUTO_BRIGHTNESS] if options["brightness"] else [],
            }
            for key, (box, row) in rows.items():
                available = choices[key]
                self.visible(box, bool(available))
                if available:
                    known = [value for value, _label in available]
                    active = entry[key] if entry[key] in known else "keep"
                    row.update([("keep", "Keep")] + available, active)

    def pick_auto(self, source, key, value):
        try:
            config = load_auto()
            config[source][key] = None if value == "keep" else value
            save_auto(config)
        except ActionError as err:
            self.say(str(err), True)
            return
        self.auto_view(config)

    def pick_auto_enabled(self, enabled):
        try:
            config = load_auto()
            config["enabled"] = enabled
            save_auto(config)
        except ActionError as err:
            self.say(str(err), True)
            return
        source = power_source()
        if enabled:
            start_daemon()
        self.auto_view(config)
        if enabled and source and not self.busy:
            self.auto_last = source
            self.act(lambda: apply_auto(source), "Applying settings…")
        else:
            self.say("Auto switch is on." if enabled else "Auto switch is off.")

    def apply_auto_now(self):
        source = power_source()
        if source is None:
            self.say("The power source is unknown.", True)
            return
        self.act(lambda: apply_auto(source), "Applying settings…")

    def auto_check(self, data):
        """Fallback while no background service runs: switch when this window sees a change."""
        source = {True: "ac", False: "battery"}.get(data["ac"])
        if source is None:
            return
        if self.auto_last is None:
            self.auto_last = source
            return
        if source == self.auto_last or self.busy:
            return
        self.auto_last = source
        if load_auto()["enabled"] and not daemon_running():
            self.act(lambda: apply_auto(source), "Switching settings…")

    def build_display(self):
        page = self.page("display", "Display")
        card = self.card(page, "Refresh rate")
        self.rate_row = Choice(self, lambda v: self.act(lambda: set_refresh(v)))
        self.add(card, self.rate_row.box)
        self.rate_note = self.add(card, self.label("", "muted"))
        self.light_card = self.card(page, "Screen brightness")
        self.scale = self.Gtk.Scale.new_with_range(self.Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.scale_quiet = False
        self.scale_timer = None
        self.scale.connect("value-changed", self.on_scale)
        self.add(self.light_card, self.scale)
        self.keyboard_card = self.card(page, "Keyboard light")
        self.keyboard_row = Choice(self, lambda v: self.act(lambda: set_keyboard(v)))
        self.add(self.keyboard_card, self.keyboard_row.box)
        self.toggle_card = self.card(page, "Device switches")
        self.toggle_rows = {}
        for name, title in TOGGLE_LABELS.items():
            box = self.vbox(4)
            self.add(box, self.label(title))
            row = Choice(self, lambda v, n=name: self.act(lambda: set_toggle(n, v)))
            self.add(box, row.box)
            self.add(self.toggle_card, box)
            self.toggle_rows[name] = (box, row)

    def build_graphics(self):
        page = self.page("graphics", "Graphics")
        card = self.card(page, "NVIDIA GPU")
        self.gpu_power = self.add(card, self.label("…"))
        self.gpu_values = self.add(card, self.label("Live values are read only on request, "
                                                    "so the GPU can sleep.", "muted"))
        self.add(card, self.button("Read GPU sensors", self.read_gpu))
        card = self.card(page, "GPU mode (needs reboot)")
        self.mode_label = self.add(card, self.label("Checking…"))
        self.mode_row = Choice(self, self.ask_gpu)
        self.add(card, self.mode_row.box)
        self.add(card, self.label("Integrated: NVIDIA is switched off.\n"
                                  "Hybrid: Intel runs the desktop; start a game with prime-run.\n"
                                  "dGPU only: NVIDIA drives the screen. Uses more battery.",
                                  "muted"))
        self.reboot = self.add(card, self.button("Reboot now", self.ask_reboot))
        self.reboot.set_no_show_all(True)

    # ---- actions
    def set_busy(self, busy):
        self.busy = busy
        self.actions = [w for w in self.actions if w.get_parent() is not None]
        for widget in self.actions:
            widget.set_sensitive(not busy)
        self.scale.set_sensitive(not busy)

    def say(self, text, error=False):
        self.status.set_text(text)
        context = self.status.get_style_context()
        if error:
            context.add_class("error")
        else:
            context.remove_class("error")

    def background(self, work, done):
        def runner():
            try:
                result, error = work(), None
            except ActionError as err:
                result, error = None, str(err)
            except Exception as err:
                result, error = None, f"Unexpected error: {type(err).__name__}: {err}"

            def finish():
                done(result, error)
                return False

            self.GLib.idle_add(finish)

        threading.Thread(target=runner, daemon=True).start()

    def act(self, work, message="Working…", after=None):
        if self.busy:
            return
        self.set_busy(True)
        self.say(message)

        def done(result, error):
            self.set_busy(False)
            self.say(error or result or "Done", bool(error))
            self.refresh()
            if after:
                after(error)

        self.background(work, done)

    def on_scale(self, scale):
        if self.scale_quiet:
            return
        if self.scale_timer:
            self.GLib.source_remove(self.scale_timer)
        self.scale_timer = self.GLib.timeout_add(200, self.apply_scale)

    def apply_scale(self):
        self.scale_timer = None
        value = self.scale.get_value()

        def done(result, error):
            self.say(error or result, bool(error))

        self.background(lambda: set_brightness(value), done)
        return False

    def read_gpu(self):
        def done(result, error):
            self.set_busy(False)
            self.gpu_values.set_text(error or result)
            self.say(error or "GPU sensors read", bool(error))

        if self.busy:
            return
        if nvidia_state() == "off":
            self.gpu_values.set_text("The NVIDIA GPU is switched off.")
            return
        self.set_busy(True)
        self.background(gpu_stats, done)

    def confirm(self, title, body):
        dialog = self.Gtk.MessageDialog(
            transient_for=self.window, modal=True, message_type=self.Gtk.MessageType.WARNING,
            buttons=self.Gtk.ButtonsType.OK_CANCEL, text=title)
        dialog.format_secondary_text(body)
        answer = dialog.run()
        dialog.destroy()
        return answer == self.Gtk.ResponseType.OK

    def ask_gpu(self, mode):
        if self.busy or self.gpu_current is None:
            return
        kind, message = gpu_action(mode, graphics_state())
        if kind in ("none", "blocked"):
            self.say(message, kind == "blocked")
            return
        if kind == "mux":
            title = f"Switch screen to {GPU_LABELS[mode]}?"
            body = "This changes a firmware setting. It takes effect after a reboot."
            if mode == "dgpu":
                body += ("\n\nBattery life will be much shorter. This is new and not yet tested "
                         "on real hardware.\n\nIf the screen stays black after reboot: restart, "
                         "press F2, and set Graphics Device back to the switchable option.")
                if os.environ.get("AQ_DRM_DEVICES"):
                    body += ("\n\nWARNING: AQ_DRM_DEVICES is set in your Hyprland config. "
                             "Remove it first, or the desktop may not start.")
            work, wait = (lambda: set_mux(mode)), "Asking the firmware…"
        else:
            title = f"Switch GPU to {GPU_LABELS[mode]}?"
            body = ("Save your work first. This rewrites driver settings and rebuilds the boot "
                    "image, which can take a few minutes. Do not power off until it finishes.\n\n"
                    "If the screen stays black after reboot, press Ctrl+Alt+F3, log in and run:\n"
                    "sudo envycontrol -s hybrid && sudo reboot")
            if mode == "integrated":
                body += "\n\nExternal screens on NVIDIA-wired ports (often HDMI) will stop working."
            work, wait = (lambda: set_gpu(mode)), "Switching GPU mode. Please wait…"
        if not self.confirm(title, body):
            return

        def after(error):
            self.refresh_gpu_mode()
            if not error:
                self.reboot.set_no_show_all(False)
                self.reboot.show_all()

        self.act(work, wait, after)

    def ask_reboot(self):
        if self.confirm("Reboot now?", "Unsaved work will be lost."):
            def reboot():
                code, _, err = run(["systemctl", "reboot"])
                if code != 0:
                    raise ActionError(err or "Reboot failed.")
                return "Rebooting…"
            self.act(reboot)

    def refresh_gpu_mode(self):
        def done(state, error):
            self.gpu_current = state
            if error:
                self.mode_label.set_text(error)
                return
            options = [(name, label) for name, label in GPU_LABELS.items()
                       if name != "integrated" or state["config"] is not None]
            if state["pending"]:
                text = f"{GPU_LABELS[state['pending']]} selected. Reboot to apply."
            elif state["dgpu"]:
                text = "Running now: dGPU only (the screen is on NVIDIA)."
            elif state["config"] is None:
                text = "Integrated mode needs the optional tool envycontrol (not installed)."
            else:
                text = f"Configured mode: {state['config']}"
            self.mode_label.set_text(text)
            self.mode_row.update(options, selected_gpu(state))

        self.background(graphics_state, done)

    # ---- refresh
    def spin(self):
        """Turns the Dashboard fans. Does nothing while another tab is showing."""
        now = time.monotonic()
        dt = min(now - self.spin_last, 0.25)
        self.spin_last = now
        if self.stack.get_visible_child_name() == "dashboard" and self.window.is_visible():
            for wheel in self.fan_wheels:
                wheel.step(dt)
        return True

    def tick(self):
        self.load_theme()
        self.refresh()
        return True

    def refresh(self):
        if self.reading:
            return
        self.reading = True

        def done(data, error):
            self.reading = False
            if error:
                self.say(error, True)
            else:
                self.show_data(data)

        self.background(lambda: snapshot(self.meter, self.fan_watcher), done)

    def stat(self, key, text, fraction=None):
        value, bar = self.stats[key]
        value.set_text(text)
        if bar is not None:
            bar.set_fraction(max(0.0, min(1.0, fraction or 0.0)))

    def show_data(self, data):
        temp, use, memory, battery = (data[k] for k in ("cpu_temp", "cpu_use", "memory", "battery"))
        self.stat("cpu_temp", "n/a" if temp is None else f"{temp:.0f} °C", (temp or 0) / 100)
        self.stat("cpu_use", "…" if use is None else f"{use:.0f}%", (use or 0) / 100)
        if memory:
            self.stat("memory", f"{memory[0]:.1f} / {memory[1]:.1f} GiB", memory[0] / memory[1])
        else:
            self.stat("memory", "n/a")
        if battery and battery["capacity"] is not None:
            self.stat("battery", f"{battery['capacity']}%", battery["capacity"] / 100)
        else:
            self.stat("battery", "n/a")
        watts = battery["watts"] if battery else None
        self.stat("watts", "n/a" if watts is None else f"{watts:.1f} W")
        self.stat("fans", "  ".join(f"{v}" for v in data["fans"]) + " RPM" if data["fans"] else "n/a")
        fans = data["fans"]
        for index, wheel in enumerate(self.fan_wheels):
            wheel.set_rpm(fans[index] if index < len(fans) else None)
            self.visible(wheel.area, index < max(1, len(fans)))

        source = {True: "On charger", False: "On battery", None: "Power source unknown"}[data["ac"]]
        status = f" · {battery['status']}" if battery else ""
        self.subtitle.set_text(source + status)

        profile = data["profile"]
        if profile:
            self.profile_row.update([(p, PROFILE_LABELS.get(p, p)) for p in profile["options"]],
                                    profile["active"])
            if profile["active"] == "cooling":
                fans = ("Fans at full speed." if profile["fans_direct"] else
                        "Fans are NOT at full speed: no working fan interface.")
                self.profile_note.set_text(f"Cooling (purple): low power. {fans} Pick another mode to restore.")
            elif profile["active"] == "max-power":
                self.profile_note.set_text(
                    "Max power (purple): high power. Keep the charger connected." if data["ac"] is not False else
                    "Charger unplugged. Plug it in and click Max power again.")
            else:
                active = PROFILE_LABELS.get(profile["active"], profile["active"] or "Unknown")
                self.profile_note.set_text(
                    f"Current: {active}. Fn+Q changes it too. Max power needs the charger.")
        else:
            self.profile_row.update([], None)
            self.profile_note.set_text("This kernel exposes no performance modes.")

        charge = data["charge"]
        if charge:
            self.charge_row.update([(c, CHARGE_LABELS[c]) for c in charge["options"]], charge["active"])
            self.charge_note.set_text(charge_note(charge, battery, data["ac"]))
        else:
            self.charge_row.update([], None)
            self.charge_note.set_text("Not available. Check that ideapad_laptop is loaded.")

        idle = data["idle"]
        self.visible(self.idle_card, idle is not None)
        if idle:
            self.idle_row.update([(k, v[0]) for k, v in IDLE_PRESETS.items()], idle["active"])
            self.idle_note.set_text(idle["note"])

        lines = []
        if battery:
            if battery["health"] is not None:
                lines.append(f"Capacity left compared with new: {battery['health']:.1f}%")
            if battery["cycles"] is not None:
                lines.append(f"Charge cycles: {battery['cycles']}")
        self.health.set_text("\n".join(lines) or "No health data reported.")

        screen = data["display"]
        if screen and screen["options"]:
            self.rate_row.update([(r, f"{r} Hz") for r in screen["options"]], screen["active"])
            self.rate_note.set_text(f"{screen['name']}: {screen['active']} Hz. "
                                    "Resets when Hyprland reloads.")
        else:
            self.rate_row.update([], None)
            self.rate_note.set_text("Built-in screen not found through hyprctl.")

        light = data["backlight"]
        self.visible(self.light_card, light is not None)
        if light and not self.scale_timer and not self.scale.has_focus():
            self.scale_quiet = True
            self.scale.set_value(round(light["value"] * 100 / light["max"]))
            self.scale_quiet = False

        keys = data["keyboard"]
        self.visible(self.keyboard_card, keys is not None)
        if keys:
            self.keyboard_row.update(
                [(n, "Off" if n == 0 else str(n)) for n in range(keys["max"] + 1)], keys["value"])

        toggles = data["toggles"]
        self.visible(self.toggle_card, bool(toggles))
        for name, (box, row) in self.toggle_rows.items():
            self.visible(box, name in toggles)
            if name in toggles:
                row.update([("1", "On"), ("0", "Off")], toggles[name])

        states = {"active": "awake", "suspended": "sleeping (saving power)",
                  "off": "switched off or not detected"}
        self.gpu_power.set_text(f"State: {states.get(data['nvidia'], data['nvidia'])}")

        self.auto_options = {
            "profile": profile["options"] if profile else [],
            "refresh": list(screen["options"]) if screen and screen["options"] else [],
            "idle": idle is not None,
            "brightness": light is not None,
        }
        self.auto_view()
        self.auto_check(data)

    def visible(self, widget, show):
        widget.set_no_show_all(not show)
        if show:
            widget.show_all()
        else:
            widget.hide()

    # ---- window
    def load_theme(self):
        try:
            stamp = THEME_FILE.stat().st_mtime_ns
        except OSError:
            stamp = 0
        if stamp == self.theme_stamp:
            return
        css = build_css(read(THEME_FILE))
        try:
            self.provider.load_from_data(css.encode())
            self.theme_stamp = stamp
        except self.GLib.Error as err:
            print(f"Theme not applied: {err}", file=sys.stderr)

    def on_key(self, _window, event):
        if event.keyval == self.Gdk.KEY_Escape:
            self.window.close()
            return True
        return False

    def on_close(self, *_):
        if self.busy:
            self.say("Please wait for the current task to finish.", True)
            return True
        return False


def main(argv):
    if argv[1:] == ["--version"]:
        print(VERSION)
        return 0
    if argv[1:] == ["--status"]:
        meter = CpuMeter()
        data = snapshot(meter)
        data["gpu_mode"] = gpu_mode()
        data["helper_installed"] = os.path.exists(HELPER)
        print(json.dumps(data, indent=2))
        return 0
    if argv[1:] == ["--daemon"]:
        return daemon_main()
    if argv[1:]:
        print("Usage: loq-center [--status | --version | --daemon]", file=sys.stderr)
        return 2
    return start_gui()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
LOQ_FILE_LOQ_CENTER

cat > "$work/loq-center-helper" <<'LOQ_FILE_LOQ_CENTER_HELPER'
#!/usr/bin/python3 -I
"""Root helper for LOQ Center, run through pkexec. Only whitelisted actions exist."""
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SYS = Path("/sys")
COOLING_STATE = Path("/run/loq-center-cooling.json")
ENVYCONTROL = "/usr/bin/envycontrol"
CHARGE_MODES = ("Standard", "Long_Life", "Fast")
TOGGLES = ("fn_lock", "camera_power")
GPU_MODES = {"integrated": [], "hybrid": ["--rtd3", "2"]}
CMDLINE = Path("/proc/cmdline")
MUX_PENDING = Path("/run/loq-center-mux")  # emptied by every reboot
GAMEZONE_GUID = "887B54E3-DDDC-4B2C-8B88-68A26A8835D0"
MUX_SUPPORTED, MUX_GET, MUX_SET = 0x28, 0x29, 0x2A  # GameZone "GSync" methods
MUX_MODES = {"hybrid": 0, "dgpu": 1}
MUX_LABELS = {"hybrid": "Hybrid", "dgpu": "dGPU only"}
BIOS_HINT = "You can still change it in the BIOS (F2 at startup, Graphics Device)."
PPD_NAMES = {"low-power": "power-saver", "balanced": "balanced", "performance": "performance"}
CLEAN_ENV = {"PATH": "/usr/bin:/usr/sbin:/bin:/sbin", "LANG": "C.UTF-8"}


class Fail(Exception):
    pass


def read(path):
    return path.read_text().strip()


def safe_read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def write(path, value):
    path.write_text(str(value) + "\n")


def safe_write(path, value):
    try:
        Path(path).write_text(str(value) + "\n")
        return True
    except OSError:
        return False


def ideapad(name):
    for dev in sorted((SYS / "bus/platform/drivers/ideapad_acpi").glob("VPC2004:*")):
        if (dev / name).exists():
            return dev / name
    return None


def platform_profile_nodes():
    """The Lenovo class device if present, else the legacy ACPI file, else any class device."""
    found = []
    for d in (SYS / "class/platform-profile").glob("platform-profile-*"):
        p, c = d / "profile", d / "choices"
        if p.exists() and c.exists():
            name = (safe_read(d / "name") or "").lower()
            other = not any(k in name for k in ("lenovo", "ideapad", "legion"))
            found.append((other, "custom" not in (safe_read(c) or "").split(), d.name, p, c))
    found.sort()
    if found and not found[0][0]:
        return [(found[0][3], found[0][4])]
    legacy_p = SYS / "firmware/acpi/platform_profile"
    legacy_c = SYS / "firmware/acpi/platform_profile_choices"
    if legacy_p.exists() and legacy_c.exists():
        return [(legacy_p, legacy_c)]
    return [(f[3], f[4]) for f in found]


def custom_profile_node():
    """The class device that accepts "custom". The legacy ACPI file rejects it since kernel 6.14."""
    dirs = sorted((SYS / "class/platform-profile").glob("platform-profile-*"),
                  key=lambda p: (not any(k in (safe_read(p / "name") or "").lower()
                                         for k in ("lenovo", "ideapad", "legion")), p.name))
    for d in dirs:
        if "custom" in (safe_read(d / "choices") or "").split():
            return d / "profile"
    return None


def wmi_fan_targets():
    """Fan RPM targets of the mainline lenovo_wmi_other driver. Writing 0 means automatic."""
    out = []
    for hw in lenovo_hwmon_dirs():
        if safe_read(hw / "name") == "lenovo_wmi_other":
            out.extend(sorted(hw.glob("fan*_target")))
    return out


def nvidia_smi(*args):
    exe = shutil.which("nvidia-smi", path=CLEAN_ENV["PATH"])
    if not exe:
        return None
    return subprocess.run([exe, *args], capture_output=True, text=True,
                          errors="replace", env=CLEAN_ENV, check=False)


def legion_fan_nodes():
    nodes = []
    for base in (SYS / "module/legion_laptop/drivers", SYS / "devices/platform"):
        if base.exists():
            nodes.extend(sorted(base.glob("**/fan_fullspeed")))
    seen, out = set(), []
    for n in nodes:
        r = str(n)
        if r not in seen and n.exists():
            seen.add(r)
            out.append(n)
    return out


def lenovo_hwmon_dirs():
    out = []
    for hw in sorted((SYS / "class/hwmon").glob("hwmon*")):
        name = (safe_read(hw / "name") or "").lower()
        if any(k in name for k in ("legion", "lenovo", "ideapad")):
            out.append(hw)
    return out


def set_charge(mode):
    if mode not in CHARGE_MODES:
        raise Fail("Unknown charge mode.")
    for bat in sorted((SYS / "class/power_supply").glob("BAT*")):
        node = bat / "charge_types"
        if not node.exists():
            continue
        try:
            listed = read(node).replace("[", "").replace("]", "").split()
        except OSError:
            listed = ["Standard", "Long_Life", "Fast"]  # unreadable: both modes are on
        if mode not in listed:
            raise Fail(f"{mode} is not supported by this battery.")
        write(node, mode)
        if f"[{mode}]" not in read(node):
            raise Fail("The firmware did not accept the charge mode.")
        return
    node = ideapad("conservation_mode")
    if node is None or mode == "Fast":
        raise Fail(f"{mode} is not supported on this machine.")
    value = "1" if mode == "Long_Life" else "0"
    write(node, value)
    if read(node) != value:
        raise Fail("The firmware did not accept the charge mode.")


OTHER_GUID = "DC2A8805-3A8C-41BA-A6F7-092E0089CD3B"
ACPI_CALL = Path("/proc/acpi/call")
ACPI_LOCK = Path("/run/loq-center-acpi.lock")
FULL_SPEED_ID = "0x04020000"  # Lenovo "Other Method" feature: fan full speed
FAN_RPM_IDS = ("0x04030001", "0x04030002")  # current RPM of fan 1 and fan 2


def wmi_method(guid):
    """ACPI path of a Lenovo WMI method block, such as \\_SB_.GZFD.WMAE, or None."""
    if safe_read(SYS / "class/dmi/id/sys_vendor") != "LENOVO":
        return None
    for dev in sorted((SYS / "bus/wmi/devices").glob(guid + "*")):
        object_id = safe_read(dev / "object_id") or ""
        if not re.fullmatch(r"[A-Z0-9]{2}", object_id):
            continue
        for parent in dev.resolve().parents:
            path = safe_read(parent / "firmware_node/path")
            if path and re.fullmatch(r"\\[A-Z0-9_.]+", path):
                return f"{path}.WM{object_id}"
    return None


def other_method():
    return wmi_method(OTHER_GUID)


def acpi_call(command):
    if not ACPI_CALL.exists():
        subprocess.run(["/usr/bin/modprobe", "acpi_call"], capture_output=True,
                       env=CLEAN_ENV, check=False)
    if not ACPI_CALL.exists():
        return None
    # /proc/acpi/call holds one reply for everybody: keep each write and read together
    with open(ACPI_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not safe_write(ACPI_CALL, command):
            return None
        reply = safe_read(ACPI_CALL)
    return reply.strip("\x00\n ") if reply else None


def full_speed_get(method):
    """0 or 1, or None when the firmware does not give a clear answer."""
    reply = acpi_call(f"{method} 0x0 0x11 {FULL_SPEED_ID}")
    return int(reply, 16) if reply in ("0x0", "0x1") else None


def full_speed_set(method, value):
    # Argument buffer: feature id then value, both 32-bit little endian
    acpi_call(f"{method} 0x0 0x12 b00000204{int(value):02x}000000")
    return full_speed_get(method) == value


def fan_rpm(method):
    speeds = []
    for feature in FAN_RPM_IDS:
        try:
            value = int(acpi_call(f"{method} 0x0 0x11 {feature}") or "", 16)
        except ValueError:
            continue
        if 0 <= value <= 10000:
            speeds.append(value)
    return speeds


def watch_fans():
    """Prints the fan speeds every 2 seconds until the app closes its end of the pipe. Read only."""
    method = other_method()
    if not method or not fan_rpm(method):
        raise Fail("Fan speed is not available through acpi_call on this machine.")
    try:
        while True:
            print(json.dumps(fan_rpm(method)), flush=True)
            time.sleep(2)
    except BrokenPipeError:
        os._exit(0)


def set_fans_full(state):
    """Tries each full-speed interface and returns the name of the one that confirmed it."""
    for node in legion_fan_nodes():
        if safe_write(node, "1") and safe_read(node) == "1":
            return "legion_laptop"
    method = other_method()
    if method:
        before = full_speed_get(method)
        if before is not None:
            state.setdefault("acpi_fan", before)
            if full_speed_set(method, 1):
                return "acpi_call"
    done = False
    for target in wmi_fan_targets():
        top = safe_read(target.with_name(target.name.replace("_target", "_max")))
        if top and safe_write(target, top):
            done = True
    return "lenovo_wmi_other" if done else None


def power_limits():
    """Custom-mode CPU and GPU wattage settings. Temperature and time limits are left alone."""
    found = []
    for attr in sorted((SYS / "class/firmware-attributes").glob("lenovo-wmi-other*/attributes/*")):
        name = attr.name
        if name.startswith(("ppt_", "gpu_nv_", "dgpu_")) and not name.endswith(("tau", "temp", "clk")):
            found.append(attr)
    return found


def set_power_limits(bound):
    """Writes each limit's firmware minimum or maximum. Returns how many were confirmed."""
    count = 0
    for attr in power_limits():
        value = safe_read(attr / bound)
        if value is not None and safe_write(attr / "current_value", value) \
                and safe_read(attr / "current_value") == value:
            count += 1
    return count


def nvidia_present():
    return any(safe_read(dev / "vendor") == "0x10de" and (safe_read(dev / "class") or "").startswith("0x03")
               for dev in (SYS / "bus/pci/devices").glob("*"))


def _collect_cooling_state():
    state = {"files": {}, "policies": {}, "rapl": {}, "wmi_other": {}}

    for p in [SYS / "devices/system/cpu/intel_pstate/no_turbo",
              SYS / "devices/system/cpu/intel_pstate/max_perf_pct",
              SYS / "devices/system/cpu/cpufreq/boost"]:
        val = safe_read(p)
        if val is not None:
            state["files"][str(p)] = val

    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        entry = {}
        for k in ("scaling_governor", "energy_performance_preference", "scaling_max_freq"):
            v = safe_read(pol / k)
            if v is not None:
                entry[k] = v
        if entry:
            state["policies"][str(pol)] = entry

    for cap in sorted((SYS / "class/powercap").glob("intel-rapl*")):
        if cap.name.count(":") > 1:
            continue
        c0 = safe_read(cap / "constraint_0_power_limit_uw")
        c1 = safe_read(cap / "constraint_1_power_limit_uw")
        if c0 is not None or c1 is not None:
            state["rapl"][str(cap)] = {"c0": c0, "c1": c1}

    for p in sorted((SYS / "class/drm").glob("card*/gt_max_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt_boost_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt/gt*/rps_max_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt/gt*/rps_boost_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/device/power_dpm_force_performance_level")):
        v = safe_read(p)
        if v is not None:
            state["files"][str(p)] = v

    for n in legion_fan_nodes():
        v = safe_read(n)
        if v is not None:
            state["files"][str(n)] = v

    state["fan_targets"] = {str(p): safe_read(p) or "0" for p in wmi_fan_targets()}
    return state


def _enter_custom(custom, state):
    """Switches to Custom (purple) and remembers its own power limits the first time."""
    if not safe_write(custom, "custom"):
        return False
    time.sleep(0.5)
    if safe_read(custom) != "custom":
        return False
    if not state.get("wmi_from_custom"):
        for attr in power_limits():
            value = safe_read(attr / "current_value")
            if value is not None:
                state["wmi_other"][str(attr / "current_value")] = value
        state["wmi_from_custom"] = True
    return True


def _save_state(state):
    COOLING_STATE.write_text(json.dumps(state))
    os.chmod(COOLING_STATE, 0o644)


def _restore_cooling():
    if not COOLING_STATE.exists():
        return
    try:
        state = json.loads(COOLING_STATE.read_text())
    except (OSError, ValueError):
        COOLING_STATE.unlink(missing_ok=True)
        return

    # Fan and power settings of Custom mode can only be put back while in Custom mode
    custom = custom_profile_node()
    if state.get("wmi_from_custom") and custom is not None and safe_write(custom, "custom"):
        time.sleep(0.5)

    if "acpi_fan" in state:
        method = other_method()
        if method and not full_speed_set(method, state["acpi_fan"]):
            print("Warning: could not confirm that fan full speed was switched off.", file=sys.stderr)

    for path_str, val in state.get("files", {}).items():
        safe_write(path_str, val)

    saved_targets = state.get("fan_targets", {})
    for target in wmi_fan_targets():
        safe_write(target, saved_targets.get(str(target), "0"))

    if state.get("nvidia_locked"):
        nvidia_smi("-rgc")

    for pol_str, vals in state.get("policies", {}).items():
        pol = Path(pol_str)
        for k in ("scaling_governor", "energy_performance_preference", "scaling_max_freq"):
            if k in vals:
                safe_write(pol / k, vals[k])

    for cap_str, vals in state.get("rapl", {}).items():
        cap = Path(cap_str)
        if vals.get("c0") is not None:
            if not safe_write(cap / "constraint_0_power_limit_uw", vals["c0"]):
                mx = safe_read(cap / "constraint_0_max_power_uw")
                if mx and mx != "0":
                    safe_write(cap / "constraint_0_power_limit_uw", mx)
        if vals.get("c1") is not None:
            safe_write(cap / "constraint_1_power_limit_uw", vals["c1"])

    for path_str, val in state.get("wmi_other", {}).items():
        safe_write(path_str, val)

    COOLING_STATE.unlink(missing_ok=True)


def _require_custom(title):
    custom = custom_profile_node()
    if custom is None:
        raise Fail(f"{title} needs Custom (purple) mode, but this kernel does not offer it. "
                   "Nothing was changed. Check: cat /sys/class/platform-profile/*/choices")
    return custom


def _apply_cooling():
    custom = _require_custom("Cooling")
    state = None
    if COOLING_STATE.exists():
        try:
            state = json.loads(COOLING_STATE.read_text())
        except (OSError, ValueError):
            state = None
        if state is None or state.get("mode", "cooling") != "cooling":
            _restore_cooling()
            state = None
    if state is None:
        state = _collect_cooling_state()

    # 1. Custom mode first: fan and power settings only work there. Never Performance.
    if not _enter_custom(custom, state):
        raise Fail("The firmware refused Custom (purple) mode. Performance mode was not selected.")
    state.update(mode="cooling", fans_direct=False, applied_profile="custom")
    _save_state(state)  # saved early, so another mode can always undo a partial change

    # 2. Lowest firmware power limits for CPU and GPU
    limits = set_power_limits("min_value")

    # 3. Low CPU clocks
    time.sleep(0.5)  # let power daemons react to the mode change before capping the CPU
    cpu_capped = any([
        safe_write(SYS / "devices/system/cpu/intel_pstate/no_turbo", "1"),
        safe_write(SYS / "devices/system/cpu/cpufreq/boost", "0"),
        safe_write(SYS / "devices/system/cpu/intel_pstate/max_perf_pct", "55"),
    ])

    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        govs = (safe_read(pol / "scaling_available_governors") or "").split()
        for g in ("powersave", "conservative", "schedutil"):
            if g in govs and safe_write(pol / "scaling_governor", g):
                break
        epps = (safe_read(pol / "energy_performance_available_preferences") or "").split()
        for e in ("power", "balance_power"):
            if e in epps and safe_write(pol / "energy_performance_preference", e):
                break
        if safe_read(pol / "scaling_driver") != "intel_pstate":
            try:
                mn = int(safe_read(pol / "cpuinfo_min_freq") or 0)
                mx = int(safe_read(pol / "cpuinfo_max_freq") or 0)
                if mx > mn > 0:
                    safe_write(pol / "scaling_max_freq", str(max(mn, int(mx * 0.55))))
            except ValueError:
                pass

    for cap in sorted((SYS / "class/powercap").glob("intel-rapl*")):
        if cap.name.count(":") > 1:
            continue
        if (cap / "constraint_0_power_limit_uw").exists():
            try:
                mx0 = int(safe_read(cap / "constraint_0_max_power_uw") or 0)
                pl1 = 25_000_000 if mx0 <= 0 else max(15_000_000, min(25_000_000, mx0))
                safe_write(cap / "constraint_0_power_limit_uw", str(pl1))
            except ValueError:
                pass
        if (cap / "constraint_1_power_limit_uw").exists():
            try:
                mx1 = int(safe_read(cap / "constraint_1_max_power_uw") or 0)
                pl2 = 35_000_000 if mx1 <= 0 else max(20_000_000, min(35_000_000, mx1))
                safe_write(cap / "constraint_1_power_limit_uw", str(pl2))
            except ValueError:
                pass

    # 4. Low GPU clocks
    for card in sorted((SYS / "class/drm").glob("card*")):
        if "-" in card.name:
            continue
        rpn = safe_read(card / "gt_RPn_freq_mhz")
        rp1 = safe_read(card / "gt_RP1_freq_mhz")
        if rpn or rp1:
            try:
                low_mhz = max(int(rpn or 300), int(rp1 or 450))
                for fn in ("gt_max_freq_mhz", "gt_boost_freq_mhz"):
                    if (card / fn).exists():
                        safe_write(card / fn, str(low_mhz))
                for gt in sorted(card.glob("gt/gt*")):
                    for fn in ("rps_max_freq_mhz", "rps_boost_freq_mhz"):
                        if (gt / fn).exists():
                            safe_write(gt / fn, str(low_mhz))
            except ValueError:
                pass
        amd_dpm = card / "device/power_dpm_force_performance_level"
        if amd_dpm.exists():
            safe_write(amd_dpm, "low")

    if nvidia_present():
        res = nvidia_smi("-lgc", "210,900")  # wakes a sleeping GPU once
        if res and res.returncode == 0:
            state["nvidia_locked"] = True

    # 5. Fans at full speed, last so that nothing above resets them
    fans = set_fans_full(state)
    state["fans_direct"] = bool(fans)
    _save_state(state)

    if safe_read(custom) != "custom":
        raise Fail("Another power service moved the laptop out of Custom mode. Click Cooling again.")
    fan_text = f"fans FULL ({fans})" if fans else "FANS NOT AT FULL SPEED (no working fan interface)"
    cpu = "CPU capped" if cpu_capped else "CPU cap refused"
    gpu = "GPU capped" if state.get("nvidia_locked") else "NVIDIA cap not confirmed"
    print(f"Cooling [custom/purple]: {fan_text}; {cpu}; {gpu}; {limits} firmware limits at minimum.")


def on_battery():
    for dev in (SYS / "class/power_supply").glob("*"):
        if safe_read(dev / "type") == "Mains":
            return safe_read(dev / "online") == "0"
    return False


def _write_profile(name):
    nodes = platform_profile_nodes()
    if nodes:
        wrote = False
        for node, choices_node in nodes:
            choices = (safe_read(choices_node) or "").split()
            if name == "custom" or name not in choices:
                continue
            write(node, name)
            if read(node) != name:
                raise Fail("The firmware did not accept the mode (is the charger connected?).")
            wrote = True
        if not wrote:
            raise Fail("That performance mode is not supported.")
    elif name in PPD_NAMES:
        ppd = shutil.which("powerprofilesctl", path=CLEAN_ENV["PATH"])
        if not ppd:
            raise Fail("No platform profile driver or powerprofilesctl found.")
        done = subprocess.run([ppd, "set", PPD_NAMES[name]], capture_output=True,
                              text=True, env=CLEAN_ENV, check=False)
        if done.returncode != 0:
            raise Fail(done.stderr.strip() or "powerprofilesctl refused the mode.")
    else:
        raise Fail("That performance mode is not supported.")


def _apply_max_power():
    if on_battery():
        raise Fail("Plug in the charger before using Max power.")
    nodes = platform_profile_nodes()
    choices = (safe_read(nodes[0][1]) or "").split() if nodes else []
    if "max-power" in choices:  # the firmware's own Extreme mode (purple)
        _restore_cooling()
        _write_profile("max-power")
        print("Max power [max-power/purple]: firmware Extreme mode is on.")
        return

    custom = _require_custom("Max power")
    _restore_cooling()
    state = _collect_cooling_state()
    if not _enter_custom(custom, state):
        raise Fail("The firmware refused Custom (purple) mode. Performance mode was not selected.")
    state.update(mode="max-power", applied_profile="custom")
    _save_state(state)
    limits = set_power_limits("max_value")
    time.sleep(0.5)
    safe_write(SYS / "devices/system/cpu/intel_pstate/no_turbo", "0")
    safe_write(SYS / "devices/system/cpu/cpufreq/boost", "1")
    safe_write(SYS / "devices/system/cpu/intel_pstate/max_perf_pct", "100")
    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        if "performance" in (safe_read(pol / "scaling_available_governors") or "").split():
            safe_write(pol / "scaling_governor", "performance")
        safe_write(pol / "energy_performance_preference", "performance")
    detail = (f"{limits} firmware power limits at maximum" if limits else
              "NO firmware power limits available, so Custom mode keeps its stored wattage")
    print(f"Max power [custom/purple]: {detail}; CPU unrestricted.")


def set_profile(name):
    if name == "cooling":
        _apply_cooling()
    elif name == "max-power":
        _apply_max_power()
    else:
        _restore_cooling()
        _write_profile(name)


def set_toggle(name, value):
    if name not in TOGGLES or value not in ("0", "1"):
        raise Fail("Unknown switch or value.")
    node = ideapad(name)
    if node is None:
        raise Fail("This machine does not have that switch.")
    write(node, value)
    if read(node) != value:
        raise Fail("The firmware did not accept the change.")


def panel_on_nvidia():
    drm = SYS / "class/drm"
    for connector in drm.glob("card*-eDP-*"):
        try:
            if read(connector / "status") != "connected":
                continue
            if read(drm / connector.name.split("-")[0] / "device/vendor") == "0x10de":
                return True
        except OSError:
            continue
    return False


def envy(*args):
    return subprocess.run([ENVYCONTROL, *args], capture_output=True, text=True,
                          errors="replace", env=CLEAN_ENV, check=False)


def panel_mode():
    """Which GPU drives the built-in screen right now: "hybrid", "dgpu" or Non