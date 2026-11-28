#!/usr/bin/env bash
# Copyright (C) 2026 aditandava
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# LOQ RGB — standalone RGB plugin & udev installer for LOQ Center.
#
# Run AFTER loq_controller_install.sh has been run:
#   bash loq_rgb.sh             # install RGB tab into LOQ Center + udev rules
#   bash loq_rgb.sh --uninstall # remove RGB tab and udev rules
#
# All RGB UI and USB/HID logic lives in this file; loq_controller_install.sh stays purely for
# Dashboard, Power, Display, and Graphics. You can freely edit this script
# and re-run it — loq_controller_install.sh loads the plugin automatically.

set -euo pipefail

RULES=/etc/udev/rules.d/99-ite-kbd.rules
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/loq-center"
PLUGIN_DIR="$CONFIG/plugins"
PLUGIN="$PLUGIN_DIR/rgb.py"
BIN="${HOME}/.local/bin/loq-center"

say() { printf '\033[1;35m::\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -ne 0 ] || die "Run as your normal user, without sudo."
if [ ! -x "$BIN" ] && ! command -v loq-center > /dev/null; then
  die "LOQ Center is not installed yet. Run loq_controller_install.sh first, then loq_rgb.sh."
fi

