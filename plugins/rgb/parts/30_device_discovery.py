def rule_config():
    pids, catchall = [], False
    if ITE_RULES.exists():
        for raw in (_read(ITE_RULES) or "").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or "048d" not in line.lower():
                continue
            m = re.search(r'ATTRS?\{idProduct\}=="([0-9A-Fa-f]{4})"', line)
            if m:
                pid = int(m.group(1), 16)
                if pid not in pids:
                    pids.append(pid)
            elif re.search(r'ATTRS?\{idVendor\}=="048d"', line, re.I):
                catchall = True
    for pid in ITE_PIDS:
        if pid not in pids:
            pids.append(pid)
    return pids, catchall


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


def _usb_has_0xcc_hid(pid):
    for node in (SYS / "bus/hid/devices").glob(f"*:048D:{pid:04X}.*"):
        try:
            if b"\x85\xcc" in (node / "report_descriptor").read_bytes():
                return True
        except OSError:
            pass
    return False


def find_device():
    if not HAS_USB:
        return None
    pids, catchall = rule_config()
    for pid in pids:
        dev = usb.core.find(idVendor=ITE_VENDOR, idProduct=pid)
        if dev is not None:
            return dev
    if catchall:
        candidates = list(usb.core.find(find_all=True, idVendor=ITE_VENDOR) or [])
        for dev in candidates:
            if _usb_has_0xcc_hid(dev.idProduct):
                return dev
        for dev in candidates:
            if dev.bNumConfigurations and dev[0].bNumInterfaces >= 2:
                return dev
    return None


