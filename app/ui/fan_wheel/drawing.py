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


