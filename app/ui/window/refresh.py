class RefreshMixin:
    """Periodic refresh and filling the tabs with fresh data."""

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

        self.auto_now = {True: "ac", False: "battery"}.get(data["ac"])
        self.auto_options = {
            "profile": profile["options"] if profile else [],
            "refresh": list(screen["options"]) if screen and screen["options"] else [],
            "idle": idle is not None,
            "brightness": light is not None,
        }
        self.auto_view()
        self.auto_check(data)


