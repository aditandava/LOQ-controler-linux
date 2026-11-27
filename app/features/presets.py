# ----------------------------------------------------------------------- presets

# key: (title, performance modes to try in order, refresh pick, brightness %, extras)
PRESETS = {
    "ultra": ("Ultra saver", ["ultra-saver"], min, 20, {"keyboard": 0, "idle": 5}),
    "saver": ("Battery saver", ["low-power", "quiet"], min, 40, {}),
    "daily": ("Daily", ["balanced"], max, 70, {}),
    "boost": ("Performance", ["performance", "balanced-performance"], max, None, {}),
}


def apply_preset(key):
    title, wanted, pick_rate, brightness, extras = PRESETS[key]
    if key == "boost" and on_ac() is False:
        raise ActionError(f"Plug in the charger to use the {title} preset.")
    done, failed = [], []
    steps = []
    profile = profile_info()
    if profile:
        name = next((p for p in wanted if p in profile["options"]), None)
        if name:
            steps.append(lambda: set_profile(name))
    screen = display_info()
    if screen and screen["options"]:
        rate = pick_rate(screen["options"])
        if rate != screen["active"]:
            steps.append(lambda: set_refresh(rate))
    if brightness and backlight_info():
        steps.append(lambda: set_brightness(brightness))
    if extras.get("keyboard") is not None and keyboard_info():
        steps.append(lambda: set_keyboard(extras["keyboard"]))
    if extras.get("idle") in IDLE_PRESETS and idle_info():
        steps.append(lambda: set_idle(extras["idle"]))
    for step in steps:
        try:
            done.append(step())
        except ActionError as err:
            failed.append(str(err))
    if failed:
        raise ActionError(f"{title} partly applied. " + " ".join(failed))
    return f"{title} applied" if done else f"{title}: nothing to change"


