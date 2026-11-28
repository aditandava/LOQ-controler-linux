def panel_on_nvidia():
    drm = SYS / "class/drm"
    for connector in drm.glob("card*-eDP-*"):
        try:
            if read(connector / "status") != "connected":
                continue
            if read(drm / connector.name.split("-")[0] / "device/vendor") == "0x10de":
                return True
        except OSError:
            continue
    return False


def envy(*args):
    return subprocess.run([ENVYCONTROL, *args], capture_output=True, text=True,
                          errors="replace", env=CLEAN_ENV, check=False)


def panel_mode():
    """Which GPU drives the built-in screen right now: "hybrid", "dgpu" or None."""
    drm = SYS / "class/drm"
    vendors = set()
    for connector in drm.glob("card*-eDP-*"):
        if safe_read(connector / "status") == "connected":
            vendors.add(safe_read(drm / connector.name.split("-")[0] / "device/vendor"))
    return {("0x10de",): "dgpu", ("0x8086",): "hybrid"}.get(tuple(vendors))


