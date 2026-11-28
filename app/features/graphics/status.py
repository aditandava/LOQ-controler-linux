# --------------------------------------------------------------------- graphics

def nvidia_state():
    """Reads sysfs only, so it never wakes a sleeping GPU."""
    for dev in (SYS / "bus/pci/devices").glob("*"):
        if read(dev / "vendor") == "0x10de" and (read(dev / "class") or "").startswith("0x03"):
            return read(dev / "power/runtime_status") or "unknown"
    return "off"


def panel_on_nvidia():
    drm = SYS / "class/drm"
    for connector in drm.glob("card*-eDP-*"):
        if read(connector / "status") == "connected":
            if read(drm / connector.name.split("-")[0] / "device/vendor") == "0x10de":
                return True
    return False


def gpu_mode():
    if not have("envycontrol"):
        return None
    code, out, _ = run(["envycontrol", "--query"])
    return out if code == 0 and out in ("integrated", "hybrid", "nvidia") else "unknown"


def gpu_stats():
    """Asks nvidia-smi. This wakes the GPU, so it only runs when the user asks."""
    fields = "temperature.gpu,power.draw,utilization.gpu,memory.used,memory.total"
    code, out, err = run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"])
    if code != 0 or not out:
        raise ActionError(err or out or "nvidia-smi failed.")
    values = [v.strip() for v in out.splitlines()[0].split(",")]
    if len(values) != 5:
        raise ActionError("Unexpected nvidia-smi output.")
    temp, watts, use, used, total = values
    return f"{temp} °C   {watts} W   {use}% load   {used} / {total} MiB"


