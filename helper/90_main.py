def main(argv):
    try:
        match argv[1:]:
            case ["set", "charge", mode]:
                with exclusive():
                    set_charge(mode)
            case ["set", "profile", name]:
                if name in HEAVY_PROFILES:
                    raise Fail(f"{name} needs the power action.")
                with exclusive():
                    set_profile(name)
            case ["power", "profile", name]:
                if name not in HEAVY_PROFILES:
                    raise Fail("Unknown power mode.")
                with exclusive():
                    set_profile(name)
            case ["set", "toggle", name, value]:
                with exclusive():
                    set_toggle(name, value)
            case ["watch", "fans"]:
                watch_fans()
            case ["watch", "mux"]:
                mux_report()
            case ["gpu", "mux", mode]:
                with exclusive():
                    set_mux(mode)
            case ["gpu", mode]:
                with exclusive():
                    set_gpu(mode)
            case _:
                print("Usage: set charge|profile|toggle ... | power profile cooling|max-power | "
                      "gpu integrated|hybrid | gpu mux dgpu|hybrid", file=sys.stderr)
                return 2
    except Fail as err:
        print(err, file=sys.stderr)
        return 3
    except OSError as err:
        print(f"System refused the change: {err}", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
