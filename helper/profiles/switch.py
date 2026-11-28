def set_profile(name):
    if name == "ultra-saver":
        _apply_ultra_saver()
    elif name == "cooling":
        _apply_cooling()
    elif name == "max-power":
        _apply_max_power()
    else:
        _restore_cooling()
        _write_profile(name)


def set_toggle(name, value):
    if name not in TOGGLES or value not in ("0", "1"):
        raise Fail("Unknown switch or value.")
    node = ideapad(name)
    if node is None:
        raise Fail("This machine does not have that switch.")
    write(node, value)
    if read(node) != value:
        raise Fail("The firmware did not accept the change.")


