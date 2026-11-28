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


