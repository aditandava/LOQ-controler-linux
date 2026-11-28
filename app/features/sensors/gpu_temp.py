# ------------------------------------------------------------- GPU temperature

GPU_TEMP_EVERY = 15.0  # seconds between nvidia-smi calls, so that the GPU can still fall asleep


def hwmon_gpu_temperature():
    """°C from a kernel sensor labelled GPU (for example legion_laptop), or None."""
    for label in (SYS / "class/hwmon").glob("hwmon*/temp*_label"):
        if "gpu" in (read(label) or "").lower():
            value = read_int(label.with_name(label.name.replace("_label", "_input")))
            if value is not None and value > 0:
                return value / 1000
    return None


class GpuTemp:
    """GPU temperature for the Dashboard. It never wakes a sleeping NVIDIA GPU."""

    def __init__(self):
        self.value, self.stamp = None, None

    def reading(self):
        """("ok", °C), ("sleep", None), ("off", None) or ("none", None)."""
        value = hwmon_gpu_temperature()
        if value is not None:
            return "ok", value
        state = nvidia_state()  # sysfs only
        if state not in ("active", "unsupported"):  # unsupported: it never sleeps
            self.value, self.stamp = None, None
            return ("off" if state == "off" else "sleep"), None
        now = time.monotonic()
        if self.stamp is None or now - self.stamp >= GPU_TEMP_EVERY:
            code, out, _ = run(["nvidia-smi", "--query-gpu=temperature.gpu",
                                "--format=csv,noheader,nounits"], timeout=5)
            try:
                self.value = float(out.splitlines()[0]) if code == 0 else None
            except (ValueError, IndexError):
                self.value = None
            self.stamp = now
        return ("none" if self.value is None else "ok"), self.value


