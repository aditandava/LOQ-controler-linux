def set_charge(mode):
    if mode not in CHARGE_MODES:
        raise Fail("Unknown charge mode.")
    for bat in sorted((SYS / "class/power_supply").glob("BAT*")):
        node = bat / "charge_types"
        if not node.exists():
            continue
        try:
            listed = read(node).replace("[", "").replace("]", "").split()
        except OSError:
            listed = ["Standard", "Long_Life", "Fast"]  # unreadable: both modes are on
        if mode not in listed:
            raise Fail(f"{mode} is not supported by this battery.")
        write(node, mode)
        if f"[{mode}]" not in read(node):
            raise Fail("The firmware did not accept the charge mode.")
        return
    node = ideapad("conservation_mode")
    if node is None or mode == "Fast":
        raise Fail(f"{mode} is not supported on this machine.")
    value = "1" if mode == "Long_Life" else "0"
    write(node, value)
    if read(node) != value:
        raise Fail("The firmware did not accept the charge mode.")


