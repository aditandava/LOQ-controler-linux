class RGBTab:
    def __init__(self, ui):
        self.ui = ui
        ui.add_css(RGB_CSS)
        page = ui.page("rgb", "LOQ RGB")

        self.profiles, self.active_slot = load_state()
        self.current = _copy_profile(self.profiles[self.active_slot])

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
        auto_row.pack_end(self.auto_switch, False, False, 0)
        ctrl_card.pack_start(auto_row, False, False, 0)
        ui.add(page, ctrl_card)

        # --- Card 2: Keyboard Zones (hidden in Wave / Spectrum / Off) ------
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

        # --- Card 3: 4 Visual Profile Slots --------------------------------
        prof_card = ui.vbox(8)
        prof_card.get_style_context().add_class("card")
        prof_hdr = ui.Gtk.Box(spacing=8)
        prof_hdr.pack_start(ui.label("Profiles", "heading"), False, False, 0)
        prof_hint = ui.label("Click slot to load · ~/.config/loq-center/rgb.json", "muted")
        prof_hint.set_xalign(1)
        prof_hdr.pack_end(prof_hint, True, True, 0)
        prof_card.pack_start(prof_hdr, False, False, 0)

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
        prof_card.pack_start(prof_row, False, False, 0)
        ui.add(page, prof_card)

        self._refresh_ui()

        self._json_stamp = self._stamp()
        ui.GLib.timeout_add_seconds(2, self._poll_external)

    def _stamp(self):
        try:
            return RGB_JSON.stat().st_mtime_ns
        except OSError:
            return 0

    def _poll_external(self):
        """HyDE's hook runs outside this window; pick up the colours it saved."""
        stamp = self._stamp()
        if stamp != self._json_stamp:
            self._json_stamp = stamp
            self.profiles, self.active_slot = load_state()
            colors = self.profiles[self.active_slot]["colors"]
            if colors != self.current["colors"]:
                self.current["colors"] = list(colors)
            self.auto_quiet = True
            self.auto_switch.set_active(load_hyde_auto())
            self.auto_quiet = False
            self._refresh_ui()
        return True

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
        self.ui.visible(self.zone_card, effect in ("Static", "Breath"))
        self.ui.visible(self.ctrl_sub, effect != "Off")
        self.ui.visible(self.spd_box, effect in ("Breath", "Wave", "Smooth Spectrum"))
        notes = {
            "Wave": "Wave uses automatic rainbow colours across the keyboard.",
            "Smooth Spectrum": "Spectrum cycles smoothly through all colours automatically.",
            "Off": "Keyboard backlight is turned off.",
        }
        self.mode_note.set_text(notes.get(effect, ""))
        self.ui.visible(self.mode_note, effect in notes)

        self.effect_row.update(EFFECT_OPTS, effect)
        self.bri_row.update(BRIGHTNESS_OPTS, self.current["brightness"])
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

    def _set_hyde_auto(self, switch, _param):
        if self.auto_quiet:
            return
        on = switch.get_active()
        try:
            save_state(self.profiles, self.active_slot, hyde_auto=on)
            self._json_stamp = self._stamp()
        except OSError as err:
            self.ui.say(f"Save failed: {err}", True)
            return
        if on:
            self._hyde_sync()  # sync now, not only at the next theme change
        else:
            self.ui.say("Auto HyDE Sync is off.")

    def _set_effect(self, name):
        self.current["effect"] = name
        self._refresh_ui()
        self._apply()

    def _set_brightness(self, value):
        self.current["brightness"] = value
        self._refresh_ui()
        self._apply()

    def _set_speed(self, value):
        self.current["speed"] = value
        self._refresh_ui()
        self._apply()

    def _load_profile(self, idx):
        self.current = _copy_profile(self.profiles[idx])
        self.active_slot = idx
        try:
            save_state(self.profiles, self.active_slot)
            self._json_stamp = self._stamp()
        except OSError:
            pass
        self._refresh_ui()
        self._apply()

    def _save_profile(self, idx):
        self.profiles[idx] = _copy_profile(self.current)
        self.active_slot = idx
        try:
            save_state(self.profiles, self.active_slot)
            self._json_stamp = self._stamp()
            self._refresh_ui()
            self.ui.say(f"Profile {idx + 1} saved.")
        except OSError as err:
            self.ui.say(f"Save failed: {err}", True)

    def _apply(self):
        profile = _copy_profile(self.current)
        self.ui.act(lambda: send_rgb(profile, self.ui.ActionError), "Applying RGB…")


