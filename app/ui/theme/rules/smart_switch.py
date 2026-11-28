# CSS: Smart Switch cards and drop-downs.
RULES_SMART_SWITCH = """\
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
"""


