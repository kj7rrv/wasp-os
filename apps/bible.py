# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2021 Francesco Gazzetta
# Copyright (C) 2023 Samuel Sloniker

"""Bible reader
~~~~~~~~~~~~~~~

This app is a Bible reader for Wasp-os. It relies on a properly coded Bible
file existing at `bible.txt`.

Text display code is based in part on the Morse app by Francesco Gazzetta.


.. figure:: res/screenshots/BibleApp.png
    :width: 179
"""

import os
import wasp
import icons
import fonts
import json
from math import floor
from micropython import const


_WIDTH = const(240)
_HEIGHT = const(240)
# No easy way to make this depend on _WIDTH
_MAXINPUT = const(16)

# These two need to match
_FONTH = const(24)
_FONT = fonts.sans24

# Precomputed for efficiency
_LINEH = const(30)  # int(_FONTH * 1.25)
_MAXLINES = const(7)  # floor(_HEIGHT / _LINEH) - 1 # the "-1" is the input line


class BibleApp:
    NAME = "Bible"

    def __init__(self):
        self.index = []

        with open("/flash/bible/KJV/index.txt") as index_file:
            while True:
                file_name = index_file.readline().strip()

                if not file_name:
                    break

                try:
                    open("/flash/bible/KJV/" + file_name).close()
                except OSError:
                    continue

                self.index.append(file_name)

    def read_header(self, file):
        file.seek(0)
        magic = file.readline()
        index_line = file.readline()

        index = []
        position = len(magic + index_line)

        for length_str in index_line.strip().split(","):
            length = int(length_str)
            index.append(
                (
                    position,
                    length,
                )
            )
            position += length

        return index

    def get_text(self, file_name, chapter):
        with open("/flash/bible/KJV/" + file_name) as f:
            location, length = self.read_header(file)[chapter - 1]
            file.seek(location)
            return file.read(length)

    def get_chapters(self, file_name):
        with open("/flash/bible/KJV/" + file_name) as f:
            f.readline()
            return len(f.readline().split(","))

    def foreground(self):
        draw = wasp.watch.drawable
        draw.fill()

        draw.string("Ready", 0, 108, width=240)

        wasp.system.request_event(
            wasp.EventMask.TOUCH
            | wasp.EventMask.SWIPE_LEFTRIGHT
            | wasp.EventMask.SWIPE_UPDOWN
        )
