class DisplayMixin:
    """Display tab (refresh rate, brightness, background)."""

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

    def background_view(self):
        options = list(BACKGROUNDS.items())
        chosen = load_look()["background"]
        if chosen not in dict(options):
            chosen = "scenes"
        self.look_row.update(options, chosen)

    def pick_background(self, choice):
        look = load_look()
        if choice == "picture":  # clicking it again chooses a different one
            picture = self.choose_picture()
            if not picture:
                return
            look["picture"] = picture
        look["background"] = choice
        try:
            save_look(look)
        except ActionError as err:
            self.say(str(err), True)
            return
        self.load_theme()
        self.background_view()
        self.say("Background changed")

    def choose_picture(self):
        dialog = self.Gtk.FileChooserDialog(title="Choose a background picture",
                                            transient_for=self.window,
                                            action=self.Gtk.FileChooserAction.OPEN)
        dialog.add_buttons("Cancel", self.Gtk.ResponseType.CANCEL,
                           "Use picture", self.Gtk.ResponseType.OK)
        pictures = self.Gtk.FileFilter()
        pictures.set_name("Pictures")
        pictures.add_pixbuf_formats()
        dialog.add_filter(pictures)
        picked = dialog.get_filename() if dialog.run() == self.Gtk.ResponseType.OK else None
        dialog.destroy()
        return picked

    def on_scale(self, scale):
        if self.scale_quiet:
            return
        if self.scale_timer:
            self.GLib.source_remove(self.scale_timer)
        self.scale_timer = self.GLib.timeout_add(200, self.apply_scale)

    def apply_scale(self):
        self.scale_timer = None
        value = self.scale.get_value()

        def done(result, error):
            self.say(error or result, bool(error))

        self.background(lambda: set_brightness(value), done)
        return False


