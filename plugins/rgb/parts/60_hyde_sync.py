def _theme_rgb_colors():
    """The four keyboard colours HyDE wrote into theme.css on its last run (loq_rgb1..4)."""
    text = _read(THEME_FILE)
    if not text:
        return None
    found = dict(re.findall(r"@define-color\s+loq_rgb([1-4])\s+(#[0-9A-Fa-f]{6})", text))
    if len(found) == 4:
        return [found[str(i)].upper() for i in (1, 2, 3, 4)]
    return None


def hyde_colors():
    # theme.css is written by HyDE in the same run that calls --hyde-sync, so it is never stale.
    fresh = _theme_rgb_colors()
    if fresh:
        return fresh
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
        picked = []
        for group in (1, 2, 3, 4):
            for shade in (7, 8, 6, 5, 4):
                if (group, shade) in found:
                    picked.append(found[(group, shade)])
                    break
        if len(picked) == 4:
            return picked

    text = _read(THEME_FILE)
    if text:
        hits = re.findall(r"@define-color\s+loq_accent\S*\s+(#[0-9A-Fa-f]{6})", text)
        if hits:
            return [c.upper() for c in (hits * 4)[:4]]
    return None


def hyde_sync_headless():
    """Called by HyDE after every theme / wallpaper / mode change (see assets/loq-center.dcol)."""
    if not load_hyde_auto():
        return "HyDE auto-sync is off."
    colors = hyde_colors()
    if not colors:
        return "HyDE theme colours not found."
    profs, slot = load_state()
    profile = profs[slot]
    profile["colors"] = list(colors)
    save_state(profs, slot)
    if profile["effect"] == "Off":  # keep the light off if the user turned it off
        return "HyDE colours saved (keyboard light is off)."
    return send_rgb(profile)

