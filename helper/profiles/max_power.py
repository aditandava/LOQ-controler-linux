def _apply_max_power():
    if on_battery():
        raise Fail("Plug in the charger before using Max power.")
    nodes = platform_profile_nodes()
    choices = (safe_read(nodes[0][1]) or "").split() if nodes else []
    if "max-power" in choices:  # the firmware's own Extreme mode (purple)
        _restore_cooling()
        _write_profile("max-power")
        print("Max power [max-power/purple]: firmware Extreme mode is on.")
        return

    custom = _require_custom("Max power")
    _restore_cooling()
    state = _collect_cooling_state()
    if not _enter_custom(custom, state):
        raise Fail("The firmware refused Custom (purple) mode. Performance mode was not selected.")
    state.update(mode="max-power", applied_profile="custom")
    _save_state(state)
    limits = set_power_limits("max_value")
    time.sleep(0.5)
    safe_write(SYS / "devices/system/cpu/intel_pstate/no_turbo", "0")
    safe_write(SYS / "devices/system/cpu/cpufreq/boost", "1")
    safe_write(SYS / "devices/system/cpu/intel_pstate/max_perf_pct", "100")
    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        if "performance" in (safe_read(pol / "scaling_available_governors") or "").split():
            safe_write(pol / "scaling_governor", "performance")
        safe_write(pol / "energy_performance_preference", "performance")
    detail = (f"{limits} firmware power limits at maximum" if limits else
              "NO firmware power limits available, so Custom mode keeps its stored wattage")
    print(f"Max power [custom/purple]: {detail}; CPU unrestricted.")


