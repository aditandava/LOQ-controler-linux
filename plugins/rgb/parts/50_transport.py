def _send_hidraw(path, pkt):
    fd = os.open(str(path), os.O_RDWR)
    try:
        fcntl.ioctl(fd, HIDIOCSFEATURE_33, bytearray(pkt))
    finally:
        os.close(fd)


def _send_pyusb(dev, pkt):
    reattach = False
    claimed = False
    try:
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
                reattach = True
        except (usb.core.USBError, NotImplementedError):
            pass
        usb.util.claim_interface(dev, 0)
        claimed = True
        dev.ctrl_transfer(0x21, 0x09, 0x03CC, 0x0000, pkt, timeout=1000)
    finally:
        if claimed:
            try:
                usb.util.release_interface(dev, 0)
            except Exception:
                pass
        if reattach:
            try:
                dev.attach_kernel_driver(0)
            except Exception:
                pass
        usb.util.dispose_resources(dev)


def send_rgb(profile, err_cls=RGBError):
    pkt = build_packet(profile)
    hid_path, _ = find_hidraw()
    if hid_path is not None:
        try:
            _send_hidraw(hid_path, pkt)
            return f"RGB applied ({profile.get('effect', 'Static')})."
        except PermissionError:
            pass
        except OSError as err:
            if not HAS_USB:
                raise err_cls(f"HID write failed: {err}")

    if not HAS_USB:
        raise err_cls("Permissions missing on hidraw and PyUSB is not installed.")
    dev = find_device()
    if dev is None:
        raise err_cls("No ITE RGB keyboard found. Check udev rules and USB connection.")
    try:
        _send_pyusb(dev, pkt)
    except Exception as exc:
        raise err_cls(f"USB error: {exc} (re-run loq_rgb.sh if permission denied)")
    return f"RGB applied ({profile.get('effect', 'Static')})."


