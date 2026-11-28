class PowerMixin:
    """Power tab (performance mode, charging, sleep timer)."""

    def build_power(self):
        page = self.page("power", "Power")
        card = self.card(page, "Performance mode")
        self.profile_row = Choice(self, lambda v: self.act(lambda: set_profile(v)))
        self.add(card, self.profile_row.box)
        self.profile_note = self.add(card, self.label("", "muted"))
        card = self.card(page, "Battery charging")
        self.charge_row = Choice(self, lambda v: self.act(lambda: set_charge(v)))
        self.add(card, self.charge_row.box)
        self.charge_note = self.add(card, self.label("", "muted"))
        self.idle_card = self.card(page, "Sleep & idle timer (hypridle)")
        self.idle_row = Choice(self, lambda v: self.act(lambda: set_idle(v)))
        self.add(self.idle_card, self.idle_row.box)
        self.idle_note = self.add(self.idle_card, self.label("", "muted"))
        card = self.card(page, "Battery health")
        self.health = self.add(card, self.label("…"))


