#pragma once

#include <stdint.h>

typedef enum : uint8_t {
    BUTTON_NONE  = 0,
    BUTTON_UP    = 1 << 0,
    BUTTON_DOWN  = 1 << 1,
    BUTTON_LEFT  = 1 << 2,
    BUTTON_RIGHT = 1 << 3,
} Button;

typedef struct {
    uint8_t down;
    // Every button that was down at some point since the last tick, so a tap shorter than a tick is not lost.
    uint8_t since_last_tick;
} Input;

// Once per rendered frame.
void input_poll(Input *input);

// Once per tick: the buttons the tick sees.
uint8_t input_take(Input *input);
