class WidgetsMixin:
    """Widget helpers, plugin loading and show/hide."""

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

    def add_css(self, css_text):
        prov = self.Gtk.CssProvider()
        prov.load_from_data(css_text.encode())
        self.Gtk.StyleContext.add_provider_for_screen(
            self.Gdk.Screen.get_default(), prov, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 2)
        self.plugin_providers.append(prov)
        return prov

    def load_plugins(self):
        if not PLUGIN_DIR.is_dir():
            return
        for path in sorted(PLUGIN_DIR.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f"loq_plugin_{path.stem}", path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if callable(getattr(mod, "register", None)):
                        mod.register(self)
            except Exception as err:
                print(f"Plugin {path.name} failed: {err}", file=sys.stderr)
                log(f"plugin {path.name} failed: {traceback.format_exc()}")

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


