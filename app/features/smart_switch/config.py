# --------------------------------------------- settings per power source (auto switch)

AUTO_FILE = CONFIG_DIR / "loq-center" / "auto.json"


AUTO_SOURCES = {"ac": "On charger", "battery": "On battery"}


SWITCH_NAME = "Smart Switch"  # the tab that changes settings with the charger


SWITCH_HINTS = {"ac": "Applied when plugged in", "battery": "Applied when unplugged"}


AUTO_KEYS = ("profile", "refresh", "idle", "brightness")


AUTO_TITLES = {"profile": "Performance", "refresh": "Refresh rate", "idle": "Sleep after",
               "brightness": "Brightness"}


AUTO_BRIGHTNESS = (20, 30, 40, 50, 60, 70, 80, 90, 100)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def clean_auto_value(key, value):
    """A saved value that makes sense, or None, which means 'leave this setting alone'."""
    if key == "profile":
        return value if isinstance(value, str) and re.fullmatch(r"[a-z-]{2,30}", value) else None
    if key == "refresh":
        return value if _is_int(value) and 24 <= value <= 500 else None
    if key == "idle":
        return value if _is_int(value) and value in IDLE_PRESETS else None
    if key == "brightness":
        return value if _is_int(value) and 5 <= value <= 100 else None
    return None


def load_auto():
    config = {"enabled": False, **{s: dict.fromkeys(AUTO_KEYS) for s in AUTO_SOURCES}}
    try:
        data = json.loads(AUTO_FILE.read_text())
    except (OSError, ValueError):
        return config
    if not isinstance(data, dict):
        return config
    config["enabled"] = data.get("enabled") is True
    for source in AUTO_SOURCES:
        saved = data.get(source)
        if isinstance(saved, dict):
            for key in AUTO_KEYS:
                config[source][key] = clean_auto_value(key, saved.get(key))
    if config["battery"]["profile"] in CHARGER_ONLY:  # saved by an older version
        config["battery"]["profile"] = "balanced"
    return config


def save_auto(config):
    try:
        AUTO_FILE.parent.mkdir(parents=True, exist_ok=True)
        part = AUTO_FILE.with_suffix(".tmp")
        part.write_text(json.dumps(config, indent=2))
        part.replace(AUTO_FILE)
    except OSError as err:
        raise ActionError(f"Could not save {AUTO_FILE}: {err}")


def auto_choices(key, source, options, saved=None):
    """The (value, label) pairs one drop-down offers, without "Keep"."""
    if key == "profile":
        return [(p, PROFILE_LABELS.get(p, p)) for p in usable_profiles(options["profile"], source)]
    if key == "refresh":
        return [(r, f"{r} Hz") for r in options["refresh"]]
    if key == "idle":
        return [(k, v[0]) for k, v in IDLE_PRESETS.items()] if options["idle"] else []
    if not options["brightness"]:
        return []
    levels = set(AUTO_BRIGHTNESS) | ({saved} if saved else set())
    return [(b, f"{b}%") for b in sorted(levels)]


def power_source():
    ac = on_ac()
    return None if ac is None else ("ac" if ac else "battery")


