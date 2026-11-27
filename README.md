# LOQ Center for Linux

##Developed using Claude AI

A control panel for Lenovo LOQ / Legion laptops, built for Arch / EndeavourOS with Hyprland and HyDE.
Manage performance, battery, display, GPU mode and the optional 4-zone RGB keyboard from one window.

## Features

| Area | What you can do |
|---|---|
| **Dashboard** | See live system readings and apply a preset: Ultra saver, Battery saver, Daily or Performance |
| **Power** | Choose a performance mode and charging mode, set the sleep timer, check battery health |
| **Smart Switch** | Apply separate settings on charger and on battery: performance, refresh rate, sleep time, brightness |
| **Display** | Set refresh rate, brightness and keyboard light, toggle Fn lock and camera, change the app background |
| **Graphics** | Read NVIDIA sensors and switch between Integrated, Hybrid and dGPU only |
| **LOQ RGB** (optional) | Control keyboard zones, effects and profiles, or follow your HyDE colours |

The options you see depend on what your laptop and installed tools support.

### Modes

- **Performance:** Quiet, Balanced, Performance, Max power, Cooling, Ultra saver
- **Charging:** Battery care, Full charge, Rapid charge
- **Sleep timer:** 5, 10 or 30 minutes, or Never (uses `hypridle`)

Performance, Max power and Cooling need the charger.

## Requirements

- A Lenovo LOQ or Legion laptop
- Python 3.10 or newer with GTK 3 (`python-gobject`, `gtk3`)
- `polkit`, `brightnessctl`, `librsvg`
- Hyprland and HyDE for the shortcut, display controls and theme colours
- Optional: `envycontrol` for Integrated GPU mode
- Optional: `acpi_call` for full fan speed and dGPU only mode

The installer installs missing packages where it can. On Arch it also tries to set up `envycontrol`
(through `yay` or `paru`) and `acpi_call-dkms`.

## Install

```bash
git clone https://github.com/aditandava/LOQ-controler-linux loq-center-linux
cd loq-center-linux
bash loq_controller_install.sh
```

Run it as your normal user. It asks for `sudo` when needed.

To add the RGB keyboard tab, run this afterwards:

```bash
bash loq_rgb.sh
```

To update, get the new files and run the same scripts again. Then close and reopen LOQ Center.

## Use

Open **LOQ Center** from your app launcher, press `SUPER + SHIFT + L` (added only if the shortcut
is free), or run:

```bash
~/.local/bin/loq-center
```

| Command option | Result |
|---|---|
| `--status` | Print detected hardware data as JSON |
| `--version` | Print the version |
| `--daemon` | Run the Smart Switch background watcher |

## RGB keyboard

- **Effects:** Static, Breath, Wave, Spectrum, Off
- **Controls:** Low or High brightness, speed 1–4 for animated effects
- **Zones:** four separate colours in Static and Breath
- **Profiles:** four saved slots

### Auto HyDE Sync

On by default. The keyboard follows your colours whenever the HyDE theme, wallpaper or mode changes,
even when LOQ Center is closed.

While it is **on**:

- The keyboard stays Static in the HyDE colours
- Only brightness can be changed
- Effects, speed, zones and profiles are hidden
- Saved profiles are not used or changed

Turn it **off** to get all controls back and restore your active profile.
To switch the keyboard light off, turn sync off and choose **Off**.

The app does not reapply colours on its own after login or sleep.

## GPU modes

| Mode | Behaviour |
|---|---|
| Integrated | NVIDIA is off. External ports wired to NVIDIA (often HDMI) stop working |
| Hybrid | Intel runs the desktop. Start games with `prime-run` |
| dGPU only | NVIDIA drives the screen and uses more battery |

Switching needs your password and a reboot. Save your work first, and do not power off while a
switch is in progress.

> **Warning:** dGPU only mode has not been tested on real hardware. Remove `AQ_DRM_DEVICES` from your
> Hyprland config before using it.

## Troubleshooting

| Problem | Fix |
|---|---|
| Black screen after switching to or from Integrated | Press `Ctrl+Alt+F3`, log in, run `sudo envycontrol -s hybrid && sudo reboot` |
| Black screen after dGPU only | Restart, press `F2`, set Graphics Device back to the switchable option |
| Fans do not reach full speed | Reboot, and check that `acpi_call` loads (Secure Boot can block it) |
| HyDE colours not found | Change the wallpaper once |
| RGB keyboard needs permission | Run `bash loq_rgb.sh` again |
| RGB keyboard not detected | Add its ID to `/etc/udev/rules.d/99-ite-kbd.rules`, then reload the rules or reboot |
| Anything else | Check `~/.cache/loq-center/log` and `loq-center --status` |

Re-running `loq_rgb.sh` overwrites the udev rules file. To keep a new keyboard ID, also add it to
`plugins/rgb/99-ite-kbd.rules` and `plugins/rgb/parts/10_constants.py`, then run `make build`.

## Uninstall

Remove the RGB tab **first**, because its script needs LOQ Center to be installed.

```bash
bash loq_rgb.sh --uninstall
bash loq_controller_install.sh --uninstall
```

Battery and performance settings stay as you last set them.

## Security

The app runs as your user. System changes go through a small root helper that accepts only a fixed
list of actions. Your active session can change power and device settings without a password;
GPU mode changes always ask for one.

## Develop

```bash
make build      # section files -> src/, loq_controller_install.sh, loq_rgb.sh
make check      # build + syntax + bash -n + tests
make run        # open the GUI from this folder
```

Edit the section files in `app/`, `helper/`, `installer/` and `plugins/rgb/`, never the built files.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the section map and how to add a tab.

```
app/          GUI and background watcher, split by feature and tab
helper/       root helper (pkexec), split by area
installer/    installer script sections
plugins/rgb/  RGB plugin sections, udev rules, installer template
assets/       polkit policy, HyDE theme template, tab wallpapers
src/          built files the installer uses (committed)
tools/        build and check scripts
tests/        unit tests
docs/         architecture guide
```

## License

GPL-3.0-or-later, © 2026 aditandava. See [LICENSE](LICENSE).
