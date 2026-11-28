class ModeSwitch:
    """Off / Light / Dark: one control with a pill that slides to the picked mode.

    The pill shows the HyDE colours of that mode. Click a segment, or use the arrow keys.
    """

    def __init__(self, ui, mode, on_pick):
        self.ui, self.on_pick = ui, on_pick
        self.index = self._index_of(mode)
        self.edges = self.start = (self.index, self.index + 1)
        self.progress = 1.0
        self.hover = None
        self.timer = None
        self.last = 0
        self.shades = hyde_shades()
        self.area = ui.Gtk.DrawingArea()
        self.area.set_size_request(320, 44)
        self.area.set_can_focus(True)
        self.area.get_accessible().set_name("HyDE sync mode")
        mask = ui.Gdk.EventMask
        self.area.add_events(mask.BUTTON_PRESS_MASK | mask.POINTER_MOTION_MASK
                             | mask.LEAVE_NOTIFY_MASK
                             | mask.KEY_PRESS_MASK | mask.FOCUS_CHANGE_MASK)
        self.area.connect("draw", self.on_draw)
        self.area.connect("button-press-event", self.on_click)
        self.area.connect("motion-notify-event", self.on_motion)
        self.area.connect("leave-notify-event", self.on_leave)
        self.area.connect("key-press-event", self.on_key)
        self.area.connect("focus-in-event", self.on_focus)
        self.area.connect("focus-out-event", self.on_focus)
        self.area.connect("style-updated", lambda _a: self.reload_colours())  # new HyDE theme

    @staticmethod
    def _index_of(mode):
        return [value for value, _label in HYDE_MODE_OPTS].index(mode)

    # ---- state and animation
    def set_mode(self, mode):
        index = self._index_of(mode)
        if index == self.index:
            return
        self.index = index
        settings = self.ui.Gtk.Settings.get_default()
        if settings is not None and not settings.get_property("gtk-enable-animations"):
            self.edges, self.progress = (index, index + 1), 1.0
            self.area.queue_draw()
            return
        self.start, self.progress = self.edges, 0.0  # also fine halfway through a slide
        if self.timer is None:
            self.last = self.ui.GLib.get_monotonic_time()
            self.timer = self.ui.GLib.timeout_add(16, self._tick)

    def step(self, dt):
        """Moves the pill on by dt seconds. True while it is still moving."""
        self.progress = min(1.0, self.progress + dt / MODE_SLIDE_SECONDS)
        self.edges = pill_edges(self.start, (self.index, self.index + 1), self.progress)
        self.area.queue_draw()
        return self.progress < 1.0

    def _tick(self):
        now = self.ui.GLib.get_monotonic_time()  # microseconds
        moving = self.step(min(0.05, (now - self.last) / 1e6))  # no jumps after a stall
        self.last = now
        if not moving:
            self.timer = None
        return moving

    def reload_colours(self):
        self.shades = hyde_shades()
        self.area.queue_draw()

    # ---- input
    def _segment_at(self, x):
        segment = (self.area.get_allocated_width() - 2 * MODE_PAD) / len(HYDE_MODE_OPTS)
        return max(0, min(len(HYDE_MODE_OPTS) - 1, int((x - MODE_PAD) // max(1.0, segment))))

    def _pick(self, index):
        if index != self.index and 0 <= index < len(HYDE_MODE_OPTS):
            self.on_pick(HYDE_MODE_OPTS[index][0])  # the tab saves it, then calls set_mode

    def on_click(self, _area, event):
        if event.button == 1:
            self._pick(self._segment_at(event.x))
        return True

    def on_key(self, _area, event):
        move = {self.ui.Gdk.KEY_Left: -1, self.ui.Gdk.KEY_Right: 1}.get(event.keyval)
        if move is None:
            return False
        self._pick(self.index + move)
        return True

    def on_motion(self, _area, event):
        hover = self._segment_at(event.x)
        if hover != self.hover:
            self.hover = hover
            self.area.queue_draw()
        return False

    def on_leave(self, _area, _event):
        self.hover = None
        self.area.queue_draw()
        return False

    def on_focus(self, _area, _event):
        self.area.queue_draw()
        return False

    # ---- drawing
    def _theme(self, area):
        context = area.get_style_context()
        theme = {}
        for key, fallback in (("bg", (0.12, 0.12, 0.18)), ("fg", (0.80, 0.84, 0.96)),
                              ("muted", (0.65, 0.68, 0.78)), ("accent", (0.54, 0.71, 0.98)),
                              ("accent2", (0.58, 0.89, 0.84))):
            found, rgba = context.lookup_color(f"loq_{key}")
            theme[key] = (rgba.red, rgba.green, rgba.blue) if found else fallback
        return theme

    def _palettes(self, theme):
        """Pill colours for Off (grey), Light and Dark."""
        palettes = [[theme["muted"]] * 4]
        for tone in ("light", "dark"):
            if self.shades:
                palettes.append([tuple(v / 255 for v in hex_to_rgb(pick_tone(zone, tone)))
                                 for zone in self.shades])
            else:
                palettes.append([theme["accent"]] * 4)
        return palettes

    def on_draw(self, area, cr):
        theme = self._theme(area)
        font = area.get_pango_context().get_font_description()
        draw_mode_switch(cr, area.get_allocated_width(), area.get_allocated_height(),
                         self.edges, self._palettes(theme), theme,
                         family=font.get_family() or "sans-serif",
                         hover=self.hover if area.get_sensitive() else None,
                         focus=area.has_focus())
        return False
