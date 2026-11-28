class ChromeMixin:
    """Window frame: title row, tab bar, status line."""

    def header(self):
        row = self.Gtk.Box(spacing=12)
        row.pack_start(self.label("LOQ Center", "title"), False, False, 0)
        self.subtitle = self.label("Reading hardware…", "chip")
        self.subtitle.set_line_wrap(False)
        self.subtitle.set_valign(self.Gtk.Align.CENTER)
        row.pack_end(self.subtitle, False, False, 0)
        return row

    def status_line(self):
        self.status = self.label("Ready", "status")
        self.status.set_halign(self.Gtk.Align.START)
        return self.status

    def tab_bar(self):
        switcher = self.Gtk.StackSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_homogeneous(True)
        switcher.set_spacing(8)
        switcher.get_style_context().remove_class("linked")  # separate tabs, not one joined strip
        return switcher


