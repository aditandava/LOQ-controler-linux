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


