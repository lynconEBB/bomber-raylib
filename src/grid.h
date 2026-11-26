#pragma once

#include <stdint.h>

#define TILE_SIZE 16

#define GRID_MAX_W 32
#define GRID_MAX_H 32

typedef struct {
    int16_t x, y;
} GridPos;

int32_t grid_cell_to_px(int16_t cell);
int32_t grid_cell_center_px(int16_t cell);
int16_t grid_px_to_cell(int32_t px);
