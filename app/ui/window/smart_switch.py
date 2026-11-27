class SmartSwitchMixin:
    """Smart Switch tab (settings per power source)."""

    def build_auto(self):
        page = self.page("auto", SWITCH_NAME)
        card = self.vbox(18)
        card.get_style_context().add_class("card")

        top = self.Gtk.Box(spacing=12)
        text = self.vbox(2)
        self.add(text, self.label(SWITCH_NAME, "heading"))
        self.auto_note = self.add(text, self.label("", "muted"))
        top.pack_start(text, True, True, 0)
        self.auto_switch = self.Gtk.Switch()
        self.auto_switch.set_valign(self.Gtk.Align.CENTER)
        self.auto_quiet = False
        self.auto_switch.connect("notify::active", self.on_auto_switch)
        top.pack_end(self.auto_switch, False, False, 0)
        self.add(card, top)

        grid = self.Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)
        same_width = self.Gtk.SizeGroup.new(self.Gtk.SizeGroupMode.HORIZONTAL)
        self.auto_heads = {}
        for column, (source, title) in enumerate(SWITCH_COLUMNS.items(), 1):
            head = self.label(title, "column")
            head.set_xalign(0.5)
            head.set_hexpand(True)
            same_width.add_widget(head)
            grid.attach(head, column, 0, 1, 1)
            self.auto_heads[source] = head
        self.auto_rows = {}
        for line, (key, title) in enumerate(AUTO_TITLES.items(), 1):
            name = self.label(title, "muted")
            name.set_line_wrap(False)
            grid.attach(name, 0, line, 1, 1)
            cells = {}
            for column, source in enumerate(SWITCH_COLUMNS, 1):
                cell = Dropdown(self, lambda v, s=source, k=key: self.pick_auto(s, k, v))
                same_width.add_widget(cell.box)
                grid.attach(cell.box, column, line, 1, 1)
                self.actions.append(cell.box)  # locked while a change is being applied
                cells[source] = cell
            self.auto_rows[key] = (name, cells)
        self.add(card, grid)
        self.add(page, card)

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
        for source, head in self.auto_heads.items():
            current = source == self.auto_now
            head.set_text(("● " if current else "") + SWITCH_COLUMNS[source])
            context = head.get_style_context()
            if current:
                context.add_class("now")
            else:
                context.remove_class("now")
        for key, (name, cells) in self.auto_rows.items():
            for source, cell in cells.items():
                saved = config[source][key]
                choices = auto_choices(key, source, self.auto_options, saved)
                known = [value for value, _label in choices]
                cell.update([("keep", "Keep")] + choices, saved if saved in known else "keep")
                self.visible(cell.box, bool(choices))
            self.visible(name, any(auto_choices(key, s, self.auto_options) for s in cells))

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


