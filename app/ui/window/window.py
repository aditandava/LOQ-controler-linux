class Window(
        WidgetsMixin, ChromeMixin, PluginsMixin, ActionsMixin, ThemeMixin, EventsMixin,
        DashboardMixin, FanCardMixin, PowerMixin,
        SmartSwitchMixin, SmartSwitchViewMixin, SmartSwitchEventsMixin,
        DisplayMixin, BackgroundPickerMixin, BrightnessMixin,
        GraphicsMixin, GpuModeMixin,
        RefreshMixin, ShowDashboardMixin, ShowFansMixin, ShowPowerMixin, ShowHardwareMixin):
    """The LOQ Center window. Its behaviour lives in the mixins under ui/window/."""

    def __init__(self, app, Gtk, Gdk, GLib):
        self.Gtk, self.Gdk, self.GLib = Gtk, Gdk, GLib
        self.busy = False
        self.reading = False
        self.gpu_current = None  # graphics_state() once it is read
        self.actions = []
        self.meter = CpuMeter()
        self.fan_watcher = FanWatcher()
        self.gpu_temp = GpuTemp()
        self.theme_stamp = None
        self.scenes_on = False
        self.fan_wheels = []
        self.spin_last = time.monotonic()
        self.auto_last = None  # power source seen on the previous refresh
        self.auto_now = None  # power source highlighted on the Auto tab
        self.auto_options = {"profile": [], "refresh": [], "idle": False, "brightness": False}
        self.Choice = Choice
        self.ActionError = ActionError
        self.CONFIG_DIR = CONFIG_DIR
        self.DATA_DIR = DATA_DIR
        self.THEME_FILE = THEME_FILE
        self.read = read
        self.plugin_providers = []
        self.provider = Gtk.CssProvider()
        self.load_theme()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.provider, Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)

        self.window = Gtk.ApplicationWindow(application=app, title="LOQ Center")
        self.window.set_default_size(880, 760)
        self.window.get_style_context().add_class("loq")
        self.window.connect("key-press-event", self.on_key)
        self.window.connect("delete-event", self.on_close)

        root = self.vbox(12)
        root.set_border_width(18)
        self.window.add(root)
        root.pack_start(self.header(), False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(180)
        self.stack.connect("notify::visible-child-name", lambda *_: self.apply_scene())
        root.pack_start(self.tab_bar(), False, False, 0)
        root.pack_start(self.stack, True, True, 0)
        self.build_dashboard()
        self.build_power()
        self.build_auto()
        self.build_display()
        self.build_graphics()
        self.load_plugins()

        root.pack_end(self.status_line(), False, False, 0)
        self.window.show_all()
        self.window.set_focus(None)  # no focus outline on the first tab at startup
        self.apply_scene()
        self.refresh()
        self.refresh_gpu_mode()
        GLib.timeout_add_seconds(2, self.tick)
        GLib.timeout_add(16, self.spin)  # about 60 frames per second
        if load_auto()["enabled"]:
            start_daemon()  # keeps switching after this window is closed


