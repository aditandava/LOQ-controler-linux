class DashboardMixin:
    """Dashboard tab (stats, fans, presets)."""

    def build_dashboard(self):
        page = self.page("dashboard", "Dashboard")
        grid = self.Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        page.pack_start(grid, False, False, 0)
        self.stats = {}
        items = [("cpu_temp", "CPU temperature"), ("cpu_use", "CPU load"), ("memory", "Memory"),
                 ("battery", "Battery"), ("watts", "Battery power"), ("fans", "Fans")]
        for index, (key, title) in enumerate(items):
            box = self.vbox(6)
            box.get_style_context().add_class("card")
            self.add(box, self.label(title, "muted"))
            value = self.add(box, self.label("…", "value"))
            bar = None
            if key in ("cpu_temp", "cpu_use", "memory", "battery"):
                bar = self.add(box, self.Gtk.ProgressBar())
            if key == "fans":
                wheels = self.Gtk.Box(spacing=10)
                for _ in range(2):
                    wheel = FanWheel(self)
                    wheels.pack_start(wheel.area, False, False, 0)
                    self.fan_wheels.append(wheel)
                self.add(box, wheels)
            self.stats[key] = (value, bar)
            grid.attach(box, index % 3, index // 3, 1, 1)
        card = self.card(page, "One-click presets")
        row = self.Gtk.Box(spacing=8)
        row.set_homogeneous(True)
        self.preset_buttons = {}
        for key, preset in PRESETS.items():
            button = self.button(preset[0], lambda k=key: self.act(lambda: apply_preset(k)))
            row.pack_start(button, True, True, 0)
            self.preset_buttons[key] = button
        self.add(card, row)


