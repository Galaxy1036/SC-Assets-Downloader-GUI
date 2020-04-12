# -*- coding: utf-8 -*-

from io import BytesIO


class Writer(BytesIO):

    @property
    def buffer(self):
        return self.getvalue()

    def write_int(self, value):
        self.write(value.to_bytes(4, 'big'))

    def write_string(self, value=None):
        if value is not None:
            encoded = value.encode('utf-8')

            self.write_int(len(encoded))
            self.write(encoded)

        else:
            self.write_int(0xffffffff)
