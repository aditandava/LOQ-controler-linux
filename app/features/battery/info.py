# ---------------------------------------------------------------------- battery

def batteries():
    found = []
    for dev in sorted((SYS / "class/power_supply").glob("*")):
        if read(dev / "type") == "Battery" and dev.name.startswith("BAT"):
            found.append(dev)
    return found


def battery_info():
    bats = batteries()
    if not bats:
        return None
    bat = bats[0]
    watts = None
    power = read_int(bat / "power_now")
    if power is None:
        current, volts = read_int(bat / "current_now"), read_int(bat / "voltage_now")
        if current is not None and volts is not None:
            power = abs(current) * volts / 1_000_000
    if power is not None:
        watts = abs(power) / 1_000_000
    health = None
    for kind in ("energy", "charge"):
        full, design = read_int(bat / f"{kind}_full"), read_int(bat / f"{kind}_full_design")
        if full and design:
            health = min(100.0, full * 100 / design)
            break
    cycles = read_int(bat / "cycle_count")
    return {
        "capacity": read_int(bat / "capacity"),
        "status": read(bat / "status") or "Unknown",
        "watts": watts,
        "health": health,
        "cycles": cycles if cycles else None,
    }


def on_ac():
    for dev in (SYS / "class/power_supply").glob("*"):
        if read(dev / "type") == "Mains":
            return read(dev / "online") == "1"
    return None


