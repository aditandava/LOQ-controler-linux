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


def load_hyde_auto():
    """True when the keyboard colours follow HyDE on every theme or wallpaper change (default: on)."""
    try:
        return bool(json.loads(RGB_JSON.read_text()).get("hyde_auto", True))
    except (OSError, ValueError, TypeError, AttributeError):
        return True


def save_state(profiles, active=0, hyde_auto=None):
    if hyde_auto is None:
        hyde_auto = load_hyde_auto()
    RGB_JSON.parent.mkdir(parents=True, exist_ok=True)
    RGB_JSON.write_text(json.dumps(
        {"active": active, "hyde_auto": bool(hyde_auto), "profiles": profiles}, indent=2))


