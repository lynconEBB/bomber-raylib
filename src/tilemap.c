#include "tilemap.h"

#include <stdio.h>

#include "raylib.h"

#define DEBUG_DRAW_SPAWNS 1

static int spawn_index(char c)
{
    if (c >= '1' && c < '1' + TILEMAP_MAX_SPAWNS) {
        return c - '1';
    }
    return -1;
}

Tilemap tilemap_from_text(const char *text)
{
    Tilemap m = {0};
    if (text == NULL) {
        text = "";
    }

    bool spawn_seen[TILEMAP_MAX_SPAWNS] = {0};
    int x = 0;
    int y = 0;
    int w = 0;

    for (const char *c = text;; c++) {
        bool end_of_text = (*c == '\0');

        if (*c == '\n' || end_of_text) {
            if (x > 0) {
                if (y == 0) {
                    w = x;
                } else if (x != w) {
                    fprintf(stderr, "tilemap: line %d has %d columns, expected %d\n", y + 1, x, w);
                    return (Tilemap){0};
                }
                y++;
                x = 0;
            } else if (!end_of_text) {
                fprintf(stderr, "tilemap: line %d is empty\n", y + 1);
                return (Tilemap){0};
            }

            if (end_of_text) {
                break;
            }
            continue;
        }

        if (x >= GRID_MAX_W || y >= GRID_MAX_H) {
            fprintf(stderr, "tilemap: map larger than %dx%d\n", GRID_MAX_W, GRID_MAX_H);
            return (Tilemap){0};
        }

        TileType tile;
        switch (*c) {
        case '.': tile = TILE_FLOOR; break;
        case '#': tile = TILE_HARD; break;
        case '+': tile = TILE_SOFT; break;
        default: {
            int i = spawn_index(*c);
            if (i < 0) {
                fprintf(stderr, "tilemap: unknown character '%c' (line %d, column %d)\n", *c, y + 1, x + 1);
                return (Tilemap){0};
            }
            if (spawn_seen[i]) {
                fprintf(stderr, "tilemap: duplicate spawn %c (line %d, column %d)\n", *c, y + 1, x + 1);
                return (Tilemap){0};
            }
            spawn_seen[i] = true;
            m.spawns[i] = (GridPos){ (int16_t)x, (int16_t)y };
            tile = TILE_FLOOR;
        } break;
        }

        m.tiles[y][x] = tile;
        x++;
    }

    if (y == 0) {
        fprintf(stderr, "tilemap: empty map\n");
        return (Tilemap){0};
    }

    int count = 0;
    while (count < TILEMAP_MAX_SPAWNS && spawn_seen[count]) {
        count++;
    }
    for (int i = count; i < TILEMAP_MAX_SPAWNS; i++) {
        if (spawn_seen[i]) {
            fprintf(stderr, "tilemap: spawn %d exists but spawn %d is missing\n", i + 1, count + 1);
            return (Tilemap){0};
        }
    }

    m.w = (int16_t)w;
    m.h = (int16_t)y;
    m.spawn_count = (int16_t)count;
    return m;
}

bool tilemap_in_bounds(const Tilemap *m, GridPos p)
{
    return p.x >= 0 && p.y >= 0 && p.x < m->w && p.y < m->h;
}

TileType tilemap_get(const Tilemap *m, GridPos p)
{
    if (!tilemap_in_bounds(m, p)) {
        return TILE_HARD;
    }
    return m->tiles[p.y][p.x];
}

static const Color TILE_COLOR[TILE_MAX] = {
    [TILE_FLOOR] = {  56, 152,  56, 255 },
    [TILE_HARD]  = {  88,  88, 100, 255 },
    [TILE_SOFT]  = { 176, 176, 168, 255 },
};

void tilemap_draw(const Tilemap *m)
{
    for (int16_t y = 0; y < m->h; y++) {
        for (int16_t x = 0; x < m->w; x++) {
            TileType tile = m->tiles[y][x];
            int px = grid_cell_to_px(x);
            int py = grid_cell_to_px(y);
            Color color = TILE_COLOR[tile];

            DrawRectangle(px, py, TILE_SIZE, TILE_SIZE, color);
            if (tile != TILE_FLOOR) {
                DrawRectangleLines(px, py, TILE_SIZE, TILE_SIZE, ColorBrightness(color, -0.35f));
            }
        }
    }

    if (DEBUG_DRAW_SPAWNS) {
        for (int i = 0; i < m->spawn_count; i++) {
            GridPos p = m->spawns[i];
            int px = grid_cell_to_px(p.x);
            int py = grid_cell_to_px(p.y);
            DrawText(TextFormat("%d", i + 1), px + 5, py + 3, 10, WHITE);
        }
    }
}
