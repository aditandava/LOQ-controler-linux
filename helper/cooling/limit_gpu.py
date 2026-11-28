def _cap_cooling_gpu(state):
    """Low Intel, AMD and NVIDIA clocks. Records an NVIDIA lock in `state`."""
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


