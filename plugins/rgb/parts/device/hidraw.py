def _hidraw_has_0xcc(sys_dev):
    try:
        return b"\x85\xcc" in (sys_dev / "device/report_descriptor").read_bytes()
    except OSError:
        return False


def find_hidraw():
    pids, catchall = rule_config()
    allowed = set(pids)
    for node in sorted((SYS / "class/hidraw").glob("hidraw*")):
        uevent = _read(node / "device/uevent") or ""
        m = re.search(r"HID_ID=([0-9A-Fa-f]+):([0-9A-Fa-f]+):([0-9A-Fa-f]+)", uevent)
        if not m:
            continue
        vid, pid = int(m.group(2), 16), int(m.group(3), 16)
        if vid == ITE_VENDOR and _hidraw_has_0xcc(node) and (pid in allowed or catchall):
            return Path("/dev") / node.name, pid
    return None, None


