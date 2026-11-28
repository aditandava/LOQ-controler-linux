# CSS: Window, labels, scroll areas and cards.
RULES_WINDOW = """\
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
"""


