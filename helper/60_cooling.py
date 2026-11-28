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


def _enter_custom(custom, state):
    """Switches to Custom (purple) and remembers its own power limits the first time."""
    if not safe_write(custom, "custom"):
        return False
    time.sleep(0.5)
    if safe_read(custom) != "custom":
        return False
    if not state.get("wmi_from_custom"):
        for attr in power_limits():
            value = safe_read(attr / "current_value")
            if value is not None:
                state["wmi_other"][str(attr / "current_value")] = value
        state["wmi_from_custom"] = True
    return True


def _save_state(state):
    COOLING_STATE.write_text(json.dumps(state))
    os.chmod(COOLING_STATE, 0o644)


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


def _require_custom(title):
    custom = custom_profile_node()
    if custom is None:
        raise Fail(f"{title} needs Custom (purple) mode, but this kernel does not offer it. "
                   "Nothing was changed. Check: cat /sys/class/platform-profile/*/choices")
    return custom


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

    # 3. Low CPU clocks
    time.sleep(0.5)  # let power daemons react to the mode change before capping the CPU
    cpu_capped = any([
        safe_write(SYS / "devices/system/cpu/intel_pstate/no_turbo", "1"),
        safe_write(SYS / "devices/system/cpu/cpufreq/boost", "0"),
        safe_write(SYS / "devices/system/cpu/intel_pstate/max_perf_pct", "55"),
    ])

    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        govs = (safe_read(pol / "scaling_available_governors") or "").split()
        for g in ("powersave", "conservative", "schedutil"):
            if g in govs and safe_write(pol / "scaling_governor", g):
                break
        epps = (safe_read(pol / "energy_performance_available_preferences") or "").split()
        for e in ("power", "balance_power"):
            if e in epps and safe_write(pol / "energy_performance_preference", e):
                break
        if safe_read(pol / "scaling_driver") != "intel_pstate":
            try:
                mn = int(safe_read(pol / "cpuinfo_min_freq") or 0)
                mx = int(safe_read(pol / "cpuinfo_max_freq") or 0)
                if mx > mn > 0:
                    safe_write(pol / "scaling_max_freq", str(max(mn, int(mx * 0.55))))
            except ValueError:
                pass

    for cap in sorted((SYS / "class/powercap").glob("intel-rapl*")):
        if cap.name.count(":") > 1:
            continue
        if (cap / "constraint_0_power_limit_uw").exists():
            try:
                mx0 = int(safe_read(cap / "constraint_0_max_power_uw") or 0)
                pl1 = 25_000_000 if mx0 <= 0 else max(15_000_000, min(25_000_000, mx0))
                safe_write(cap / "constraint_0_power_limit_uw", str(pl1))
            except ValueError:
                pass
        if (cap / "constraint_1_power_limit_uw").exists():
            try:
                mx1 = int(safe_read(cap / "constraint_1_max_power_uw") or 0)
                pl2 = 35_000_000 if mx1 <= 0 else max(20_000_000, min(35_000_000, mx1))
                safe_write(cap / "constraint_1_power_limit_uw", str(pl2))
            except ValueError:
                pass

    # 4. Low GPU clocks
    for card in sorted((SYS / "class/drm").glob("card*")):
        if "-" in card.name:
            continue
        rpn = safe_read(card / "gt_RPn_freq_mhz")
        rp1 = safe_read(card / "gt_RP1_freq_mhz")
        if rpn or rp1:
            try:
                low_mhz = max(int(rpn or 300), int(rp1 or 450))
                for fn in ("gt_max_freq_mhz", "gt_boost_freq_mhz"):
                    if (card / fn).exists():
                        safe_write(card / fn, str(low_mhz))
                for gt in sorted(card.glob("gt/gt*")):
                    for fn in ("rps_max_freq_mhz", "rps_boost_freq_mhz"):
                        if (gt / fn).exists():
                            safe_write(gt / fn, str(low_mhz))
            except ValueError:
                pass
        amd_dpm = card / "device/power_dpm_force_performance_level"
        if amd_dpm.exists():
            safe_write(amd_dpm, "low")

    if nvidia_present():
        res = nvidia_smi("-lgc", "210,900")  # wakes a sleeping GPU once
        if res and res.returncode == 0:
            state["nvidia_locked"] = True

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


