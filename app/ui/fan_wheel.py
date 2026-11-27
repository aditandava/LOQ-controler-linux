FAN_RPM_FULL = 6000.0  # fan speed drawn at top speed and fully blue


def fan_level(rpm):
    """0 for a stopped or unknown fan, rising to 1 at FAN_RPM_FULL."""
    if not rpm or rpm <= 0:
        return 0.0
    return min(1.0, rpm / FAN_RPM_FULL)


def spin_rate_for(level):
    """Turns per second drawn for a level between 0 and 1. A stopped fan does not turn.

    The real speed is far too fast to draw, so this only has to look faster when the fan is
    faster. At most 4.8 turns per second: at 60 frames per second that is under 30 degrees per
    frame, less than half the 72 degrees between two blades, so the blades never seem to turn
    backwards."""
    return 0.0 if level <= 0 else 0.2 + 4.6 * level


def spin_rate(rpm):
    return spin_rate_for(fan_level(rpm))


def speed_color(level):
    """Red for a slow fan, then orange, yellow and green, to blue for a fast one."""
    level = max(0.0, min(1.0, level))
    red, green, blue = colorsys.hsv_to_rgb(220 / 360 * level, 0.62, 0.97)
    return (red, green, blue, 1.0)


def draw_fan(cr, width, height, angle, colors, active=True, blades=5):
    """Draws a small fan with its blades turned by `angle` radians."""
    cx, cy = width / 2, height / 2
    radius = min(width, height) / 2 - 2
    cr.set_line_width(2)
    cr.set_source_rgba(*colors["ring"])
    cr.new_path()
    cr.arc(cx, cy, radius, 0, 2 * math.pi)
    cr.stroke()
    blade = colors["blade"] if active else (*colors["idle"][:3], 0.45)
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(angle)
    for _ in range(blades):
        cr.new_path()
        cr.move_to(radius * 0.16, -radius * 0.04)
        cr.curve_to(radius * 0.28, -radius * 0.70, radius * 0.80, -radius * 0.62,
                    radius * 0.90, -radius * 0.14)
        cr.curve_to(radius * 0.62, -radius * 0.02, radius * 0.40, radius * 0.10,
                    radius * 0.16, radius * 0.08)
        cr.close_path()
        cr.set_source_rgba(*blade)
        cr.fill()
        cr.rotate(2 * math.pi / blades)
    cr.restore()
    cr.new_path()
    cr.set_source_rgba(*(colors["hub"] if active else (*colors["idle"][:3], 0.6)))
    cr.arc(cx, cy, radius * 0.17, 0, 2 * math.pi)
    cr.fill()


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


