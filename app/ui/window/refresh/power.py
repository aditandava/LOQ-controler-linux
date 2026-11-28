class ShowPowerMixin:
    """Fills the Power tab."""

    def show_profile(self, data):
        profile = data["profile"]
        unplugged = data["ac"] is False
        self.visible(self.preset_buttons["boost"], not unplugged)
        if profile:
            usable = usable_profiles(profile["options"], "battery" if unplugged else "ac")
            self.profile_row.update([(p, PROFILE_LABELS.get(p, p)) for p in usable],
                                    profile["active"])
            active = PROFILE_LABELS.get(profile["active"], profile["active"] or "Unknown")
            if unplugged and profile["active"] in CHARGER_ONLY:
                note = f"{active} needs the charger. Plug it in, or pick another mode."
            elif profile["active"] == "cooling":
                fans = ("Fans at full speed." if profile["fans_direct"] else
                        "Fans are NOT at full speed: no working fan interface.")
                note = f"Cooling (purple): low power. {fans} Pick another mode to restore."
            elif profile["active"] == "ultra-saver":
                note = ("Ultra saver: Quiet mode, no CPU turbo, about half CPU speed. "
                        "Pick another mode to restore.")
            elif profile["active"] == "max-power":
                note = "Max power (purple): high power. Keep the charger connected."
            elif unplugged:
                note = f"Current: {active}. Plug in for Performance, Max power and Cooling."
            else:
                note = f"Current: {active}. Fn+Q changes it too."
            self.profile_note.set_text(note)
        else:
            self.profile_row.update([], None)
            self.profile_note.set_text("This kernel exposes no performance modes.")

    def show_charge(self, data):
        battery = data["battery"]
        charge = data["charge"]
        if charge:
            self.charge_row.update([(c, CHARGE_LABELS[c]) for c in charge["options"]], charge["active"])
            self.charge_note.set_text(charge_note(charge, battery, data["ac"]))
        else:
            self.charge_row.update([], None)
            self.charge_note.set_text("Not available. Check that ideapad_laptop is loaded.")

    def show_idle(self, data):
        idle = data["idle"]
        self.visible(self.idle_card, idle is not None)
        if idle:
            self.idle_row.update([(k, v[0]) for k, v in IDLE_PRESETS.items()], idle["active"])
            self.idle_note.set_text(idle["note"])

    def show_health(self, data):
        battery = data["battery"]
        lines = []
        if battery:
            if battery["health"] is not None:
                lines.append(f"Capacity left compared with new: {battery['health']:.1f}%")
            if battery["cycles"] is not None:
                lines.append(f"Charge cycles: {battery['cycles']}")
        self.health.set_text("\n".join(lines) or "No health data reported.")


