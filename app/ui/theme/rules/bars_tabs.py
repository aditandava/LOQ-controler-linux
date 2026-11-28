# CSS: Progress bars, sliders and the tab bar.
RULES_BARS_TABS = """\
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
"""


