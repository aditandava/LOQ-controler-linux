def ideapad(name):
    for dev in sorted((SYS / "bus/platform/drivers/ideapad_acpi").glob("VPC2004:*")):
        if (dev / name).exists():
            return dev / name
    return None


def platform_profile_nodes():
    """The Lenovo class device if present, else the legacy ACPI file, else any class device."""
    found = []
    for d in (SYS / "class/platform-profile").glob("platform-profile-*"):
        p, c = d / "profile", d / "choices"
        if p.exists() and c.exists():
            name = (safe_read(d / "name") or "").lower()
            other = not any(k in name for k in ("lenovo", "ideapad", "legion"))
            found.append((other, "custom" not in (safe_read(c) or "").split(), d.name, p, c))
    found.sort()
    if found and not found[0][0]:
        return [(found[0][3], found[0][4])]
    legacy_p = SYS / "firmware/acpi/platform_profile"
    legacy_c = SYS / "firmware/acpi/platform_profile_choices"
    if legacy_p.exists() and legacy_c.exists():
        return [(legacy_p, legacy_c)]
    return [(f[3], f[4]) for f in found]


def custom_profile_node():
    """The class device that accepts "custom". The legacy ACPI file rejects it since kernel 6.14."""
    dirs = sorted((SYS / "class/platform-profile").glob("platform-profile-*"),
                  key=lambda p: (not any(k in (safe_read(p / "name") or "").lower()
                                         for k in ("lenovo", "ideapad", "legion")), p.name))
    for d in dirs:
        if "custom" in (safe_read(d / "choices") or "").split():
            return d / "profile"
    return None


def wmi_fan_targets():
    """Fan RPM targets of the mainline lenovo_wmi_other driver. Writing 0 means automatic."""
    out = []
    for hw in lenovo_hwmon_dirs():
        if safe_read(hw / "name") == "lenovo_wmi_other":
            out.extend(sorted(hw.glob("fan*_target")))
    return out


def nvidia_smi(*args):
    exe = shutil.which("nvidia-smi", path=CLEAN_ENV["PATH"])
    if not exe:
        return None
    return subprocess.run([exe, *args], capture_output=True, text=True,
                          errors="replace", env=CLEAN_ENV, check=False)


def legion_fan_nodes():
    nodes = []
    for base in (SYS / "module/legion_laptop/drivers", SYS / "devices/platform"):
        if base.exists():
            nodes.extend(sorted(base.glob("**/fan_fullspeed")))
    seen, out = set(), []
    for n in nodes:
        r = str(n)
        if r not in seen and n.exists():
            seen.add(r)
            out.append(n)
    return out


def lenovo_hwmon_dirs():
    out = []
    for hw in sorted((SYS / "class/hwmon").glob("hwmon*")):
        name = (safe_read(hw / "name") or "").lower()
        if any(k in name for k in ("legion", "lenovo", "ideapad")):
            out.append(hw)
    return out


