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


