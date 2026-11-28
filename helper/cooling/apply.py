def _apply_cooling():
    custom = _require_custom("Cooling")
    state = None
    if COOLING_STATE.exists():
        try:
            state = json.loads(COOLING_STATE.read_text())
        except (OSError, ValueError):
            state = None
        if state is None or state.get("mode", "cooling") != "cooling":
            _restore_cooling()
            state = None
    if state is None:
        state = _collect_cooling_state()

    # 1. Custom mode first: fan and power settings only work there. Never Performance.
    if not _enter_custom(custom, state):
        raise Fail("The firmware refused Custom (purple) mode. Performance mode was not selected.")
    state.update(mode="cooling", fans_direct=False, applied_profile="custom")
    _save_state(state)  # saved early, so another mode can always undo a partial change

    # 2. Lowest firmware power limits for CPU and GPU
    limits = set_power_limits("min_value")

    # 3. Low CPU clocks and package power
    cpu_capped = _cap_cooling_cpu()
    _cap_cooling_rapl()

    # 4. Low GPU clocks
    _cap_cooling_gpu(state)

    # 5. Fans at full speed, last so that nothing above resets them
    fans = set_fans_full(state)
    state["fans_direct"] = bool(fans)
    _save_state(state)

    if safe_read(custom) != "custom":
        raise Fail("Another power service moved the laptop out of Custom mode. Click Cooling again.")
    fan_text = f"fans FULL ({fans})" if fans else "FANS NOT AT FULL SPEED (no working fan interface)"
    cpu = "CPU capped" if cpu_capped else "CPU cap refused"
    gpu = "GPU capped" if state.get("nvidia_locked") else "NVIDIA cap not confirmed"
    print(f"Cooling [custom/purple]: {fan_text}; {cpu}; {gpu}; {limits} firmware limits at minimum.")


