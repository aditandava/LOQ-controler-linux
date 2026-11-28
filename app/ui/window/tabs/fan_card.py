class FanCardMixin:
    """Dashboard fan box: CPU fan on the left, temperatures in the middle, GPU fan on the right."""

    def build_fan_card(self, box):
        row = self.Gtk.Box(spacing=12)
        self.fan_sides = []  # (column, name label, RPM label, wheel): CPU first, then GPU
        for name, pack in (("CPU fan", row.pack_start), ("GPU fan", row.pack_end)):
            side = self.vbox(4)
            wheel = FanWheel(self, mirror=name == "GPU fan")
            wheel.area.set_halign(self.Gtk.Align.CENTER)
            self.add(side, wheel.area)
            title = self.add(side, self.centered(name, "caption"))
            rpm = self.add(side, self.centered("…", "muted"))
            pack(side, False, False, 0)
            self.fan_sides.append((side, title, rpm, wheel))
            self.fan_wheels.append(wheel)

        middle = self.vbox(2)
        middle.set_valign(self.Gtk.Align.CENTER)
        self.add(middle, self.centered("CPU temp", "caption"))
        self.fan_cpu_temp = self.add(middle, self.centered("…", "value"))
        gpu_title = self.add(middle, self.centered("GPU temp", "caption"))
        gpu_title.set_margin_top(8)
        self.fan_gpu_temp = self.add(middle, self.centered("…", "value"))
        row.pack_start(middle, True, True, 0)
        self.add(box, row)

    def centered(self, text, style):
        """A one-line label in the middle of its column."""
        widget = self.label(text, style)
        widget.set_xalign(0.5)
        widget.set_line_wrap(False)
        return widget


