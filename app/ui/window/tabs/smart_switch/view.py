class SmartSwitchViewMixin:
    """Smart Switch tab: showing the settings."""

    def auto_view(self, config=None):
        config = config or load_auto()
        self.auto_quiet = True
        self.auto_switch.set_active(config["enabled"])
        self.auto_quiet = False
        if not config["enabled"]:
            self.auto_note.set_text("Off · different settings for charger and battery")
        elif daemon_running():
            self.auto_note.set_text("On · changes when you plug in or unplug")
        else:
            self.auto_note.set_text("On · starts when you log in or reopen this window")
        for source, card in self.auto_cards.items():
            current = source == self.auto_now
            badge = self.auto_badges[source]
            badge.set_text("● Active now" if config["enabled"] else "● Current")
            self.visible(badge, current)
            self.flag(card, "now", current)
            self.flag(card, "dim", not config["enabled"])
            for key, (field, cell) in self.auto_rows[source].items():
                saved = config[source][key]
                choices = auto_choices(key, source, self.auto_options, saved)
                known = [value for value, _label in choices]
                cell.update([("keep", "Keep")] + choices, saved if saved in known else "keep")
                self.visible(field, bool(choices))


