class CpuMeter:
    def __init__(self):
        self.last = None

    def percent(self):
        text = read(PROC / "stat")
        if not text:
            return None
        values = [int(v) for v in text.splitlines()[0].split()[1:9]]
        idle, total = values[3] + values[4], sum(values)
        previous, self.last = self.last, (idle, total)
        if not previous or total <= previous[1]:
            return None
        busy = 1 - (idle - previous[0]) / (total - previous[1])
        return max(0.0, min(100.0, busy * 100))


def memory_info():
    values = {}
    for line in (read(PROC / "meminfo") or "").splitlines():
        key, _, rest = line.partition(":")
        if key in ("MemTotal", "MemAvailable"):
            values[key] = int(rest.split()[0]) / 1_048_576
    if len(values) != 2:
        return None
    return values["MemTotal"] - values["MemAvailable"], values["MemTotal"]


def snapshot(meter, watcher=None):
    return {
        "cpu_temp": cpu_temperature(), "cpu_use": meter.percent(), "memory": memory_info(),
        "fans": fan_speeds() or (watcher.speeds() if watcher else []), "battery": battery_info(), "ac": on_ac(), "charge": charge_info(),
        "profile": profile_info(), "idle": idle_info(),
        "toggles": toggle_info(), "backlight": backlight_info(), "keyboard": keyboard_info(),
        "display": display_info(), "nvidia": nvidia_state(),
    }


