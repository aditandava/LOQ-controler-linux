# --------------------------------------------------- Off / Light / Dark: drawing

MODE_PAD = 4  # space between the track and the pill


def pill_path(cr, x, y, width, height):
    radius = height / 2
    cr.new_sub_path()
    cr.arc(x + width - radius, y + radius, radius, -math.pi / 2, math.pi / 2)
    cr.arc(x + radius, y + radius, radius, math.pi / 2, 3 * math.pi / 2)
    cr.close_path()


def draw_mode_labels(cr, segment, height, position, ink):
    """Icon and name in the middle of every segment, all in one colour."""
    cr.set_source_rgb(*ink)
    for i, (mode, name) in enumerate(HYDE_MODE_OPTS):
        wide = cr.text_extents(name).x_advance
        x = MODE_PAD + segment * (i + 0.5) - (wide + 22) / 2
        draw_mode_icon(cr, mode, x + 7, height / 2, max(0.0, 1 - abs(position - i)))
        cr.move_to(x + 22, height / 2 + 4.8)
        cr.show_text(name)
    cr.new_path()


def draw_mode_switch(cr, width, height, edges, palettes, theme, family="sans-serif",
                     hover=None, focus=False):
    """The whole control. `palettes` holds four pill colours for each of the three modes."""
    import cairo
    segment = (width - 2 * MODE_PAD) / len(HYDE_MODE_OPTS)
    inner = height - 2 * MODE_PAD
    left, right = edges
    position = (left + right) / 2 - 0.5
    x, wide = MODE_PAD + left * segment, (right - left) * segment

    cr.select_font_face(family, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(13)

    pill_path(cr, 1, 1, width - 2, height - 2)  # track
    cr.set_source_rgba(*theme["bg"], 0.75)
    cr.fill_preserve()
    cr.set_source_rgba(*(theme["accent2"] if focus else theme["fg"]), 0.95 if focus else 0.14)
    cr.set_line_width(2 if focus else 1)
    cr.stroke()

    if hover is not None and abs(position - hover) > 0.5:
        pill_path(cr, MODE_PAD + hover * segment, MODE_PAD, segment, inner)
        cr.set_source_rgba(*theme["fg"], 0.08)
        cr.fill()
    draw_mode_labels(cr, segment, height, position, theme["muted"])

    colours = blend_palette(palettes, position)
    mean = tuple(sum(channel) / len(colours) for channel in zip(*colours))
    for grow, alpha in ((3.0, 0.08), (2.0, 0.12), (1.0, 0.18)):  # soft glow around the pill
        pill_path(cr, x - grow, MODE_PAD - grow, wide + 2 * grow, inner + 2 * grow)
        cr.set_source_rgba(*mean, alpha)
        cr.fill()

    fill = cairo.LinearGradient(x, 0, x + wide, 0)
    for i, colour in enumerate(colours):
        fill.add_color_stop_rgb(i / (len(colours) - 1), *colour)
    pill_path(cr, x, MODE_PAD, wide, inner)
    cr.set_source(fill)
    cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, 0.22)
    cr.set_line_width(1)
    cr.stroke()

    cr.save()  # the same labels again in a contrasting colour, only where the pill is
    pill_path(cr, x, MODE_PAD, wide, inner)
    cr.clip()
    bright = 0.299 * mean[0] + 0.587 * mean[1] + 0.114 * mean[2] > 0.57
    draw_mode_labels(cr, segment, height, position, (0.07, 0.07, 0.11) if bright else (1, 1, 1))
    cr.restore()
