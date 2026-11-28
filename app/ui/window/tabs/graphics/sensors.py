class GraphicsMixin:
    """Graphics tab: layout and NVIDIA sensors."""

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


