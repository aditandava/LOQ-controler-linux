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


