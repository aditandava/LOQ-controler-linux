def panel_on_nvidia():
    drm = SYS / "class/drm"
    for connector in drm.glob("card*-eDP-*"):
        try:
            if read(connector / "status") != "connected":
                continue
            if read(drm / connector.name.split("-")[0] / "device/vendor") == "0x10de":
                return True
        except OSError:
            continue
    return False


def envy(*args):
    return subprocess.run([ENVYCONTROL, *args], capture_output=True, text=True,
                          errors="replace", env=CLEAN_ENV, check=False)


def panel_mode():
    """Which GPU drives the built-in screen right now: "hybrid", "dgpu" or None."""
    drm = SYS / "class/drm"
    vendors = set()
    for connector in drm.glob("card*-eDP-*"):
        if safe_read(connector / "status") == "connected":
            vendors.add(safe_read(drm / connector.name.split("-")[0] / "device/vendor"))
    return {("0x10de",): "dgpu", ("0x8086",): "hybrid"}.get(tuple(vendors))


def mux_read(method, method_id):
    reply = acpi_call(f"{method} 0x0 0x{method_id:02x} b00000000")
    return int(reply, 16) if reply in ("0x0", "0x1") else None


def mux_firmware():
    """(method path, "hybrid" or "dgpu") when the firmware reports a switchable MUX."""
    method = wmi_method(GAMEZONE_GUID)
    if method is None or mux_read(method, MUX_SUPPORTED) != 1:
        return None, None
    value = mux_read(method, MUX_GET)
    return method, next((name for name, number in MUX_MODES.items() if number == value), None)


def dgpu_blocker():
    """Why dGPU only could leave a black screen right now, or None."""
    if on_battery():
        return "Plug in the charger first."
    if safe_read(SYS / "module/nvidia_drm/parameters/modeset") != "Y":
        return ("The NVIDIA display driver is not ready (nvidia_drm modeset is not on). "
                "The screen could stay black.")
    words = (safe_read(CMDLINE) or "").split()
    if "nomodeset" in words:
        return "The kernel option nomodeset is set. Remove it and reboot first."
    if Path(ENVYCONTROL).exists() and envy("--query").stdout.strip() == "integrated":
        return "NVIDIA is set to Integrated (off). Switch to Hybrid, reboot, then try again."
    return None


def mux_report():
    """Read-only check for the terminal. Changes nothing."""
    method, firmware = mux_firmware()
    print(json.dumps({"supported": method is not None, "firmware": firmware,
                      "screen": panel_mode(), "pending": safe_read(MUX_PENDING),
                      "dgpu_check": dgpu_blocker() or "ok"}))


def set_mux(mode):
    if mode not in MUX_MODES:
        raise Fail("Unknown display mode.")
    method, firmware = mux_firmware()
    if method is None:
        raise Fail("The firmware did not report a switchable display (check that acpi_call "
                   f"is loaded). Nothing was changed. {BIOS_HINT}")
    screen = panel_mode()
    if firmware is None or screen is None:
        raise Fail(f"Could not read the current display mode. Nothing was changed. {BIOS_HINT}")
    pending = safe_read(MUX_PENDING)
    if pending is None and firmware != screen:
        # Either a change is waiting for a reboot, or this model answers differently
        raise Fail(f"The firmware says {MUX_LABELS[firmware]} but the screen is on "
                   f"{MUX_LABELS[screen]}. Nothing was changed. Reboot first. {BIOS_HINT}")
    if mode == "dgpu":
        blocker = dgpu_blocker()
        if blocker:
            raise Fail(f"{blocker} Nothing was changed.")
    if pending is None and mode == screen:
        print(f"Already in {MUX_LABELS[mode]}.")
        return
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGPIPE):
        signal.signal(sig, signal.SIG_IGN)
    # Remember the request first, so a half finished switch still blocks Integrated
    MUX_PENDING.write_text(mode + "\n")
    MUX_PENDING.chmod(0o644)
    reply = acpi_call(f"{method} 0x0 0x{MUX_SET:02x} b{MUX_MODES[mode]:02x}000000")
    after = mux_read(method, MUX_GET)
    if reply is not None and reply.startswith("Error"):
        if pending:
            MUX_PENDING.write_text(pending + "\n")
        elif after == MUX_MODES[screen]:
            MUX_PENDING.unlink(missing_ok=True)
        raise Fail(f"The firmware refused the switch. {BIOS_HINT}")
    if mode == screen and after == MUX_MODES[mode]:
        MUX_PENDING.unlink(missing_ok=True)
        print(f"Change cancelled. The screen stays on {MUX_LABELS[mode]}.")
        return
    proof = ("The firmware confirms it." if after == MUX_MODES[mode]
             else "The firmware has not confirmed it yet; check again after reboot.")
    print(f"{MUX_LABELS[mode]} requested. {proof} Reboot to apply.")


def set_gpu(mode):
    if mode not in GPU_MODES:
        raise Fail("Unknown GPU mode.")
    if not Path(ENVYCONTROL).exists():
        raise Fail("envycontrol is not installed.")
    if mode == "integrated" and panel_on_nvidia():
        raise Fail("Blocked: the built-in screen is wired to NVIDIA. Switch to Hybrid and reboot first.")
    if mode == "integrated" and (safe_read(MUX_PENDING) == "dgpu" or mux_firmware()[1] == "dgpu"):
        raise Fail("Blocked: dGPU only is selected for the next boot. Pick Hybrid and reboot first.")
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM, signal.SIGPIPE):
        signal.signal(sig, signal.SIG_IGN)
    done = envy("-s", mode, *GPU_MODES[mode])
    output = f"{done.stdout}\n{done.stderr}"
    errors = [line for line in output.splitlines() if "ERROR" in line]
    now = envy("--query").stdout.strip()
    if done.returncode != 0 or errors or now != mode:
        detail = "\n".join(errors or output.strip().splitlines()[-8:])
        raise Fail(f"GPU switch had a problem. Do not reboot until it is fixed.\n{detail}\n"
                   "To go back: sudo envycontrol -s hybrid")
    print(f"GPU mode set to {mode}. Reboot to apply.")


