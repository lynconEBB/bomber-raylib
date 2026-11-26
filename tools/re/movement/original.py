"""The original SB4 movement algorithm, decoded from the ROM and verified tick by tick against the emulator."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dis65816 as D

ZONE = [b & 0x0F for b in D.rd(0xC32520, 256)]
DIRT = {0: list(D.rd(0xC32C60, 112)), 1: list(D.rd(0xC32D40, 112)), 2: list(D.rd(0xC32CD0, 112)), 3: list(D.rd(0xC32C60, 112))}
INPUT_DIR = list(D.rd(0xC32C50, 16))
_c = D.rd(0xC32620, 1024)
CORNER = [[(int.from_bytes(_c[(sy*16+sx)*4:(sy*16+sx)*4+2], 'little', signed=True),
            int.from_bytes(_c[(sy*16+sx)*4+2:(sy*16+sx)*4+4], 'little', signed=True)) for sx in range(16)] for sy in range(16)]
VEC = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, 0)]
CLASS_OF_INDEX = [1, 3, 0, 2]

# arena from the RAM dump at battle start ('#' hard, '+' soft, '.' floor)
MAP = """###############
#..++++.++++..#
#.#+#.#.#+#+#.#
#+++.+++++++++#
#.#+#+#+#+#+#+#
#.++++...+++.+#
#+#.#+#.#+#+#+#
#+++++...+.+++#
#+#+#+#+#+#+#+#
#.+.++++++++++#
#.#+#.#+#.#.#.#
#..+++++++++..#
###############""".split('\n')

def blocked(col, row):
    if row < 0 or row >= len(MAP) or col < 0 or col >= len(MAP[0]):
        return True
    return MAP[row][col] != '.'

def scan(ax, ay):
    col, row = ax >> 4, ay >> 4
    mask = 0
    for n, (dx, dy) in enumerate(VEC[:8]):
        if blocked(col + dx, row + dy):
            mask |= 1 << n
    index = ((row & 1) << 1) | (1 - (col & 1))
    return CLASS_OF_INDEX[index], mask

def tick(ax, ay, buttons):
    cls, mask = scan(ax, ay)
    zone = ZONE[(ay & 15) * 16 + (ax & 15)]
    bits = (8 if 'up' in buttons else 0) | (4 if 'down' in buttons else 0) | (2 if 'left' in buttons else 0) | (1 if 'right' in buttons else 0)
    din = INPUT_DIR[bits]
    d = 8
    if din != 8:
        out = DIRT[cls][zone * 8 + din]
        d, flag = out & 0x0F, out >> 4
        if flag and (mask >> flag) & 1:
            d = 8
            if cls != 0:
                d = DIRT[cls][13 * 8 + din] & 0x0F
    tx, ty = ax + VEC[d][0], ay + VEC[d][1]
    if (tx >> 4, ty >> 4) != (ax >> 4, ay >> 4):
        cls, mask = scan(tx, ty)
    sx, sy = tx & 15, ty & 15
    cx = cy = 0
    if mask & 0x01: cy = max(0, 7 - sy)
    if cy == 0 and mask & 0x10: cy = min(0, 7 - sy)
    if mask & 0x04: cx = min(0, 7 - sx)
    if cx == 0 and mask & 0x40: cx = max(0, 7 - sx)
    if cls == 0 and cx == 0 and cy == 0:
        cx, cy = CORNER[sy][sx]
    return tx + cx, ty + cy, d

def run(screen_x, screen_y, buttons, ticks):
    ax, ay = screen_x - 8, screen_y - 24
    path = [(ax + 8, ay + 24)]
    for _ in range(ticks):
        ax, ay, d = tick(ax, ay, buttons)
        path.append((ax + 8, ay + 24))
    return path
