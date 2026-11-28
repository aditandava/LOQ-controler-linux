SYS = Path("/sys")


COOLING_STATE = Path("/run/loq-center-cooling.json")


ENVYCONTROL = "/usr/bin/envycontrol"


CHARGE_MODES = ("Standard", "Long_Life", "Fast")


TOGGLES = ("fn_lock", "camera_power")


GPU_MODES = {"integrated": [], "hybrid": ["--rtd3", "2"]}


CMDLINE = Path("/proc/cmdline")


HELPER_LOCK = Path("/run/loq-center-helper.lock")  # one change at a time


HEAVY_PROFILES = ("cooling", "max-power", "ultra-saver")  # only reachable through the "power" action


MUX_PENDING = Path("/run/loq-center-mux")  # emptied by every reboot


GAMEZONE_GUID = "887B54E3-DDDC-4B2C-8B88-68A26A8835D0"


MUX_SUPPORTED, MUX_GET, MUX_SET = 0x28, 0x29, 0x2A  # GameZone "GSync" methods


MUX_MODES = {"hybrid": 0, "dgpu": 1}


MUX_LABELS = {"hybrid": "Hybrid", "dgpu": "dGPU only"}


BIOS_HINT = "You can still change it in the BIOS (F2 at startup, Graphics Device)."


PPD_NAMES = {"low-power": "power-saver", "balanced": "balanced", "performance": "performance"}


CLEAN_ENV = {"PATH": "/usr/bin:/usr/sbin:/bin:/sbin", "LANG": "C.UTF-8"}


