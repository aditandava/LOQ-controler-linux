def power_limits():
    """Custom-mode CPU and GPU wattage settings. Temperature and time limits are left alone."""
    found = []
    for attr in sorted((SYS / "class/firmware-attributes").glob("lenovo-wmi-other*/attributes/*")):
        name = attr.name
        if name.startswith(("ppt_", "gpu_nv_", "dgpu_")) and not name.endswith(("tau", "temp", "clk")):
            found.append(attr)
    return found


def set_power_limits(bound):
    """Writes each limit's firmware minimum or maximum. Returns how many were confirmed."""
    count = 0
    for attr in power_limits():
        value = safe_read(attr / bound)
        if value is not None and safe_write(attr / "current_value", value) \
                and safe_read(attr / "current_value") == value:
            count += 1
    return count


def nvidia_present():
    return any(safe_read(dev / "vendor") == "0x10de" and (safe_read(dev / "class") or "").startswith("0x03")
               for dev in (SYS / "bus/pci/devices").glob("*"))


