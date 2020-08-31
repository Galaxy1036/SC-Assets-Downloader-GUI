# -*- coding: utf-8 -*-
import zlib

from io import BytesIO


class Reader(BytesIO):

    def read_byte(self):
        return int.from_bytes(self.read(1), 'big')

    def read_int(self):
        return int.from_bytes(self.read(4), 'big')

    def read_vint(self):
        shift = 0
        result = 0

        while True:
            i = self.read_byte()

            if shift == 0:
                seventh = (i & 0x40) >> 6  # save 7th bit
                msb = (i & 0x80) >> 7  # save msb
                i <<= 1  # rotate to the left
                i &= ~(0x181)  # clear 8th and 1st bit and 9th if any
                i |= (msb << 7) | (seventh)  # insert msb and 6th back in

            result |= (i & 0x7f) << shift
            shift += 7

            if not i & 0x80:
                break

        return ((result) >> 1) ^ (-((result) & 1))

    def read_string(self):
        length = self.read_int()

        if length != 0xffffffff:
            return self.read(length).decode('utf-8')

    def read_compressed_string(self):
        length = self.read_int()

        if length != 0xffffffff:
            zlength = int.from_bytes(self.read(4), 'little')
            return zlib.decompress(self.read(length - 4), 15, zlength).decode('utf-8')
