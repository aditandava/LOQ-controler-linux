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


def _require_custom(title):
    custom = custom_profile_node()
    if custom is None:
        raise Fail(f"{title} needs Custom (purple) mode, but this kernel does not offer it. "
                   "Nothing was changed. Check: cat /sys/class/platform-profile/*/choices")
    return custom


