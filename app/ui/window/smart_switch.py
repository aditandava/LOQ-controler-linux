class SmartSwitchMixin:
    """Smart Switch tab (settings per power source)."""

    def build_auto(self):
        page = self.page("auto", SWITCH_NAME)

        # Hero: name, one-line status and the master switch
        hero = self.vbox(0)
        for name in ("card", "hero"):
            hero.get_style_context().add_class(name)
        top = self.Gtk.Box(spacing=16)
        text = self.vbox(4)
        self.add(text, self.label(SWITCH_NAME, "title2"))
        self.auto_note = self.add(text, self.label("", "muted"))
        top.pack_start(text, True, True, 0)
        self.auto_switch = self.Gtk.Switch()
        self.auto_switch.set_valign(self.Gtk.Align.CENTER)
        self.auto_quiet = False
        self.auto_switch.connect("notify::active", self.on_auto_switch)
        top.pack_end(self.auto_switch, False, False, 0)
        self.add(hero, top)
        self.add(page, hero)

        # One card per power source, side by side; the one in use is highlighted
        cards = self.Gtk.Box(spacing=14)
        cards.set_homogeneous(True)
        self.auto_cards, self.auto_badges, self.auto_rows = {}, {}, {}
        for source, title in AUTO_SOURCES.items():
            card = self.vbox(16)
            for name in ("card", "source"):
                card.get_style_context().add_class(name)
            head = self.Gtk.Box(spacing=8)
            text = self.vbox(2)
            self.add(text, self.label(title, "title2"))
            self.add(text, self.label(SWITCH_HINTS[source], "muted"))
            head.pack_start(text, True, True, 0)
            badge = self.label("", "badge")
            badge.set_line_wrap(False)
            badge.set_valign(self.Gtk.Align.START)
            head.pack_end(badge, False, False, 0)
            self.add(card, head)
            self.visible(badge, False)
            rows = {}
            for key, label in AUTO_TITLES.items():
                field = self.vbox(6)
                self.add(field, self.label(label, "caption"))
                cell = Dropdown(self, lambda v, s=source, k=key: self.pick_auto(s, k, v))
                self.add(field, cell.box)
                self.actions.append(cell.box)  # locked while a change is being applied
                self.add(card, field)
                rows[key] = (field, cell)
            cards.pack_start(card, True, True, 0)
            self.auto_cards[source], self.auto_badges[source] = card, badge
            self.auto_rows[source] = rows
        self.add(page, cards)

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


