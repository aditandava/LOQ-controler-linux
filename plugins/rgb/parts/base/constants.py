SYS = Path("/sys")


ITE_RULES = Path("/etc/udev/rules.d/99-ite-kbd.rules")


ITE_VENDOR = 0x048D


ITE_PIDS = [0xC995, 0xC994, 0xC993, 0xC985, 0xC984, 0xC983,
            0xC975, 0xC973, 0xC965, 0xC963, 0xC955]


ZONE_NAMES = ["Zone 1", "Zone 2", "Zone 3", "Zone 4"]


EFFECTS = ["Static", "Breath", "Wave", "Smooth Spectrum", "Off"]


EFFECT_OPTS = [("Static", "Static"), ("Breath", "Breath"), ("Wave", "Wave"),
               ("Smooth Spectrum", "Spectrum"), ("Off", "Off")]


EFFECT_CODES = {"Static": 0x01, "Breath": 0x03, "Wave": 0x04,
                "Smooth Spectrum": 0x06, "Off": 0x01}


BRIGHTNESS_OPTS = [(1, "Low"), (2, "High")]


SPEED_OPTS = [(s, str(s)) for s in range(1, 5)]


# HyDE sync: off, or follow the theme with its lighter or its darker colours.
HYDE_MODE_OPTS = [("off", "Off"), ("light", "Light"), ("dark", "Dark")]


# Dark mode: how rich (0 to 1, higher = less white) and how bright (0 to 1) its colours are.
DARK_SATURATION = 0.95
DARK_VALUE = 0.70


EMPTY_PROFILE = {"colors": ["#FF0000", "#00FF00", "#0000FF", "#FF00FF"],
                 "effect": "Static", "brightness": 2, "speed": 1}


HIDIOCSFEATURE_33 = (3 << 30) | (33 << 16) | (ord("H") << 8) | 0x06


CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


RGB_JSON = CONFIG_DIR / "loq-center" / "rgb.json"


THEME_FILE = CONFIG_DIR / "loq-center" / "theme.css"


