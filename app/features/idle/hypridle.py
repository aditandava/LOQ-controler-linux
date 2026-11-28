# ----------------------------------------------------------- hypridle sleep timer

def hypridle_running():
    code, _, _ = run(["pgrep", "-x", "hypridle"], timeout=3)
    return code == 0


def ensure_hypridle_conf():
    if HYPRIDLE_CONF.exists():
        return HYPRIDLE_CONF.read_text(errors="replace")
    HYPRIDLE_CONF.parent.mkdir(parents=True, exist_ok=True)
    if HYPRIDLE_SHARE.exists():
        text = HYPRIDLE_SHARE.read_text(errors="replace")
    else:
        text = DEFAULT_HYPRIDLE_TEMPLATE
    HYPRIDLE_CONF.write_text(text)
    return text


def restart_hypridle():
    code, _, _ = run(["systemctl", "--user", "list-unit-files", "hypridle.service"], timeout=4)
    if code == 0:
        r_code, _, _ = run(["systemctl", "--user", "restart", "hypridle.service"], timeout=5)
        if r_code == 0 and hypridle_running():
            return
    run(["pkill", "-x", "hypridle"], timeout=3)
    time.sleep(0.15)
    subprocess.Popen(["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def stop_hypridle():
    run(["systemctl", "--user", "stop", "hypridle.service"], timeout=4)
    run(["pkill", "-x", "hypridle"], timeout=3)


