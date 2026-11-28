def set_gpu(mode):
    return helper("gpu", mode, timeout=None)


def set_mux(mode):
    return helper("gpu", "mux", mode, timeout=None)


GPU_LABELS = {"integrated": "Integrated", "hybrid": "Hybrid", "dgpu": "dGPU only"}


def graphics_state():
    pending = read(MUX_PENDING)
    return {"config": gpu_mode(), "dgpu": panel_on_nvidia(),
            "pending": pending if pending in ("hybrid", "dgpu") else None}


def selected_gpu(state):
    # No envycontrol and a screen that is not on NVIDIA means plain hybrid
    return state["pending"] or ("dgpu" if state["dgpu"] else state["config"] or "hybrid")


def gpu_action(pick, state):
    """What a GPU button does: ("none" | "blocked" | "mux" | "envy", message)."""
    if pick == selected_gpu(state):
        return "none", f"Already set to {GPU_LABELS[pick]}."
    if pick == "integrated" and (state["dgpu"] or state["pending"] == "dgpu"):
        return "blocked", "The screen needs NVIDIA right now. Pick Hybrid and reboot first."
    if pick == "dgpu":
        if state["config"] == "integrated" and not state["dgpu"]:
            return "blocked", "Pick Hybrid and reboot first, then pick dGPU only."
        return "mux", ""
    if pick == "hybrid" and (state["dgpu"] or state["pending"]):
        return "mux", ""
    return "envy", ""


