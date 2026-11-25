#include "grid.h"

int32_t grid_cell_to_px(int16_t cell)
{
    return (int32_t)cell * TILE_SIZE;
}

int16_t grid_px_to_cell(int32_t px)
{
    return (int16_t)(px / TILE_SIZE);
}
