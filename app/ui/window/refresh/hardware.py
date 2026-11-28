class ShowHardwareMixin:
    """Fills the Display, Graphics and Smart Switch tabs and the switches."""

    def show_screen(self, data):
        screen = data["display"]
        if screen and screen["options"]:
            self.rate_row.update([(r, f"{r} Hz") for r in screen["options"]], screen["active"])
            self.rate_note.set_text(f"{screen['name']}: {screen['active']} Hz. "
                                    "Resets when Hyprland reloads.")
        else:
            self.rate_row.update([], None)
            self.rate_note.set_text("Built-in screen not found through hyprctl.")

    def show_light(self, data):
        light = data["backlight"]
        self.visible(self.light_card, light is not None)
        if light and not self.scale_timer and not self.scale.has_focus():
            self.scale_quiet = True
            self.scale.set_value(round(light["value"] * 100 / light["max"]))
            self.scale_quiet = False

    def show_keyboard(self, data):
        keys = data["keyboard"]
        self.visible(self.keyboard_card, keys is not None)
        if keys:
            self.keyboard_row.update(
                [(n, "Off" if n == 0 else str(n)) for n in range(keys["max"] + 1)], keys["value"])

    def show_toggles(self, data):
        toggles = data["toggles"]
        self.visible(self.toggle_card, bool(toggles))
        for name, (box, row) in self.toggle_rows.items():
            self.visible(box, name in toggles)
            if name in toggles:
                row.update([("1", "On"), ("0", "Off")], toggles[name])

    def show_gpu(self, data):
        states = {"active": "awake", "suspended": "sleeping (saving power)",
                  "off": "switched off or not detected"}
        self.gpu_power.set_text(f"State: {states.get(data['nvidia'], data['nvidia'])}")

    def show_auto(self, data):
        profile, screen, idle, light = (
            data[k] for k in ("profile", "display", "idle", "backlight"))
        self.auto_now = {True: "ac", False: "battery"}.get(data["ac"])
        self.auto_options = {
            "profile": profile["options"] if profile else [],
            "refresh": list(screen["options"]) if screen and screen["options"] else [],
            "idle": idle is not None,
            "brightness": light is not None,
        }
        self.auto_view()
        self.auto_check(data)


