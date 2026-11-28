class SmartSwitchMixin:
    """Smart Switch tab: layout."""

    def build_auto(self):
        page = self.page("auto", SWITCH_NAME)

        # Hero: name, one-line status and the master switch
        hero = self.vbox(0)
        for name in ("card", "hero"):
            hero.get_style_context().add_class(name)
        top = self.Gtk.Box(spacing=16)
        text = self.vbox(4)
        self.add(text, self.label(SWITCH_NAME, "title2"))
        self.auto_note = self.add(text, self.label("", "muted"))
        top.pack_start(text, True, True, 0)
        self.auto_switch = self.Gtk.Switch()
        self.auto_switch.set_valign(self.Gtk.Align.CENTER)
        self.auto_quiet = False
        self.auto_switch.connect("notify::active", self.on_auto_switch)
        top.pack_end(self.auto_switch, False, False, 0)
        self.add(hero, top)
        self.add(page, hero)

        # One card per power source, side by side; the one in use is highlighted
        cards = self.Gtk.Box(spacing=14)
        cards.set_homogeneous(True)
        self.auto_cards, self.auto_badges, self.auto_rows = {}, {}, {}
        for source, title in AUTO_SOURCES.items():
            self._build_source_card(cards, source, title)
        self.add(page, cards)

    def _build_source_card(self, cards, source, title):
        card = self.vbox(16)
        for name in ("card", "source"):
            card.get_style_context().add_class(name)
        head = self.Gtk.Box(spacing=8)
        text = self.vbox(2)
        self.add(text, self.label(title, "title2"))
        self.add(text, self.label(SWITCH_HINTS[source], "muted"))
        head.pack_start(text, True, True, 0)
        badge = self.label("", "badge")
        badge.set_line_wrap(False)
        badge.set_valign(self.Gtk.Align.START)
        head.pack_end(badge, False, False, 0)
        self.add(card, head)
        self.visible(badge, False)
        rows = {}
        for key, label in AUTO_TITLES.items():
            field = self.vbox(6)
            self.add(field, self.label(label, "caption"))
            cell = Dropdown(self, lambda v, s=source, k=key: self.pick_auto(s, k, v))
            self.add(field, cell.box)
            self.actions.append(cell.box)  # locked while a change is being applied
            self.add(card, field)
            rows[key] = (field, cell)
        cards.pack_start(card, True, True, 0)
        self.auto_cards[source], self.auto_badges[source] = card, badge
        self.auto_rows[source] = rows


