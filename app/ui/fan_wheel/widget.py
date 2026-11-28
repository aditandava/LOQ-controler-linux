class FanWheel:
    """A fan on the Dashboard. It spins faster and changes colour as the real fan speeds up."""

    def __init__(self, ui, size=160, mirror=False):
        self.ui = ui
        self.mirror = mirror
        self.area = ui.Gtk.DrawingArea()
        self.area.set_size_request(size, size)
        self.area.connect("draw", self.on_draw)
        self.angle = 0.0   # blades
        self.streak = 0.0  # motion blur
        self.level = 0.0   # 0 to 1, drawn right now; eases towards the target
        self.target = 0.0
        self.rpm = None    # None: no reading
        self.base, self.base_key = None, None  # cached picture of the parts that do not turn

    def set_rpm(self, rpm):
        changed = (rpm is None) != (self.rpm is None)
        self.rpm = rpm
        self.target = fan_level(rpm)
        if changed:
            self.area.queue_draw()

    def step(self, dt):
        """Moves the fan for dt seconds. Speeding up and slowing down is gradual."""
        before = self.level
        self.level += (self.target - self.level) * min(1.0, dt * 2.5)
        if abs(self.level - self.target) < 0.005:
            self.level = self.target
        moving = self.level > 0
        if moving:
            turn = 2 * math.pi
            self.angle = (self.angle + spin_rate_for(self.level) * turn * dt) % turn
            self.streak = (self.streak + streak_rate_for(self.level) * turn * dt) % turn
        if moving or self.level != before:
            self.area.queue_draw()
        return moving

    def on_draw(self, area, cr):
        import cairo
        width, height = area.get_allocated_width(), area.get_allocated_height()
        active = self.rpm is not None
        # Redrawing the casing on every frame wastes CPU: do it only when its look changes
        step = round(self.level * 50)
        key = (width, height, step, active)
        if key != self.base_key:
            self.base = cr.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA, width, height)
            draw_fan_base(cairo.Context(self.base), width, height, step / 50, active, self.mirror)
            self.base_key = key
        cr.set_source_surface(self.base, 0, 0)
        cr.paint()
        draw_fan_rotor(cr, width, height, self.angle, self.streak, self.level, active, self.mirror)
        return False


