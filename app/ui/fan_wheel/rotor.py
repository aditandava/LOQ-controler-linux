# ------------------------------------------------------------------- fan rotor


def draw_glow(cr, tint, level):
    """The coloured ring around the inlet. It glows wider and brighter on a fast fan."""
    spread = 5 + 16 * level
    for step in (4, 3, 2, 1):  # soft glow: wide faint rings under narrower ones
        fan_circle(cr, 200, 200, 157)
        cr.set_line_width(3 + spread * step / 4)
        cr.set_source_rgba(*tint, 0.04 + 0.07 * level)
        cr.stroke()
    fan_circle(cr, 200, 200, 157)
    cr.set_line_width(3)
    cr.set_source_rgba(*tint, 0.35 + 0.65 * level)
    cr.stroke()


def draw_blades(cr, angle, tint, level):
    """Thin curved blades and the rim that joins their tips. They fade as the fan speeds up."""
    def point(radius, turn):
        return radius * math.cos(turn), radius * math.sin(turn)

    start, bend, tip = (62.0, 0.0), point(108, -0.08), point(143, -0.36)
    # the same curve as a quadratic through `bend`, written as the cubic that Cairo draws
    first = tuple(s + 2 / 3 * (b - s) for s, b in zip(start, bend))
    second = tuple(t + 2 / 3 * (b - t) for t, b in zip(tip, bend))
    cr.save()
    cr.translate(200, 200)
    cr.rotate(angle)
    cr.set_line_width(5)
    cr.set_line_cap(1)  # round
    cr.set_source_rgba(*tint, 0.95 - 0.45 * level)
    cr.new_path()
    for _ in range(FAN_BLADES):
        cr.rotate(2 * math.pi / FAN_BLADES)
        cr.move_to(*start)
        cr.curve_to(*first, *second, *tip)
    cr.stroke()
    fan_circle(cr, 0, 0, 145)
    cr.set_line_width(3)
    cr.set_source_rgba(*tint, 0.55)
    cr.stroke()
    cr.restore()


def draw_streaks(cr, angle, tint, level):
    """Motion blur: three fading sweeps that turn faster than the blades."""
    if level <= 0:
        return
    cr.save()
    cr.translate(200, 200)
    cr.rotate(angle)
    cr.set_line_width(80)
    cr.set_line_cap(0)  # butt
    for sweep in range(3):
        base = sweep * 2 * math.pi / 3
        for part in range(7):
            cr.new_path()
            cr.arc(0, 0, 103, base + part * 0.14, base + (part + 1) * 0.14)
            cr.set_source_rgba(*tint, level * level * 0.2 * part / 7)
            cr.stroke()
    cr.restore()


def draw_hub(cr, angle, tint):
    """The metal hub with its coloured ring and a dot that shows the rotation."""
    import cairo
    metal = cairo.RadialGradient(178, 176, 6, 200, 200, 64)
    metal.add_color_stop_rgb(0.0, 0.349, 0.376, 0.435)
    metal.add_color_stop_rgb(1.0, 0.090, 0.102, 0.133)
    fan_circle(cr, 200, 200, 63)
    cr.set_source(metal)
    cr.fill()
    fan_circle(cr, 200, 200, 47)
    cr.set_line_width(4)
    cr.set_source_rgba(*tint, 0.9)
    cr.stroke()
    fan_circle(cr, 200 + 30 * math.cos(angle), 200 + 30 * math.sin(angle), 5)
    cr.set_source_rgba(*tint, 1.0)
    cr.fill()
    fan_circle(cr, 200, 200, 13)
    cr.set_source_rgb(0.043, 0.051, 0.071)
    cr.fill()


