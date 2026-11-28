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


