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


