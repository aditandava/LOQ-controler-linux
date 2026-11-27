def register(ui):
    ui._rgb_tab = RGBTab(ui)


if __name__ == "__main__" and sys.argv[1:] == ["--apply"]:
    profs, slot = load_state()
    print(send_rgb(profs[slot]))
elif __name__ == "__main__" and sys.argv[1:] == ["--hyde-sync"]:
    try:
        print(hyde_sync_headless())
    except RGBError as err:
        print(f"HyDE sync: {err}", file=sys.stderr)
        sys.exit(1)
