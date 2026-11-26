import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emulator_trial import trial
from original import run

def emu_path(rows):
    # positions from the first moving frame on (movement starts after the post-load delay)
    pos = [(int(x), int(y)) for f, x, y, d, vx, vy, t in rows]
    start = 0
    while start + 1 < len(pos) and pos[start + 1] == pos[start]:
        start += 1
    return pos[start:]

def compare(label, sx, sy, buttons):
    rows = trial(x=sx, y=sy, holds=[(3, 80, buttons)], frames=60, name='cmp')
    emu = emu_path(rows)
    model = run(sx, sy, buttons, len(emu) - 1)
    ok = emu == model
    if not ok:
        first = next(i for i in range(len(emu)) if emu[i] != model[i])
        print('MISMATCH %-28s tick %d emu=%s model=%s' % (label, first, emu[first - 1:first + 3], model[first - 1:first + 3]))
    return ok

results = []
for d in range(17):
    results.append(compare('down d=%d' % d, 31 + d, 47, ['down']))
for d in range(17):
    results.append(compare('right d=%d' % d, 31, 47 + d, ['right']))
results.append(compare('down+right aligned', 31, 47, ['down', 'right']))
results.append(compare('down+right +4', 35, 47, ['down', 'right']))
results.append(compare('left+right', 31, 47, ['left', 'right']))
results.append(compare('right from spawn', 32, 48, ['right']))
results.append(compare('up from (31,63)', 31, 63, ['up']))
results.append(compare('left from (47,47)', 47, 47, ['left']))
print('%d / %d scenarios match the emulator exactly' % (sum(results), len(results)))
