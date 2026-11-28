def _collect_cooling_state():
    state = {"files": {}, "policies": {}, "rapl": {}, "wmi_other": {}}

    for p in [SYS / "devices/system/cpu/intel_pstate/no_turbo",
              SYS / "devices/system/cpu/intel_pstate/max_perf_pct",
              SYS / "devices/system/cpu/cpufreq/boost"]:
        val = safe_read(p)
        if val is not None:
            state["files"][str(p)] = val

    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        entry = {}
        for k in ("scaling_governor", "energy_performance_preference", "scaling_max_freq"):
            v = safe_read(pol / k)
            if v is not None:
                entry[k] = v
        if entry:
            state["policies"][str(pol)] = entry

    for cap in sorted((SYS / "class/powercap").glob("intel-rapl*")):
        if cap.name.count(":") > 1:
            continue
        c0 = safe_read(cap / "constraint_0_power_limit_uw")
        c1 = safe_read(cap / "constraint_1_power_limit_uw")
        if c0 is not None or c1 is not None:
            state["rapl"][str(cap)] = {"c0": c0, "c1": c1}

    for p in sorted((SYS / "class/drm").glob("card*/gt_max_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt_boost_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt/gt*/rps_max_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/gt/gt*/rps_boost_freq_mhz")) + \
             sorted((SYS / "class/drm").glob("card*/device/power_dpm_force_performance_level")):
        v = safe_read(p)
        if v is not None:
            state["files"][str(p)] = v

    for n in legion_fan_nodes():
        v = safe_read(n)
        if v is not None:
            state["files"][str(n)] = v

    state["fan_targets"] = {str(p): safe_read(p) or "0" for p in wmi_fan_targets()}
    return state


