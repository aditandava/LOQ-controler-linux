import os
import unittest
from pathlib import Path

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
        rgb.save_state(profs, slot, hyde_auto=False)
        rgb.hyde_sync_headless()
        self.assertEqual(self.sent, [])
        rgb.save_state(profs, slot)  # a normal save keeps the switch as it was
        self.assertFalse(rgb.load_hyde_auto())

    def test_sync_brightness_survives_a_normal_save(self):
        profs, slot = rgb.load_state()
        rgb.save_state(profs, slot, hyde_brightness=1)
        rgb.save_state(profs, slot)
        self.assertEqual(rgb.load_hyde_brightness(), 1)


if __name__ == "__main__":
    unittest.main()
