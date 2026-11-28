class WidgetsMixin:
    """Small widget builders and show/hide."""

    # ---- widgets
    def vbox(self, spacing):
        return self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=spacing)

    def label(self, text, style=None):
        widget = self.Gtk.Label(label=text)
        widget.set_xalign(0)
        widget.set_line_wrap(True)
        widget.set_max_width_chars(60)
        if style:
            widget.get_style_context().add_class(style)
        return widget

    def page(self, name, title):
        scroller = self.Gtk.ScrolledWindow()
        box = self.vbox(12)
        scroller.add(box)
        self.stack.add_titled(scroller, name, title)
        return box

    def card(self, parent, heading):
        box = self.vbox(8)
        box.get_style_context().add_class("card")
        box.pack_start(self.label(heading, "heading"), False, False, 0)
        parent.pack_start(box, False, False, 0)
        return box

    def button(self, text, callback):
        widget = self.Gtk.Button(label=text)
        widget.connect("clicked", lambda _w: callback())
        self.actions.append(widget)
        return widget

    def add(self, parent, widget):
        parent.pack_start(widget, False, False, 0)
        return widget

    def flag(self, widget, name, on):
        """Add or remove a style class on a widget."""
        context = widget.get_style_context()
        if on:
            context.add_class(name)
        else:
            context.remove_class(name)

    def visible(self, widget, show):
        widget.set_no_show_all(not show)
        if show:
            widget.show_all()
        else:
            widget.hide()


