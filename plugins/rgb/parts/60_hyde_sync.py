def hyde_colors():
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


