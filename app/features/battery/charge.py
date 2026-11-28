def ideapad_dir():
    found = sorted((SYS / "bus/platform/drivers/ideapad_acpi").glob("VPC2004:*"))
    return found[0] if found else None


def charge_info():
    """Returns {"options": [...], "active": name or None, "note": str} or None."""
    for bat in batteries():
        node = bat / "charge_types"
        if not node.exists():
            continue
        text = read(node)
        if text is None:
            return {"options": ["Long_Life", "Standard", "Fast"], "active": None,
                    "note": "The firmware reports conflicting charge modes (seen after hibernate). "
                            "Choose a mode to repair it."}
        active = re.search(r"\[([^\]]+)\]", text)
        options = [o for o in text.replace("[", "").replace("]", "").split() if o in CHARGE_LABELS]
        if options:
            return {"options": options, "active": active.group(1) if active else None, "note": ""}
    dev = ideapad_dir()
    if dev and (dev / "conservation_mode").exists():
        value = read(dev / "conservation_mode")
        active = {"1": "Long_Life", "0": "Standard"}.get(value)
        return {"options": ["Long_Life", "Standard"], "active": active, "note": ""}
    return None


def charge_note(charge, battery, ac):
    """Explains the selected mode and what the battery is really doing."""
    if charge["note"]:
        return charge["note"]
    active = charge["active"]
    if active is None:
        return "The current charging mode could not be read."
    level = battery["capacity"] if battery else None
    if active == "Long_Life":
        text = "Battery care: stops at a Lenovo firmware limit (about 80% on many LOQ models)."
    else:
        text = ("Rapid charge: goes to 100%, faster mainly at lower levels." if active == "Fast"
                else "Full charge: goes to 100%.")
        if ac is False:
            text += " Plug in the charger."
        elif level is not None and level < 95 and battery["status"] != "Charging":
            text += " Not charging: unplug the charger for 10 seconds, then plug it in again."
    if level is not None:
        text += f"\nNow: {level}% · {battery['status']}"
    return text


def set_charge(mode):
    helper("set", "charge", mode)
    return f"Charging mode: {CHARGE_LABELS.get(mode, mode)}"


