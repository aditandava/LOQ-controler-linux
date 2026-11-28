def theme_colors(theme_text):
    """Defaults, overridden only by well-formed colour lines from the wallbash theme."""
    colors = dict(BASE_COLORS)
    for name, value in re.findall(r"@define-color\s+(loq_\w+)\s+(#[0-9A-Fa-f]{6})\s*;", theme_text or ""):
        if name in colors:
            colors[name] = value
    return colors


def build_css(theme_text, picture=None, scenes=None):
    colors = theme_colors(theme_text)
    css = "".join(f"@define-color {k} {v};\n" for k, v in colors.items()) + RULES
    if picture:  # the picture, dimmed towards the bottom so that text stays readable
        css += ("window.loq { background-image: linear-gradient(to bottom, alpha(@loq_bg, 0.15), "
                f'alpha(@loq_bg, 0.55)), url("{picture.as_uri()}"); background-size: cover; '
                "background-position: center; background-repeat: no-repeat; }\n")
    for name, image in (scenes or {}).items():  # one wallpaper per tab, chosen by a window class
        css += (f"window.loq.scene-{name} {{ background-image: linear-gradient(to bottom, "
                f'alpha(@loq_bg, 0.30), alpha(@loq_bg, 0.62)), url("{image.as_uri()}"); '
                "background-size: cover; background-position: center bottom; "
                "background-repeat: no-repeat; }\n")
    return css


