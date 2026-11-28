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


