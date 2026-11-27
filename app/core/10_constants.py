VERSION = "1.17"
SYS = Path("/sys")
PROC = Path("/proc")
HELPER = "/usr/local/libexec/loq-center-helper"
COOLING_STATE = Path("/run/loq-center-cooling.json")
MUX_PENDING = Path("/run/loq-center-mux")  # written by the helper until the next reboot
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
PLUGIN_DIR = CONFIG_DIR / "loq-center" / "plugins"
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
LOG_FILE = CACHE_DIR / "loq-center" / "log"
THEME_FILE = CONFIG_DIR / "loq-center" / "theme.css"
HYPRIDLE_CONF = CONFIG_DIR / "hypr" / "hypridle.conf"
HYPRIDLE_SHARE = DATA_DIR / "hypr" / "hypridle.conf"

CHARGE_LABELS = {"Long_Life": "Battery care", "Standard": "Full charge", "Fast": "Rapid charge"}
PROFILE_LABELS = {
    "low-power": "Quiet", "quiet": "Quiet", "cool": "Cool", "balanced": "Balanced",
    "balanced-performance": "Balanced+", "performance": "Performance", "max-power": "Max power",
    "cooling": "Cooling", "ultra-saver": "Ultra saver", "custom": "Custom",
}
CHARGER_ONLY = ("performance", "max-power", "cooling")  # not offered on battery
PPD_NAMES = {"low-power": "power-saver", "balanced": "balanced", "performance": "performance"}
TOGGLE_LABELS = {"fn_lock": "Fn lock", "camera_power": "Camera"}

# Sleep presets in minutes: (label, dim_sec, lock_sec, dpms_sec, suspend_sec)
IDLE_PRESETS = {
    5:  ("5 min",  120,  180,  240,  300),
    10: ("10 min", 300,  480,  540,  600),
    30: ("30 min", 600, 1200, 1500, 1800),
    0:  ("Never",    0,    0,    0,    0),
}

DEFAULT_HYPRIDLE_TEMPLATE = """$LOCKSCREEN = hyprlock

general {
    lock_cmd = $LOCKSCREEN
    unlock_cmd =
    before_sleep_cmd = loginctl lock-session
    after_sleep_cmd = hyprctl dispatch dpms on
    ignore_dbus_inhibit = false
}

listener {
    timeout = 120
    on-timeout = brightnessctl -s && brightnessctl s 1%
    on-resume = brightnessctl -r
}

listener {
    timeout = 180
    on-timeout = loginctl lock-session
}

listener {
    timeout = 240
    on-timeout = hyprctl dispatch dpms off
    on-resume = hyprctl dispatch dpms on
}

listener {
    timeout = 300
    on-timeout = systemctl suspend
}
"""


