class EventsMixin:
    """Window key and close handlers."""

    def on_key(self, _window, event):
        if event.keyval == self.Gdk.KEY_Escape:
            self.window.close()
            return True
        return False

    def on_close(self, *_):
        if self.busy:
            self.say("Please wait for the current task to finish.", True)
            return True
        return False


