class ActionsMixin:
    """Background work, busy state, status line and dialogs."""

    # ---- actions
    def set_busy(self, busy):
        self.busy = busy
        self.actions = [w for w in self.actions if w.get_parent() is not None]
        for widget in self.actions:
            widget.set_sensitive(not busy)
        self.scale.set_sensitive(not busy)

    def say(self, text, error=False):
        self.status.set_text(text)
        context = self.status.get_style_context()
        if error:
            context.add_class("error")
        else:
            context.remove_class("error")

    def background(self, work, done):
        def runner():
            try:
                result, error = work(), None
            except ActionError as err:
                result, error = None, str(err)
            except Exception as err:
                log(f"unexpected error: {traceback.format_exc()}")
                result, error = None, f"Unexpected error: {type(err).__name__}: {err}"

            def finish():
                done(result, error)
                return False

            self.GLib.idle_add(finish)

        threading.Thread(target=runner, daemon=True).start()

    def act(self, work, message="Working…", after=None):
        if self.busy:
            return
        self.set_busy(True)
        self.say(message)

        def done(result, error):
            self.set_busy(False)
            self.say(error or result or "Done", bool(error))
            self.refresh()
            if after:
                after(error)

        self.background(work, done)

    def confirm(self, title, body):
        dialog = self.Gtk.MessageDialog(
            transient_for=self.window, modal=True, message_type=self.Gtk.MessageType.WARNING,
            buttons=self.Gtk.ButtonsType.OK_CANCEL, text=title)
        dialog.format_secondary_text(body)
        answer = dialog.run()
        dialog.destroy()
        return answer == self.Gtk.ResponseType.OK


