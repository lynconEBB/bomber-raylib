#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "grid.h"

#define TILEMAP_MAX_SPAWNS 8

typedef enum : uint8_t {
    TILE_FLOOR,
    TILE_HARD,
    TILE_SOFT,
    TILE_MAX
} TileType;

typedef struct {
    int16_t width, height;
    TileType tiles[GRID_MAX_H][GRID_MAX_W];
    int16_t spawn_count;
    GridPos spawns[TILEMAP_MAX_SPAWNS];
} Tilemap;

// Returns a zeroed (empty) Tilemap on error.
Tilemap tilemap_from_text(const char *text);

bool tilemap_in_bounds(const Tilemap *tilemap, GridPos pos);

// Out of bounds returns TILE_HARD.
TileType tilemap_get(const Tilemap *tilemap, GridPos pos);

void tilemap_draw(const Tilemap *tilemap);
