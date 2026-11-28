class ShowDashboardMixin:
    """Fills the dashboard and the title row."""

    def show_stats(self, data):
        temp, use, memory, battery = (data[k] for k in ("cpu_temp", "cpu_use", "memory", "battery"))
        self.stat("cpu_temp", "n/a" if temp is None else f"{temp:.0f} °C", (temp or 0) / 100)
        self.stat("cpu_use", "…" if use is None else f"{use:.0f}%", (use or 0) / 100)
        if memory:
            self.stat("memory", f"{memory[0]:.1f} / {memory[1]:.1f} GiB", memory[0] / memory[1])
        else:
            self.stat("memory", "n/a")
        if battery and battery["capacity"] is not None:
            self.stat("battery", f"{battery['capacity']}%", battery["capacity"] / 100)
        else:
            self.stat("battery", "n/a")
        watts = battery["watts"] if battery else None
        self.stat("watts", "n/a" if watts is None else f"{watts:.1f} W")

    def show_source(self, data):
        battery = data["battery"]
        source = {True: "On charger", False: "On battery", None: "Power source unknown"}[data["ac"]]
        status = f" · {battery['status']}" if battery else ""
        self.subtitle.set_text(source + status)


