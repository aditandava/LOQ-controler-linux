def _apply_ultra_saver():
    """Quiet mode plus a CPU cap. Saved like Cooling, so any other mode puts everything back.

    Leaves the NVIDIA GPU and the fans alone: no clock lock (that would wake a sleeping GPU)."""
    nodes = platform_profile_nodes()
    choices = (safe_read(nodes[0][1]) or "").split() if nodes else []
    quiet = next((c for c in ("low-power", "quiet") if c in choices), "low-power")
    _restore_cooling()  # undo Cooling, Max power or an earlier Ultra saver first
    state = _collect_cooling_state()
    _write_profile(quiet)  # raises Fail when this machine has no quiet mode
    state.update(mode="ultra-saver", applied_profile=quiet)
    _save_state(state)  # saved early, so another mode can always undo a partial change
    time.sleep(0.5)  # let power daemons react to the mode change before capping the CPU
    capped = any([
        safe_write(SYS / "devices/system/cpu/intel_pstate/no_turbo", "1"),
        safe_write(SYS / "devices/system/cpu/cpufreq/boost", "0"),
        safe_write(SYS / "devices/system/cpu/intel_pstate/max_perf_pct", "50"),
    ])
    for pol in sorted((SYS / "devices/system/cpu/cpufreq").glob("policy*")):
        govs = (safe_read(pol / "scaling_available_governors") or "").split()
        for g in ("powersave", "conservative", "schedutil"):
            if g in govs and safe_write(pol / "scaling_governor", g):
                break
        epps = (safe_read(pol / "energy_performance_available_preferences") or "").split()
        if "power" in epps:
            safe_write(pol / "energy_performance_preference", "power")
        if safe_read(pol / "scaling_driver") != "intel_pstate":
            try:
                mn = int(safe_read(pol / "cpuinfo_min_freq") or 0)
                mx = int(safe_read(pol / "cpuinfo_max_freq") or 0)
                if mx > mn > 0:
                    safe_write(pol / "scaling_max_freq", str(max(mn, int(mx * 0.5))))
            except ValueError:
                pass
    cpu = "CPU capped (no turbo, about half speed)" if capped else "CPU cap refused by this kernel"
    print(f"Ultra saver [{quiet}]: {cpu}.")


