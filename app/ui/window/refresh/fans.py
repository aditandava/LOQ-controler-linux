class ShowFansMixin:
    """Fills the Dashboard fan box."""

    def show_fans(self, data):
        fans = data["fans"]
        for index, (side, title, rpm_label, wheel) in enumerate(self.fan_sides):
            rpm = fans[index] if index < len(fans) else None
            wheel.set_rpm(rpm)
            rpm_label.set_text("n/a" if rpm is None else f"{rpm} RPM")
            self.visible(side, index == 0 or len(fans) != 1)
        # A machine that reports a single fan cannot say which part it cools
        self.fan_sides[0][1].set_text("Fan" if len(fans) == 1 else "CPU fan")

        cpu = data["cpu_temp"]
        self.fan_cpu_temp.set_text("n/a" if cpu is None else f"{cpu:.0f} °C")
        state, gpu = data["gpu_temp"]
        words = {"sleep": "Sleep", "off": "Off"}
        self.fan_gpu_temp.set_text(f"{gpu:.0f} °C" if state == "ok" else words.get(state, "n/a"))


