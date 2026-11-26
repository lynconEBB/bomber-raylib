#pragma once

#include <stdint.h>

// 1/256 px per tick: 256 moves one pixel every tick.
#define PLAYER_START_SPEED 256

// Below half a tile because raylib counts touching as colliding: with exactly 8 the body would not fit a corridor.
#define BODY_RADIUS 7.99f

typedef enum : uint8_t {
    ENTITY_NONE,
    ENTITY_PLAYER,
} EntityKind;

typedef enum : uint8_t {
    AXIS_X,
    AXIS_Y,
} Axis;

typedef struct {
    EntityKind kind;

    // Center of the body in pixels; a body centered on a tile is at grid_cell_center_px.
    int16_t x, y;

    uint16_t speed;
    uint16_t move_progress;
    Axis last_step_axis;
    int8_t input_dx, input_dy;
    int8_t corner_help_dx, corner_help_dy;
} Entity;

void entity_draw(const Entity *entity);
