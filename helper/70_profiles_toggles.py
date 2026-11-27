def on_battery():
    for dev in (SYS / "class/power_supply").glob("*"):
        if safe_read(dev / "type") == "Mains":
            return safe_read(dev / "online") == "0"
    return False


def _write_profile(name):
    nodes = platform_profile_nodes()
    if nodes:
        wrote = False
        for node, choices_node in nodes:
            choices = (safe_read(choices_node) or "").split()
            if name == "custom" or name not in choices:
                continue
            write(node, name)
            if read(node) != name:
                raise Fail("The firmware did not accept the mode (is the charger connected?).")
            wrote = True
        if not wrote:
            raise Fail("That performance mode is not supported.")
    elif name in PPD_NAMES:
        ppd = shutil.which("powerprofilesctl", path=CLEAN_ENV["PATH"])
        if not ppd:
            raise Fail("No platform profile driver or powerprofilesctl found.")
        done = subprocess.run([ppd, "set", PPD_NAMES[name]], capture_output=True,
                              text=True, env=CLEAN_ENV, check=False)
        if done.returncode != 0:
            raise Fail(done.stderr.strip() or "powerprofilesctl refused the mode.")
    else:
        raise Fail("That performance mode is not supported.")


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


def set_profile(name):
    if name == "ultra-saver":
        _apply_ultra_saver()
    elif name == "cooling":
        _apply_cooling()
    elif name == "max-power":
        _apply_max_power()
    else:
        _restore_cooling()
        _write_profile(name)


def set_toggle(name, value):
    if name not in TOGGLES or value not in ("0", "1"):
        raise Fail("Unknown switch or value.")
    node = ideapad(name)
    if node is None:
        raise Fail("This machine does not have that switch.")
    write(node, value)
    if read(node) != value:
        raise Fail("The firmware did not accept the change.")


