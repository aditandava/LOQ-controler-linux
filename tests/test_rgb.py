import colorsys
import os
import re
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from helpers import load

rgb = load("plugins/rgb/rgb.py", "loq_rgb_plugin")


class PacketTests(unittest.TestCase):
    def test_static_packet(self):
        pkt = rgb.build_packet({"effect": "Static", "brightness": 2, "speed": 1,
                                "colors": ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF"]})
        self.assertEqual(len(pkt), 33)
        self.assertEqual(pkt[:5], bytes([0xCC, 0x16, 0x01, 1, 2]))
        self.assertEqual(pkt[5:17], bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255]))

    def test_wave_sets_direction_byte(self):
        pkt = rgb.build_packet({"effect": "Wave", "brightness": 1, "speed": 3})
        self.assertEqual((pkt[2], pkt[3], pkt[4], pkt[19]), (0x04, 3, 1, 0x01))

    def test_off_packet(self):
        pkt = rgb.build_packet({"effect": "Off"})
        self.assertEqual(pkt[:5], bytes([0xCC, 0x16, 0x01, 0x01, 0x01]))
        self.assertEqual(sum(pkt[5:]), 0)

    def test_values_are_clamped(self):
        pkt = rgb.build_packet({"effect": "Breath", "brightness": 99, "speed": 0})
        self.assertEqual((pkt[3], pkt[4]), (1, 2))


class ProfileTests(unittest.TestCase):
    def test_copy_profile_sanitises(self):
        p = rgb._copy_profile({"effect": "Nope", "brightness": 7, "speed": 9, "colors": ["#123456"] * 9})
        self.assertEqual((p["effect"], p["brightness"], p["speed"], len(p["colors"])), ("Static", 2, 1, 4))

    def test_colour_helpers(self):
        self.assertEqual(rgb.hex_to_rgb("#0A0B0C"), (10, 11, 12))
        self.assertEqual(rgb.hex_to_rgb("bad"), (255, 0, 0))
        self.assertEqual(rgb.contrast_fg("#FFFFFF"), "#11111B")
        self.assertEqual(rgb.contrast_fg("#000000"), "#FFFFFF")

    def test_zone_swatch_style_beats_app_theme(self):
        import inspect
        src = inspect.getsource(rgb.RGBTab._refresh_ui)
        self.assertIn("STYLE_PROVIDER_PRIORITY_USER + 3", src)  # theme is USER + 1

    def test_register_entry_point_exists(self):
        self.assertTrue(callable(rgb.register))


class HydeSyncTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self._saved = (rgb.RGB_JSON, rgb.THEME_FILE, rgb.send_rgb, os.environ.get("HYDE_CACHE_HOME"))
        rgb.RGB_JSON = self.tmp / "rgb.json"
        rgb.THEME_FILE = self.tmp / "theme.css"
        os.environ["HYDE_CACHE_HOME"] = str(self.tmp / "hyde")  # empty cache: only theme.css can answer
        self.sent = []
        rgb.send_rgb = lambda profile, *a, **k: self.sent.append(dict(profile)) or "sent"

    def tearDown(self):
        rgb.RGB_JSON, rgb.THEME_FILE, rgb.send_rgb, cache = self._saved
        if cache is None:
            os.environ.pop("HYDE_CACHE_HOME", None)
        else:
            os.environ["HYDE_CACHE_HOME"] = cache

    def write_theme(self, colors=("#112233", "#445566", "#778899", "#AABBCC")):
        rgb.THEME_FILE.write_text("@define-color loq_accent #FFFFFF;\n" + "".join(
            f"@define-color loq_rgb{i + 1} {c};\n" for i, c in enumerate(colors)))

    def test_auto_sync_is_on_by_default(self):
        self.assertTrue(rgb.load_hyde_auto())

    def test_theme_css_colours_are_read(self):
        self.write_theme()
        self.assertEqual(rgb.hyde_colors(), ["#112233", "#445566", "#778899", "#AABBCC"])

    def test_old_theme_css_without_rgb_colours_falls_back_to_accent(self):
        rgb.THEME_FILE.write_text("@define-color loq_accent #ABCDEF;\n")
        self.assertEqual(rgb.hyde_colors(), ["#ABCDEF"] * 4)

    def test_headless_sync_applies_static_theme_colours(self):
        self.write_theme()
        self.assertEqual(rgb.hyde_sync_headless(), "sent")
        self.assertEqual(self.sent, [{"colors": ["#112233", "#445566", "#778899", "#AABBCC"],
                                      "effect": "Static", "brightness": 2, "speed": 1}])

    def test_headless_sync_ignores_and_keeps_the_profiles(self):
        self.write_theme()
        profs, slot = rgb.load_state()
        profs[slot].update(effect="Off", brightness=2)
        rgb.save_state(profs, slot, hyde_brightness=1)
        before = rgb.RGB_JSON.read_text()
        rgb.hyde_sync_headless()
        self.assertEqual((self.sent[0]["effect"], self.sent[0]["brightness"]), ("Static", 1))
        self.assertEqual(rgb.RGB_JSON.read_text(), before)

    def test_headless_sync_respects_the_switch(self):
        self.write_theme()
        profs, slot = rgb.load_state()
        rgb.save_state(profs, slot, hyde_mode="off")
        rgb.hyde_sync_headless()
        self.assertEqual(self.sent, [])
        rgb.save_state(profs, slot)  # a normal save keeps the switch as it was
        self.assertFalse(rgb.load_hyde_auto())

    def test_old_on_off_setting_is_still_understood(self):
        for saved, mode in (('{"hyde_auto": true}', "light"), ('{"hyde_auto": false}', "off"),
                            ('{"hyde_mode": "dark"}', "dark"), ('{"hyde_mode": "x"}', "light"),
                            ("not json", "light")):
            rgb.RGB_JSON.write_text(saved)
            self.assertEqual(rgb.load_hyde_mode(), mode, saved)

    def test_light_and_dark_pick_the_brighter_and_deeper_shade(self):
        # The template renders both; HyDE's light mode swaps which one is brighter.
        for main, alt in (("#E0C0C0", "#704040"), ("#704040", "#E0C0C0")):
            rgb.THEME_FILE.write_text("".join(
                f"@define-color loq_rgb{i} {main};\n@define-color loq_rgb{i}_alt {alt};\n"
                for i in range(1, 5)))
            self.assertEqual(rgb.hyde_colors("light"), ["#E0C0C0"] * 4)
            self.assertEqual(rgb.hyde_colors("dark"), ["#B20909"] * 4)

    def test_dark_turns_pale_colours_into_rich_ones(self):
        pale = ("#F2C4D6", "#C4F2D0", "#C4D4F2", "#E4C4F2")  # whitish pink, green, blue, violet
        self.write_theme(pale)
        self.assertEqual(rgb.hyde_colors("light"), list(pale))  # normal sync is unchanged
        for before, after in zip(pale, rgb.hyde_colors("dark")):
            was = colorsys.rgb_to_hsv(*(v / 255 for v in rgb.hex_to_rgb(before)))
            now = colorsys.rgb_to_hsv(*(v / 255 for v in rgb.hex_to_rgb(after)))
            self.assertAlmostEqual(now[0], was[0], delta=0.01)  # same hue
            self.assertGreater(now[1], 0.9)
            self.assertLess(now[2], 0.72)

    def test_dark_keeps_grey_themes_grey(self):
        self.write_theme(("#C8C8C8",) * 4)
        self.assertEqual(rgb.hyde_colors("dark"), ["#6E6E6E"] * 4)

    def test_dark_deepens_colours_when_there_is_only_one_shade(self):
        self.write_theme(("#C86432",) * 4)
        self.assertEqual(rgb.hyde_colors("light"), ["#C86432"] * 4)
        self.assertEqual(rgb.hyde_colors("dark"), ["#B24109"] * 4)

    def test_shades_from_the_hyde_cache(self):
        (self.tmp / "hyde" / "wallbash").mkdir(parents=True)
        (self.tmp / "hyde" / "wallbash" / "shell-colors").write_text("".join(
            f'wallbash_{g}xa3="302010"\nwallbash_{g}xa7="D0C0B0"\n' for g in range(1, 5)))
        self.assertEqual(rgb.hyde_colors("light"), ["#D0C0B0"] * 4)
        self.assertEqual(rgb.hyde_colors("dark"), ["#B25E09"] * 4)

    def test_template_writes_both_shades(self):
        template = (Path(__file__).resolve().parent.parent / "assets" / "loq-center.dcol").read_text()
        rendered = template.replace("xa3>", "xa3>111111").replace("xa7>", "xa7>EEEEEE")
        rendered = re.sub(r"#<wallbash_\wxa[37]>", "#", rendered)
        rgb.THEME_FILE.write_text(rendered)
        self.assertEqual(rgb.hyde_colors("light"), ["#EEEEEE"] * 4)
        self.assertEqual(rgb.hyde_colors("dark"), ["#111111"] * 4)

    def test_headless_sync_in_dark_mode_sends_the_dark_colours(self):
        self.write_theme(("#C86432",) * 4)
        profs, slot = rgb.load_state()
        rgb.save_state(profs, slot, hyde_mode="dark")
        rgb.hyde_sync_headless()
        self.assertEqual(self.sent[0]["colors"], ["#B24109"] * 4)

    def test_sync_brightness_survives_a_normal_save(self):
        profs, slot = rgb.load_state()
        rgb.save_state(profs, slot, hyde_brightness=1)
        rgb.save_state(profs, slot)
        self.assertEqual(rgb.load_hyde_brightness(), 1)

class ModeSwitchTests(unittest.TestCase):
    def make(self, mode="off"):
        ui = MagicMock()
        ui.Gdk.KEY_Left, ui.Gdk.KEY_Right = 1, 2
        ui.GLib.get_monotonic_time.return_value = 0
        picked = []
        switch = rgb.ModeSwitch(ui, mode, picked.append)
        switch.area.get_allocated_width.return_value = 308  # three segments of 100
        return switch, picked

    def test_pill_stretches_and_lands_on_the_target(self):
        left, right = rgb.pill_edges((0, 1), (2, 3), 0.4)
        self.assertGreater(right - left, 1.3)
        self.assertEqual(rgb.pill_edges((0, 1), (2, 3), 1.0), (2, 3))
        self.assertEqual(rgb.pill_edges((2, 3), (0, 1), 1.0), (0, 1))
        for step in range(101):
            for start, goal in (((0, 1), (2, 3)), ((2, 3), (0, 1)), ((0.2, 2.6), (0, 1))):
                left, right = rgb.pill_edges(start, goal, step / 100)
                self.assertGreaterEqual(right - left, 0.79)

    def test_slide_runs_one_timer_and_finishes(self):
        switch, _ = self.make()
        switch.set_mode("light")
        switch.set_mode("dark")  # changed mind halfway
        self.assertEqual(switch.ui.GLib.timeout_add.call_count, 1)
        for _frame in range(40):
            switch.step(1 / 60)
        self.assertEqual(switch.edges, (2, 3))
        self.assertFalse(switch._tick())
        self.assertIsNone(switch.timer)

    def test_click_and_arrow_keys_pick_a_mode(self):
        switch, picked = self.make("light")
        switch.on_click(None, MagicMock(button=1, x=250))
        switch.on_click(None, MagicMock(button=1, x=150))  # already selected
        switch.on_click(None, MagicMock(button=3, x=20))   # not the main button
        switch.on_key(None, MagicMock(keyval=1))
        self.assertEqual(picked, ["dark", "off"])
        self.assertFalse(switch.on_key(None, MagicMock(keyval=99)))


if __name__ == "__main__":
    unittest.main()
