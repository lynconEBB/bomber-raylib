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
    Tilemap tilemap = {0};
    if (text == NULL) {
        text = "";
    }

    bool spawn_seen[TILEMAP_MAX_SPAWNS] = {0};
    int x = 0;
    int y = 0;
    int width = 0;

    for (const char *c = text; *c != '\0'; c++) {
        if (*c == '\n') {
            if (x == 0) {
                fprintf(stderr, "tilemap: line %d is empty\n", y + 1);
                return (Tilemap){0};
            }
            if (y == 0) {
                width = x;
            } else if (x != width) {
                fprintf(stderr, "tilemap: line %d has %d columns, expected %d\n", y + 1, x, width);
                return (Tilemap){0};
            }
            y++;
            x = 0;
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
            int spawn = spawn_index(*c);
            if (spawn < 0) {
                fprintf(stderr, "tilemap: unknown character '%c' (line %d, column %d)\n", *c, y + 1, x + 1);
                return (Tilemap){0};
            }
            if (spawn_seen[spawn]) {
                fprintf(stderr, "tilemap: duplicate spawn %c (line %d, column %d)\n", *c, y + 1, x + 1);
                return (Tilemap){0};
            }
            spawn_seen[spawn] = true;
            tilemap.spawns[spawn] = (GridPos){ (int16_t)x, (int16_t)y };
            tile = TILE_FLOOR;
        } break;
        }

        tilemap.tiles[y][x] = tile;
        x++;
    }

    if (x != 0) {
        fprintf(stderr, "tilemap: line %d does not end with a newline\n", y + 1);
        return (Tilemap){0};
    }
    if (y == 0) {
        fprintf(stderr, "tilemap: empty map\n");
        return (Tilemap){0};
    }

    int spawn_count = 0;
    while (spawn_count < TILEMAP_MAX_SPAWNS && spawn_seen[spawn_count]) {
        spawn_count++;
    }
    for (int spawn = spawn_count; spawn < TILEMAP_MAX_SPAWNS; spawn++) {
        if (spawn_seen[spawn]) {
            fprintf(stderr, "tilemap: spawn %d exists but spawn %d is missing\n", spawn + 1, spawn_count + 1);
            return (Tilemap){0};
        }
    }

    tilemap.width = (int16_t)width;
    tilemap.height = (int16_t)y;
    tilemap.spawn_count = (int16_t)spawn_count;
    return tilemap;
}

bool tilemap_in_bounds(const Tilemap *tilemap, GridPos pos)
{
    return pos.x >= 0 && pos.y >= 0 && pos.x < tilemap->width && pos.y < tilemap->height;
}

TileType tilemap_get(const Tilemap *tilemap, GridPos pos)
{
    if (!tilemap_in_bounds(tilemap, pos)) {
        return TILE_HARD;
    }
    return tilemap->tiles[pos.y][pos.x];
}

static const Color TILE_COLOR[TILE_MAX] = {
    [TILE_FLOOR] = {  56, 152,  56, 255 },
    [TILE_HARD]  = {  88,  88, 100, 255 },
    [TILE_SOFT]  = { 176, 176, 168, 255 },
};

void tilemap_draw(const Tilemap *tilemap)
{
    for (int16_t y = 0; y < tilemap->height; y++) {
        for (int16_t x = 0; x < tilemap->width; x++) {
            TileType tile = tilemap->tiles[y][x];
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
        for (int spawn = 0; spawn < tilemap->spawn_count; spawn++) {
            GridPos spawn_pos = tilemap->spawns[spawn];
            int px = grid_cell_to_px(spawn_pos.x);
            int py = grid_cell_to_px(spawn_pos.y);
            DrawText(TextFormat("%d", spawn + 1), px + 5, py + 3, 10, WHITE);
        }
    }
}
