def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (255, 0, 0)


def luminance(hex_color):
    """How bright a colour looks, 0 to 255."""
    r, g, b = hex_to_rgb(hex_color)
    return 0.299 * r + 0.587 * g + 0.114 * b


def contrast_fg(hex_color):
    return "#11111B" if luminance(hex_color) > 145 else "#FFFFFF"


def darker(hex_color, factor=0.55):
    return "#" + "".join(f"{round(v * factor):02X}" for v in hex_to_rgb(hex_color))


def deepen(hex_color):
    """The same hue as a rich, dark colour. Keyboard LEDs show pale colours as nearly white."""
    hue, saturation, _value = colorsys.rgb_to_hsv(*(v / 255 for v in hex_to_rgb(hex_color)))
    rich = colorsys.hsv_to_rgb(hue, max(saturation, DARK_SATURATION), DARK_VALUE)
    return "#" + "".join(f"{round(v * 255):02X}" for v in rich)


def is_grey(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return max(r, g, b) - min(r, g, b) <= 0.08 * max(r, g, b)


def pick_tone(shades, tone):
    """From HyDE's shades of one colour: the brightest for "light", a rich dark one for "dark"."""
    ordered = sorted(shades, key=luminance)
    if tone != "dark":
        return ordered[-1]
    if not is_grey(ordered[0]):
        return deepen(ordered[0])
    # A grey theme has no hue to enrich: use its dark shade, or dim the only one.
    return ordered[0] if ordered[0] != ordered[-1] else darker(ordered[0])


