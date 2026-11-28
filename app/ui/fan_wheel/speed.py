# --------------------------------------------------------------- fan speed look

FAN_RPM_FULL = 6000.0  # fan speed drawn at top speed and fully blue
FAN_BLADES = 33


def fan_level(rpm):
    """0 for a stopped or unknown fan, rising to 1 at FAN_RPM_FULL."""
    if not rpm or rpm <= 0:
        return 0.0
    return min(1.0, rpm / FAN_RPM_FULL)


def spin_rate_for(level):
    """Turns per second of the blades for a level between 0 and 1. A stopped fan does not turn.

    The real speed is far too fast to draw. At most 0.77 turns per second: at 60 frames per
    second that is under half the angle between two of the 33 blades, so the blades never seem
    to turn backwards. The motion blur (streak_rate_for) shows the rest of the speed."""
    return 0.0 if level <= 0 else 0.15 + 0.62 * level


def streak_rate_for(level):
    """Turns per second of the three motion blur streaks."""
    return 0.0 if level <= 0 else 0.3 + 2.4 * level


def spin_rate(rpm):
    return spin_rate_for(fan_level(rpm))


def speed_color(level):
    """Red for a slow fan, then orange, yellow and green, to blue for a fast one."""
    level = max(0.0, min(1.0, level))
    red, green, blue = colorsys.hsv_to_rgb(220 / 360 * level, 0.62, 0.97)
    return (red, green, blue, 1.0)


