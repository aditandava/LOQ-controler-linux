class Fail(Exception):
    pass


@contextlib.contextmanager
def exclusive(timeout=30):
    """Only one changing action runs at a time (GUI and the Auto watcher can overlap)."""
    with open(HELPER_LOCK, "a") as handle:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise Fail("Another LOQ Center change is still running. Try again in a moment.")
                time.sleep(0.2)
        yield


def read(path):
    return path.read_text().strip()


def safe_read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def write(path, value):
    path.write_text(str(value) + "\n")


def safe_write(path, value):
    try:
        Path(path).write_text(str(value) + "\n")
        return True
    except OSError:
        return False


