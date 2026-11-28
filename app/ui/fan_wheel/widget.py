class FanWheel:
    """A small fan on the Dashboard. It turns faster when the fan really runs faster."""

    def __init__(self, ui, size=60):
        self.ui = ui
        self.area = ui.Gtk.DrawingArea()
        self.area.set_size_request(size, size)
        self.area.connect("draw", self.on_draw)
        self.angle = 0.0
        self.level = 0.0   # 0 to 1, drawn right now; eases towards the target
        self.target = 0.0
        self.rpm = None    # None: no reading

    def set_rpm(self, rpm):
        changed = (rpm is None) != (self.rpm is None)
        self.rpm = rpm
        self.target = fan_level(rpm)
        if changed:
            self.area.queue_draw()

    def step(self, dt):
        """Moves the blades for dt seconds. Speeding up and slowing down is gradual."""
        before = self.level
        self.level += (self.target - self.level) * min(1.0, dt * 3.0)
        if abs(self.level - self.target) < 0.005:
            self.level = self.target
        moving = self.level > 0
        if moving:
            self.angle = (self.angle + spin_rate_for(self.level) * 2 * math.pi * dt) % (2 * math.pi)
        if moving or self.level != before:
            self.area.queue_draw()
        return moving

    def on_draw(self, area, cr):
        context = area.get_style_context()

        def pick(name, fallback):
            found, color = context.lookup_color(name)
            return (color.red, color.green, color.blue, 1.0) if found else fallback

        blade = speed_color(self.level)
        hub = tuple(c + (1.0 - c) * 0.45 for c in blade[:3]) + (1.0,)  # a lighter shade of the blades
        colors = {"ring": pick("loq_border", (0.27, 0.28, 0.35, 1.0)),
                  "blade": blade, "hub": hub,
                  "idle": pick("loq_muted", (0.70, 0.72, 0.82, 1.0))}
        draw_fan(cr, area.get_allocated_width(), area.get_allocated_height(),
                 self.angle, colors, self.rpm is not None)
        return False


