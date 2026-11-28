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


