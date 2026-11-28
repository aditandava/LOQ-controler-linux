class Choice:
    """A row of buttons where the active one is highlighted."""

    def __init__(self, ui, on_pick):
        self.ui, self.on_pick = ui, on_pick
        self.box = ui.Gtk.Box(spacing=8)
        self.box.set_homogeneous(True)
        self.options, self.buttons = None, {}

    def update(self, options, active):
        options = list(options)
        if options != self.options:
            for child in self.box.get_children():
                child.destroy()
            self.options, self.buttons = options, {}
            for value, label in options:
                button = self.ui.Gtk.Button(label=label)
                button.connect("clicked", lambda _w, v=value: self.on_pick(v))
                button.set_sensitive(not self.ui.busy)
                self.box.pack_start(button, True, True, 0)
                self.buttons[value] = button
                self.ui.actions.append(button)
            self.box.show_all()
        for value, button in self.buttons.items():
            context = button.get_style_context()
            if value == active:
                context.add_class("active")
            else:
                context.remove_class("active")


