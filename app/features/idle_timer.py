# ----------------------------------------------------------- hypridle sleep timer

def hypridle_running():
    code, _, _ = run(["pgrep", "-x", "hypridle"], timeout=3)
    return code == 0


def ensure_hypridle_conf():
    if HYPRIDLE_CONF.exists():
        return HYPRIDLE_CONF.read_text(errors="replace")
    HYPRIDLE_CONF.parent.mkdir(parents=True, exist_ok=True)
    if HYPRIDLE_SHARE.exists():
        text = HYPRIDLE_SHARE.read_text(errors="replace")
    else:
        text = DEFAULT_HYPRIDLE_TEMPLATE
    HYPRIDLE_CONF.write_text(text)
    return text


def classify_listener(block):
    low = block.lower()
    if "suspend" in low:
        return "suspend"
    if "dpms" in low:
        return "dpms"
    if "lock" in low:
        return "lock"
    if "brightnessctl" in low:
        return "dim"
    return "other"


def idle_info():
    """Detects current sleep timeout in minutes (5, 10, 30, or 0 for Never)."""
    if not have("hypridle"):
        return None
    if not hypridle_running():
        return {"active": 0, "note": "Idle timer is off (hypridle stopped). Screen will not lock or sleep automatically."}
    conf_path = HYPRIDLE_CONF if HYPRIDLE_CONF.exists() else HYPRIDLE_SHARE
    text = read(conf_path) or ""
    listeners = re.findall(r"listener\s*\{[^}]*\}", text, re.S)
    suspend_sec = None
    max_sec = 0
    for block in listeners:
        m = re.search(r"timeout\s*=\s*(\d+)", block)
        if not m:
            continue
        sec = int(m.group(1))
        max_sec = max(max_sec, sec)
        if classify_listener(block) == "suspend":
            suspend_sec = sec
    target_sec = suspend_sec if suspend_sec is not None else max_sec
    mins = round(target_sec / 60) if target_sec else 0
    active = mins if mins in (5, 10, 30) else None
    detail = f"Sleep after {mins} min of inactivity." if mins else "Custom hypridle timer active."
    return {"active": active, "note": f"{detail} Stages: dim → lock (hyprlock) → screen off → sleep."}


def restart_hypridle():
    code, _, _ = run(["systemctl", "--user", "list-unit-files", "hypridle.service"], timeout=4)
    if code == 0:
        r_code, _, _ = run(["systemctl", "--user", "restart", "hypridle.service"], timeout=5)
        if r_code == 0 and hypridle_running():
            return
    run(["pkill", "-x", "hypridle"], timeout=3)
    time.sleep(0.15)
    subprocess.Popen(["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def stop_hypridle():
    run(["systemctl", "--user", "stop", "hypridle.service"], timeout=4)
    run(["pkill", "-x", "hypridle"], timeout=3)


def set_idle(minutes):
    if not have("hypridle"):
        raise ActionError("hypridle is not installed.")
    minutes = int(minutes)
    if minutes not in IDLE_PRESETS:
        raise ActionError("Unsupported sleep timer value.")
    if minutes == 0:
        stop_hypridle()
        return "Sleep timer: Never (hypridle stopped)"

    _, dim_s, lock_s, dpms_s, susp_s = IDLE_PRESETS[minutes]
    stage_map = {"dim": dim_s, "lock": lock_s, "dpms": dpms_s, "suspend": susp_s}
    fallback_order = [dim_s, lock_s, dpms_s, susp_s]

    text = ensure_hypridle_conf()
    idx = 0

    def repl(match):
        nonlocal idx
        block = match.group(0)
        kind = classify_listener(block)
        new_timeout = stage_map.get(kind, fallback_order[min(idx, len(fallback_order) - 1)])
        idx += 1
        return re.sub(r"(timeout\s*=\s*)\d+", rf"\g<1>{new_timeout}", block, count=1)

    updated, count = re.subn(r"listener\s*\{[^}]*\}", repl, text, flags=re.S)
    if count == 0:
        updated = DEFAULT_HYPRIDLE_TEMPLATE
        updated = re.sub(r"listener\s*\{[^}]*\}", repl, updated, flags=re.S)
    elif "suspend" not in updated.lower():
        updated = updated.rstrip() + f"\n\nlistener {{\n    timeout = {susp_s}\n    on-timeout = systemctl suspend\n}}\n"

    try:
        HYPRIDLE_CONF.write_text(updated)
    except OSError as err:
        raise ActionError(f"Could not write {HYPRIDLE_CONF}: {err}")

    restart_hypridle()
    return f"Sleep timer set to {minutes} min (dim {dim_s // 60}m, lock {lock_s // 60}m, sleep {minutes}m)"


