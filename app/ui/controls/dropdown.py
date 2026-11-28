class Dropdown:
    """A compact drop-down with the same update(options, active) shape as Choice."""

    def __init__(self, ui, on_pick):
        self.on_pick = on_pick
        self.box = ui.Gtk.ComboBoxText()
        self.box.set_hexpand(True)
        self.options, self.values, self.quiet = None, {}, False
        self.box.connect("changed", self.on_changed)
        self.box.connect("scroll-event", self.on_scroll)

    def update(self, options, active):
        options = list(options)
        self.quiet = True  # changes made here are not picks by the user
        if options != self.options:
            self.box.remove_all()
            self.options = options
            self.values = {str(value): value for value, _label in options}
            for value, label in options:
                self.box.append(str(value), label)
        # Untouched when unchanged, so the periodic refresh does not disturb an open list
        if self.box.get_active_id() != str(active):
            self.box.set_active_id(str(active))
        self.quiet = False

    def on_changed(self, box):
        key = box.get_active_id()
        if not self.quiet and key in self.values:
            self.on_pick(self.values[key])

    def on_scroll(self, box, _event):
        box.stop_emission_by_name("scroll-event")  # the wheel must not change a setting
        return False


