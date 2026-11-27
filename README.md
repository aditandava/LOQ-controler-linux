# LOQ Center for Linux

Control panel for Lenovo LOQ / Legion laptops (Arch / EndeavourOS, Hyprland + HyDE):
performance mode, battery care, display, GPU/MUX, fans, optional 4-zone RGB keyboard.
GPL-3.0-or-later, © 2026 aditandava. See [LICENSE](LICENSE).

## Use
```bash
bash loq_controller_install.sh      # install   (--uninstall to remove)
bash loq_rgb.sh                     # optional RGB tab (--uninstall to remove)
```

## Develop
```bash
make build      # section files -> src/, loq_controller_install.sh, loq_rgb.sh
make check      # build + syntax + bash -n + tests
make run        # open the GUI from this folder
```
Edit the section files (`app/`, `helper/`, `installer/`, `plugins/rgb/`), never the built files.
Layout, a section map and "how to add a tab" are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
app/        LOQ Center GUI + daemon, split by feature and by tab

helper/     root helper (pkexec), split by area
installer/  installer script sections
plugins/rgb RGB plugin sections, udev rules, installer template
assets/     polkit policy, HyDE theme template, wallpapers/ (one SVG per tab)
src/        built files the installer downloads (committed)
tools/      build.py, check.py
tests/      unit tests
docs/       architecture / where to edit
```
