"""Neighbor-based movement rules (option A), plus an exhaustive comparison against the original algorithm."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import original as M

VEC = M.VEC
ZONE = M.ZONE
CORNER = M.CORNER
U, UR, R, DR, D, DL, L, UL, STOP = range(9)
VERTICAL_DOMINANT = {0, 3, 4, 7, 8, 10}    # zones where |dy| >= |dx| (off-center mostly vertically)
HORIZONTAL_DOMINANT = {1, 2, 5, 6, 9, 11}  # zones where |dx| > |dy|
# Two-direction input intentionally differs from the original (always diagonal, collisions decide),
# so equivalence is only checked for no input and single directions.
DIRECTIONS_TO_COMPARE = (U, R, D, L, STOP)


def combine(vertical, horizontal):
    return {(U, R): UR, (D, R): DR, (D, L): DL, (U, L): UL}[(vertical, horizontal)]


def neighbors(grid, col, row):
    return [grid_blocked(grid, col + VEC[n][0], row + VEC[n][1]) for n in range(8)]


def is_hard(grid, col, row):
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
        return True
    return grid[row][col] == '#'


def grid_blocked(grid, col, row):
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
        return True
    return grid[row][col] != '.'


def decide(grid, x, y, din, variant):
    col, row = x >> 4, y >> 4
    blocked = neighbors(grid, col, row)
    sx, sy = x & 15, y & 15
    dx, dy = sx - 7, sy - 7
    zone = ZONE[sy * 16 + sx]

    if din == STOP:
        return STOP, 'no input'

    if din in (UR, DR, DL, UL):
        return din, 'diagonal'

    horizontal_move = din in (R, L)
    perp = dy if horizontal_move else dx
    if blocked[din] and abs(perp) >= 4:
        side = (U if perp < 0 else D) if horizontal_move else (L if perp < 0 else R)
        diagonal = combine(side, din) if horizontal_move else combine(din, side)
        if not blocked[diagonal]:
            return side, 'corner slide'
        if variant == 'stop':
            return STOP, 'blocked, no slide'
        if variant == 'stop_if_axis_closed':
            opposite = (din + 4) % 8
            if blocked[opposite]:
                return STOP, 'blocked, no slide'
        if variant == 'stop_in_solid_corridor':
            opposite = (din + 4) % 8
            if is_hard(grid, col + VEC[din][0], row + VEC[din][1]) and is_hard(grid, col + VEC[opposite][0], row + VEC[opposite][1]):
                return STOP, 'solid corridor, no slide'

    dominant = VERTICAL_DOMINANT if horizontal_move else HORIZONTAL_DOMINANT
    if zone in dominant:
        toward_center = (D if perp < 0 else U) if horizontal_move else (R if perp < 0 else L)
        if horizontal_move:
            return combine(toward_center, din), 'lane alignment'
        return combine(din, toward_center), 'lane alignment'
    return din, 'straight'


def push(grid, x, y):
    col, row = x >> 4, y >> 4
    blocked = neighbors(grid, col, row)
    sx, sy = x & 15, y & 15
    cx = cy = 0
    if blocked[U]: cy = max(0, 7 - sy)
    if cy == 0 and blocked[D]: cy = min(0, 7 - sy)
    if blocked[R]: cx = min(0, 7 - sx)
    if cx == 0 and blocked[L]: cx = max(0, 7 - sx)
    if cx == 0 and cy == 0 and (sx != 7 and sy != 7):
        quadrant = (UR if sy < 7 else DR) if sx > 7 else (UL if sy < 7 else DL)
        if blocked[quadrant]:
            cx, cy = CORNER[sy][sx]
    return cx, cy


def tick(grid, x, y, din, variant='realign'):
    d, why = decide(grid, x, y, din, variant)
    tx, ty = x + VEC[d][0], y + VEC[d][1]
    cx, cy = push(grid, tx, ty)
    return tx + cx, ty + cy, d, why


# ---------- original algorithm on the same grid ----------
def original_tick(grid, x, y, din):
    M.MAP = [''.join(r) for r in grid]
    bits = {U: 8, D: 4, L: 2, R: 1, UR: 9, DR: 5, DL: 6, UL: 10, STOP: 0}[din]
    buttons = []
    if bits & 8: buttons.append('up')
    if bits & 4: buttons.append('down')
    if bits & 2: buttons.append('left')
    if bits & 1: buttons.append('right')
    nx, ny, d = M.tick(x, y, buttons)
    return nx, ny


def standard_grid(width=13, height=11):
    grid = []
    for row in range(height):
        line = []
        for col in range(width):
            border = row in (0, height - 1) or col in (0, width - 1)
            pillar = col % 2 == 0 and row % 2 == 0
            line.append('#' if border or pillar else '.')
        grid.append(line)
    return grid


def valid_positions(grid, col, row):
    out = []
    for sy in range(16):
        for sx in range(16):
            x, y = col * 16 + sx, row * 16 + sy
            # a position the game can rest at: the original push-back leaves it where it is
            M.MAP = [''.join(r) for r in grid]
            nx, ny, _ = M.tick(x, y, [])
            if (nx, ny) == (x, y):
                out.append((x, y))
    return out


def compare(variant, samples_per_inner=24, seed=1):
    rng = random.Random(seed)
    total = mismatches = 0
    examples = {}
    for label, (col, row) in (('intersection', (5, 5)), ('vertical corridor', (5, 4)), ('horizontal corridor', (4, 5))):
        base = standard_grid()
        inner = [(col + VEC[n][0], row + VEC[n][1]) for n in range(8)]
        inner = [(c, r) for c, r in inner if base[r][c] == '.']
        outer = [(c, r) for r in range(row - 2, row + 3) for c in range(col - 2, col + 3)
                 if base[r][c] == '.' and (c, r) not in inner and (c, r) != (col, row)]
        for bits in range(1 << len(inner)):
            for sample in range(samples_per_inner):
                grid = [line[:] for line in base]
                for i, (c, r) in enumerate(inner):
                    if bits >> i & 1:
                        grid[r][c] = '+'
                for (c, r) in outer:
                    if rng.random() < 0.5:
                        grid[r][c] = '+'
                for (x, y) in valid_positions(grid, col, row):
                    for din in DIRECTIONS_TO_COMPARE:
                        a = original_tick(grid, x, y, din)
                        b = tick(grid, x, y, din, variant)[:2]
                        total += 1
                        if a != b:
                            mismatches += 1
                            key = (label, tick(grid, x, y, din, variant)[3])
                            examples.setdefault(key, (x & 15, y & 15, din, a, b))
    return total, mismatches, examples


if __name__ == '__main__':
    variant = sys.argv[1] if len(sys.argv) > 1 else 'realign'
    total, bad, examples = compare(variant, samples_per_inner=int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    print('variant %-20s ticks compared: %d  mismatches: %d (%.3f%%)' % (variant, total, bad, 100.0 * bad / total))
    names = ['U', 'UR', 'R', 'DR', 'D', 'DL', 'L', 'UL', 'none']
    for (label, why), (sx, sy, din, a, b) in sorted(examples.items()):
        print('   %-20s rule=%-18s e.g. sub=(%d,%d) input=%s original->%s new->%s' % (label, why, sx, sy, names[din], a, b))
