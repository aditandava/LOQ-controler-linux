class SmartSwitchEventsMixin:
    """Smart Switch tab: user changes."""

    def on_auto_switch(self, switch, _param):
        if not self.auto_quiet:
            self.pick_auto_enabled(switch.get_active())

    def pick_auto(self, source, key, value):
        try:
            config = load_auto()
            config[source][key] = None if value == "keep" else value
            save_auto(config)
        except ActionError as err:
            self.say(str(err), True)
            return
        self.auto_view(config)
        if config["enabled"] and source == self.auto_now:  # in use right now, so apply it
            self.act(lambda: apply_auto(source, key), "Applying…")
        else:
            self.say("Saved")

    def pick_auto_enabled(self, enabled):
        try:
            config = load_auto()
            config["enabled"] = enabled
            save_auto(config)
        except ActionError as err:
            self.say(str(err), True)
            self.auto_view()  # put the switch back
            return
        source = power_source()
        if enabled:
            start_daemon()
        self.auto_view(config)
        if enabled and source and not self.busy:
            self.auto_last = source
            self.act(lambda: apply_auto(source), "Applying settings…")
        else:
            self.say(f"{SWITCH_NAME} is {'on' if enabled else 'off'}.")

    def auto_check(self, data):
        """Fallback while no background service runs: switch when this window sees a change."""
        source = {True: "ac", False: "battery"}.get(data["ac"])
        if source is None:
            return
        if self.auto_last is None:
            self.auto_last = source
            return
        if source == self.auto_last or self.busy:
            return
        self.auto_last = source
        if load_auto()["enabled"] and not daemon_running():
            self.act(lambda: apply_auto(source), "Switching settings…")


