# CSS: On/off switches.
RULES_SWITCH = """\
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
"""


