def _cap_cooling_cpu():
    """Turbo off and low clocks. True when the kernel accepted a global cap."""
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
    return cpu_capped


def _cap_cooling_rapl():
    """Lowers the Intel package power limits (PL1 / PL2)."""
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


