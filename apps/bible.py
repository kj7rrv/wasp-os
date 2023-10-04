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
import io
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


class FileSegment(io.StringIO):
    def __init__(self, file, offset, length):
        super().__init__()
        self.file = file
        self.offset = offset
        self.length = length
        self.position = 0

    def read(self, size=-1):
        if size == -1:
            remaining_bytes = self.length - self.position
        else:
            remaining_bytes = min(size, self.length - self.position)

        self.file.seek(self.offset + self.position)
        data = self.file.read(remaining_bytes)
        self.position += len(data)

        return data

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            new_position = self.offset + offset
        elif whence == io.SEEK_CUR:
            new_position = self.position + offset
        elif whence == io.SEEK_END:
            new_position = self.offset + self.length + offset
        else:
            raise ValueError("Invalid 'whence' argument")

        if (
            new_position < self.offset
            or new_position > self.offset + self.length
        ):
            raise ValueError("Seek position is out of range")

        self.position = new_position
        return new_position

    def tell(self):
        return self.position

    def close(self):
        return self.file.close()


class BibleApp:
    NAME = "Bible"

    def __init__(self):
        pass

    def books(self):
        for file_name in [
            "01_Genesis.txt",
            "02_Exodus.txt",
            "03_Leviticus.txt",
            "04_Numbers.txt",
            "05_Deuteronomy.txt",
            "06_Joshua.txt",
            "07_Judges.txt",
            "08_Ruth.txt",
            "09_1_Samuel.txt",
            "10_2_Samuel.txt",
            "11_1_Kings.txt",
            "12_2_Kings.txt",
            "13_1_Chronicles.txt",
            "14_2_Chronicles.txt",
            "15_Ezra.txt",
            "16_Nehemiah.txt",
            "17_Esther.txt",
            "18_Job.txt",
            "19_Psalms.txt",
            "20_Proverbs.txt",
            "21_Ecclesiastes.txt",
            "22_Song_of_Solomon.txt",
            "23_Isaiah.txt",
            "24_Jeremiah.txt",
            "25_Lamentations.txt",
            "26_Ezekiel.txt",
            "27_Daniel.txt",
            "28_Hosea.txt",
            "29_Joel.txt",
            "30_Amos.txt",
            "31_Obadiah.txt",
            "32_Jonah.txt",
            "33_Micah.txt",
            "34_Nahum.txt",
            "35_Habakkuk.txt",
            "36_Zephaniah.txt",
            "37_Haggai.txt",
            "38_Zechariah.txt",
            "39_Malachi.txt",
            "40_Matthew.txt",
            "41_Mark.txt",
            "42_Luke.txt",
            "43_John.txt",
            "44_Acts.txt",
            "45_Romans.txt",
            "46_1_Corinthians.txt",
            "47_2_Corinthians.txt",
            "48_Galatians.txt",
            "49_Ephesians.txt",
            "50_Philippians.txt",
            "51_Colossians.txt",
            "52_1_Thessalonians.txt",
            "53_2_Thessalonians.txt",
            "54_1_Timothy.txt",
            "55_2_Timothy.txt",
            "56_Titus.txt",
            "57_Philemon.txt",
            "58_Hebrews.txt",
            "59_James.txt",
            "60_1_Peter.txt",
            "61_2_Peter.txt",
            "62_1_John.txt",
            "63_2_John.txt",
            "64_3_John.txt",
            "65_Jude.txt",
            "66_Revelation.txt",
        ]:
            try:
                open("/flash/bible/KJV/" + file_name).close()
            except OSError:
                continue

            yield file_name

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
        f = open("/flash/bible/KJV/" + file_name)
        location, length = self.read_header(f)[chapter - 1]
        return FileSegment(f, location, length)

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
