# ---------------------------------------------------------------------- display

def monitors():
    code, out, _ = run(["hyprctl", "-j", "monitors"], timeout=5)
    if code != 0:
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def internal_monitor():
    return next((m for m in monitors() if str(m.get("name", "")).startswith("eDP")), None)


def refresh_options(monitor):
    """Maps a rounded refresh rate to a Hyprland mode string at the current resolution."""
    found = {}
    for mode in monitor.get("availableModes", []):
        match = re.fullmatch(r"(\d+)x(\d+)@(\d+(?:\.\d+)?)Hz", str(mode))
        if not match:
            continue
        width, height, rate = int(match[1]), int(match[2]), float(match[3])
        if width == monitor.get("width") and height == monitor.get("height"):
            found.setdefault(round(rate), f"{width}x{height}@{match[3]}")
    return dict(sorted(found.items()))


def display_info():
    mon = internal_monitor()
    if not mon:
        return None
    return {"name": mon["name"], "options": refresh_options(mon),
            "active": round(float(mon.get("refreshRate", 0)))}


def set_refresh(rate):
    mon = internal_monitor()
    if not mon:
        raise ActionError("Built-in screen not found in Hyprland.")
    mode = refresh_options(mon).get(int(rate))
    name = str(mon["name"])
    if not mode or not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise ActionError(f"{rate} Hz is not available.")
    position = f"{int(mon.get('x', 0))}x{int(mon.get('y', 0))}"
    scale = f"{float(mon.get('scale', 1)):g}"
    turn = int(mon.get("transform", 0))
    lua = (f'hl.monitor({{ output = "{name}", mode = "{mode}", position = "{position}", '
           f"scale = {scale}, transform = {turn} }})")
    legacy = f"{name},{mode},{position},{scale},transform,{turn}"
    errors = []
    for cmd in (["hyprctl", "eval", lua], ["hyprctl", "keyword", "monitor", legacy]):
        code, out, err = run(cmd)
        errors.append(err or out)
        for _ in range(10):
            now = internal_monitor()
            if now and abs(float(now.get("refreshRate", 0)) - float(rate)) < 1.5:
                return f"Refresh rate: {rate} Hz (until Hyprland reloads)"
            if code != 0 or "can't" in out or "error" in out.lower():
                break
            time.sleep(0.2)
    raise ActionError("Hyprland did not change the refresh rate. " + " | ".join(filter(None, errors)))


