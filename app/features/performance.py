# ------------------------------------------------------------------ performance

def platform_profile_nodes():
    """(profile_path, choices_path). The Lenovo class device comes first, then the legacy ACPI file."""
    found = []
    for d in (SYS / "class/platform-profile").glob("platform-profile-*"):
        p, c = d / "profile", d / "choices"
        if p.exists() and c.exists():
            name = (read(d / "name") or "").lower()
            other = not any(k in name for k in ("lenovo", "ideapad", "legion"))
            found.append((other, "custom" not in (read(c) or "").split(), d.name, p, c))
    found.sort()
    if found and not found[0][0]:
        return found[0][3], found[0][4]
    legacy_p = SYS / "firmware/acpi/platform_profile"
    legacy_c = SYS / "firmware/acpi/platform_profile_choices"
    if legacy_p.exists() and legacy_c.exists():
        return legacy_p, legacy_c
    return (found[0][3], found[0][4]) if found else (None, None)


def cooling_available():
    node, _ = platform_profile_nodes()
    if node is not None or have("powerprofilesctl"):
        return True
    if any((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        return True
    if any((SYS / "class/powercap").glob("intel-rapl*")):
        return True
    dev = ideapad_dir()
    return bool(dev and (dev / "fan_mode").exists())


def override_state(sys_profile=None):
    """The helper's record of an active Cooling (or substitute Max power) mode, else None."""
    try:
        data = json.loads(read(COOLING_STATE) or "")
    except ValueError:
        return None
    applied = data.get("applied_profile")
    if sys_profile is not None and applied is not None and sys_profile != applied:
        return None
    return data


def mode_row(choices):
    """Always the same order: Quiet, Balanced, Performance, Max power, Cooling, Ultra saver."""
    quiet = next((c for c in ("low-power", "quiet") if c in choices), None)
    row = [quiet] if quiet else []
    row += [c for c in ("balanced", "performance") if c in choices]
    if "max-power" in choices or "performance" in choices:
        row.append("max-power")
    return row + ["cooling", "ultra-saver"]


def usable_profiles(options, source):
    """The modes worth offering for "ac" or "battery"."""
    return [p for p in options if source != "battery" or p not in CHARGER_ONLY]


def _profile_result(choices, current):
    state = override_state(current)
    row = mode_row(choices)
    active = state.get("mode", "cooling") if state else current
    if active in ("low-power", "quiet"):
        active = row[0]
    return {"options": row, "active": active,
            "fans_direct": bool(state and state.get("fans_direct"))}


def profile_info():
    node, choices_node = platform_profile_nodes()
    if node is not None:
        current = read(node)
        choices = (read(choices_node) or "").split()
        if current and choices:
            return _profile_result(choices, current)
    if have("powerprofilesctl"):
        code, out, _ = run(["powerprofilesctl", "list"], timeout=5)
        choices = [k for k, v in PPD_NAMES.items() if re.search(rf"^\*?\s*{v}:", out, re.M)]
        if code == 0 and choices:
            _, now, _ = run(["powerprofilesctl", "get"], timeout=5)
            active = next((k for k, v in PPD_NAMES.items() if v == now), None)
            info = _profile_result(choices, None)
            if not override_state():
                info["active"] = active
            return info
    if cooling_available():
        return _profile_result([], None)
    return None


def set_profile(name):
    if name in CHARGER_ONLY and on_ac() is False:
        raise ActionError(f"Plug in the charger to use {PROFILE_LABELS[name]}.")
    if name in ("cooling", "max-power", "ultra-saver"):
        out = helper("power", "profile", name)
        return out or f"Performance mode: {PROFILE_LABELS.get(name, name)}"
    if COOLING_STATE.exists():  # leaving Cooling or Max power restores the saved settings
        out = helper("set", "profile", name)
        return out or f"Performance mode: {PROFILE_LABELS.get(name, name)}"
    node, _ = platform_profile_nodes()
    if name in PPD_NAMES and have("powerprofilesctl"):
        code, _, err = run(["powerprofilesctl", "set", PPD_NAMES[name]])
        if code == 0 and (node is None or read(node) == name):
            return f"Performance mode: {PROFILE_LABELS.get(name, name)}"
        if node is None:
            raise ActionError(err or "power-profiles-daemon refused the change.")
    out = helper("set", "profile", name)
    return out or f"Performance mode: {PROFILE_LABELS.get(name, name)}"


