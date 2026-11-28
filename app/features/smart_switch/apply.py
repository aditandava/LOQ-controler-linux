def apply_auto(source, only=None):
    """Applies the saved settings for "ac" or "battery". Only changes what is different.

    `only` limits this to one setting, so that picking it does not reset the others."""
    saved = load_auto()[source]
    entry = {key: saved[key] if only in (None, key) else None for key in AUTO_KEYS}
    title = AUTO_SOURCES[source]
    steps = []

    want = entry["profile"]
    check = only in (None, "profile") and (want or source == "battery")
    now = profile_info() if check else None
    if now:
        # "Keep" must not leave a charger-only mode running after unplugging
        if not want and source == "battery" and now["active"] in CHARGER_ONLY:
            want = "balanced"
        if want in now["options"] and now["active"] != want:
            steps.append(lambda: set_profile(want))
    rate = entry["refresh"]
    if rate:
        screen = display_info()
        if screen and rate in screen["options"] and screen["active"] != rate:
            steps.append(lambda: set_refresh(rate))
    minutes = entry["idle"]
    if minutes is not None:
        idle = idle_info()
        if idle is not None and idle["active"] != minutes:
            steps.append(lambda: set_idle(minutes))
    level = entry["brightness"]
    light = backlight_info()
    if level and light and round(light["value"] * 100 / light["max"]) != level:
        steps.append(lambda: set_brightness(level))

    done, failed = [], []
    for step in steps:
        try:
            done.append(step())
        except ActionError as err:
            failed.append(str(err))
    if failed:
        raise ActionError(f"{title}: " + " ".join(failed))
    return f"{title}: settings applied" if done else f"{title}: already set"


