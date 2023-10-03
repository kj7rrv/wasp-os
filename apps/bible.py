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
            for line in index_file.readlines():
                file_name = line.strip()

                try:
                    open("/flash/bible/KJV/" + file_name).close()
                except OSError:
                    continue

                self.index.append(file_name)

    def read_header(self, file):
        file.seek(0)
        magic = file.readline()

        if not magic == "Wasp-os Bible v1\n":
            raise ValueError("invalid file")

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

    @property
    def books(self):
        return {
            file_name: file_name.split("_", 1)[1].replace("_", " ")
            for file_name in self.index
        }

    def get_text(self, file_name, chapter):
        with open("/flash/bible/KJV/" + file_name) as f:
            location, length = read_header(file)[chapter - 1]
            file.seek(location)
            return file.read(length)

    def get_chapters(self, file_name):
        with open("/flash/bible/KJV/" + file_name) as f:
            return len(read_header(file))

    def foreground(self):
        draw = wasp.watch.drawable
        draw.fill()

        draw.string("Ready", 0, 108, width=240)

        wasp.system.request_event(
            wasp.EventMask.TOUCH
            | wasp.EventMask.SWIPE_LEFTRIGHT
            | wasp.EventMask.SWIPE_UPDOWN
        )

    def swipe(self, event):
        if event[0] == wasp.EventType.LEFT:
            if self.letter == "":
                if self.text[-1] == "" and len(self.text) > 1:
                    self.text.pop(-1)
                else:
                    self.text[-1] = str(self.text[-1])[:-1]
            self.letter = ""
            self.text[-1] = "{}  ".format(
                self.text[-1]
            )  # adds space, otherwise the screen will not be erased there
            self._update()
            self.text[-1] = str(self.text[-1])[:-2]  # removes space
        elif event[0] == wasp.EventType.RIGHT:
            if self.text[-1].endswith(" "):
                self.text.append("")
                self._draw()
            else:
                self._add_letter(" ")
        else:
            if len(self.letter) < _MAXINPUT:
                self.letter += "-" if event[0] == wasp.EventType.UP else "."
                self._update()

    def touch(self, event):
        self._add_letter(self._lookup(self.letter))

    def _add_letter(self, addition):
        merged = self.text[-1] + addition
        # Check if the new text overflows the screen and add a new line if that's the case
        split = wasp.watch.drawable.wrap(merged, _WIDTH)
        if len(split) > 2:
            self.text.append(self.text[-1][split[1] : split[2]] + addition)
            self.text[-2] = self.text[-2][split[0] : split[1]]
            if len(self.text) > _MAXLINES:
                self.text.pop(0)
            # Ideally a full refresh should be done only when we exceed
            # _MAXLINES, but this should be fast enough
            self._draw()
        else:
            self.text[-1] = merged
        self.letter = ""
        self._update()

    def _draw(self):
        """Draw the display from scratch"""
        draw = wasp.watch.drawable
        draw.fill()
        i = 0
        for line in self.text:
            draw.string(line, 0, _LINEH * i)
            i += 1
        self._update()

    def _update(self):
        """Update the dynamic parts of the application display, specifically the
        input line and last line of the text.
        The full text area is updated in _draw() instead."""
        draw = wasp.watch.drawable
        draw.string(self.text[-1], 0, _LINEH * (len(self.text) - 1))
        guess = self._lookup(self.letter)
        draw.string(
            "{} {}".format(self.letter, guess),
            0,
            _HEIGHT - _FONTH,
            width=_WIDTH,
        )
