def main(argv):
    if argv[1:] == ["--version"]:
        print(VERSION)
        return 0
    if argv[1:] == ["--status"]:
        meter = CpuMeter()
        data = snapshot(meter)
        data["gpu_mode"] = gpu_mode()
        data["helper_installed"] = os.path.exists(HELPER)
        print(json.dumps(data, indent=2))
        return 0
    if argv[1:] == ["--daemon"]:
        return daemon_main()
    if argv[1:]:
        print("Usage: loq-center [--status | --version | --daemon]", file=sys.stderr)
        return 2
    return start_gui()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
