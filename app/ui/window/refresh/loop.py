class RefreshMixin:
    """Periodic refresh. show_data() hands the new data to the show_* mixins."""

    # ---- refresh
    def spin(self):
        """Turns the Dashboard fans. Does nothing while another tab is showing."""
        now = time.monotonic()
        dt = min(now - self.spin_last, 0.25)
        self.spin_last = now
        if self.stack.get_visible_child_name() == "dashboard" and self.window.is_visible():
            for wheel in self.fan_wheels:
                wheel.step(dt)
        return True

    def tick(self):
        self.load_theme()
        self.refresh()
        return True

    def refresh(self):
        if self.reading:
            return
        self.reading = True

        def done(data, error):
            self.reading = False
            if error:
                self.say(error, True)
            else:
                self.show_data(data)

        self.background(lambda: snapshot(self.meter, self.fan_watcher), done)

    def stat(self, key, text, fraction=None):
        value, bar = self.stats[key]
        value.set_text(text)
        if bar is not None:
            bar.set_fraction(max(0.0, min(1.0, fraction or 0.0)))

    def show_data(self, data):
        self.show_stats(data)
        self.show_source(data)
        self.show_profile(data)
        self.show_charge(data)
        self.show_idle(data)
        self.show_health(data)
        self.show_screen(data)
        self.show_light(data)
        self.show_keyboard(data)
        self.show_toggles(data)
        self.show_gpu(data)
        self.show_auto(data)


