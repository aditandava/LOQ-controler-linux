def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else (255, 0, 0)


def contrast_fg(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return "#11111B" if (0.299 * r + 0.587 * g + 0.114 * b) > 145 else "#FFFFFF"


