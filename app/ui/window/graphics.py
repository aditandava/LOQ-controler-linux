class GraphicsMixin:
    """Graphics tab (NVIDIA sensors, GPU / MUX mode)."""

    def build_graphics(self):
        page = self.page("graphics", "Graphics")
        card = self.card(page, "NVIDIA GPU")
        self.gpu_power = self.add(card, self.label("…"))
        self.gpu_values = self.add(card, self.label("Live values are read only on request, "
                                                    "so the GPU can sleep.", "muted"))
        self.add(card, self.button("Read GPU sensors", self.read_gpu))
        card = self.card(page, "GPU mode (needs reboot)")
        self.mode_label = self.add(card, self.label("Checking…"))
        self.mode_row = Choice(self, self.ask_gpu)
        self.add(card, self.mode_row.box)
        self.add(card, self.label("Integrated: NVIDIA is switched off.\n"
                                  "Hybrid: Intel runs the desktop; start a game with prime-run.\n"
                                  "dGPU only: NVIDIA drives the screen. Uses more battery.",
                                  "muted"))
        self.reboot = self.add(card, self.button("Reboot now", self.ask_reboot))
        self.reboot.set_no_show_all(True)

    def read_gpu(self):
        def done(result, error):
            self.set_busy(False)
            self.gpu_values.set_text(error or result)
            self.say(error or "GPU sensors read", bool(error))

        if self.busy:
            return
        if nvidia_state() == "off":
            self.gpu_values.set_text("The NVIDIA GPU is switched off.")
            return
        self.set_busy(True)
        self.background(gpu_stats, done)

    def ask_gpu(self, mode):
        if self.busy or self.gpu_current is None:
            return
        kind, message = gpu_action(mode, graphics_state())
        if kind in ("none", "blocked"):
            self.say(message, kind == "blocked")
            return
        if kind == "mux":
            title = f"Switch screen to {GPU_LABELS[mode]}?"
            body = "This changes a firmware setting. It takes effect after a reboot."
            if mode == "dgpu":
                body += ("\n\nBattery life will be much shorter. This is new and not yet tested "
                         "on real hardware.\n\nIf the screen stays black after reboot: restart, "
                         "press F2, and set Graphics Device back to the switchable option.")
                if os.environ.get("AQ_DRM_DEVICES"):
                    body += ("\n\nWARNING: AQ_DRM_DEVICES is set in your Hyprland config. "
                             "Remove it first, or the desktop may not start.")
            work, wait = (lambda: set_mux(mode)), "Asking the firmware…"
        else:
            title = f"Switch GPU to {GPU_LABELS[mode]}?"
            body = ("Save your work first. This rewrites driver settings and rebuilds the boot "
                    "image, which can take a few minutes. Do not power off until it finishes.\n\n"
                    "If the screen stays black after reboot, press Ctrl+Alt+F3, log in and run:\n"
                    "sudo envycontrol -s hybrid && sudo reboot")
            if mode == "integrated":
                body += "\n\nExternal screens on NVIDIA-wired ports (often HDMI) will stop working."
            work, wait = (lambda: set_gpu(mode)), "Switching GPU mode. Please wait…"
        if not self.confirm(title, body):
            return

        def after(error):
            self.refresh_gpu_mode()
            if not error:
                self.reboot.set_no_show_all(False)
                self.reboot.show_all()

        self.act(work, wait, after)

    def ask_reboot(self):
        if self.confirm("Reboot now?", "Unsaved work will be lost."):
            def reboot():
                code, _, err = run(["systemctl", "reboot"])
                if code != 0:
                    raise ActionError(err or "Reboot failed.")
                return "Rebooting…"
            self.act(reboot)

    def refresh_gpu_mode(self):
        def done(state, error):
            self.gpu_current = state
            if error:
                self.mode_label.set_text(error)
                return
            options = [(name, label) for name, label in GPU_LABELS.items()
                       if name != "integrated" or state["config"] is not None]
            if state["pending"]:
                text = f"{GPU_LABELS[state['pending']]} selected. Reboot to apply."
            elif state["dgpu"]:
                text = "Running now: dGPU only (the screen is on NVIDIA)."
            elif state["config"] is None:
                text = "Integrated mode needs the optional tool envycontrol (not installed)."
            else:
                text = f"Configured mode: {state['config']}"
            self.mode_label.set_text(text)
            self.mode_row.update(options, selected_gpu(state))

        self.background(graphics_state, done)


