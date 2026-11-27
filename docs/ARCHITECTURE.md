# Architecture and where to edit

You edit **section files**. `python3 tools/build.py` (or `make build`) joins them into the
single files that get installed. Never edit the built files; they are overwritten.

| You edit | Built into | Runs as |
|---|---|---|
| `app/**`                | `src/loq-center`            | the GTK window, `--status`, `--daemon` (normal user) |
| `helper/*.py`           | `src/loq-center-helper`     | root, through `pkexec`, whitelisted actions only |
| `assets/dev.loqcenter.policy` | `src/dev.loqcenter.policy` | polkit rules for the helper |
| `assets/wallpapers/*.svg` | embedded in `src/loq-center` as `SCENE_SVG` | the built-in tab wallpapers |
| `assets/loq-center.dcol`| `src/loq-center.dcol`       | HyDE wallbash theme template |
| `installer/*.sh`        | `loq_controller_install.sh` | installer / uninstaller |
| `plugins/rgb/**`        | `plugins/rgb/rgb.py` and `loq_rgb.sh` | optional RGB tab (plugin + udev rules) |

`src/`, `loq_controller_install.sh` and `loq_rgb.sh` are committed on purpose: the installer
downloads `src/*` from GitHub, and users run the two scripts directly.

Each folder has a `manifest.txt` with the join order. A new section file must be added there
(the build refuses files that are not listed).

## app/ — LOQ Center

| Section | What it holds |
|---|---|
| `core/00_header.py` | licence, docstring, imports |
| `core/10_constants.py` | VERSION, paths, labels, idle presets, hypridle template |
| `core/20_helpers.py` | `ActionError`, `read`, `run`, `log`, `helper()` (pkexec call) |
| `features/battery.py` | battery info, charge mode |
| `features/idle_timer.py` | hypridle sleep timer |
| `features/performance.py` | platform profiles (Quiet … Max power, Cooling) |
| `features/toggles.py` | Fn lock, camera |
| `features/brightness.py` | screen and keyboard backlight |
| `features/display.py` | monitors, refresh rate |
| `features/graphics.py` | NVIDIA state, GPU / MUX mode |
| `features/sensors.py` | CPU temp, fans, CPU meter, memory, `snapshot()` |
| `features/presets.py` | one-click presets |
| `features/smart_switch.py` | settings per power source + background daemon |
| `ui/theme.py` | CSS and theme colours |
| `ui/background.py` | wallpaper / generated art / own picture |
| `ui/start_gui.py` | `start_gui()` GTK bootstrap |
| `ui/controls.py` | `Choice` and `Dropdown` widgets |
| `ui/fan_wheel.py` | animated fan drawing |
| `ui/window/*.py` | **one mixin per tab**: dashboard, power, smart_switch, display, graphics; plus widgets, actions, refresh |
| `ui/window/window.py` | `class Window(...mixins)`: constructor, theme loading, key/close handlers |
| `core/90_main.py` | `main()` and CLI flags |

### Add a new tab
1. Create `app/ui/window/mytab.py` with `class MyTabMixin:` and a `build_mytab(self)` method
   (use `self.page(...)`, `self.card(...)`, `self.add(...)`).
2. Add `MyTabMixin` to the bases in `ui/window/window.py` and call `self.build_mytab()` where the
   other pages are built in `Window.__init__`.
3. Add data in `ui/window/refresh.py` (`show_data`) if it needs periodic updates.
4. Put the system access in `app/features/mytab.py`; if it needs root, add an action to
   `helper/` **and** `assets/dev.loqcenter.policy`.
5. List the new files in `app/manifest.txt` (feature file before the mixin, mixin before `window.py`).

### Tab wallpapers
Each tab has its own built-in SVG in `assets/wallpapers/<tab>.svg` (`dashboard`, `power`, `auto`,
`display`, `graphics`): mountains, aurora, dunes, ocean sunset, ringed planet. `tools/build.py`
embeds them into the app (the `@generated:wallpapers` line in `app/manifest.txt`). At runtime
`prepare_scenes()` draws each one to a PNG in `~/.cache/loq-center/` (needs `librsvg`) and
`Window.apply_scene()` switches the window's `scene-<tab>` CSS class when the tab changes.
To add a scene for a new tab: add `assets/wallpapers/<page>.svg` and a line in `TAB_SCENES`
(`app/ui/background.py`). A tab without a scene (plugin tabs) shows the dashboard one.
The HyDE wallpaper is no longer used; HyDE is only used for the colour theme.

## helper/ — root helper
Only whitelisted actions in `90_main.py` exist. Add the function in the matching section
(`30_charge`, `60_cooling`, `80_gpu_mux`, …), add a `case` in `main()`, and a polkit action
in `assets/dev.loqcenter.policy`.

## plugins/rgb — optional RGB tab
`parts/` are the sections of the plugin (built into `plugins/rgb/rgb.py`) (`register(ui)` is called by LOQ Center's `load_plugins`);
`99-ite-kbd.rules` holds the udev rules; `loq_rgb.sh.in` is the installer template where
`@@RULES@@` and `@@PLUGIN@@` are filled in. Add a keyboard PID in the `.rules` file *and* in
`parts/10_constants.py` (`ITE_PIDS`).

## Checks
`make check` rebuilds, compiles every section, runs `bash -n` on the scripts and the unit tests
in `tests/`. The GTK window itself needs a desktop session: use `make run`.
