import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import neighbors as G

VARIANT = 'stop_in_solid_corridor'
names = ['U', 'UR', 'R', 'DR', 'D', 'DL', 'L', 'UL', 'none']

def border_tiles_check(samples=6, seed=7):
    rng = random.Random(seed)
    tiles = [('corner intersection (1,1)', (1, 1)), ('vertical corridor (1,2)', (1, 2)), ('horizontal corridor (2,1)', (2, 1)),
             ('corner intersection (11,9)', (11, 9)), ('vertical corridor (11,8)', (11, 8)), ('horizontal corridor (10,9)', (10, 9))]
    total = bad = 0
    for label, (col, row) in tiles:
        base = G.standard_grid()
        cells = [(c, r) for r in range(row - 2, row + 3) for c in range(col - 2, col + 3)
                 if 0 <= r < len(base) and 0 <= c < len(base[0]) and base[r][c] == '.' and (c, r) != (col, row)]
        for _ in range(64 * samples):
            grid = [line[:] for line in base]
            for (c, r) in cells:
                if rng.random() < 0.5:
                    grid[r][c] = '+'
            for (x, y) in G.valid_positions(grid, col, row):
                for din in G.DIRECTIONS_TO_COMPARE:
                    a = G.original_tick(grid, x, y, din)
                    b = G.tick(grid, x, y, din, VARIANT)[:2]
                    total += 1
                    if a != b:
                        bad += 1
                        if bad < 5:
                            print('  border mismatch', label, (x & 15, y & 15), names[din], a, b)
    print('border tiles: %d ticks compared, %d mismatches' % (total, bad))

def random_walks(walks=400, ticks=300, seed=11):
    rng = random.Random(seed)
    total = bad_walks = 0
    for w in range(walks):
        grid = G.standard_grid()
        for r in range(1, len(grid) - 1):
            for c in range(1, len(grid[0]) - 1):
                if grid[r][c] == '.' and rng.random() < 0.35:
                    grid[r][c] = '+'
        grid[1][1] = '.'
        x, y = 16 + 7, 16 + 7
        ox, oy = x, y
        din = rng.choice(G.DIRECTIONS_TO_COMPARE)
        for t in range(ticks):
            if rng.random() < 0.08:
                din = rng.choice(G.DIRECTIONS_TO_COMPARE)
            ox, oy = G.original_tick(grid, ox, oy, din)
            x, y = G.tick(grid, x, y, din, VARIANT)[:2]
            total += 1
            if (ox, oy) != (x, y):
                bad_walks += 1
                print('  walk %d diverged at tick %d: original=%s new=%s' % (w, t, (ox, oy), (x, y)))
                break
    print('random walks: %d walks, %d ticks, %d walks diverged' % (walks, total, bad_walks))

border_tiles_check()
random_walks()
