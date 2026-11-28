class ThemeMixin:
    """Loading the CSS and the per-tab wallpaper."""

    # ---- window
    def load_theme(self):
        """Reloads the style when the colours, the background choice or the wallpaper change."""
        try:
            colors_stamp = THEME_FILE.stat().st_mtime_ns
        except OSError:
            colors_stamp = 0
        source = background_source(load_look())
        try:
            picture_stamp = source[1].stat().st_mtime_ns if source[1] else 0
        except OSError:
            picture_stamp = 0
        stamp = (colors_stamp, source, picture_stamp)
        if stamp == self.theme_stamp:
            return
        theme = read(THEME_FILE)
        scenes = prepare_scenes() if source[0] == "scenes" else {}
        picture = None if scenes else prepare_background(source, theme_colors(theme))
        if scenes:
            attempts = [(None, scenes), (None, None)]
        else:
            attempts = [(picture, None), (None, None)] if picture else [(None, None)]
        for use, tabs in attempts:  # plain colours if the pictures fail
            try:
                self.provider.load_from_data(build_css(theme, use, tabs).encode())
                self.theme_stamp = stamp
                self.scenes_on = bool(tabs)
                self.apply_scene()
                return
            except self.GLib.Error as err:
                log(f"theme not applied: {err}")
                print(f"Theme not applied: {err}", file=sys.stderr)

    def apply_scene(self):
        """Gives the window the wallpaper of the tab that is showing."""
        window = getattr(self, "window", None)
        if window is None:
            return
        context = window.get_style_context()
        for name in set(TAB_SCENES.values()) | {DEFAULT_SCENE}:
            context.remove_class(f"scene-{name}")
        if getattr(self, "scenes_on", False):
            context.add_class(scene_class(self.stack.get_visible_child_name()))


