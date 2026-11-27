import unittest

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


if __name__ == "__main__":
    unittest.main()
