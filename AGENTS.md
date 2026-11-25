# BomberC

Bomberman-style game, **battle (arena) mode only**, written in **C23 + raylib** for **Linux and Windows**.
Mechanics (movement, timers, items, mounts) must match *Super Bomberman 4* (SFC), obtained through
reverse engineering. Art, sound and name are our own: we only take numbers from the ROM.

This is a learning project: the goal is to learn low-level game development and move away from object-oriented thinking.

## Rules

- Plain C, no OOP and no ECS: "fat structs" in fixed-size arrays. Simplicity over abstraction.
- One feature or architectural decision at a time, presented for review. Never implement whole stages at once.
- A single arena (green floor, gray walls). 5 players like the original for now; up to 8 later, with a larger 16:9 arena.
- Later: online rooms mixing local and remote players. A player's client hosts the game; no dedicated servers.
  Networking libraries are not chosen yet.
- Commit directly on `main`, and only when asked.

## Code conventions

- **ZII (Zero Is Initialization)**: the all-zero value of every struct is valid and means "empty/default".
  Enum value 0 is the default/none case. Functions behave correctly when given zeroed input.
  Builder functions return structs by value and return a zeroed struct on error (e.g. `tilemap_from_text`).
- Modules: one `.h` (types + prototypes) and one `.c`, functions named `module_verb(Struct *s, ...)`,
  private helpers `static`. Each module owns its drawing (`tilemap_draw`); there is no central render module.
- Debug toggles are `#define` flags checked with a plain `if (FLAG)`, not `#if`.
- Everything in the code is in English. Comments only for complex or non-intuitive code.

## What exists

- `src/`: `grid` (cell coordinates), `tilemap` (terrain, text parser, drawing),
  `maps` (arenas as text: `MAP_CLASSIC` 15×13 for 2–5 players, `MAP_WIDE` 23×13 for 6–8),
  `main.c` (window, loop; the game screen is always 16:9: the largest 16:9 rectangle that fits in the window
  is filled with the panel color, the arena render texture is fitted inside it, and anything outside is black).
- `CMakeLists.txt`: raylib 6.2 via FetchContent, Ninja Multi-Config generator.
  Build: `cmake --build build --config Debug` → `build/Debug/bomber`.
- `docs/roadmap.md`: stage checklist.
- `docs/re/super-bomberman-4.md`: reverse engineering findings (RAM map, tables, timers).
- `tools/re/`: reverse engineering harness with headless MesenCE (`/opt/mesence`, on PATH),
  `experiments.py` (reproducible experiments) and `dis65816.py` (disassembler). See `tools/re/README.md`.
- ROM: `~/Downloads/Super Bomberman 4 (Japan).sfc` (never commit it).
