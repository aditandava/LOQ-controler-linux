VERSION = "1.16"


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


