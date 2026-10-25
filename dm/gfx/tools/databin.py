"""Team Ninja's indexed zlib archives (NINJA GAIDEN Sigma's databin and patchbin)."""
import os
import struct
import zlib

HEADER = struct.pack('<4I', 1, 24, 1, 0)


def entries(path):
    """Return (index, file offset, stored length, length) rows, or None for another format.

    The header names an index at +0x10 with its length at +0x14. The index starts
    with a count, a map offset, the count again and zero, then relative u32 record
    offsets. Each 28-byte record holds u64 data offset, u32 length, stored length
    and three metadata words. Data offsets are relative to the payload, whose
    last entry ends at EOF: the base archive has no padding before it, patchbin
    pads to 64 KB. Empty entries use offset -1; a zero-length zlib member needs
    no decoding (the base archive holds one with a six-byte stream).
    """
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        h = f.read(32)
        if h[:16] != HEADER: return None
        if len(h) != 32: raise ValueError('truncated databin header')
        off, length = struct.unpack_from('<II', h, 16)
        if off < 32 or length < 16 or off + length > size: raise ValueError('databin index outside the file')
        f.seek(off); table = f.read(length)
        n, mapping, count, reserved = struct.unpack_from('<4I', table)
        if n != count or reserved or not 16 + 4 * n <= mapping <= length:
            raise ValueError('invalid databin index')
        out = []
        for i in range(n):
            rec = struct.unpack_from('<I', table, 16 + 4 * i)[0]
            if rec < 16 + 4 * n or rec + 28 > length: raise ValueError(f'databin entry {i}: record outside the index')
            data, raw, stored = struct.unpack_from('<QII', table, rec)
            if data == 0xffffffffffffffff: continue
            if not stored and raw: raise ValueError(f'databin entry {i}: no stored data')
            out.append((i, data, stored, raw))
        base = size - max((a + c for _, a, c, _ in out), default=0)
        if base < off + length: raise ValueError('databin payload overlaps its index')
        f.seek(off + length)
        if any(f.read(base - off - length)): raise ValueError('nonzero padding before databin payload')
    return [(i, base + a, c, n) for i, a, c, n in out if n]


def read(f, entry):
    i, off, stored, length = entry
    f.seek(off); data = f.read(stored)
    try: out = zlib.decompress(data)
    except zlib.error as e: raise ValueError(f'databin entry {i}: {e}') from e
    if len(out) != length: raise ValueError(f'databin entry {i}: {len(out)} bytes decoded, the entry says {length}')
    return out
