class BackgroundPickerMixin:
    """Display tab: window background."""

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


