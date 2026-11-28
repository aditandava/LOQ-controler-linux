# ----------------------------------------------------------- background picture

LOOK_FILE = CONFIG_DIR / "loq-center" / "look.json"
BACKGROUNDS = {"scenes": "Scenes", "picture": "My picture", "plain": "Plain"}
# Which built-in scene (SCENE_SVG) each tab shows. A tab that is not listed (a plugin tab) uses "dashboard".
TAB_SCENES = {"dashboard": "dashboard", "power": "power", "auto": "auto",
              "display": "display", "graphics": "graphics"}
DEFAULT_SCENE = "dashboard"


def load_look():
    look = {"background": "scenes", "picture": None}
    try:
        data = json.loads(LOOK_FILE.read_text())
    except (OSError, ValueError):
        return look
    if isinstance(data, dict):
        if data.get("background") in BACKGROUNDS:
            look["background"] = data["background"]
        if isinstance(data.get("picture"), str):
            look["picture"] = data["picture"]
    return look


def save_look(look):
    try:
        LOOK_FILE.parent.mkdir(parents=True, exist_ok=True)
        part = LOOK_FILE.with_suffix(".tmp")
        part.write_text(json.dumps(look, indent=2))
        part.replace(LOOK_FILE)
    except OSError as err:
        raise ActionError(f"Could not save {LOOK_FILE}: {err}")


def background_source(look):
    """("image", path), ("scenes", None), ("art", None) or ("plain", None). Art stands in for a missing picture."""
    choice = look["background"]
    if choice == "plain":
        return "plain", None
    if choice == "picture" and look["picture"] and Path(look["picture"]).is_file():
        return "image", Path(look["picture"]).resolve()
    if choice == "scenes":
        return "scenes", None
    return "art", None


def scene_class(page):
    """CSS class that gives a tab its own wallpaper."""
    return "scene-" + TAB_SCENES.get(page, DEFAULT_SCENE)


def prepare_scenes():
    """{scene name: PNG path} for the built-in wallpapers, drawn once into the cache. {} if none work."""
    folder = CACHE_DIR / "loq-center"
    found = {}
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        log(f"no scene cache: {err}")
        return found
    for name, svg in SCENE_SVG.items():
        target = folder / f"scene-{name}-{hashlib.sha1(svg.encode()).hexdigest()[:12]}.png"
        try:
            if not target.exists():
                source = folder / f"scene-{name}.svg"
                source.write_text(svg, encoding="utf-8")
                part = target.with_suffix(".part")
                scale_picture(source, part)  # needs the SVG loader of gdk-pixbuf (librsvg)
                part.replace(target)
            for old in folder.glob(f"scene-{name}-*.png"):
                if old != target:
                    old.unlink(missing_ok=True)
            found[name] = target
        except Exception as err:
            log(f"scene {name} not drawn (is librsvg installed?): {err}")
    return found


def hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def mix(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def write_png(path, width, height, pixels):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    stride = width * 3
    rows = b"".join(b"\0" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def draw_art(path, colors, width=1200, height=800):
    """Draws a night landscape (sky, moon, stars, mountains) in the theme colours."""
    bg, surface, accent, accent2 = (hex_rgb(colors[f"loq_{name}"])
                                    for name in ("bg", "surface", "accent", "accent2"))
    stride = width * 3
    pixels = bytearray(stride * height)

    def blend(x, y, color, amount):
        at = y * stride + x * 3
        pixels[at:at + 3] = bytes(mix(pixels[at:at + 3], color, amount))

    horizon = mix(surface, accent, 0.45)
    for y in range(height):
        pixels[y * stride:(y + 1) * stride] = bytes(mix(bg, horizon, (y / height) ** 1.3)) * width

    cx, cy, radius, reach = int(width * 0.76), int(height * 0.22), 52, 240
    for y in range(max(0, cy - reach), min(height, cy + reach)):
        for x in range(cx - reach, min(width, cx + reach)):
            distance = math.hypot(x - cx, y - cy)
            if distance < reach:
                moon = max(0.0, min(1.0, radius + 0.5 - distance))
                blend(x, y, accent2, max(moon, 0.45 * (1 - distance / reach) ** 2))

    stars = random.Random(7)  # the same sky every time
    for _ in range(190):
        x, y = stars.randrange(width - 1), stars.randrange(int(height * 0.55))
        light = stars.uniform(0.25, 0.9)
        for dx in range(stars.choice((1, 1, 2))):
            blend(x + dx, y, (255, 255, 255), light)

    def peaks(value):
        return abs((value % 1.0) * 2 - 1)

    layers = ((0.66, 0.20, mix(surface, accent, 0.30), 0.15),
              (0.76, 0.17, mix(surface, bg, 0.40), 0.62),
              (0.90, 0.15, mix(bg, (0, 0, 0), 0.20), 0.37))
    for base, rise, color, shift in layers:
        for x in range(width):
            u = x / width
            ridge = (0.62 * peaks(u * 1.7 + shift) + 0.28 * peaks(u * 4.3 + shift * 3)
                     + 0.10 * peaks(u * 13 + shift * 7))
            top = (base - rise * ridge) * height
            first = int(top)
            blend(x, first, color, 1 - (top - first))  # smooth edge
            below = height - first - 1
            for channel in range(3):
                start = (first + 1) * stride + x * 3 + channel
                pixels[start::stride] = bytes([color[channel]]) * below
    write_png(path, width, height, pixels)


def scale_picture(source, target):
    """A smaller copy, so that large wallpapers do not slow the window down."""
    from gi.repository import GdkPixbuf
    picture = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(source), 1600, 1200, True)
    picture.savev(str(target), "png", [], [])


def prepare_background(source, colors):
    """A PNG in the cache that is ready to use behind the window, or None for plain."""
    kind, path = source
    if kind == "plain":
        return None
    folder = CACHE_DIR / "loq-center"

    def cached(key, make):
        target = folder / f"bg-{hashlib.sha1(key.encode()).hexdigest()[:16]}.png"
        if not target.exists():
            part = target.with_suffix(".part")
            make(part)
            part.replace(target)
        for old in folder.glob("bg-*.png"):
            if old != target:
                old.unlink(missing_ok=True)
        return target

    try:
        folder.mkdir(parents=True, exist_ok=True)
        if kind == "image":
            try:
                return cached(f"{path} {path.stat().st_mtime_ns}", lambda out: scale_picture(path, out))
            except Exception as err:  # unreadable or unknown picture format
                log(f"background picture {path} not used: {err}")
        return cached("art 1 " + json.dumps(colors, sort_keys=True), lambda out: draw_art(out, colors))
    except Exception as err:
        log(f"no background picture: {err}")
        return None


