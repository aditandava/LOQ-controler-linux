def full_speed_get(method):
    """0 or 1, or None when the firmware does not give a clear answer."""
    reply = acpi_call(f"{method} 0x0 0x11 {FULL_SPEED_ID}")
    return int(reply, 16) if reply in ("0x0", "0x1") else None


def full_speed_set(method, value):
    # Argument buffer: feature id then value, both 32-bit little endian
    acpi_call(f"{method} 0x0 0x12 b00000204{int(value):02x}000000")
    return full_speed_get(method) == value


def fan_rpm(method):
    speeds = []
    for feature in FAN_RPM_IDS:
        try:
            value = int(acpi_call(f"{method} 0x0 0x11 {feature}") or "", 16)
        except ValueError:
            continue
        if 0 <= value <= 10000:
            speeds.append(value)
    return speeds


def watch_fans():
    """Prints the fan speeds every 2 seconds until the app closes its end of the pipe. Read only."""
    method = other_method()
    if not method or not fan_rpm(method):
        raise Fail("Fan speed is not available through acpi_call on this machine.")
    try:
        while True:
            print(json.dumps(fan_rpm(method)), flush=True)
            time.sleep(2)
    except BrokenPipeError:
        os._exit(0)


def set_fans_full(state):
    """Tries each full-speed interface and returns the name of the one that confirmed it."""
    for node in legion_fan_nodes():
        if safe_write(node, "1") and safe_read(node) == "1":
            return "legion_laptop"
    method = other_method()
    if method:
        before = full_speed_get(method)
        if before is not None:
            state.setdefault("acpi_fan", before)
            if full_speed_set(method, 1):
                return "acpi_call"
    done = False
    for target in wmi_fan_targets():
        top = safe_read(target.with_name(target.name.replace("_target", "_max")))
        if top and safe_write(target, top):
            done = True
    return "lenovo_wmi_other" if done else None


