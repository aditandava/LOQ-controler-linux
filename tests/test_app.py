import unittest

from helpers import load

app = load("src/loq-center", "loq_center_app")


class AppTests(unittest.TestCase):
    def test_version_and_cli(self):
        self.assertRegex(app.VERSION, r"^\d+\.\d+")
        self.assertEqual(app.main(["loq-center", "--version"]), 0)
        self.assertEqual(app.main(["loq-center", "--bogus"]), 2)

    def test_colour_helpers(self):
        self.assertEqual(app.hex_rgb("#FF8000"), (255, 128, 0))
        self.assertEqual(app.mix((0, 0, 0), (100, 200, 50), 0.5), (50, 100, 25))

    def test_fan_level(self):
        self.assertEqual(app.fan_level(None), 0.0)
        self.assertEqual(app.fan_level(0), 0.0)
        self.assertEqual(app.fan_level(10_000), 1.0)
        self.assertLess(app.fan_level(2000), app.fan_level(4000))

    def test_every_tab_has_its_own_builtin_wallpaper(self):
        import re
        from pathlib import Path
        pages = set()
        for f in (Path(__file__).resolve().parent.parent / "app/ui/window").rglob("*.py"):
            pages |= set(re.findall(r'self\.page\("(\w+)"', f.read_text()))
        self.assertEqual(pages, {"dashboard", "power", "auto", "display", "graphics"})
        for page in pages:
            self.assertIn(app.TAB_SCENES[page], app.SCENE_SVG)
        self.assertEqual(len(set(app.SCENE_SVG.values())), 5)  # five different pictures
        for svg in app.SCENE_SVG.values():
            self.assertTrue(svg.lstrip().startswith("<?xml") and "</svg>" in svg)

    def test_scene_css_and_defaults(self):
        from pathlib import Path
        css = app.build_css("", None, {"power": Path("/tmp/x.png")})
        self.assertIn("window.loq.scene-power", css)
        self.assertIn("file:///tmp/x.png", css)
        self.assertEqual(app.scene_class("rgb"), "scene-dashboard")  # plugin tab falls back
        self.assertEqual(app.scene_class("graphics"), "scene-graphics")
        self.assertEqual(app.BACKGROUNDS.get("scenes"), "Scenes")
        self.assertNotIn("wallpaper", app.BACKGROUNDS)

    def test_window_has_every_tab_mixin(self):
        bases = {b.__name__ for b in app.Window.__mro__}
        for name in ("WidgetsMixin", "ActionsMixin", "DashboardMixin", "PowerMixin",
                     "SmartSwitchMixin", "DisplayMixin", "GraphicsMixin", "RefreshMixin"):
            self.assertIn(name, bases)
        for method in ("build_dashboard", "build_power", "build_auto", "build_display",
                       "build_graphics", "load_plugins", "act", "show_data"):
            self.assertTrue(callable(getattr(app.Window, method)), method)


if __name__ == "__main__":
    unittest.main()
