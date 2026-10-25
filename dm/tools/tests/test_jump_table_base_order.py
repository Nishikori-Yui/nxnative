"""Exercise jump-table recognition when the dispatch precedes its table setup."""
import ast
from pathlib import Path
import re
import struct
import sys
import unittest

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from nso_asm import ADDI, ADRP, NOP

tree = ast.parse((TOOLS / 'patch_nso.py').read_text())
FUNCS = {'num', 'regset', 'jump_offsets', 'check_before_copy', 'table_base', 'copied_base', 'table_cands'}
body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCS]


def jump_image(ambiguous=False):
    image = bytearray(0x500)
    start, table = 0x100, 0x300
    words = [
        0x7100265f,  # cmp w18, #9
        0x54000848,  # b.hi
        0xb8b27a32,  # ldrsw x18, [x17, x18, lsl #2]
        0x8b110252,  # add x18, x18, x17
        0xd61f0240,  # br x18
        NOP,
        NOP,
        NOP,
        ADRP(17, 0x120, table),
        ADDI(17, 17, table & 0xfff),
    ]
    struct.pack_into('<' + 'I' * len(words), image, start, *words)
    struct.pack_into('<10i', image, table, *(start + 4 * i - table for i in range(10)))
    if ambiguous:
        struct.pack_into('<II', image, 0x12c, ADRP(17, 0x12c, 0x400), ADDI(17, 17, 0x400))
        struct.pack_into('<10i', image, 0x400, *(start + 4 * i - 0x400 for i in range(10)))
    return image


def rewrite_targets(image):
    scope = {'re': re, 'struct': struct, 'IMG': image}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(TOOLS / 'patch_nso.py'), 'exec'), scope)
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    ins = list(md.disasm(image[0x100:0x134], 0x100))
    return scope['jump_offsets'](ins, len(ins) - 1, far_base=True)


class JumpTableBaseOrder(unittest.TestCase):
    def test_dispatch_before_table_setup(self):
        self.assertEqual(rewrite_targets(jump_image()), [0x100 + 4 * i for i in range(10)])

    def test_ambiguous_later_table_is_rejected(self):
        self.assertIsNone(rewrite_targets(jump_image(ambiguous=True)))


if __name__ == '__main__':
    unittest.main()
