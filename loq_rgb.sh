#!/usr/bin/env bash
# Copyright (C) 2026 aditandava
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# LOQ RGB — standalone RGB plugin & udev installer for LOQ Center.
#
# Run AFTER loq_controller_install.sh has been run:
#   bash loq_rgb.sh             # install RGB tab into LOQ Center + udev rules
#   bash loq_rgb.sh --uninstall # remove RGB tab and udev rules
#
# All RGB UI and USB/HID logic lives in this file; loq_controller_install.sh stays purely for
# Dashboard, Power, Display, and Graphics. You can freely edit this script
# and re-run it — loq_controller_install.sh loads the plugin automatically.

set -euo pipefail

RULES=/etc/udev/rules.d/99-ite-kbd.rules
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/loq-center"
PLUGIN_DIR="$CONFIG/plugins"
PLUGIN="$PLUGIN_DIR/rgb.py"
BIN="${HOME}/.local/bin/loq-center"

say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run as your normal user, without sudo."
if [ ! -x "$BIN" ] && ! command -v loq-center > /dev/null; then
  die "LOQ Center is not installed yet. Run loq_controller_install.sh first, then loq_rgb.sh."
fi

# ------------------------------------------------------------------ uninstall
if [ "${1:-}" = "--uninstall" ]; then
  say "Removing LOQ RGB plugin and udev rules"
  rm -f "$PLUGIN" "$CONFIG/rgb-enabled"
  rmdir "$PLUGIN_DIR" 2>/dev/null || true
  sudo rm -f "$RULES"
  sudo udevadm control --reload-rules 2>/dev/null || true
  sudo udevadm trigger --subsystem-match=usb --subsystem-match=hidraw 2>/dev/null || true
  say "Done. The LOQ RGB tab disappears next time LOQ Center opens."
  exit 0
fi

[ -z "${1:-}" ] || die "Unknown option: $1"

# ------------------------------------------------------------------ pyusb dep
if python3 -c "import usb.core" 2>/dev/null; then
  say "python-pyusb is already installed."
else
  say "Installing PyUSB (fallback USB backend)"
  if command -v pacman > /dev/null; then
    sudo pacman -S --needed python-pyusb || die "pacman install failed."
  elif command -v apt-get > /dev/null; then
    sudo apt-get update && sudo apt-get install -y python3-usb || die "apt-get install failed."
  elif command -v dnf > /dev/null; then
    sudo dnf install -y python3-pyusb || die "dnf install failed."
  elif command -v zypper > /dev/null; then
    sudo zypper install -y python3-pyusb || die "zypper install failed."
  else
    say "Unknown package manager — install PyUSB if hidraw permissions alone are not used."
  fi
fi

# ------------------------------------------------------------------ udev rules
# Edit PIDs freely for newer Lenovo LOQ / Legion / IdeaPad Gaming models.
say "Installing udev rules for ITE RGB keyboard"
sudo tee "$RULES" > /dev/null << 'RULES_EOF'
# ITE keyboard controllers (Lenovo LOQ / Legion / IdeaPad Gaming)
# All known 4-zone RGB keyboard PIDs (2020–2024 + new reports)
# Edit freely — rgb.py reads PIDs from this file automatically.

# 2024 models
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c995", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c994", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c993", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c995", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c994", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c993", TAG+="uaccess"

# 2023 models
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c985", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c984", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c983", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c985", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c984", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c983", TAG+="uaccess"

# 2022 models
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c975", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c973", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c975", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c973", TAG+="uaccess"

# 2021 models
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c965", TAG+="uaccess"
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c963", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c965", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c963", TAG+="uaccess"

# 2020 models
SUBSYSTEM=="usb", ATTR{idVendor}=="048d", ATTR{idProduct}=="c955", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", ATTRS{idProduct}=="c955", TAG+="uaccess"

# Generic ITE catch-all (optional; uncomment both lines if your PID is not listed above)
# SUBSYSTEM=="usb", ATTR{idVendor}=="048d", TAG+="uaccess"
# SUBSYSTEM=="hidraw", ATTRS{idVendor}=="048d", TAG+="uaccess"
RULES_EOF

# ------------------------------------------------------------------ RGB plugin
say "Installing LOQ RGB plugin into $PLUGIN"
mkdir -p "$PLUGIN_DIR"
rm -f "$CONFIG/rgb-enabled"

cat > "$PLUGIN" << 'RGB_PLUGIN_EOF'
# Copyright (C) 2026 aditandava
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""LOQ RGB plugin for LOQ Center — self-contained 4-zone ITE RGB control."""
import colorsys
import fcntl
import json
import math
import os
import re
import sys
from pathlib import Path

try:
    import usb.core
    import usb.util
    HAS_USB = True
except ImportError:
    HAS_USB = False

SYS = Path("/sys")


ITE_RULES = Path("/etc/udev/rules.d/99-ite-kbd.rules")


ITE_VENDOR = 0x048D


ITE_PIDS = [0xC995, 0xC994, 0xC993, 0xC985, 0xC984, 0xC983,
            0xC975, 0xC973, 0xC965, 0xC963, 0xC955]


ZONE_NAMES = ["Zone 1", "Zone 2", "Zone 3", "Zone 4"]


EFFECTS = ["Static", "Breath", "Wave", "Smooth Spectrum", "Off"]


EFFECT_OPTS = [("Static", "Static"), ("Breath", "Breath"), ("Wave", "Wave"),
               ("Smooth Spectrum", "Spectrum"), ("Off", "Off")]


EFFECT_CODES = {"Static": 0x01, "Breath": 0x03, "Wave": 0x04,
                "Smooth Spectrum": 0x06, "Off": 0x01}


BRIGHTNESS_OPTS = [(1, "Low"), (2, "High")]


SPEED_OPTS = [(s, str(s)) for s in range(1, 5)]


# HyDE sync: off, or follow the theme with its lighter or its darker colours.
HYDE_MODE_OPTS = [("off", "Off"), ("light", "Light"), ("dark", "Dark")]


# Dark mode: how rich (0 to 1, higher = less white) and how bright (0 to 1) its colours are.
DARK_SATURATION = 0.95
DARK_VALUE = 0.70


EMPTY_PROFILE = {"colors": ["#FF0000", "#00FF00", "#0000FF", "#FF00FF"],
                 "effect": "Static", "brightness": 2, "speed": 1}


HIDIOCSFEATURE_33 = (3 << 30) | (33 << 16) | (ord("H") << 8) | 0x06


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


RGB_JSON = CONFIG_DIR / "loq-center" / "rgb.json"


THEME_FILE = CONFIG_DIR / "loq-center" / "theme.css"


RGB_CSS = """
window.loq button.rgb-zone {
  min-height: 50px;
  border-radius: 10px;
  padding: 6px 8px;
  border: 2px solid @loq_border;
  background-image: none;
}
window.loq button.rgb-zone:hover { border-color: @loq_fg; }
window.loq button.rgb-zone label { font-size: 12px; font-weight: bold; }
window.loq button.rgb-mini { padding: 4px 8px; font-size: 11px; }
"""


class RGBError(Exception):
    pass


def _read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def _copy_profile(p):
    return {
        "colors": list(p.get("colors", EMPTY_PROFILE["colors"]))[:4],
        "effect": p.get("effect", "Static") if p.get("effect") in EFFECTS else "Static",
        "brightness": int(p.get("brightness", 2)) if p.get("brightness") in (1, 2) else 2,
        "speed": int(p.get("speed", 1)) if p.get("speed") in (1, 2, 3, 4) else 1,
    }


def load_state():
    try:
        data = json.loads(RGB_JSON.read_text())
        raw = data.get("profiles", [])
        profiles = [_copy_profile(p) for p in raw[:4] if isinstance(p, dict)]
        while len(profiles) < 4:
            profiles.append(_copy_profile(EMPTY_PROFILE))
        active = int(data.get("active", 0))
        return profiles, active if 0 <= active < 4 else 0
    except (OSError, ValueError, TypeError):
        return [_copy_profile(EMPTY_PROFILE) for _ in range(4)], 0


def load_hyde_mode():
    """"off", "light" or "dark" (default: "light")."""
    try:
        data = json.loads(RGB_JSON.read_text())
        mode = data.get("hyde_mode")
        if mode in [value for value, _label in HYDE_MODE_OPTS]:
            return mode
        # Settings saved by the older on/off switch.
        return "light" if data.get("hyde_auto", True) else "off"
    except (OSError, ValueError, TypeError, AttributeError):
        return "light"


def load_hyde_auto():
    """True when the keyboard colours follow HyDE on every theme or wallpaper change."""
    return load_hyde_mode() != "off"


def load_hyde_brightness():
    """Brightness used while HyDE sync is on. Kept apart from the profiles."""
    try:
        return 1 if json.loads(RGB_JSON.read_text()).get("hyde_brightness") == 1 else 2
    except (OSError, ValueError, TypeError, AttributeError):
        return 2


def save_state(profiles, active=0, hyde_mode=None, hyde_brightness=None):
    if hyde_mode is None:
        hyde_mode = load_hyde_mode()
    if hyde_brightness is None:
        hyde_brightness = load_hyde_brightness()
    RGB_JSON.parent.mkdir(parents=True, exist_ok=True)
    RGB_JSON.write_text(json.dumps(
        {"active": active, "hyde_mode": hyde_mode, "hyde_brightness": hyde_brightness,
         "profiles": profiles}, indent=2))


def rule_config():
    pids, catchall = [], False
    if ITE_RULES.exists():
        for raw in (_read(ITE_RULES) or "").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or "048d" not in line.lower():
                continue
            m = re.search(r'ATTRS?\{idProduct\}=="([0-9A-Fa-f]{4})"', line)
            if m:
                pid = int(m.group(1), 16)
                if pid not in pids:
                    pids.append(pid)
            elif re.search(r'ATTRS?\{idVendor\}=="048d"', line, re.I):
                catchall = True
    for pid in ITE_PIDS:
        if pid not in pids:
            pids.append(pid)
    return pids, catchall


def _hidraw_has_0xcc(sys_dev):
    try:
        return b"\x85\xcc" in (sys_dev / "device/report_descriptor").read_bytes()
    except OSError:
        return False


def find_hidraw():
    pids, catchall = rule_config()
    allowed = set(pids)
    for node in sorted((SYS / "class/hidraw").glob("hidraw*")):
        uevent = _read(node / "device/uevent") or ""
        m = re.search(r"HID_ID=([0-9A-Fa-f]+):([0-9A-Fa-f]+):([0-9A-Fa-f]+)", uevent)
        if not m:
            continue
        vid, pid = int(m.group(2), 16), int(m.group(3), 16)
        if vid == ITE_VENDOR and _hidraw_has_0xcc(node) and (pid in allowed or catchall):
            return Path("/dev") / node.name, pid
    return None, None


def _usb_has_0xcc_hid(pid):
    for node in (SYS / "bus/hid/devices").glob(f"*:048D:{pid:04X}.*"):
        try:
            if b"\x85\xcc" in (node / "report_descriptor").read_bytes():
                return True
        except OSError:
            pass
    return False


def find_device():
    if not HAS_USB:
        return None
    pids, catchall = rule_config()
    for pid in pids:
        dev = usb.core.find(idVendor=ITE_VENDOR, idProduct=pid)
        if dev is not None:
            return dev
    if catchall:
        candidates = list(usb.core.find(find_all=True, idVendor=ITE_VENDOR) or [])
        for dev in candidates:
            if _usb_has_0xcc_hid(dev.idProduct):
                return dev
        for dev in candidates:
            if dev.bNumConfigurations and dev[0].bNumInterfaces >= 2:
                return dev
    return None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (255, 0, 0)


def luminance(hex_color):
    """How bright a colour looks, 0 to 255."""
    r, g, b = hex_to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def contrast_fg(hex_color):
    return "#11111B" if luminance(hex_color) > 145 else "#FFFFFF"


def darker(hex_color, factor=0.55):
    return "#" + "".join(f"{round(v * factor):02X}" for v in hex_to_rgb(hex_color))


def deepen(hex_color):
    """The same hue as a rich, dark colour. Keyboard LEDs show pale colours as nearly white."""
    hue, saturation, _value = colorsys.rgb_to_hsv(*(v / 255 for v in hex_to_rgb(hex_color)))
    rich = colorsys.hsv_to_rgb(hue, max(saturation, DARK_SATURATION), DARK_VALUE)
    return "#" + "".join(f"{round(v * 255):02X}" for v in rich)


def is_grey(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return max(r, g, b) - min(r, g, b) <= 0.08 * max(r, g, b)


def pick_tone(shades, tone):
    """From HyDE's shades of one colour: the brightest for "light", a rich dark one for "dark"."""
    ordered = sorted(shades, key=luminance)
    if tone != "dark":
        return ordered[-1]
    if not is_grey(ordered[0]):
        return deepen(ordered[0])
    # A grey theme has no hue to enrich: use its dark shade, or dim the only one.
    return ordered[0] if ordered[0] != ordered[-1] else darker(ordered[0])


def build_packet(profile):
    """33-byte ITE 8295 HID Feature Report (Report ID 0xCC, command 0x16)."""
    effect = profile.get("effect", "Static")
    colors = profile.get("colors", EMPTY_PROFILE["colors"])
    brightness = max(1, min(2, int(profile.get("brightness", 2))))
    speed = max(1, min(4, int(profile.get("speed", 1))))

    pkt = bytearray(33)
    pkt[0] = 0xCC
    pkt[1] = 0x16
    if effect == "Off":
        pkt[2], pkt[3], pkt[4] = 0x01, 0x01, 0x01
        return bytes(pkt)

    pkt[2] = EFFECT_CODES.get(effect, 0x01)
    pkt[3] = speed
    pkt[4] = brightness
    idx = 5
    for hx in colors[:4]:
        r, g, b = hex_to_rgb(hx)
        pkt[idx], pkt[idx + 1], pkt[idx + 2] = r & 0xFF, g & 0xFF, b & 0xFF
        idx += 3
    if effect == "Wave":
        pkt[19] = 0x01
    return bytes(pkt)


def _send_hidraw(path, pkt):
    fd = os.open(str(path), os.O_RDWR)
    try:
        fcntl.ioctl(fd, HIDIOCSFEATURE_33, bytearray(pkt))
    finally:
        os.close(fd)


def _send_pyusb(dev, pkt):
    reattach = False
    claimed = False
    try:
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
                reattach = True
        except (usb.core.USBError, NotImplementedError):
            pass
        usb.util.claim_interface(dev, 0)
        claimed = True
        dev.ctrl_transfer(0x21, 0x09, 0x03CC, 0x0000, pkt, timeout=1000)
    finally:
        if claimed:
            try:
                usb.util.release_interface(dev, 0)
            except Exception:
                pass
        if reattach:
            try:
                dev.attach_kernel_driver(0)
            except Exception:
                pass
        usb.util.dispose_resources(dev)


def send_rgb(profile, err_cls=RGBError):
    pkt = build_packet(profile)
    hid_path, _ = find_hidraw()
    if hid_path is not None:
        try:
            _send_hidraw(hid_path, pkt)
            return f"RGB applied ({profile.get('effect', 'Static')})."
        except PermissionError:
            pass
        except OSError as err:
            if not HAS_USB:
                raise err_cls(f"HID write failed: {err}")

    if not HAS_USB:
        raise err_cls("Permissions missing on hidraw and PyUSB is not installed.")
    dev = find_device()
    if dev is None:
        raise err_cls("No ITE RGB keyboard found. Check udev rules and USB connection.")
    try:
        _send_pyusb(dev, pkt)
    except Exception as exc:
        raise err_cls(f"USB error: {exc} (re-run loq_rgb.sh if permission denied)")
    return f"RGB applied ({profile.get('effect', 'Static')})."


def _theme_shades():
    """Keyboard colours from theme.css: [main] or [main, alt] for each of the four zones.

    theme.css is written by HyDE in the same run that calls --hyde-sync, so it is never stale.
    """
    text = _read(THEME_FILE)
    if not text:
        return None
    found = {(int(zone), bool(alt)): colour.upper() for zone, alt, colour in re.findall(
        r"@define-color\s+loq_rgb([1-4])(_alt)?\s+(#[0-9A-Fa-f]{6})", text)}
    if not all((zone, False) in found for zone in (1, 2, 3, 4)):
        return None
    return [[found[key] for key in ((zone, False), (zone, True)) if key in found]
            for zone in (1, 2, 3, 4)]


def _cache_shades():
    """The same from HyDE's own wallbash files, for a theme.css without keyboard colours."""
    cache = Path(os.environ.get("HYDE_CACHE_HOME") or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    if cache.name != "hyde":
        cache = cache / "hyde"
    cfg = Path(os.environ.get("HYDE_CONFIG_HOME") or CONFIG_DIR / "hyde")

    for cand in [cache / "wallbash" / "shell-colors", cache / "wall.dcol",
                 cfg / "wallbash" / "Wall.dcol", cfg / "wallbash" / "theme.dcol"]:
        text = _read(cand)
        if not text:
            continue
        found = {}
        for m in re.finditer(r"(?:wallbash|dcol)_([1-4])xa([1-9])\s*=\s*['\"]?#?([0-9A-Fa-f]{6})['\"]?", text):
            found[(int(m.group(1)), int(m.group(2)))] = f"#{m.group(3).upper()}"
        zones = []
        for group in (1, 2, 3, 4):
            # Shades 3 and 7 are the deep and the bright one (HyDE's light mode swaps them).
            shades = [found[(group, s)] for s in (3, 7) if (group, s) in found]
            if not shades:
                shades = [found[(group, s)] for s in (8, 6, 5, 4) if (group, s) in found][:1]
            if shades:
                zones.append(shades)
        if len(zones) == 4:
            return zones
    return None


def hyde_shades():
    """The HyDE shades available for each of the four zones, or None."""
    zones = _theme_shades() or _cache_shades()
    if zones:
        return zones
    text = _read(THEME_FILE)
    if text:
        hits = re.findall(r"@define-color\s+loq_accent\S*\s+(#[0-9A-Fa-f]{6})", text)
        if hits:
            return [[c.upper()] for c in (hits * 4)[:4]]
    return None


def hyde_colors(tone="light"):
    """The four keyboard colours in the "light" or "dark" tone, or None."""
    zones = hyde_shades()
    if not zones:
        return None
    return [pick_tone(shades, tone) for shades in zones]


def hyde_profile():
    """What the keyboard shows while HyDE sync is on. Saved profiles play no part."""
    colors = hyde_colors(load_hyde_mode())
    if not colors:
        return None
    return {"colors": colors, "effect": "Static",
            "brightness": load_hyde_brightness(), "speed": 1}


def hyde_sync_headless():
    """Called by HyDE after every theme / wallpaper / mode change (see assets/loq-center.dcol)."""
    if not load_hyde_auto():
        return "HyDE auto-sync is off."
    profile = hyde_profile()
    if not profile:
        return "HyDE theme colours not found."
    return send_rgb(profile)
# ---------------------------------------------------- Off / Light / Dark: motion

MODE_SLIDE_SECONDS = 0.38


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (2 - 2 * t) ** 3 / 2


def pill_edges(start, goal, t):
    """Left and right edge of the sliding pill, counted in segments, at progress t (0 to 1).

    The edge facing the target leads and the other one follows, so the pill stretches.
    """
    (left, right), (to_left, to_right) = start, goal
    fast, slow = ease_out(min(1.0, t * 1.25)), ease_in_out(t)
    forward = to_left + to_right > left + right
    k_left, k_right = (slow, fast) if forward else (fast, slow)
    return left + (to_left - left) * k_left, right + (to_right - right) * k_right


def mix_rgb(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def blend_palette(palettes, position):
    """The pill colours when it sits at `position` (0 = first segment, 1 = second, ...)."""
    position = max(0.0, min(len(palettes) - 1.0, position))
    first = min(int(position), len(palettes) - 2)
    return [mix_rgb(a, b, position - first) for a, b in zip(palettes[first], palettes[first + 1])]
# ----------------------------------------------------- Off / Light / Dark: icons
# Each icon is drawn around (0, 0). `amount` is how far the pill has reached it (0 to 1).


def draw_power_icon(cr, r, amount):
    gap = 0.75
    cr.new_sub_path()
    cr.arc(0, 0.6, r * 0.85, -math.pi / 2 + gap, 3 * math.pi / 2 - gap)
    cr.stroke()
    cr.move_to(0, -r)
    cr.line_to(0, -r * 0.1)
    cr.stroke()


def draw_sun_icon(cr, r, amount):
    cr.rotate((amount - 1) * math.pi / 2)  # the rays turn into place
    cr.new_sub_path()
    cr.arc(0, 0, r * 0.42, 0, 2 * math.pi)
    cr.fill()
    for i in range(8):
        a = i * math.pi / 4
        cr.move_to(math.cos(a) * r * 0.72, math.sin(a) * r * 0.72)
        cr.line_to(math.cos(a) * r * 1.05, math.sin(a) * r * 1.05)
        cr.stroke()


def draw_moon_icon(cr, r, amount):
    cr.rotate((1 - amount) * -1.1)  # the crescent swings into place
    dx, dy, cut = r * 0.58, -r * 0.42, r * 0.82
    d, towards = math.hypot(dx, dy), math.atan2(dy, dx)
    outer = math.acos((r * r + d * d - cut * cut) / (2 * r * d))
    inner = math.acos((cut * cut + d * d - r * r) / (2 * cut * d))
    back = towards + math.pi
    cr.new_sub_path()
    cr.arc(0, 0, r, towards + outer, towards - outer + 2 * math.pi)
    cr.arc_negative(dx, dy, cut, back + inner, back - inner)
    cr.close_path()
    cr.fill()


def draw_mode_icon(cr, mode, x, y, amount):
    cr.save()
    cr.translate(x, y)
    pop = 1 + 0.22 * math.sin(math.pi * amount)
    cr.scale(pop, pop)
    cr.set_line_width(1.8)
    cr.set_line_cap(1)  # round
    {"off": draw_power_icon, "light": draw_sun_icon, "dark": draw_moon_icon}[mode](cr, 7.0, amount)
    cr.restore()
# --------------------------------------------------- Off / Light / Dark: drawing

MODE_PAD = 4  # space between the track and the pill


def pill_path(cr, x, y, width, height):
    radius = height / 2
    cr.new_sub_path()
    cr.arc(x + width - radius, y + radius, radius, -math.pi / 2, math.pi / 2)
    cr.arc(x + radius, y + radius, radius, math.pi / 2, 3 * math.pi / 2)
    cr.close_path()


def draw_mode_labels(cr, segment, height, position, ink):
    """Icon and name in the middle of every segment, all in one colour."""
    cr.set_source_rgb(*ink)
    for i, (mode, name) in enumerate(HYDE_MODE_OPTS):
        wide = cr.text_extents(name).x_advance
        x = MODE_PAD + segment * (i + 0.5) - (wide + 22) / 2
        draw_mode_icon(cr, mode, x + 7, height / 2, max(0.0, 1 - abs(position - i)))
        cr.move_to(x + 22, height / 2 + 4.8)
        cr.show_text(name)
    cr.new_path()


def draw_mode_switch(cr, width, height, edges, palettes, theme, family="sans-serif",
                     hover=None, focus=False):
    """The whole control. `palettes` holds four pill colours for each of the three modes."""
    import cairo
    segment = (width - 2 * MODE_PAD) / len(HYDE_MODE_OPTS)
    inner = height - 2 * MODE_PAD
    left, right = edges
    position = (left + right) / 2 - 0.5
    x, wide = MODE_PAD + left * segment, (right - left) * segment

    cr.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(13)

    pill_path(cr, 1, 1, width - 2, height - 2)  # track
    cr.set_source_rgba(*theme["bg"], 0.75)
    cr.fill_preserve()
    cr.set_source_rgba(*(theme["accent2"] if focus else theme["fg"]), 0.95 if focus else 0.14)
    cr.set_line_width(2 if focus else 1)
    cr.stroke()

    if hover is not None and abs(position - hover) > 0.5:
        pill_path(cr, MODE_PAD + hover * segment, MODE_PAD, segment, inner)
        cr.set_source_rgba(*theme["fg"], 0.08)
        cr.fill()
    draw_mode_labels(cr, segment, height, position, theme["muted"])

    colours = blend_palette(palettes, position)
    mean = tuple(sum(channel) / len(colours) for channel in zip(*colours))
    for grow, alpha in ((3.0, 0.08), (2.0, 0.12), (1.0, 0.18)):  # soft glow around the pill
        pill_path(cr, x - grow, MODE_PAD - grow, wide + 2 * grow, inner + 2 * grow)
        cr.set_source_rgba(*mean, alpha)
        cr.fill()

    fill = cairo.LinearGradient(x, 0, x + wide, 0)
    for i, colour in enumerate(colours):
        fill.add_color_stop_rgb(i / (len(colours) - 1), *colour)
    pill_path(cr, x, MODE_PAD, wide, inner)
    cr.set_source(fill)
    cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 0.22)
    cr.set_line_width(1)
    cr.stroke()

    cr.save()  # the same labels again in a contrasting colour, only where the pill is
    pill_path(cr, x, MODE_PAD, wide, inner)
    cr.clip()
    bright = 0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2] > 0.57
    draw_mode_labels(cr, segment, height, position, (0.07, 0.07, 0.11) if bright else (1, 1, 1))
    cr.restore()
class ModeSwitch:
    """Off / Light / Dark: one control with a pill that slides to the picked mode.

    The pill shows the HyDE colours of that mode. Click a segment, or use the arrow keys.
    """

    def __init__(self, ui, mode, on_pick):
        self.ui, self.on_pick = ui, on_pick
        self.index = self._index_of(mode)
        self.edges = self.start = (self.index, self.index + 1)
        self.progress = 1.0
        self.hover = None
        self.timer = None
        self.last = 0
        self.shades = hyde_shades()
        self.area = ui.Gtk.DrawingArea()
        self.area.set_size_request(320, 44)
        self.area.set_can_focus(True)
        self.area.get_accessible().set_name("HyDE sync mode")
        mask = ui.Gdk.EventMask
        self.area.add_events(mask.BUTTON_PRESS_MASK | mask.POINTER_MOTION_MASK
                             | mask.LEAVE_NOTIFY_MASK
                             | mask.KEY_PRESS_MASK | mask.FOCUS_CHANGE_MASK)
        self.area.connect("draw", self.on_draw)
        self.area.connect("button-press-event", self.on_click)
        self.area.connect("motion-notify-event", self.on_motion)
        self.area.connect("leave-notify-event", self.on_leave)
        self.area.connect("key-press-event", self.on_key)
        self.area.connect("focus-in-event", self.on_focus)
        self.area.connect("focus-out-event", self.on_focus)
        self.area.connect("style-updated", lambda _a: self.reload_colours())  # new HyDE theme

    @staticmethod
    def _index_of(mode):
        return [value for value, _label in HYDE_MODE_OPTS].index(mode)

    # ---- state and animation
    def set_mode(self, mode):
        index = self._index_of(mode)
        if index == self.index:
            return
        self.index = index
        settings = self.ui.Gtk.Settings.get_default()
        if settings is not None and not settings.get_property("gtk-enable-animations"):
            self.edges, self.progress = (index, index + 1), 1.0
            self.area.queue_draw()
            return
        self.start, self.progress = self.edges, 0.0  # also fine halfway through a slide
        if self.timer is None:
            self.last = self.ui.GLib.get_monotonic_time()
            self.timer = self.ui.GLib.timeout_add(16, self._tick)

    def step(self, dt):
        """Moves the pill on by dt seconds. True while it is still moving."""
        self.progress = min(1.0, self.progress + dt / MODE_SLIDE_SECONDS)
        self.edges = pill_edges(self.start, (self.index, self.index + 1), self.progress)
        self.area.queue_draw()
        return self.progress < 1.0

    def _tick(self):
        now = self.ui.GLib.get_monotonic_time()  # microseconds
        moving = self.step(min(0.05, (now - self.last) / 1e6))  # no jumps after a stall
        self.last = now
        if not moving:
            self.timer = None
        return moving

    def reload_colours(self):
        self.shades = hyde_shades()
        self.area.queue_draw()

    # ---- input
    def _segment_at(self, x):
        segment = (self.area.get_allocated_width() - 2 * MODE_PAD) / len(HYDE_MODE_OPTS)
        return max(0, min(len(HYDE_MODE_OPTS) - 1, int((x - MODE_PAD) // max(1.0, segment))))

    def _pick(self, index):
        if index != self.index and 0 <= index < len(HYDE_MODE_OPTS):
            self.on_pick(HYDE_MODE_OPTS[index][0])  # the tab saves it, then calls set_mode

    def on_click(self, _area, event):
        if event.button == 1:
            self._pick(self._segment_at(event.x))
        return True

    def on_key(self, _area, event):
        move = {self.ui.Gdk.KEY_Left: -1, self.ui.Gdk.KEY_Right: 1}.get(event.keyval)
        if move is None:
            return False
        self._pick(self.index + move)
        return True

    def on_motion(self, _area, event):
        hover = self._segment_at(event.x)
        if hover != self.hover:
            self.hover = hover
            self.area.queue_draw()
        return False

    def on_leave(self, _area, _event):
        self.hover = None
        self.area.queue_draw()
        return False

    def on_focus(self, _area, _event):
        self.area.queue_draw()
        return False

    # ---- drawing
    def _theme(self, area):
        context = area.get_style_context()
        theme = {}
        for key, fallback in (("bg", (0.12, 0.12, 0.18)), ("fg", (0.80, 0.84, 0.96)),
                              ("muted", (0.65, 0.68, 0.78)), ("accent", (0.54, 0.71, 0.98)),
                              ("accent2", (0.58, 0.89, 0.84))):
            found, rgba = context.lookup_color(f"loq_{key}")
            theme[key] = (rgba.red, rgba.green, rgba.blue) if found else fallback
        return theme

    def _palettes(self, theme):
        """Pill colours for Off (grey), Light and Dark."""
        palettes = [[theme["muted"]] * 4]
        for tone in ("light", "dark"):
            if self.shades:
                palettes.append([tuple(v / 255 for v in hex_to_rgb(pick_tone(zone, tone)))
                                 for zone in self.shades])
            else:
                palettes.append([theme["accent"]] * 4)
        return palettes

    def on_draw(self, area, cr):
        theme = self._theme(area)
        font = area.get_pango_context().get_font_description()
        draw_mode_switch(cr, area.get_allocated_width(), area.get_allocated_height(),
                         self.edges, self._palettes(theme), theme,
                         family=font.get_family() or "sans-serif",
                         hover=self.hover if area.get_sensitive() else None,
                         focus=area.has_focus())
        return False
class ControlsCardMixin:
    """Card 1: HyDE sync mode, effect, brightness, speed."""

    def _build_controls(self, page):
        ui = self.ui
        # --- Card 1: Mode & Controls (always shown) -----------------------
        ctrl_card = ui.vbox(8)
        ctrl_card.get_style_context().add_class("card")
        ctrl_hdr = ui.Gtk.Box(spacing=8)
        ctrl_hdr.pack_start(ui.label("Mode & Controls", "heading"), False, False, 0)
        self.hw_label = ui.label("Detecting…", "muted")
        self.hw_label.set_xalign(1)
        ctrl_hdr.pack_end(self.hw_label, True, True, 0)
        ctrl_card.pack_start(ctrl_hdr, False, False, 0)
        ui.background(self._hw_work, self._hw_done)

        # First in the card, so it stays put while the rows below appear and disappear.
        ctrl_card.pack_start(ui.label(
            "HyDE Sync: Light and Dark follow your theme and wallpaper.", "muted"), False, False, 0)
        self.mode_switch = ModeSwitch(ui, load_hyde_mode(), self._set_hyde_mode)
        ui.actions.append(self.mode_switch.area)
        ctrl_card.pack_start(self.mode_switch.area, False, False, 0)

        self.effect_row = ui.Choice(ui, self._set_effect)
        self.effect_row.update(EFFECT_OPTS, self.current["effect"])
        ctrl_card.pack_start(self.effect_row.box, False, False, 0)

        self.ctrl_sub = ui.Gtk.Box(spacing=16)
        bri_box = ui.Gtk.Box(spacing=8)
        bri_box.pack_start(ui.label("Brightness", "muted"), False, False, 0)
        self.bri_row = ui.Choice(ui, self._set_brightness)
        self.bri_row.update(BRIGHTNESS_OPTS, self.current["brightness"])
        bri_box.pack_start(self.bri_row.box, True, True, 0)
        self.ctrl_sub.pack_start(bri_box, True, True, 0)

        self.spd_box = ui.Gtk.Box(spacing=8)
        self.spd_box.pack_start(ui.label("Speed", "muted"), False, False, 0)
        self.spd_row = ui.Choice(ui, self._set_speed)
        self.spd_row.update(SPEED_OPTS, self.current["speed"])
        self.spd_box.pack_start(self.spd_row.box, True, True, 0)
        self.ctrl_sub.pack_start(self.spd_box, True, True, 0)
        ctrl_card.pack_start(self.ctrl_sub, False, False, 0)

        self.mode_note = ui.label("", "muted")
        ctrl_card.pack_start(self.mode_note, False, False, 0)

        ui.add(page, ctrl_card)

    def _hw_work(self):
        hid_path, hid_pid = find_hidraw()
        if hid_path is not None and os.access(hid_path, os.R_OK | os.W_OK):
            return f"ITE 0x{hid_pid:04x} ({hid_path.name}) ready"
        dev = find_device()
        if dev is not None:
            pid, bus, addr = dev.idProduct, dev.bus, dev.address
            usb.util.dispose_resources(dev)
            devnode = Path(f"/dev/bus/usb/{bus:03d}/{addr:03d}")
            if devnode.exists() and not os.access(devnode, os.R_OK | os.W_OK):
                return f"ITE 0x{pid:04x} needs permission — re-run loq_rgb.sh"
            return f"ITE 0x{pid:04x} (USB) ready"
        if hid_path is not None:
            return f"{hid_path.name} needs permission — re-run loq_rgb.sh"
        return "No ITE RGB keyboard detected"

    def _hw_done(self, result, error):
        self.hw_label.set_text(result or error or "")


class ZonesCardMixin:
    """Card 2: the four keyboard zones."""

    def _build_zones(self, page):
        ui = self.ui
        # --- Card 2: Keyboard Zones (hidden in Wave / Spectrum / Off / HyDE sync)
        self.zone_card = ui.vbox(8)
        self.zone_card.get_style_context().add_class("card")
        self.zone_card.pack_start(ui.label("Keyboard Zones", "heading"), False, False, 0)

        zone_bar = ui.Gtk.Box(spacing=6)
        zone_bar.set_homogeneous(True)
        self.swatches = []
        for i in range(4):
            btn = ui.Gtk.Button(label=f"Z{i + 1}")
            btn.get_style_context().add_class("rgb-zone")
            btn.connect("clicked", lambda _w, zi=i: self._zone_click(zi))
            ui.actions.append(btn)
            zone_bar.pack_start(btn, True, True, 0)
            self.swatches.append(btn)
        self.zone_card.pack_start(zone_bar, False, False, 0)

        act_row = ui.Gtk.Box(spacing=8)
        act_row.set_homogeneous(True)
        act_row.pack_start(ui.button("Set All Zones", self._set_all), True, True, 0)
        act_row.pack_start(ui.button("HyDE Sync", self._hyde_sync), True, True, 0)
        act_row.pack_start(ui.button("Apply", self._apply), True, True, 0)
        self.zone_card.pack_start(act_row, False, False, 0)
        ui.add(page, self.zone_card)

    def _pick_color(self, title, initial_hex):
        dialog = self.ui.Gtk.ColorChooserDialog(title=title, transient_for=self.ui.window)
        dialog.set_use_alpha(False)
        try:
            dialog.props.show_editor = True
        except Exception:
            pass
        rgba = self.ui.Gdk.RGBA()
        rgba.parse(initial_hex)
        dialog.set_rgba(rgba)
        picked = None
        if dialog.run() == self.ui.Gtk.ResponseType.OK:
            c = dialog.get_rgba()
            picked = f"#{max(0, min(255, round(c.red * 255))):02X}" \
                     f"{max(0, min(255, round(c.green * 255))):02X}" \
                     f"{max(0, min(255, round(c.blue * 255))):02X}"
        dialog.destroy()
        return picked

    def _zone_click(self, idx):
        picked = self._pick_color(f"Choose colour — {ZONE_NAMES[idx]}", self.current["colors"][idx])
        if picked:
            self.current["colors"][idx] = picked
            if self.current["effect"] == "Off":
                self.current["effect"] = "Static"
            self._refresh_ui()
            self._apply()

    def _set_all(self):
        picked = self._pick_color("Choose colour — All Zones", self.current["colors"][0])
        if picked:
            self.current["colors"] = [picked] * 4
            if self.current["effect"] == "Off":
                self.current["effect"] = "Static"
            self._refresh_ui()
            self._apply()

    def _hyde_sync(self):
        colors = hyde_colors()
        if not colors:
            self.ui.say("HyDE theme colours not found — change wallpaper once in HyDE.", True)
            return
        self.current["colors"] = list(colors)
        if self.current["effect"] == "Off":
            self.current["effect"] = "Static"
        self._refresh_ui()
        self._apply()


class ProfilesCardMixin:
    """Card 3: the four profile slots."""

    def _build_profiles(self, page):
        ui = self.ui
        # --- Card 3: 4 Visual Profile Slots (hidden during HyDE sync) ------
        self.prof_card = ui.vbox(8)
        self.prof_card.get_style_context().add_class("card")
        prof_hdr = ui.Gtk.Box(spacing=8)
        prof_hdr.pack_start(ui.label("Profiles", "heading"), False, False, 0)
        prof_hint = ui.label("Click slot to load · ~/.config/loq-center/rgb.json", "muted")
        prof_hint.set_xalign(1)
        prof_hdr.pack_end(prof_hint, True, True, 0)
        self.prof_card.pack_start(prof_hdr, False, False, 0)

        prof_row = ui.Gtk.Box(spacing=8)
        prof_row.set_homogeneous(True)
        self.slot_bars = []
        self.slot_btns = []
        for i in range(4):
            col = ui.vbox(4)
            bar = ui.Gtk.DrawingArea()
            bar.set_size_request(-1, 8)
            bar.connect("draw", self._draw_bar, i)
            col.pack_start(bar, False, False, 0)
            self.slot_bars.append(bar)

            lb = ui.Gtk.Button(label=f"P{i + 1}")
            lb.connect("clicked", lambda _w, idx=i: self._load_profile(idx))
            ui.actions.append(lb)
            col.pack_start(lb, False, False, 0)
            self.slot_btns.append(lb)

            sb = ui.Gtk.Button(label="Save")
            sb.get_style_context().add_class("rgb-mini")
            sb.connect("clicked", lambda _w, idx=i: self._save_profile(idx))
            ui.actions.append(sb)
            col.pack_start(sb, False, False, 0)
            prof_row.pack_start(col, True, True, 0)
        self.prof_card.pack_start(prof_row, False, False, 0)
        ui.add(page, self.prof_card)

    def _draw_bar(self, area, cr, idx):
        w, h = area.get_allocated_width(), area.get_allocated_height()
        if w <= 0 or h <= 0:
            return False
        p = self.profiles[idx]
        if p["effect"] in ("Wave", "Smooth Spectrum"):
            colors = ["#FF4D4D", "#FFD93D", "#6BCB77", "#4D96FF"]
        elif p["effect"] == "Off":
            colors = ["#313244"] * 4
        else:
            colors = p["colors"]
        rad = min(4.0, h / 2.0)
        cr.new_sub_path()
        cr.arc(w - rad, rad, rad, -1.5708, 0)
        cr.arc(w - rad, h - rad, rad, 0, 1.5708)
        cr.arc(rad, h - rad, rad, 1.5708, 3.1416)
        cr.arc(rad, rad, rad, 3.1416, 4.7124)
        cr.close_path()
        cr.clip()
        seg = w / 4.0
        for zi, hx in enumerate(colors[:4]):
            rr, gg, bb = hex_to_rgb(hx)
            cr.set_source_rgb(rr / 255.0, gg / 255.0, bb / 255.0)
            cr.rectangle(zi * seg, 0, seg + 0.5, h)
            cr.fill()
        return False

    def _load_profile(self, idx):
        self.current = _copy_profile(self.profiles[idx])
        self.active_slot = idx
        try:
            save_state(self.profiles, self.active_slot)
        except OSError:
            pass
        self._refresh_ui()
        self._apply()

    def _save_profile(self, idx):
        self.profiles[idx] = _copy_profile(self.current)
        self.active_slot = idx
        try:
            save_state(self.profiles, self.active_slot)
            self._refresh_ui()
            self.ui.say(f"Profile {idx + 1} saved.")
        except OSError as err:
            self.ui.say(f"Save failed: {err}", True)


class RefreshUIMixin:
    """Makes the widgets match the current settings."""

    def _refresh_ui(self):
        for i, btn in enumerate(self.swatches):
            hx = self.current["colors"][i]
            fg = contrast_fg(hx)
            btn.set_label(f"Z{i + 1}\n{hx}")
            btn.set_tooltip_text(f"{ZONE_NAMES[i]}: {hx} (click to change)")
            btn.set_name(f"rgb_z{i}")
            prov = getattr(btn, "_rgb_prov", None)
            if prov is None:
                prov = self.ui.Gtk.CssProvider()
                # Must beat the app theme (USER + 1) and RGB_CSS (USER + 2), or the colour is hidden.
                btn.get_style_context().add_provider(
                    prov, self.ui.Gtk.STYLE_PROVIDER_PRIORITY_USER + 3)
                btn._rgb_prov = prov
            try:
                css = (f"window.loq button#rgb_z{i} {{ background-color: {hx};"
                       f" background-image: none; }}"
                       f"window.loq button#rgb_z{i} label {{ color: {fg}; }}")
                prov.load_from_data(css.encode())
            except self.ui.GLib.Error:
                pass

        effect = self.current["effect"]
        mode = load_hyde_mode()
        synced = mode != "off"
        self.mode_switch.set_mode(mode)
        self.mode_switch.reload_colours()
        self.ui.visible(self.effect_row.box, not synced)
        self.ui.visible(self.prof_card, not synced)
        self.ui.visible(self.zone_card, not synced and effect in ("Static", "Breath"))
        self.ui.visible(self.ctrl_sub, synced or effect != "Off")
        self.ui.visible(self.spd_box,
                        not synced and effect in ("Breath", "Wave", "Smooth Spectrum"))
        notes = {
            "Wave": "Wave uses automatic rainbow colours across the keyboard.",
            "Smooth Spectrum": "Spectrum cycles smoothly through all colours automatically.",
            "Off": "Keyboard backlight is turned off.",
        }
        note = notes.get(effect, "")
        if synced:
            note = (f"HyDE controls the keyboard in its {mode} colours. "
                    "Pick Off to use effects, zones and profiles.")
        self.mode_note.set_text(note)
        self.ui.visible(self.mode_note, bool(note))

        self.effect_row.update(EFFECT_OPTS, effect)
        self.bri_row.update(BRIGHTNESS_OPTS,
                            load_hyde_brightness() if synced else self.current["brightness"])
        self.spd_row.update(SPEED_OPTS, self.current["speed"])
        short_fx = {"Smooth Spectrum": "Spectrum"}
        for i, btn in enumerate(self.slot_btns):
            p = self.profiles[i]
            btn.set_label(f"{i + 1} · {short_fx.get(p['effect'], p['effect'])}")
            btn.set_tooltip_text(f"Load Profile {i + 1}: {p['effect']} | {' · '.join(p['colors'])}")
            ctx = btn.get_style_context()
            if i == self.active_slot:
                ctx.add_class("active")
            else:
                ctx.remove_class("active")
            self.slot_bars[i].queue_draw()


class SettingsMixin:
    """Changing settings and sending them to the keyboard."""

    def _set_hyde_mode(self, mode):
        try:
            save_state(self.profiles, self.active_slot, hyde_mode=mode)
        except OSError as err:
            self.ui.say(f"Save failed: {err}", True)
            return
        # Light / Dark: HyDE takes over. Off: the active profile comes back as it was saved.
        self.current = _copy_profile(self.profiles[self.active_slot])
        self._refresh_ui()
        self._apply()

    def _set_effect(self, name):
        self.current["effect"] = name
        self._refresh_ui()
        self._apply()

    def _set_brightness(self, value):
        if load_hyde_auto():
            try:
                save_state(self.profiles, self.active_slot, hyde_brightness=value)
            except OSError as err:
                self.ui.say(f"Save failed: {err}", True)
                return
        else:
            self.current["brightness"] = value
        self._refresh_ui()
        self._apply()

    def _set_speed(self, value):
        self.current["speed"] = value
        self._refresh_ui()
        self._apply()

    def _apply(self):
        profile = hyde_profile() if load_hyde_auto() else _copy_profile(self.current)
        if not profile:
            self.ui.say("HyDE theme colours not found — change wallpaper once in HyDE.", True)
            return
        self.ui.act(lambda: send_rgb(profile, self.ui.ActionError), "Applying RGB…")


class RGBTab(ControlsCardMixin, ZonesCardMixin, ProfilesCardMixin, RefreshUIMixin, SettingsMixin):
    """The "LOQ RGB" tab. Each card and its actions live in a mixin next to this file."""

    def __init__(self, ui):
        self.ui = ui
        ui.add_css(RGB_CSS)
        page = ui.page("rgb", "LOQ RGB")

        self.profiles, self.active_slot = load_state()
        self.current = _copy_profile(self.profiles[self.active_slot])

        self._build_controls(page)
        self._build_zones(page)
        self._build_profiles(page)

        self._refresh_ui()


def register(ui):
    ui._rgb_tab = RGBTab(ui)


if __name__ == "__main__" and sys.argv[1:] == ["--apply"]:
    profs, slot = load_state()
    profile = hyde_profile() if load_hyde_auto() else profs[slot]
    if not profile:
        sys.exit("HyDE theme colours not found.")
    print(send_rgb(profile))
elif __name__ == "__main__" and sys.argv[1:] == ["--hyde-sync"]:
    try:
        print(hyde_sync_headless())
    except RGBError as err:
        print(f"HyDE sync: {err}", file=sys.stderr)
        sys.exit(1)


RGB_PLUGIN_EOF

chmod 0644 "$PLUGIN"
python3 -c "import py_compile; py_compile.compile('$PLUGIN', doraise=True)"

say "Reloading udev rules"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --subsystem-match=hidraw

say "Done!"
if pgrep -u "$(id -u)" -f "loq-center" > /dev/null 2>&1; then
  say "Close the currently open LOQ Center window and reopen it to see the LOQ RGB tab."
else
  say "Open LOQ Center — the LOQ RGB tab will appear automatically."
fi
say "Remove RGB support any time with: bash loq_rgb.sh --uninstall"
