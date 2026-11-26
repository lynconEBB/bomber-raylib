import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mesen

TRIAL_LUA = r"""
local WRAM = emu.memType.snesWorkRam
local SET_X, SET_Y = %(x)s, %(y)s
%(holds)s
emu.addEventCallback(function()
  frame = frame + 1
  if loaded and frame == 1 and SET_X >= 0 then
    emu.write(0x311, 0, WRAM); emu.write(0x312, SET_X %% 256, WRAM); emu.write(0x313, SET_X // 256, WRAM)
    emu.write(0x315, 0, WRAM); emu.write(0x316, SET_Y %% 256, WRAM); emu.write(0x317, SET_Y // 256, WRAM)
  end
  if loaded and frame >= 1 and frame <= %(frames)d then
    local x = emu.read(0x311, WRAM) + emu.read(0x312, WRAM) * 256 + emu.read(0x313, WRAM) * 65536
    local y = emu.read(0x315, WRAM) + emu.read(0x316, WRAM) * 256 + emu.read(0x317, WRAM) * 65536
    print(string.format('@POS %%d %%d %%d %%d %%d %%d %%d', frame, x, y, emu.read(0x360, WRAM), emu.read16(0x364, WRAM), emu.read16(0x366, WRAM), emu.read(0x170, WRAM)))
  end
  if loaded and frame >= %(frames)d then emu.stop(0) end
end, emu.eventType.endFrame)
"""

def trial(x=-1, y=-1, holds=(), frames=50, name='trial'):
    h = '\n'.join('hold(%d, %d, 0, {%s})' % (a, b, ', '.join('%s=true' % k for k in keys)) for a, b, keys in holds)
    body = TRIAL_LUA % {'x': x, 'y': y, 'holds': h, 'frames': frames}
    r = mesen.run_from_state('battle_start', body, name=name)
    rows = []
    for l in r['LOG']:
        if l.startswith('@POS'):
            f, px, py, d, vx, vy, tick = map(int, l.split()[1:])
            s16 = lambda v: v - 65536 if v >= 32768 else v
            rows.append((f, px / 256, py / 256, d, s16(vx) / 256, s16(vy) / 256, tick))
    return rows

def show(rows, every=1, start=1):
    prev_tick = None
    for f, px, py, d, vx, vy, tick in rows:
        if f >= start and (f - start) % every == 0:
            print('  f%3d X=%7.3f (0x%05.1f) Y=%7.3f dir=%d v=(%+.3f,%+.3f)%s' % (f, px, px, py, d, vx, vy, '' if tick != prev_tick else '  [lag]'))
        prev_tick = tick

if __name__ == '__main__':
    print('A) natural spawn, hold Down 3..40')
    show(trial(holds=[(3, 40, ['down'])], frames=30), every=1)
