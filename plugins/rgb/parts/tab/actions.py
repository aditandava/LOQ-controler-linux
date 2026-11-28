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


