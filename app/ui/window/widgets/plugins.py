class PluginsMixin:
    """Plugin loading and plugin CSS."""

    def add_css(self, css_text):
        prov = self.Gtk.CssProvider()
        prov.load_from_data(css_text.encode())
        self.Gtk.StyleContext.add_provider_for_screen(
            self.Gdk.Screen.get_default(), prov, self.Gtk.STYLE_PROVIDER_PRIORITY_USER + 2)
        self.plugin_providers.append(prov)
        return prov

    def load_plugins(self):
        if not PLUGIN_DIR.is_dir():
            return
        for path in sorted(PLUGIN_DIR.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f"loq_plugin_{path.stem}", path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if callable(getattr(mod, "register", None)):
                        mod.register(self)
            except Exception as err:
                print(f"Plugin {path.name} failed: {err}", file=sys.stderr)
                log(f"plugin {path.name} failed: {traceback.format_exc()}")


