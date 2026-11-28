class ActionError(Exception):
    """A user-facing failure message."""


# ---------------------------------------------------------------- basic helpers

def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def read_int(path):
    try:
        return int(read(path))
    except (TypeError, ValueError):
        return None


