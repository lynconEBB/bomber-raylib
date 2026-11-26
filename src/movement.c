#include "movement.h"

#include <stdlib.h>

#include "input.h"
#include "raylib.h"

#define STEP_COST 256
// 256 * sqrt(2): a diagonal pixel step covers more distance than a straight one.
#define DIAGONAL_STEP_COST 362
#define NUDGE_REACH 6

typedef struct {
    int8_t dx, dy;
    bool corner;
} Step;

static bool body_fits(const Tilemap *tilemap, int32_t x, int32_t y)
{
    Vector2 center = { (float)x, (float)y };
    int16_t first_col = grid_px_to_cell(x - TILE_SIZE / 2);
    int16_t last_col = grid_px_to_cell(x + TILE_SIZE / 2);
    int16_t first_row = grid_px_to_cell(y - TILE_SIZE / 2);
    int16_t last_row = grid_px_to_cell(y + TILE_SIZE / 2);

    for (int16_t row = first_row; row <= last_row; row++) {
        for (int16_t col = first_col; col <= last_col; col++) {
            if (!tilemap_is_solid(tilemap, (GridPos){ col, row })) {
                continue;
            }
            Rectangle tile = { (float)grid_cell_to_px(col), (float)grid_cell_to_px(row), TILE_SIZE, TILE_SIZE };
            if (CheckCollisionCircleRec(center, BODY_RADIUS, tile)) {
                return false;
            }
        }
    }
    return true;
}

static bool fits_after(const Tilemap *tilemap, const Entity *entity, int dx, int dy)
{
    return body_fits(tilemap, entity->x + dx, entity->y + dy);
}

// Distance to the nearest opening beside an obstacle: the body can slide that many pixels sideways (fitting at
// every pixel) and then step forward. Signed toward the side; 0 if none is within reach or both sides tie.
static int nearest_opening(const Tilemap *tilemap, const Entity *entity, int forward_dx, int forward_dy)
{
    int side_dx = forward_dy != 0;
    int side_dy = forward_dx != 0;
    bool negative_open = true;
    bool positive_open = true;

    for (int distance = 1; distance <= NUDGE_REACH; distance++) {
        int negative_dx = -side_dx * distance, negative_dy = -side_dy * distance;
        int positive_dx = side_dx * distance, positive_dy = side_dy * distance;

        negative_open = negative_open && fits_after(tilemap, entity, negative_dx, negative_dy);
        positive_open = positive_open && fits_after(tilemap, entity, positive_dx, positive_dy);
        bool negative_passes = negative_open
            && fits_after(tilemap, entity, negative_dx + forward_dx, negative_dy + forward_dy);
        bool positive_passes = positive_open
            && fits_after(tilemap, entity, positive_dx + forward_dx, positive_dy + forward_dy);

        if (negative_passes && positive_passes) return 0;
        if (negative_passes) return -distance;
        if (positive_passes) return distance;
        if (!negative_open && !positive_open) return 0;
    }
    return 0;
}

static Step single_direction_step(const Tilemap *tilemap, const Entity *entity, int dx, int dy)
{
    if (fits_after(tilemap, entity, dx, dy)) {
        return (Step){ dx, dy, false };
    }

    int opening = nearest_opening(tilemap, entity, dx, dy);
    if (opening == 0) {
        return (Step){ 0 };
    }

    int side = opening > 0 ? 1 : -1;
    int side_dx = dy != 0 ? side : 0;
    int side_dy = dx != 0 ? side : 0;
    if (fits_after(tilemap, entity, dx + side_dx, dy + side_dy)) {
        return (Step){ dx + side_dx, dy + side_dy, true };
    }
    if (fits_after(tilemap, entity, side_dx, side_dy)) {
        return (Step){ side_dx, side_dy, true };
    }
    return (Step){ 0 };
}

static bool step_moves(Step step)
{
    return step.dx != 0 || step.dy != 0;
}

static Step two_direction_step(const Tilemap *tilemap, Entity *entity, int dx, int dy)
{
    if (fits_after(tilemap, entity, dx, dy)) {
        entity->corner_help_dx = 0;
        entity->corner_help_dy = 0;
        return (Step){ dx, dy, false };
    }

    // Keep helping the same direction around a corner; switching every step would shake back and forth.
    if (entity->corner_help_dx != 0 || entity->corner_help_dy != 0) {
        Step step = single_direction_step(tilemap, entity, entity->corner_help_dx, entity->corner_help_dy);
        if (step_moves(step)) {
            if (!step.corner) {
                entity->corner_help_dx = 0;
                entity->corner_help_dy = 0;
            }
            return step;
        }
        entity->corner_help_dx = 0;
        entity->corner_help_dy = 0;
    }

    // The axis not moved along last goes first, so holding a diagonal takes the next turn.
    Step singles[2] = { { 0, dy, false }, { dx, 0, false } };
    if (entity->last_step_axis == AXIS_Y) {
        singles[0] = (Step){ dx, 0, false };
        singles[1] = (Step){ 0, dy, false };
    }
    for (int index = 0; index < 2; index++) {
        if (fits_after(tilemap, entity, singles[index].dx, singles[index].dy)) {
            return singles[index];
        }
    }

    int distances[2];
    for (int index = 0; index < 2; index++) {
        distances[index] = abs(nearest_opening(tilemap, entity, singles[index].dx, singles[index].dy));
    }
    int order[2] = { 0, 1 };
    if (distances[1] != 0 && (distances[0] == 0 || distances[1] < distances[0])) {
        order[0] = 1;
        order[1] = 0;
    }
    for (int index = 0; index < 2; index++) {
        Step help = singles[order[index]];
        if (distances[order[index]] == 0) {
            continue;
        }
        Step step = single_direction_step(tilemap, entity, help.dx, help.dy);
        if (step_moves(step)) {
            if (step.corner) {
                entity->corner_help_dx = help.dx;
                entity->corner_help_dy = help.dy;
            }
            return step;
        }
    }
    return (Step){ 0 };
}

void movement_tick(Entity *entity, const Tilemap *tilemap, uint8_t buttons)
{
    int dx = ((buttons & BUTTON_RIGHT) != 0) - ((buttons & BUTTON_LEFT) != 0);
    int dy = ((buttons & BUTTON_DOWN) != 0) - ((buttons & BUTTON_UP) != 0);

    if (dx != entity->input_dx || dy != entity->input_dy) {
        entity->input_dx = (int8_t)dx;
        entity->input_dy = (int8_t)dy;
        entity->corner_help_dx = 0;
        entity->corner_help_dy = 0;
    }
    if (dx == 0 && dy == 0) {
        entity->move_progress = 0;
        return;
    }

    entity->move_progress += entity->speed;
    while (entity->move_progress >= STEP_COST) {
        Step step = (dx != 0 && dy != 0)
            ? two_direction_step(tilemap, entity, dx, dy)
            : single_direction_step(tilemap, entity, dx, dy);
        if (!step_moves(step)) {
            entity->move_progress = 0;
            return;
        }

        bool held_diagonal = dx != 0 && dy != 0 && step.dx == dx && step.dy == dy;
        int cost = held_diagonal ? DIAGONAL_STEP_COST : STEP_COST;
        if (entity->move_progress < cost) {
            return;
        }

        entity->x += step.dx;
        entity->y += step.dy;
        if (step.dy == 0) entity->last_step_axis = AXIS_X;
        if (step.dx == 0) entity->last_step_axis = AXIS_Y;
        entity->move_progress -= cost;
    }
}
