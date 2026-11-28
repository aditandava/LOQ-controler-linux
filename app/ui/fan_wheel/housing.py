# ------------------------------------------------------------------ fan casing
# Everything here and in rotor.py is drawn on a 400 x 400 square, centred on 200, 200.

CASE_EDGE = (0.290, 0.318, 0.388, 1.0)


def fan_circle(cr, x, y, radius):
    cr.new_path()
    cr.arc(x, y, radius, 0, 2 * math.pi)


def draw_housing(cr):
    """The spiral blower casing with its air outlet, screw tabs and round inlet."""
    import cairo  # only the window needs it
    body = cairo.LinearGradient(0, 0, 400, 400)
    body.add_color_stop_rgb(0.0, 0.231, 0.255, 0.310)
    body.add_color_stop_rgb(0.5, 0.133, 0.149, 0.192)
    body.add_color_stop_rgb(1.0, 0.082, 0.094, 0.122)
    cr.new_path()
    for i in range(91):  # the spiral grows from the top, clockwise, to the left side
        turn = -math.pi / 2 + i / 90 * math.pi * 1.5
        radius = 172 + 18 * i / 90
        cr.line_to(200 + radius * math.cos(turn), 200 + radius * math.sin(turn))
    cr.arc(36, 54, 26, math.pi, math.pi * 1.5)  # rounded corner of the outlet
    cr.close_path()
    cr.set_source(body)
    cr.fill_preserve()
    cr.set_line_width(3)
    cr.set_source_rgba(*CASE_EDGE)
    cr.stroke()
    for x, y in ((34, 52), (366, 262), (92, 354)):
        fan_circle(cr, x, y, 14)
        cr.set_source_rgb(0.169, 0.188, 0.235)
        cr.fill_preserve()
        cr.set_line_width(2)
        cr.set_source_rgba(*CASE_EDGE)
        cr.stroke()
        fan_circle(cr, x, y, 5)
        cr.set_source_rgb(0.043, 0.051, 0.071)
        cr.fill()
    fan_circle(cr, 200, 200, 158)
    cr.set_source_rgb(0.024, 0.027, 0.039)
    cr.fill()


