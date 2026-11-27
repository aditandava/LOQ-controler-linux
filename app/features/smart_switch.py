# --------------------------------------------- settings per power source (auto switch)

AUTO_FILE = CONFIG_DIR / "loq-center" / "auto.json"
AUTO_SOURCES = {"ac": "On charger", "battery": "On battery"}
SWITCH_NAME = "Smart Switch"  # the tab that changes settings with the charger
SWITCH_COLUMNS = {"ac": "Charger", "battery": "Battery"}
AUTO_KEYS = ("profile", "refresh", "idle", "brightness")
AUTO_TITLES = {"profile": "Performance", "refresh": "Refresh rate", "idle": "Sleep after",
               "brightness": "Brightness"}
AUTO_BRIGHTNESS = (20, 30, 40, 50, 60, 70, 80, 90, 100)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def clean_auto_value(key, value):
    """A saved value that makes sense, or None, which means 'leave this setting alone'."""
    if key == "profile":
        return value if isinstance(value, str) and re.fullmatch(r"[a-z-]{2,30}", value) else None
    if key == "refresh":
        return value if _is_int(value) and 24 <= value <= 500 else None
    if key == "idle":
        return value if _is_int(value) and value in IDLE_PRESETS else None
    if key == "brightness":
        return value if _is_int(value) and 5 <= value <= 100 else None
    return None


def load_auto():
    config = {"enabled": False, **{s: dict.fromkeys(AUTO_KEYS) for s in AUTO_SOURCES}}
    try:
        data = json.loads(AUTO_FILE.read_text())
    except (OSError, ValueError):
        return config
    if not isinstance(data, dict):
        return config
    config["enabled"] = data.get("enabled") is True
    for source in AUTO_SOURCES:
        saved = data.get(source)
        if isinstance(saved, dict):
            for key in AUTO_KEYS:
                config[source][key] = clean_auto_value(key, saved.get(key))
    if config["battery"]["profile"] in CHARGER_ONLY:  # saved by an older version
        config["battery"]["profile"] = "balanced"
    return config


def save_auto(config):
    try:
        AUTO_FILE.parent.mkdir(parents=True, exist_ok=True)
        part = AUTO_FILE.with_suffix(".tmp")
        part.write_text(json.dumps(config, indent=2))
        part.replace(AUTO_FILE)
    except OSError as err:
        raise ActionError(f"Could not save {AUTO_FILE}: {err}")


def auto_choices(key, source, options, saved=None):
    """The (value, label) pairs one drop-down offers, without "Keep"."""
    if key == "profile":
        return [(p, PROFILE_LABELS.get(p, p)) for p in usable_profiles(options["profile"], source)]
    if key == "refresh":
        return [(r, f"{r} Hz") for r in options["refresh"]]
    if key == "idle":
        return [(k, v[0]) for k, v in IDLE_PRESETS.items()] if options["idle"] else []
    if not options["brightness"]:
        return []
    levels = set(AUTO_BRIGHTNESS) | ({saved} if saved else set())
    return [(b, f"{b}%") for b in sorted(levels)]


def power_source():
    ac = on_ac()
    return None if ac is None else ("ac" if ac else "battery")


def apply_auto(source, only=None):
    """Applies the saved settings for "ac" or "battery". Only changes what is different.

    `only` limits this to one setting, so that picking it does not reset the others."""
    saved = load_auto()[source]
    entry = {key: saved[key] if only in (None, key) else None for key in AUTO_KEYS}
    title = AUTO_SOURCES[source]
    steps = []

    want = entry["profile"]
    check = only in (None, "profile") and (want or source == "battery")
    now = profile_info() if check else None
    if now:
        # "Keep" must not leave a charger-only mode running after unplugging
        if not want and source == "battery" and now["active"] in CHARGER_ONLY:
            want = "balanced"
        if want in now["options"] and now["active"] != want:
            steps.append(lambda: set_profile(want))
    rate = entry["refresh"]
    if rate:
        screen = display_info()
        if screen and rate in screen["options"] and screen["active"] != rate:
            steps.append(lambda: set_refresh(rate))
    minutes = entry["idle"]
    if minutes is not None:
        idle = idle_info()
        if idle is not None and idle["active"] != minutes:
            steps.append(lambda: set_idle(minutes))
    level = entry["brightness"]
    light = backlight_info()
    if level and light and round(light["value"] * 100 / light["max"]) != level:
        steps.append(lambda: set_brightness(level))

    done, failed = [], []
    for step in steps:
        try:
            done.append(step())
        except ActionError as err:
            failed.append(str(err))
    if failed:
        raise ActionError(f"{title}: " + " ".join(failed))
    return f"{title}: settings applied" if done else f"{title}: already set"


def daemon_lock_path():
    return Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "loq-center-auto.lock"


def daemon_running():
    try:
        with open(daemon_lock_path(), "w") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    except OSError:
        return False


def start_daemon():
    """Starts the background watcher unless it is already running."""
    if daemon_running():
        return
    try:
        subprocess.Popen([sys.executable, os.path.realpath(sys.argv[0]), "--daemon"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as err:
        log(f"could not start the {SWITCH_NAME} service: {err}")


def _mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return 0


def ensure_session_env():
    """A process started early may lack the variables hyprctl and hypridle need. Find them.

    Returns True when a Hyprland session was found."""
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    os.environ["XDG_RUNTIME_DIR"] = runtime
    base = Path(runtime)
    signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if not signature or not (base / "hypr" / signature / ".socket.sock").exists():
        found = sorted((base / "hypr").glob("*/.socket.sock"), key=_mtime)
        if found:
            os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = found[-1].parent.name
        else:
            os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
    if not os.environ.get("WAYLAND_DISPLAY"):
        sockets = sorted(p.name for p in base.glob("wayland-[0-9]") if p.is_socket())
        if sockets:
            os.environ["WAYLAND_DISPLAY"] = sockets[0]
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def run_daemon(stop=lambda: False, interval=3.0, wait=90.0):
    """Applies the saved settings whenever the charger is plugged in or unplugged."""
    last, pending = None, None
    started = time.monotonic()
    while not stop():
        ready = ensure_session_env() or not have("hyprctl")
        source = power_source()
        if source is not None and source != last:
            last, pending = source, source
        if pending:
            if not load_auto()["enabled"]:
                pending = None
            elif ready or time.monotonic() - started > wait:
                try:
                    print(apply_auto(pending), flush=True)
                except ActionError as err:
                    print(f"{SWITCH_NAME}: {err}", file=sys.stderr, flush=True)
                pending = None
        time.sleep(interval)
    return 0


def daemon_main():
    try:
        handle = open(daemon_lock_path(), "w")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("The background service is already running.")
        return 0
    except OSError as err:
        print(f"Cannot start the background service: {err}", file=sys.stderr)
        return 1
    try:
        return run_daemon()
    except KeyboardInterrupt:
        return 0
    finally:
        handle.close()


