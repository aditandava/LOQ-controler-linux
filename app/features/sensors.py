# ----------------------------------------------------------------------- sensors

def cpu_temperature():
    for hw in (SYS / "class/hwmon").glob("hwmon*"):
        if read(hw / "name") in ("coretemp", "k10temp"):
            value = read_int(hw / "temp1_input")
            if value is not None:
                return value / 1000
    return None


def fan_speeds():
    speeds = []
    for node in sorted((SYS / "class/hwmon").glob("hwmon*/fan*_input")):
        value = read_int(node)
        if value is not None:
            speeds.append(value)
    return speeds


class FanWatcher:
    """Fan RPM through the root helper (acpi_call). One helper process serves the whole session."""

    def __init__(self):
        self.process = None
        self.latest, self.stamp = [], 0.0

    def speeds(self):
        if self.process is None:
            if not os.path.exists(HELPER):
                return []
            try:
                self.process = subprocess.Popen(
                    ["pkexec", HELPER, "watch", "fans"], stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            except OSError:
                return []
            threading.Thread(target=self._listen, daemon=True).start()
        # An old reading is worse than none
        return self.latest if time.monotonic() - self.stamp < 7 else []

    def _listen(self):
        for line in self.process.stdout:
            try:
                values = json.loads(line)
            except ValueError:
                continue
            if isinstance(values, list) and all(isinstance(v, int) for v in values):
                self.latest, self.stamp = values, time.monotonic()
        self.process.wait()  # never restarted, so a refusal cannot cause repeated prompts


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


