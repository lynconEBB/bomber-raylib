#include "input.h"

#include "raylib.h"

void input_poll(Input *input)
{
    uint8_t down = BUTTON_NONE;
    if (IsKeyDown(KEY_UP) || IsKeyDown(KEY_W)) down |= BUTTON_UP;
    if (IsKeyDown(KEY_DOWN) || IsKeyDown(KEY_S)) down |= BUTTON_DOWN;
    if (IsKeyDown(KEY_LEFT) || IsKeyDown(KEY_A)) down |= BUTTON_LEFT;
    if (IsKeyDown(KEY_RIGHT) || IsKeyDown(KEY_D)) down |= BUTTON_RIGHT;

    input->down = down;
    input->since_last_tick |= down;
}

uint8_t input_take(Input *input)
{
    uint8_t buttons = input->since_last_tick;
    input->since_last_tick = input->down;
    return buttons;
}
