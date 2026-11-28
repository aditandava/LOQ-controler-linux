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


