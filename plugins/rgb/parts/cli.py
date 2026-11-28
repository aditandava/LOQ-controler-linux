if __name__ == "__main__" and sys.argv[1:] == ["--apply"]:
    profs, slot = load_state()
    profile = hyde_profile() if load_hyde_auto() else profs[slot]
    if not profile:
        sys.exit("HyDE theme colours not found.")
    print(send_rgb(profile))
elif __name__ == "__main__" and sys.argv[1:] == ["--hyde-sync"]:
    try:
        print(hyde_sync_headless())
    except RGBError as err:
        print(f"HyDE sync: {err}", file=sys.stderr)
        sys.exit(1)


