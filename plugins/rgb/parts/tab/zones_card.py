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


