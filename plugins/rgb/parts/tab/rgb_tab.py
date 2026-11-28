class RGBTab(ControlsCardMixin, ZonesCardMixin, ProfilesCardMixin, RefreshUIMixin, SettingsMixin):
    """The "LOQ RGB" tab. Each card and its actions live in a mixin next to this file."""

    def __init__(self, ui):
        self.ui = ui
        ui.add_css(RGB_CSS)
        page = ui.page("rgb", "LOQ RGB")

        self.profiles, self.active_slot = load_state()
        self.current = _copy_profile(self.profiles[self.active_slot])

        self._build_controls(page)
        self._build_zones(page)
        self._build_profiles(page)

        self._refresh_ui()


