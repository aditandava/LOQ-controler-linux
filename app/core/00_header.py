#!/usr/bin/python3
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
"""LOQ Center: a control panel for Lenovo LOQ and Legion laptops on Linux.

Everything shown is detected at runtime. A control only appears when the kernel
or a tool on this machine really provides it.
"""
import colorsys
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import traceback
import zlib
from pathlib import Path

