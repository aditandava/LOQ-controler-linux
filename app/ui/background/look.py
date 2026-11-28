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


