#!/usr/bin/env bash
# LOQ Center installer for EndeavourOS / Arch with Hyprland and HyDE.
# Install:   bash loq_controller_install.sh
# Remove:    bash loq_controller_install.sh --uninstall
set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN="$HOME/.local/bin"
HELPER=/usr/local/libexec/loq-center-helper
POLICY=/usr/share/polkit-1/actions/dev.loqcenter.policy
DCOL="$CONFIG/hyde/wallbash/always/loq-center.dcol"
DESKTOP="$DATA/applications/loq-center.desktop"
# Where the project files are downloaded from (a fork can set LOQ_REPO_RAW to its own address).
REPO_RAW="${LOQ_REPO_RAW:-https://github.com/aditandava/LOQ-controler-linux/raw}"
# App icon: downloaded from the icon folder of the project.
# To use a different file, run:  LOQ_ICON_URL=https://example.com/my-icon.svg bash loq_controller_install.sh
ICON_FILE="loq-center.svg"
ICON_BASE="$REPO_RAW"
ICON="$DATA/icons/hicolor/scalable/apps/$ICON_FILE"
LUA_MAIN="$CONFIG/hypr/hyprland.lua"
LUA_OWN="$CONFIG/hypr/loq-center.lua"
CONF="$CONFIG/hypr/userprefs.conf"
BEGIN="-- >>> loq-center >>>"
END="-- <<< loq-center <<<"

