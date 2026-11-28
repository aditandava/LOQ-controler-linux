def log(message):
    """Append a line to ~/.cache/loq-center/log (kept small). Never raises."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 200_000:
            LOG_FILE.replace(LOG_FILE.with_suffix(".old"))
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def run(cmd, timeout=15):
    """Run a command and never raise. Returns (code, stdout, stderr)."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
        return done.returncode, done.stdout.strip(), done.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"{cmd[0]} is not installed"
    except subprocess.TimeoutExpired:
        return 124, "", f"{cmd[0]} did not answer in time"
    except OSError as err:
        return 126, "", str(err)


def have(tool):
    return shutil.which(tool) is not None


def helper(*args, timeout=120):
    """Run the root helper through polkit. timeout=None means never interrupt it."""
    if not os.path.exists(HELPER):
        raise ActionError("Root helper is missing. Run the installer again.")
    code, out, err = run(["pkexec", HELPER, *args], timeout=timeout)
    if code == 0:
        return out
    log(f"helper {' '.join(args)} -> code {code}: {err or out}")
    if code == 126:
        raise ActionError("Authentication was cancelled.")
    if code == 127:
        raise ActionError(err or "Not authorised. Is a polkit agent running?")
    raise ActionError(err or out or f"Helper failed with code {code}.")


