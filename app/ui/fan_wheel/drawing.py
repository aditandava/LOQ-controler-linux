# --------------------------------------------------------------------- one fan

FAN_NO_READING = (0.55, 0.57, 0.64, 1.0)  # grey: the speed is unknown


def fan_tint(level, active=True):
    return (speed_color(level) if active else FAN_NO_READING)[:3]


def fan_space(cr, width, height, mirror):
    """Moves and scales `cr` so that the 400 x 400 fan fills the middle of the area."""
    size = min(width, height)
    cr.translate((width - size) / 2, (height - size) / 2)
    cr.scale(size / 400, size / 400)
    if mirror:
        cr.translate(400, 0)
        cr.scale(-1, 1)


def draw_fan_base(cr, width, height, level, active=True, mirror=False):
    """The parts that do not turn: casing and glow ring."""
    cr.save()
    fan_space(cr, width, height, mirror)
    draw_housing(cr)
    draw_glow(cr, fan_tint(level, active), level)
    cr.restore()


def draw_fan_rotor(cr, width, height, angle, streak, level, active=True, mirror=False):
    """The turning parts, drawn on top of the base."""
    tint = fan_tint(level, active)
    cr.save()
    fan_space(cr, width, height, mirror)
    draw_blades(cr, angle, tint, level)
    draw_streaks(cr, streak, tint, level)
    draw_hub(cr, angle, tint)
    cr.restore()


def draw_fan(cr, width, height, angle, streak, level, active=True, mirror=False):
    """Draws a whole laptop blower fan. `mirror` flips it, for the fan on the other side."""
    draw_fan_base(cr, width, height, level, active, mirror)
    draw_fan_rotor(cr, width, height, angle, streak, level, active, mirror)


