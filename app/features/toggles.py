# ---------------------------------------------------------------- device toggles

def toggle_info():
    dev = ideapad_dir()
    found = {}
    if dev:
        for name in TOGGLE_LABELS:
            value = read(dev / name)
            if value in ("0", "1"):
                found[name] = value
    return found


def set_toggle(name, value):
    helper("set", "toggle", name, value)
    return f"{TOGGLE_LABELS[name]}: {'on' if value == '1' else 'off'}"


