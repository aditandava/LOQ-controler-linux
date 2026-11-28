# ---------------------------------------------------- Off / Light / Dark: motion

MODE_SLIDE_SECONDS = 0.38


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (2 - 2 * t) ** 3 / 2


def pill_edges(start, goal, t):
    """Left and right edge of the sliding pill, counted in segments, at progress t (0 to 1).

    The edge facing the target leads and the other one follows, so the pill stretches.
    """
    (left, right), (to_left, to_right) = start, goal
    fast, slow = ease_out(min(1.0, t * 1.25)), ease_in_out(t)
    forward = to_left + to_right > left + right
    k_left, k_right = (slow, fast) if forward else (fast, slow)
    return left + (to_left - left) * k_left, right + (to_right - right) * k_right


def mix_rgb(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def blend_palette(palettes, position):
    """The pill colours when it sits at `position` (0 = first segment, 1 = second, ...)."""
    position = max(0.0, min(len(palettes) - 1.0, position))
    first = min(int(position), len(palettes) - 2)
    return [mix_rgb(a, b, position - first) for a, b in zip(palettes[first], palettes[first + 1])]
