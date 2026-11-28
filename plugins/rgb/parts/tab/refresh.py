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


