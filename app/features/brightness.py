# ------------------------------------------------------------------- brightness

def led_info(path):
    value, top = read_int(path / "brightness"), read_int(path / "max_brightness")
    if value is None or not top:
        return None
    return {"name": path.name, "value": value, "max": top}


def backlight_info():
    if not have("brightnessctl"):
        return None
    devices = sorted((SYS / "class/backlight").glob("*"),
                     key=lambda p: (not p.name.startswith("intel"), p.name))
    for dev in devices:
        info = led_info(dev)
        if info:
            return info
    return None


def keyboard_info():
    if not have("brightnessctl"):
        return None
    for dev in sorted((SYS / "class/leds").glob("*kbd_backlight*")):
        info = led_info(dev)
        if info and info["max"] <= 10:
            return info
    return None


def set_led(device, value):
    code, _, err = run(["brightnessctl", "-q", "-d", device, "set", str(value)])
    if code != 0:
        raise ActionError(err or "brightnessctl failed.")


def set_brightness(percent):
    info = backlight_info()
    if not info:
        raise ActionError("No screen backlight found.")
    percent = max(5, min(100, int(percent)))
    set_led(info["name"], f"{percent}%")
    return f"Brightness: {percent}%"


def set_keyboard(level):
    info = keyboard_info()
    if not info:
        raise ActionError("No keyboard backlight found.")
    set_led(info["name"], int(level))
    return f"Keyboard light: {level}"


