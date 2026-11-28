# CSS: Buttons.
RULES_BUTTONS = """\
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
"""


