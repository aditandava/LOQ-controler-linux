# ----------------------------------------------------- Off / Light / Dark: icons
# Each icon is drawn around (0, 0). `amount` is how far the pill has reached it (0 to 1).


def draw_power_icon(cr, r, amount):
    gap = 0.75
    cr.new_sub_path()
    cr.arc(0, 0.6, r * 0.85, -math.pi / 2 + gap, 3 * math.pi / 2 - gap)
    cr.stroke()
    cr.move_to(0, -r)
    cr.line_to(0, -r * 0.1)
    cr.stroke()


def draw_sun_icon(cr, r, amount):
    cr.rotate((amount - 1) * math.pi / 2)  # the rays turn into place
    cr.new_sub_path()
    cr.arc(0, 0, r * 0.42, 0, 2 * math.pi)
    cr.fill()
    for i in range(8):
        a = i * math.pi / 4
        cr.move_to(math.cos(a) * r * 0.72, math.sin(a) * r * 0.72)
        cr.line_to(math.cos(a) * r * 1.05, math.sin(a) * r * 1.05)
        cr.stroke()


def draw_moon_icon(cr, r, amount):
    cr.rotate((1 - amount) * -1.1)  # the crescent swings into place
    dx, dy, cut = r * 0.58, -r * 0.42, r * 0.82
    d, towards = math.hypot(dx, dy), math.atan2(dy, dx)
    outer = math.acos((r * r + d * d - cut * cut) / (2 * r * d))
    inner = math.acos((cut * cut + d * d - r * r) / (2 * cut * d))
    back = towards + math.pi
    cr.new_sub_path()
    cr.arc(0, 0, r, towards + outer, towards - outer + 2 * math.pi)
    cr.arc_negative(dx, dy, cut, back + inner, back - inner)
    cr.close_path()
    cr.fill()


def draw_mode_icon(cr, mode, x, y, amount):
    cr.save()
    cr.translate(x, y)
    pop = 1 + 0.22 * math.sin(math.pi * amount)
    cr.scale(pop, pop)
    cr.set_line_width(1.8)
    cr.set_line_cap(1)  # round
    {"off": draw_power_icon, "light": draw_sun_icon, "dark": draw_moon_icon}[mode](cr, 7.0, amount)
    cr.restore()
