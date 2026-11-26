#include "input.h"

#include "raylib.h"

void input_poll(Input *input)
{
    input->down = BUTTON_NONE;
    if (IsKeyDown(KEY_W)) input->down |= BUTTON_UP;
    if (IsKeyDown(KEY_S)) input->down |= BUTTON_DOWN;
    if (IsKeyDown(KEY_A)) input->down |= BUTTON_LEFT;
    if (IsKeyDown(KEY_D)) input->down |= BUTTON_RIGHT;

    input->since_last_tick |= input->down;
}

uint8_t input_take(Input *input)
{
    uint8_t buttons = input->since_last_tick;
    input->since_last_tick = input->down;
    return buttons;
}
