# Architecture and where to edit

You edit **section files**. `python3 tools/build.py` (or `make build`) joins them into the
single files that get installed. Never edit the built files; they are overwritten.

| You edit | Built into | Runs as |
|---|---|---|
| `app/**`                | `src/loq-center`            | the GTK window, `--status`, `--daemon` (normal user) |
| `helper/**`           | `src/loq-center-helper`     | root, through `pkexec`, whitelisted actions only |
| `assets/dev.loqcenter.policy` | `src/dev.loqcenter.policy` | polkit rules for the helper |
| `assets/wallpapers/*.svg` | embedded in `src/loq-center` as `SCENE_SVG` | the built-in tab wallpapers |
| `assets/loq-center.dcol`| `src/loq-center.dcol`       | HyDE wallbash theme template |
| `installer/**.sh`        | `loq_controller_install.sh` | installer / uninstaller |
| `plugins/rgb/**`        | `plugins/rgb/rgb.py` and `loq_rgb.sh` | optional RGB tab (plugin + udev rules) |

`src/`, `loq_controller_install.sh` and `loq_rgb.sh` are committed on purpose: the installer
downloads `src/*` from GitHub, and users run the two scripts directly.

Each folder has a `manifest.txt` with the join order. A new section file must be added there
(the build refuses files that are not listed).

All files of one target share a single namespace after joining: there are no imports between
section files, and every top-level name must be unique. Order matters only for code that runs on
load (constants that use other constants, and mixins that must come before their class).

## app/ — LOQ Center

| Path | What it holds |
|---|---|
| `core/header.py` | shebang, licence notice, docstring, imports |
| `core/paths.py`, `labels.py`, `idle_defaults.py` | constants |
| `core/files.py`, `process.py` | `ActionError`, `read`; `log`, `run`, `helper()` (pkexec call) |
| `core/main.py` | `main()` and CLI flags |
| `features/battery/` | battery info (`info.py`), charge mode (`charge.py`) |
| `features/idle/` | hypridle process and config (`hypridle.py`), sleep timer (`timer.py`) |
| `features/performance/` | what the machine offers (`detect.py`), profiles (`profiles.py`) |
| `features/graphics/` | NVIDIA state (`status.py`), GPU / MUX switching (`switching.py`) |
| `features/sensors/` | temperature and fans (`thermal.py`), GPU temperature (`gpu_temp.py`), CPU, memory, `snapshot()` (`system.py`) |
| `features/smart_switch/` | `config.py`, `apply.py`, background `daemon.py` |
| `features/*.py` | Fn lock and camera, backlight, display, presets |
| `ui/theme/` | colours, CSS in `rules/`, `build_css` |
| `ui/background/` | saved choice, built-in scenes, generated art, own picture |
| `ui/controls/` | `Choice` and `Dropdown` widgets |
| `ui/fan_wheel/` | speed and colour (`speed.py`), casing (`housing.py`), glow, blades and hub (`rotor.py`), one whole fan (`drawing.py`), animated widget (`widget.py`) |
| `ui/start_gui.py` | GTK bootstrap |
| `ui/window/widgets/` | widget builders, title/tab/status rows, plugin loading |
| `ui/window/tabs/` | the tabs: `dashboard.py`, `fan_card.py`, `power.py`, `smart_switch/`, `display/`, `graphics/` |
| `ui/window/refresh/` | periodic refresh (`loop.py`) and the `show_*` methods that fill the tabs |
| `ui/window/actions.py`, `theme_loader.py`, `events.py` | busy state and background work, CSS loading, key/close |
| `ui/window/window.py` | `class Window(...mixins)` and its constructor |

### Add a new tab
1. Create `app/ui/window/tabs/mytab.py` with `class MyTabMixin:` and a `build_mytab(self)` method
   (use `self.page(...)`, `self.card(...)`, `self.add(...)`).
2. Add `MyTabMixin` to the bases in `ui/window/window.py` and call `self.build_mytab()` where the
   other pages are built in `Window.__init__`.
3. For periodic updates, add a `show_mytab(self, data)` method in `ui/window/refresh/` and call it
   from `show_data` in `refresh/loop.py`.
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
(`app/ui/background/look.py`). A tab without a scene (plugin tabs) shows the dashboard one.
The HyDE wallpaper is no longer used; HyDE is only used for the colour theme.

## helper/ — root helper

| Path | What it holds |
|---|---|
| `base/` | imports, constants, `Fail`, safe read/write |
| `hardware/` | finding kernel nodes |
| `charge.py`, `power_limits.py` | charge mode, firmware power limits |
| `fans/` | ACPI calls (`acpi.py`), fan control (`control.py`) |
| `cooling/` | save state, CPU and GPU limits, apply, restore |
| `profiles/` | write a profile, Max power, Ultra saver, switches |
| `gpu/` | panel detection, MUX, envycontrol |
| `main.py` | the whitelist of actions |

Only whitelisted actions in `main.py` exist. Add the function in the matching folder, add a
`case` in `main()`, and a polkit action in `assets/dev.loqcenter.policy`.

## installer/ — `loq_controller_install.sh`
`header.sh`, `lib/` (shell functions), `uninstall.sh`, `deps/` (one file per package manager),
`app/` (download, install, icon, menu entry), then the HyDE theme, Hyprland hooks and `finish.sh`.

## plugins/rgb — optional RGB tab
`parts/` holds the plugin, built into `plugins/rgb/rgb.py`; LOQ Center's `load_plugins` calls its
`register(ui)`. Inside: `base/` (imports, constants, CSS), `device/` (discovery, packet, transport),
`tab/` (one mixin per card, plus refresh and actions), `state.py`, `colors.py`, `hyde_sync.py`.
`installer/` is the template for `loq_rgb.sh`, where `@@RULES@@` and `@@PLUGIN@@` are filled in.
Add a keyboard PID in `99-ite-kbd.rules` *and* in `parts/base/constants.py` (`ITE_PIDS`).

**Auto HyDE Sync:** `assets/loq-center.dcol` sits in HyDE's `wallbash/always/` folder, so HyDE re-renders it on every
theme, wallpaper and mode change. Its first line runs `rgb.py --hyde-sync` after `theme.css` is written, and the
template also writes the four keyboard colours as `loq_rgb1..4` so the sync never reads stale values. The on/off
switch is `hyde_auto` in `~/.config/loq-center/rgb.json` (default on).
While it is on, the keyboard is Static in the HyDE colours (brightness is `hyde_brightness`), the effect, speed,
zone and profile controls are hidden, and saved profiles are neither used nor changed.

## Checks
`make check` rebuilds, compiles every section, runs `bash -n` on the scripts and the unit tests
in `tests/`. The GTK window itself needs a desktop session: use `make run`.
