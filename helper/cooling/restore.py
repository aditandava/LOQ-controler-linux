def _restore_cooling():
    if not COOLING_STATE.exists():
        return
    try:
        state = json.loads(COOLING_STATE.read_text())
    except (OSError, ValueError):
        COOLING_STATE.unlink(missing_ok=True)
        return

    # Fan and power settings of Custom mode can only be put back while in Custom mode
    custom = custom_profile_node()
    if state.get("wmi_from_custom") and custom is not None and safe_write(custom, "custom"):
        time.sleep(0.5)

    if "acpi_fan" in state:
        method = other_method()
        if method and not full_speed_set(method, state["acpi_fan"]):
            print("Warning: could not confirm that fan full speed was switched off.", file=sys.stderr)

    for path_str, val in state.get("files", {}).items():
        safe_write(path_str, val)

    saved_targets = state.get("fan_targets", {})
    for target in wmi_fan_targets():
        safe_write(target, saved_targets.get(str(target), "0"))

    if state.get("nvidia_locked"):
        nvidia_smi("-rgc")

    for pol_str, vals in state.get("policies", {}).items():
        pol = Path(pol_str)
        for k in ("scaling_governor", "energy_performance_preference", "scaling_max_freq"):
            if k in vals:
                safe_write(pol / k, vals[k])

    for cap_str, vals in state.get("rapl", {}).items():
        cap = Path(cap_str)
        if vals.get("c0") is not None:
            if not safe_write(cap / "constraint_0_power_limit_uw", vals["c0"]):
                mx = safe_read(cap / "constraint_0_max_power_uw")
                if mx and mx != "0":
                    safe_write(cap / "constraint_0_power_limit_uw", mx)
        if vals.get("c1") is not None:
            safe_write(cap / "constraint_1_power_limit_uw", vals["c1"])

    for path_str, val in state.get("wmi_other", {}).items():
        safe_write(path_str, val)

    COOLING_STATE.unlink(missing_ok=True)


