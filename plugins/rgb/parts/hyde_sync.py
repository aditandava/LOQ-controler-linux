def _theme_shades():
    """Keyboard colours from theme.css: [main] or [main, alt] for each of the four zones.

    theme.css is written by HyDE in the same run that calls --hyde-sync, so it is never stale.
    """
    text = _read(THEME_FILE)
    if not text:
        return None
    found = {(int(zone), bool(alt)): colour.upper() for zone, alt, colour in re.findall(
        r"@define-color\s+loq_rgb([1-4])(_alt)?\s+(#[0-9A-Fa-f]{6})", text)}
    if not all((zone, False) in found for zone in (1, 2, 3, 4)):
        return None
    return [[found[key] for key in ((zone, False), (zone, True)) if key in found]
            for zone in (1, 2, 3, 4)]


def _cache_shades():
    """The same from HyDE's own wallbash files, for a theme.css without keyboard colours."""
    cache = Path(os.environ.get("HYDE_CACHE_HOME") or os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    if cache.name != "hyde":
        cache = cache / "hyde"
    cfg = Path(os.environ.get("HYDE_CONFIG_HOME") or CONFIG_DIR / "hyde")

    for cand in [cache / "wallbash" / "shell-colors", cache / "wall.dcol",
                 cfg / "wallbash" / "Wall.dcol", cfg / "wallbash" / "theme.dcol"]:
        text = _read(cand)
        if not text:
            continue
        found = {}
        for m in re.finditer(r"(?:wallbash|dcol)_([1-4])xa([1-9])\s*=\s*['\"]?#?([0-9A-Fa-f]{6})['\"]?", text):
            found[(int(m.group(1)), int(m.group(2)))] = f"#{m.group(3).upper()}"
        zones = []
        for group in (1, 2, 3, 4):
            # Shades 3 and 7 are the deep and the bright one (HyDE's light mode swaps them).
            shades = [found[(group, s)] for s in (3, 7) if (group, s) in found]
            if not shades:
                shades = [found[(group, s)] for s in (8, 6, 5, 4) if (group, s) in found][:1]
            if shades:
                zones.append(shades)
        if len(zones) == 4:
            return zones
    return None


def hyde_shades():
    """The HyDE shades available for each of the four zones, or None."""
    zones = _theme_shades() or _cache_shades()
    if zones:
        return zones
    text = _read(THEME_FILE)
    if text:
        hits = re.findall(r"@define-color\s+loq_accent\S*\s+(#[0-9A-Fa-f]{6})", text)
        if hits:
            return [[c.upper()] for c in (hits * 4)[:4]]
    return None


def hyde_colors(tone="light"):
    """The four keyboard colours in the "light" or "dark" tone, or None."""
    zones = hyde_shades()
    if not zones:
        return None
    return [pick_tone(shades, tone) for shades in zones]


def hyde_profile():
    """What the keyboard shows while HyDE sync is on. Saved profiles play no part."""
    colors = hyde_colors(load_hyde_mode())
    if not colors:
        return None
    return {"colors": colors, "effect": "Static",
            "brightness": load_hyde_brightness(), "speed": 1}


def hyde_sync_headless():
    """Called by HyDE after every theme / wallpaper / mode change (see assets/loq-center.dcol)."""
    if not load_hyde_auto():
        return "HyDE auto-sync is off."
    profile = hyde_profile()
    if not profile:
        return "HyDE theme colours not found."
    return send_rgb(profile)
