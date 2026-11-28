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


