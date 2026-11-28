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
window.loq label.title2 { font-size: 17px; font-weight: 800; }
window.loq label.caption { font-size: 11px; font-weight: bold; color: @loq_muted; }
window.loq label.badge { background-color: @loq_accent; color: @loq_on_accent;
  border-radius: 999px; padding: 3px 11px; font-size: 11px; font-weight: 800; }
window.loq .card.hero { background-image: linear-gradient(135deg, alpha(@loq_accent, 0.24),
  alpha(@loq_surface, 0.55)); border-color: alpha(@loq_accent, 0.35); border-radius: 24px;
  padding: 22px 24px; }
window.loq .card.source { border-radius: 24px; padding: 22px;
  transition: opacity 200ms ease, border-color 200ms ease, box-shadow 200ms ease; }
window.loq .card.source.now { border-color: alpha(@loq_accent, 0.80);
  background-color: alpha(@loq_surface, 0.80);
  box-shadow: 0 0 0 1px alpha(@loq_accent, 0.35), 0 10px 28px alpha(@loq_accent, 0.20); }
window.loq .card.source.dim { opacity: 0.62; }
window.loq combobox button { background-color: alpha(@loq_bg, 0.65); border-radius: 14px;
  padding: 10px 14px; min-height: 22px; }
window.loq combobox button:checked { background-image: none;
  background-color: alpha(@loq_bg, 0.85); border-color: @loq_accent; }
window.loq combobox arrow { color: @loq_muted; min-width: 14px; min-height: 14px; }
window.loq switch { min-width: 52px; min-height: 28px; padding: 0; margin: 0;
  background-image: none; background-color: alpha(@loq_bg, 0.80);
  border: none; border-radius: 999px;
  box-shadow: inset 0 0 0 1px alpha(@loq_fg, 0.20); color: transparent; text-shadow: none;
  transition: background-color 220ms ease, box-shadow 220ms ease; }
window.loq switch:hover { box-shadow: inset 0 0 0 1px alpha(@loq_accent, 0.85); }
window.loq switch:focus { box-shadow: inset 0 0 0 2px alpha(@loq_accent2, 0.90); }
window.loq switch:checked { background-image: none; background-color: @loq_accent;
  box-shadow: inset 0 0 0 1px alpha(@loq_accent, 0.60); color: transparent; }
window.loq switch:checked:hover { box-shadow: 0 0 10px alpha(@loq_accent, 0.55); }
window.loq switch:checked:focus { box-shadow: 0 0 0 2px alpha(@loq_accent2, 0.90); }
window.loq switch:disabled { opacity: 0.55; }
window.loq switch slider { min-width: 22px; min-height: 22px; margin: 3px; padding: 0;
  background-image: none; background-color: @loq_muted; border: none; border-radius: 999px;
  box-shadow: 0 1px 3px alpha(black, 0.45);
  transition: background-color 220ms ease, box-shadow 220ms ease; }
window.loq switch:hover slider { background-color: @loq_fg; }
window.loq switch:checked slider { background-color: @loq_on_accent;
  box-shadow: 0 1px 4px alpha(black, 0.35); }
window.loq switch:checked:hover slider { background-color: @loq_bg; }
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


