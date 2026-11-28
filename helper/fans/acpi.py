OTHER_GUID = "DC2A8805-3A8C-41BA-A6F7-092E0089CD3B"


ACPI_CALL = Path("/proc/acpi/call")


ACPI_LOCK = Path("/run/loq-center-acpi.lock")


FULL_SPEED_ID = "0x04020000"  # Lenovo "Other Method" feature: fan full speed


FAN_RPM_IDS = ("0x04030001", "0x04030002")  # current RPM of fan 1 and fan 2


def wmi_method(guid):
    """ACPI path of a Lenovo WMI method block, such as \\_SB_.GZFD.WMAE, or None."""
    if safe_read(SYS / "class/dmi/id/sys_vendor") != "LENOVO":
        return None
    for dev in sorted((SYS / "bus/wmi/devices").glob(guid + "*")):
        object_id = safe_read(dev / "object_id") or ""
        if not re.fullmatch(r"[A-Z0-9]{2}", object_id):
            continue
        for parent in dev.resolve().parents:
            path = safe_read(parent / "firmware_node/path")
            if path and re.fullmatch(r"\\[A-Z0-9_.]+", path):
                return f"{path}.WM{object_id}"
    return None


def other_method():
    return wmi_method(OTHER_GUID)


def acpi_call(command):
    if not ACPI_CALL.exists():
        subprocess.run(["/usr/bin/modprobe", "acpi_call"], capture_output=True,
                       env=CLEAN_ENV, check=False)
    if not ACPI_CALL.exists():
        return None
    # /proc/acpi/call holds one reply for everybody: keep each write and read together
    with open(ACPI_LOCK, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not safe_write(ACPI_CALL, command):
            return None
        reply = safe_read(ACPI_CALL)
    return reply.strip("\x00\n ") if reply else None


