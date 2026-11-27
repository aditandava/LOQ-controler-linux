# ------------------------------------------------------------------------ theme

BASE_COLORS = {
    "loq_bg": "#1e1e2e", "loq_surface": "#2a2b3d", "loq_border": "#45475a",
    "loq_fg": "#f5e9e4", "loq_muted": "#b4b7d1", "loq_accent": "#c79bf0", "loq_accent2": "#ebbcba",
    "loq_on_accent": "#1e1e2e",
}

RULES = """
window.loq { background-color: @loq_bg; color: @loq_fg; }
window.loq label { color: @loq_fg; text-shadow: none; }
window.loq label.title { font-size: 26px; font-weight: 800;
  text-shadow: 0 1px 8px alpha(@loq_bg, 0.9); }
window.loq label.chip, window.loq label.status { background-color: alpha(@loq_bg, 0.62);
  border: 1px solid alpha(@loq_fg, 0.10); border-radius: 999px; padding: 5px 14px; }
window.loq label.muted { color: @loq_muted; }
window.loq label.heading { font-weight: bold; color: @loq_accent2; }
window.loq label.value { font-size: 26px; font-weight: 800; }
window.loq label.error { color: #ff8f8f; }
window.loq scrolledwindow, window.loq viewport, window.loq stack {
  background: none; border: none; box-shadow: none; }
window.loq scrolledwindow undershoot, window.loq scrolledwindow overshoot { background: none; }
window.loq scrollbar { background: transparent; border: none; }
window.loq .card { background-color: alpha(@loq_surface, 0.60);
  border: 1px solid alpha(@loq_fg, 0.14); border-radius: 20px; padding: 18px; }
window.loq button { background-image: none; background-color: alpha(@loq_surface, 0.75);
  color: @loq_fg; border: 1px solid alpha(@loq_fg, 0.10); border-radius: 12px;
  padding: 9px 14px; box-shadow: none; text-shadow: none;
  transition: background-color 150ms ease, border-color 150ms ease; }
window.loq .card button { background-color: alpha(@loq_bg, 0.58); }
window.loq button:hover { border-color: @loq_accent; }
window.loq button:focus { border-color: @loq_accent2; }
window.loq button.active, window.loq button:checked {
  background-color: @loq_accent; background-image: linear-gradient(135deg, @loq_accent, @loq_accent2);
  border-color: transparent; }
window.loq button.active label, window.loq button:checked label { color: @loq_on_accent;
  font-weight: bold; }
window.loq button:disabled { opacity: 0.55; }
window.loq progressbar trough { background-image: none; background-color: alpha(@loq_bg, 0.65);
  border: none; border-radius: 999px; min-height: 8px; }
window.loq progressbar progress { background-image: linear-gradient(to right, @loq_accent, @loq_accent2);
  border: none; border-radius: 999px; min-height: 8px; }
window.loq scale trough { background-color: alpha(@loq_bg, 0.65); border: none;
  border-radius: 999px; min-height: 8px; }
window.loq scale highlight { background-image: linear-gradient(to right, @loq_accent, @loq_accent2);
  border: none; border-radius: 999px; }
window.loq scale slider { background-image: none; background-color: @loq_fg; border: none;
  box-shadow: 0 1px 4px alpha(black, 0.4); min-width: 20px; min-height: 20px; }
window.loq stackswitcher { background-color: alpha(@loq_bg, 0.62);
  border: 1px solid alpha(@loq_fg, 0.10); border-radius: 17px; box-shadow: none; padding: 5px; }
window.loq stackswitcher button { background-color: transparent; border: 1px solid transparent;
  border-radius: 12px; margin: 0; padding: 8px 6px; }
window.loq stackswitcher button:hover { background-color: alpha(@loq_surface, 0.80); }
window.loq stackswitcher button:focus { border-color: @loq_accent2; }
window.loq stackswitcher button:checked {
  background-image: linear-gradient(135deg, @loq_accent, @loq_accent2); }
window.loq label.column { font-weight: bold; color: @loq_muted; }
window.loq label.column.now { color: @loq_accent; }
window.loq combobox button { background-color: alpha(@loq_bg, 0.65); padding: 7px 12px; }
window.loq combobox button:checked { background-image: none;
  background-color: alpha(@loq_bg, 0.85); border-color: @loq_accent; }
window.loq combobox arrow { color: @loq_muted; min-width: 14px; min-height: 14px; }
window.loq switch { background-image: none; background-color: alpha(@loq_bg, 0.70);
  border: 1px solid alpha(@loq_fg, 0.15); border-radius: 15px; box-shadow: none; }
window.loq switch:checked { background-image: linear-gradient(135deg, @loq_accent, @loq_accent2);
  border-color: transparent; }
window.loq switch slider { background-image: none; background-color: @loq_fg; border: none;
  border-radius: 12px; box-shadow: 0 1px 4px alpha(black, 0.4); min-width: 24px;
  min-height: 24px; margin: 2px; }
window.loq switch image { color: transparent; }
menu { background-image: none; background-color: @loq_surface; border: 1px solid @loq_border;
  padding: 4px; }
menu menuitem { color: @loq_fg; padding: 6px 12px; }
menu menuitem:hover { background-color: @loq_accent; color: @loq_on_accent; }
"""


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


