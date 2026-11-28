class BrightnessMixin:
    """Display tab: brightness slider."""

    def on_scale(self, scale):
        if self.scale_quiet:
            return
        if self.scale_timer:
            self.GLib.source_remove(self.scale_timer)
        self.scale_timer = self.GLib.timeout_add(200, self.apply_scale)

    def apply_scale(self):
        self.scale_timer = None
        value = self.scale.get_value()

        def done(result, error):
            self.say(error or result, bool(error))

        self.background(lambda: set_brightness(value), done)
        return False


