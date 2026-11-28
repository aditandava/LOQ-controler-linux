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
import fcntl
import json
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


def load_hyde_auto():
    """True when the keyboard colours follow HyDE on every theme or wallpaper change (default: on)."""
    try:
        return bool(json.loads(RGB_JSON.read_text()).get("hyde_auto", True))
    except (OSError, ValueError, TypeError, AttributeError):
        return True


def load_hyde_brightness():
    """Brightness used while Auto HyDE Sync is on. Kept apart from the profiles."""
    try:
        return 1 if json.loads(RGB_JSON.read_text()).get("hyde_brightness") == 1 else 2
    except (OSError, ValueError, TypeError, AttributeError):
        return 2


def save_state(profiles, active=0, hyde_auto=None, hyde_brightness=None):
    if hyde_auto is None:
        hyde_auto = load_hyde_auto()
    if hyde_brightness is None:
        hyde_brightness = load_hyde_brightness()
    RGB_JSON.parent.mkdir(parents=True, exist_ok=True)
    RGB_JSON.write_text(json.dumps(
        {"active": active, "hyde_auto": bool(hyde_auto), "hyde_brightness": hyde_brightness,
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


def contrast_fg(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return "#11111B" if (0.299 * r + 0.587 * g + 0.114 * b) > 145 else "#FFFFFF"


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


def _theme_rgb_colors():
    """The four keyboard colours HyDE wrote into theme.css on its last run (loq_rgb1..4)."""
    text = _read(THEME_FILE)
    if not text:
        return None
    found = dict(re.findall(r"@define-color\s+loq_rgb([1-4])\s+(#[0-9A-Fa-f]{6})", text))
    if len(found) == 4:
        return [found[str(i)].upper() for i in (1, 2, 3, 4)]
    return None


def hyde_colors():
    # theme.css is written by HyDE in the same run that calls --hyde-sync, so it is never stale.
    fresh = _theme_rgb_colors()
    if fresh:
        return fresh
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
        picked = []
        for group in (1, 2, 3, 4):
            for shade in (7, 8, 6, 5, 4):
                if (group, shade) in found:
                    picked.append(found[(group, shade)])
                    break
        if len(picked) == 4:
            return picked

    text = _read(THEME_FILE)
    if text:
        hits = re.findall(r"@define-color\s+loq_accent\S*\s+(#[0-9A-Fa-f]{6})", text)
        if hits:
            return [c.upper() for c in (hits * 4)[:4]]
    return None


def hyde_profile():
    """What the keyboard shows while Auto HyDE Sync is on. Saved profiles play no part."""
    colors = hyde_colors()
    if not colors:
        return None
    return {"colors": list(colors), "effect": "Static",
            "brightness": load_hyde_brightness(), "speed": 1}


def hyde_sync_headless():
    """Called by HyDE after every theme / wallpaper / mode change (see assets/loq-center.dcol)."""
    if not load_hyde_auto():
        return "HyDE auto-sync is off."
    profile = hyde_profile()
    if not profile:
        return "HyDE theme colours not found."
    return send_rgb(profile)

class ControlsCardMixin:
    """Card 1: effect, brightness, speed, HyDE switch."""

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

        auto_row = ui.Gtk.Box(spacing=8)
        auto_text = ui.vbox(2)
        auto_text.pack_start(ui.label("Auto HyDE Sync", "heading"), False, False, 0)
        auto_text.pack_start(ui.label(
            "Colours follow HyDE every time the theme or wallpaper changes.", "muted"), False, False, 0)
        auto_row.pack_start(auto_text, True, True, 0)
        self.auto_quiet = True
        self.auto_switch = ui.Gtk.Switch()
        self.auto_switch.set_valign(ui.Gtk.Align.CENTER)
        self.auto_switch.set_active(load_hyde_auto())
        self.auto_switch.connect("notify::active", self._set_hyde_auto)
        self.auto_quiet = False
        ui.actions.append(self.auto_switch)
        auto_row.pack_end(self.auto_switch, False, False, 0)
        ctrl_card.pack_start(auto_row, False, False, 0)
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
        synced = load_hyde_auto()
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
            note = "HyDE controls the keyboard. Turn sync off to use effects, zones and profiles."
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

    def _set_hyde_auto(self, switch, _param):
        if self.auto_quiet:
            return
        try:
            save_state(self.profiles, self.active_slot, hyde_auto=switch.get_active())
        except OSError as err:
            self.ui.say(f"Save failed: {err}", True)
            return
        # On: HyDE takes over. Off: the active profile comes back as it was saved.
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


