#!/usr/bin/python3 -I
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
"""Root helper for LOQ Center, run through pkexec. Only whitelisted actions exist."""
import contextlib
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SYS = Path("/sys")
COOLING_STATE = Path("/run/loq-center-cooling.json")
ENVYCONTROL = "/usr/bin/envycontrol"
CHARGE_MODES = ("Standard", "Long_Life", "Fast")
TOGGLES = ("fn_lock", "camera_power")
GPU_MODES = {"integrated": [], "hybrid": ["--rtd3", "2"]}
CMDLINE = Path("/proc/cmdline")
HELPER_LOCK = Path("/run/loq-center-helper.lock")  # one change at a time
HEAVY_PROFILES = ("cooling", "max-power", "ultra-saver")  # only reachable through the "power" action
MUX_PENDING = Path("/run/loq-center-mux")  # emptied by every reboot
GAMEZONE_GUID = "887B54E3-DDDC-4B2C-8B88-68A26A8835D0"
MUX_SUPPORTED, MUX_GET, MUX_SET = 0x28, 0x29, 0x2A  # GameZone "GSync" methods
MUX_MODES = {"hybrid": 0, "dgpu": 1}
MUX_LABELS = {"hybrid": "Hybrid", "dgpu": "dGPU only"}
BIOS_HINT = "You can still change it in the BIOS (F2 at startup, Graphics Device)."
PPD_NAMES = {"low-power": "power-saver", "balanced": "balanced", "performance": "performance"}
CLEAN_ENV = {"PATH": "/usr/bin:/usr/sbin:/bin:/sbin", "LANG": "C.UTF-8"}


