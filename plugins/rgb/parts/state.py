class RGBError(Exception):
    pass


def _read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def _copy_profile(p):
    return {
        "colors": list(p.get("colors", EMPTY_PROFILE["colors"]))[:4],
        "effect": p.get("effect", "Static") if p.get("effect") in EFFECTS else "Static",
        "brightness": int(p.get("brightness", 2)) if p.get("brightness") in (1, 2) else 2,
        "speed": int(p.get("speed", 1)) if p.get("speed") in (1, 2, 3, 4) else 1,
    }


def load_state():
    try:
        data = json.loads(RGB_JSON.read_text())
        raw = data.get("profiles", [])
        profiles = [_copy_profile(p) for p in raw[:4] if isinstance(p, dict)]
        while len(profiles) < 4:
            profiles.append(_copy_profile(EMPTY_PROFILE))
        active = int(data.get("active", 0))
        return profiles, active if 0 <= active < 4 else 0
    except (OSError, ValueError, TypeError):
        return [_copy_profile(EMPTY_PROFILE) for _ in range(4)], 0


def load_hyde_mode():
    """"off", "light" or "dark" (default: "light")."""
    try:
        data = json.loads(RGB_JSON.read_text())
        mode = data.get("hyde_mode")
        if mode in [value for value, _label in HYDE_MODE_OPTS]:
            return mode
        # Settings saved by the older on/off switch.
        return "light" if data.get("hyde_auto", True) else "off"
    except (OSError, ValueError, TypeError, AttributeError):
        return "light"


def load_hyde_auto():
    """True when the keyboard colours follow HyDE on every theme or wallpaper change."""
    return load_hyde_mode() != "off"


def load_hyde_brightness():
    """Brightness used while HyDE sync is on. Kept apart from the profiles."""
    try:
        return 1 if json.loads(RGB_JSON.read_text()).get("hyde_brightness") == 1 else 2
    except (OSError, ValueError, TypeError, AttributeError):
        return 2


def save_state(profiles, active=0, hyde_mode=None, hyde_brightness=None):
    if hyde_mode is None:
        hyde_mode = load_hyde_mode()
    if hyde_brightness is None:
        hyde_brightness = load_hyde_brightness()
    RGB_JSON.parent.mkdir(parents=True, exist_ok=True)
    RGB_JSON.write_text(json.dumps(
        {"active": active, "hyde_mode": hyde_mode, "hyde_brightness": hyde_brightness,
         "profiles": profiles}, indent=2))


