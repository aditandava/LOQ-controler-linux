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


