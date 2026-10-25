"""Indexed zlib archives, using synthetic members and no game data."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import databin


class DatabinTests(unittest.TestCase):
    def archive(self, path, padding=0):
        a, b = zlib.compress(b'first member'), zlib.compress(b'second member')
        table = bytearray(0x9c)
        struct.pack_into('<4I', table, 0, 3, 28, 3, 0)
        struct.pack_into('<3I', table, 16, 0x40, 0x60, 0x80)
        struct.pack_into('<Q5I', table, 0x40, 0, 12, len(a), 0, 0, 0)
        struct.pack_into('<Q5I', table, 0x60, 0xffffffffffffffff, 0xffffffff, 0, 0, 0, 0)
        struct.pack_into('<Q5I', table, 0x80, len(a), 13, len(b), 0, 0, 0)
        path.write_bytes(databin.HEADER + struct.pack('<4I', 32, len(table), 0, 0) + table + bytes(padding) + a + b)
        return 32 + len(table) + padding, len(a), len(b)

    def test_members_with_and_without_payload_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive'
            for padding in (0, 0x10000 - 0xbc):
                with self.subTest(padding=padding):
                    start, na, nb = self.archive(path, padding)
                    es = databin.entries(path)
                    self.assertEqual(es, [(0, start, na, 12), (2, start + na, nb, 13)])
                    with path.open('rb') as f:
                        self.assertEqual([databin.read(f, e) for e in es], [b'first member', b'second member'])

    def test_other_format_and_truncated_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive'
            path.write_bytes(b'another format')
            self.assertIsNone(databin.entries(path))
            path.write_bytes(databin.HEADER)
            with self.assertRaisesRegex(ValueError, 'truncated.*header'):
                databin.entries(path)

    def test_index_bounds_and_member_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive'
            self.archive(path)
            data = bytearray(path.read_bytes())
            struct.pack_into('<I', data, 32 + 16, 0x9c)
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'record outside'):
                databin.entries(path)
            self.archive(path)
            es = databin.entries(path)
            with path.open('rb') as f:
                i, off, stored, length = es[0]
                with self.assertRaisesRegex(ValueError, 'entry says 13'):
                    databin.read(f, (i, off, stored, length + 1))
                with self.assertRaisesRegex(ValueError, 'entry 0'):
                    databin.read(f, (i, off, stored - 2, length))

    def test_nonzero_padding_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'archive'
            start, _, _ = self.archive(path, padding=16)
            data = bytearray(path.read_bytes()); data[start - 1] = 1
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'nonzero padding'):
                databin.entries(path)


if __name__ == '__main__':
    unittest.main()
