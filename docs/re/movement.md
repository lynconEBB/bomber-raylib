# Player movement in Super Bomberman 4 (battle mode)

Findings from the MesenCE harness (`tools/re/`), 2026-11-25. Addresses are WRAM (`$0300` = `$7E0300`)
or ROM (`C2:3660`). Player 1's struct is at `$0300` (player n at `$0300 + n*$100`).

## Summary

- **No acceleration or deceleration.** Full speed on the first tick of input; stops on the first tick without
  input, wherever it is (between tiles too). No automatic re-centering while idle.
- **Input latency:** input read on tick N moves the player on tick N+1.
- **Speed:** `position += SPEED_TABLE[speed_level][direction]` every tick (8.8 fixed point, see the main RE doc).
- **No geometric collider.** The player is a point; collision and corner correction come from lookup tables indexed
  by the point's position inside its tile. The net effect behaves like a diamond (a square rotated 45°) with an
  8 px radius against blocks: it stops at the tile center in front of a block, and corners are cut at 45°.
- **Corner correction ("cornering")** is in the direction tables: off-center movement turns into diagonal moves that
  re-center the player, and pushing into a pillar from the outer 4 px of a tile slides the player to the open lane.
- **Sprite:** one 32×32 hardware sprite at `(X − 16, Y − 24)`; the visible character is 16×24 px, spanning
  `X − 8 … X + 7` and `Y − 18 … Y + 5` (head about 10 px above the tile).

## Coordinates

- Position: X at `+$11` (fraction) / `+$12-$13` (pixels), Y at `+$15` / `+$16-$17`. 16.8 fixed point, screen pixels.
- The arena starts at screen (8, 24). Tile (col, row) covers X `16·col + 8 … +15` and Y `16·row + 24 … +15`.
- `sub = (X − 8) & 15` and `(Y − 8) & 15` = position inside the tile (0..15). **Centered = 7.**
  In arena-relative pixels that is simply `x & 15`, centered at 7, so an aligned position is `16·col + 7`.
- Current map cell: `col = (X + 8) / 16 − 1`, `row = (Y − 24) / 16` (`C2:3221`).

## Per-tick pipeline (player update, `X = $0300`)

1. **Neighbor scan** (`C2:4E63`): reads the 8 neighboring map cells. A neighbor counts as blocked unless empty;
   bombs (`$C900`) and soft blocks (`$CC80`) are recognized explicitly. Result: bitmask `+$82`,
   **bit n = direction n** (0 up, 1 up-right, 2 right, 3 down-right, 4 down, 5 down-left, 6 left, 7 up-left).
   A second mask goes to `+$86` (not decoded yet; likely bombs the player may pass through).
2. **Tile class** (`C2:4EFC`): from tile parity. `index = ((Y+8)&16)>>3 | ((X+8)&16)>>4`, class = `C2:4F25[index]`
   = `[1, 3, 0, 2]`, stored in `+$84`. Pillars sit on even/even tiles, so:
   - class 0: intersection (odd col, odd row) → table `C3:2C60`
   - class 1: vertical corridor (odd col, even row; pillars left and right) → table `C3:2D40`
   - class 2: horizontal corridor (even col, odd row; pillars above and below) → table `C3:2CD0`
   - class 3: pillar tile (unused) → table `C3:2C60`
3. **Zone** (`C2:3660`): `zone = ZONE[subY][subX]` from the 16×16 table at `C3:2520` (low nibble), stored in `+$83`.
4. **Input → direction** (`C2:3FD9`): d-pad bits in `+$31` (1 right, 2 left, 4 down, 8 up) through `C3:2C50`:
   `8 2 6 8 4 3 5 8 0 1 7 8 8 8 8 8` (opposite directions → 8 = stop; two directions → a diagonal).
5. **Final direction** (`C2:3FF0`): `out = DIR_TABLE[class][zone * 8 + input_dir]` → `+$60`. Low nibble = direction.
   High nibble n ≠ 0 means "only if neighbor n is free" (`C2:4036`): if bit n of `+$82` is set, direction = 8 (stop),
   and for classes ≠ 0 the fallback row (zone `d`) is used with the original input direction.
6. **Velocity** (`C2:2FC4`): `vx, vy = SPEED_TABLE[+$40][out] + (+$68, +$6A)` → `+$64`, `+$66`; then
   `X += vx; Y += vy` (`C2:57D4`).
7. **Collision push-back** (`C2:3341`): for each blocked orthogonal neighbor, using the sub-tile offset `s`:
   up or left blocked → `+max(0, 7 − s)` (`C3:2A20`); down or right blocked → `min(0, 7 − s)` (`C3:2A30`).
   The player can never be past the tile center toward a blocked tile.
8. **Intersection corners** (`C2:33CF`, class 0 only, when step 7 did nothing): correction `(dx, dy)` from
   `C3:2620[subY][subX]` (4 bytes per entry). It pushes the point back onto the diamond `|subX − 7| + |subY − 7| ≤ 7`
   along one axis: the four diagonal neighbors of an intersection are always pillars.
9. **Occupancy** (`C2:33FC`): when the cell changes, the player's bit (`+$90`) is ORed into another map layer.

### Zone table `C3:2520` (rows = subY, columns = subX, 0..15)

```
          0 1 2 3 4 5 6 7 8 9 a b c d e f
     0  7 7 7 7 7 7 7 8 0 0 0 0 0 0 0 1
     1  6 7 7 7 7 7 7 8 0 0 0 0 0 0 1 1
     2  6 6 7 7 7 7 7 8 0 0 0 0 0 1 1 1
     3  6 6 6 7 7 7 7 8 0 0 0 0 1 1 1 1
     4  6 6 6 6 7 7 7 c 0 0 0 1 1 1 1 1
     5  6 6 6 6 6 7 7 c 0 0 1 1 1 1 1 1
     6  6 6 6 6 6 6 7 c 0 1 1 1 1 1 1 1
     7  b b b b c c c c c c c 9 9 9 9 9
     8  5 5 5 5 5 5 5 c 2 2 2 2 2 2 2 2
     9  5 5 5 5 5 5 4 c 3 2 2 2 2 2 2 2
    10  5 5 5 5 5 4 4 c 3 3 2 2 2 2 2 2
    11  5 5 5 5 4 4 4 a 3 3 3 2 2 2 2 2
    12  5 5 5 4 4 4 4 a 3 3 3 3 2 2 2 2
    13  5 5 4 4 4 4 4 a 3 3 3 3 3 2 2 2
    14  5 4 4 4 4 4 4 a 3 3 3 3 3 3 2 2
    15  4 4 4 4 4 4 4 a 3 3 3 3 3 3 3 3
```

### Direction tables (rows = zone, columns = input direction)

**Intersection, `C3:2C60`**

| zone | U | UR | R | DR | D | DL | L | UL |
|---|---|---|---|---|---|---|---|---|
| 0 up-right, mostly up | U | U | DR | DR | D | DL | DL | U |
| 1 up-right, mostly right | UL | R | R | R | DL | DL | L | UL |
| 2 down-right, mostly right | UL | R | R | R | DL | DL | L | UL |
| 3 down-right, mostly down | U | UR | UR | D | D | D | UL | UL |
| 4 down-left, mostly down | U | UR | UR | D | D | D | UL | UL |
| 5 down-left, mostly left | UR | UR | R | DR | DR | L | L | L |
| 6 up-left, mostly left | UR | UR | R | DR | DR | L | L | L |
| 7 up-left, mostly up | U | U | DR | DR | D | DL | DL | U |
| 8 on vertical axis, above center | U | UR | DR | DR | D | DL | DL | UL |
| 9 on horizontal axis, right of center | UL | R | R | R | DL | DL | L | UL |
| a on vertical axis, below center | U | UR | UR | D | D | D | UL | UL |
| b on horizontal axis, left of center | UR | UR | R | DR | DR | L | L | L |
| c centered (±3 px on an axis) | U | UR | R | DR | D | DL | L | UL |
| d fallback row | U | UR | R | DR | D | DL | L | UL |

**Horizontal corridor (pillars above and below), `C3:2CD0`**

| zone | U | UR | R | DR | D | DL | L | UL |
|---|---|---|---|---|---|---|---|---|
| 0 up-right, mostly up | R (needs UR free) | R | R | R | R (needs DR free) | L | L | L |
| 1 up-right, mostly right | R (needs UR free) | R | R | R | R (needs DR free) | L | L | L |
| 2 down-right, mostly right | R (needs UR free) | R | R | R | R (needs DR free) | L | L | L |
| 3 down-right, mostly down | R (needs UR free) | R | R | R | R (needs DR free) | L | L | L |
| 4 down-left, mostly down | L (needs UL free) | R | R | R | L (needs DL free) | L | L | L |
| 5 down-left, mostly left | L (needs UL free) | R | R | R | L (needs DL free) | L | L | L |
| 6 up-left, mostly left | L (needs UL free) | R | R | R | L (needs DL free) | L | L | L |
| 7 up-left, mostly up | L (needs UL free) | R | R | R | L (needs DL free) | L | L | L |
| 8 on vertical axis, above center | L (needs UL free) | R | R | R | L (needs DL free) | L | L | L |
| 9 on horizontal axis, right of center | R (needs UR free) | R | R (needs R free) | R | R (needs DR free) | L | L | L |
| a on vertical axis, below center | R (needs UR free) | R | R | R | R (needs DR free) | L | L | L |
| b on horizontal axis, left of center | L (needs UL free) | R | R | R | L (needs DL free) | L | L (needs L free) | L |
| c centered (±3 px on an axis) | U | R | R | R | D | L | L (needs L free) | L |
| d fallback row | U | R | R | R | D | L | L | L |

**Vertical corridor (pillars left and right), `C3:2D40`**

| zone | U | UR | R | DR | D | DL | L | UL |
|---|---|---|---|---|---|---|---|---|
| 0 up-right, mostly up | U | U (needs UR free) | U (needs UR free) | D | D | D | U (needs UL free) | U |
| 1 up-right, mostly right | U | U (needs UR free) | U (needs UR free) | D | D | D | U (needs UL free) | U |
| 2 down-right, mostly right | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| 3 down-right, mostly down | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| 4 down-left, mostly down | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| 5 down-left, mostly left | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| 6 up-left, mostly left | U | U (needs UR free) | U (needs UR free) | D | D | D | U (needs UL free) | U |
| 7 up-left, mostly up | U | U (needs UR free) | U (needs UR free) | D | D | D | U (needs UL free) | U |
| 8 on vertical axis, above center | U | U (needs UR free) | U (needs UR free) | D | D | D | U (needs UL free) | U |
| 9 on horizontal axis, right of center | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| a on vertical axis, below center | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| b on horizontal axis, left of center | U | U | D (needs DR free) | D | D | D | D (needs DL free) | U |
| c centered (±3 px on an axis) | U | U (needs UR free) | R | D | D | D | L | U |
| d fallback row | U | U | R | D | D | D | L | U |

## Measured behavior (player 1, speed level 1 = 1 px/tick)

Hold Down from row 1 (aligned Y), starting X = column-1 center + d. Column 1 is open below; column 2 has a pillar below.

| d (px right of center) | Result |
|---|---|
| 0 | straight down |
| 1–7 | down, re-centering with diagonal steps along the way |
| 8–12 | slides left first (1 px/tick), then diagonal down-left until centered, then down |
| 13–16 | no movement (within 3 px of column 2's center, which has a pillar below) |

- Down+Right at an aligned intersection: one diagonal tick, then pushed back onto the open axis and continues right.
- Left+Right: no movement.
- Releasing input: stops immediately, even off-center.

## Sprite (`oamMode = 3`: sprites are 16×16 or 32×32)

- Player = one 32×32 OAM sprite, top-left at `(X − 16, Y − 24)`.
- Visible pixels: 16 wide × 24 tall (`X − 8 … X + 7`, `Y − 18 … Y + 5`), including the shadow.
- Horizontally the character fills exactly one tile; vertically it sits low in the tile with the head ~10 px above it.

## Option A: the same rules from real neighbors

The original infers pillars from tile parity, so on a map without the standard pillar grid it misbehaves (in an open area,
holding Right in an odd-column/even-row tile turns the player down after 4 px). Option A decides everything from the
actual neighbors. Per tick, with `blocked[n]` = neighbor n is not floor, `hard` = wall/pillar (`#`):

1. **Direction**
   - no input → stop.
   - two directions held → always move diagonally; the push-back below cancels only the blocked component, so the
     player keeps going diagonally until its body touches a wall, then slides along it. **Intentional change from the
     original** (which used its intersection table and turned early near walls).
   - one direction `I`, perpendicular offset `p` (dy for left/right, dx for up/down):
     - if `blocked[I]` and `|p| ≥ 4`: side `S` = the side of `p`; if the diagonal `I + S` is free → **corner slide**: move `S`.
       Else, if the tiles in front and behind along `I` are both **hard** → stop (a real corridor).
     - otherwise **lane alignment**: if the zone says the offset is mostly perpendicular, move diagonally (`I` + toward the
       lane center); else move straight `I`.
2. **Move** 1 step (speed table), then **push back** using the neighbors of the tile the point is now in:
   - wall clamp: up/left blocked → `max(0, 7 − sub)`, down/right blocked → `min(0, 7 − sub)`;
   - corner cut (only if no clamp and the point is off both center lines): if the diagonal neighbor of the point's
     quadrant is blocked → `C3:2620[subY][subX]`.

Tables kept as data: zone map (256 B) and corner table (1 KB).

**Verified equal to the original on standard arenas for no input and single directions:** 0 differences (every valid
position × those inputs × every soft-block arrangement around the player in each tile type, tiles next to the border,
and random walks). Two-direction input differs on purpose. Code: `tools/re/movement/` (`original.py`, `neighbors.py`, `verify.py`,
`compare_emulator.py`). Interactive explanation: `docs/re/movement.html`.

## New method: body shape + three tries (recommended)

A map-agnostic redesign, not tied to SB4's tables. Integers only (deterministic across PCs), no ROM tables.

- **Body = 16×16 pixel mask** (16 rows × 16 bits), pixel offsets −7…+8 around the position. Collision: for each
  solid tile overlapping the mask's bounding box, AND the mask rows with the overlapping column bits.
  Shapes: box, **octagon** (`|u| + |v| ≤ 9` with `u = i − 0.5`, `v = j − 0.5`), diamond (`≤ 8.5`), circle (`r ≈ 8.6`).
- **Per pixel of movement** (speed accumulates in 1/256 px; a diagonal step costs 362 = 256·√2):
  - one direction: forward → if blocked, find the nearest opening (smallest sideways shift ≤ *nudge reach* from which
    the body can go forward; equal on both sides = no opening) → diagonal toward it → sideways toward it → stop;
  - two directions: diagonal → else the free axis (preferring a turn: the axis not used last) → else the one-direction
    corner help of the held direction whose opening is closer → stop. Once corner help starts for a direction it is
    **committed** (stored in the body) until that direction gets through or the input changes; without this, a large
    nudge reach makes the help and the free-axis slide undo each other (measured: 348 oscillations at 12 px).
  - only a step that equals the held diagonal costs 362; every other step (wall slides, corner help) costs 256, so
    holding a diagonal is never faster than straight and never slower than the help it gets.
- Optional **lane centering**: while moving with the way open, if more off-center sideways than along, step
  diagonally toward the lane; when blocked with no opening, drift toward the tile center.

**Finding:** the original behaves like an **octagon body with a 6 px nudge reach**: holding a direction into an
opening from 0–16 px off-center gives exactly the original's tick counts (16 for 0–7 px, 17–21 for 8–12, stuck at 13+),
in both axes. Over random walks on standard arenas with single directions it sits at the identical position 86% of the
time; the rest comes from the original's lane centering (optional here, off by default).

Measured and dropped: box + nudge (must finish sliding before moving forward: +1 tick per px of offset) and a circle
pushed out of walls along the contact normal (sticky near the edge of an opening: 30 ticks at 7 px off).

**Audit** (`tools/re/movement/page/audit.js`, `audit_settings.js`): every position where the body fits × 8 inputs × both turn
preferences on 60 random maps (standard and open), for every shape and several nudge/centering/speed settings — about
100 million decisions: 0 cases of stopping while a held direction had an opening within reach, 0 oscillations.

Reference implementation (JavaScript, used by the page): `tools/re/movement/page/model.js` (`maskFits`, `shapeStep`,
`shapeSingleStep`, `shapeTick`). Rebuild the page with `python3 -I tools/re/movement/page/build.py`.

### Using raylib's `CheckCollisionCircleRec` instead of a mask

The method only needs "does the body fit here?", so the mask test can be replaced by raylib's circle-vs-rectangle check
against each solid tile (center = position + 1 px, so it matches the 16×16 body).
- Radius must be below 8 (`7.99f`): raylib counts touching as colliding (`<=`), so with 8 the body never fits a corridor.
- Floats are exact here: positions move in whole pixels, so the values stay small exact numbers. Verified: a `-march=native`
  (FMA) build and a generic build give identical answers for every position.
- Feel: identical to the pixel-mask circle; slower around corners than the octagon (e.g. 19 vs 16 ticks at 7 px off) and,
  with a 6 px reach, stuck from 11 px off instead of 13 (a 10 px reach extends it to 14 px).
- Audit: 0 stuck-with-help, 0 oscillations (reach 6 and 10).

