class DisplayMixin:
    """Display tab: layout."""

    def build_display(self):
        page = self.page("display", "Display")
        card = self.card(page, "Refresh rate")
        self.rate_row = Choice(self, lambda v: self.act(lambda: set_refresh(v)))
        self.add(card, self.rate_row.box)
        self.rate_note = self.add(card, self.label("", "muted"))
        self.light_card = self.card(page, "Screen brightness")
        self.scale = self.Gtk.Scale.new_with_range(self.Gtk.Orientation.HORIZONTAL, 5, 100, 1)
        self.scale_quiet = False
        self.scale_timer = None
        self.scale.connect("value-changed", self.on_scale)
        self.add(self.light_card, self.scale)
        self.keyboard_card = self.card(page, "Keyboard light")
        self.keyboard_row = Choice(self, lambda v: self.act(lambda: set_keyboard(v)))
        self.add(self.keyboard_card, self.keyboard_row.box)
        self.toggle_card = self.card(page, "Device switches")
        self.toggle_rows = {}
        for name, title in TOGGLE_LABELS.items():
            box = self.vbox(4)
            self.add(box, self.label(title))
            row = Choice(self, lambda v, n=name: self.act(lambda: set_toggle(n, v)))
            self.add(box, row.box)
            self.add(self.toggle_card, box)
            self.toggle_rows[name] = (box, row)
        card = self.card(page, "App background")
        self.look_row = Choice(self, self.pick_background)
        self.add(card, self.look_row.box)
        self.background_view()


