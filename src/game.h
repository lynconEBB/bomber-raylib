#pragma once

#include <stdint.h>

#include "entity.h"
#include "tilemap.h"

#define GAME_TICKS_PER_SECOND 60
#define GAME_MAX_ENTITIES 64

typedef struct {
    Tilemap tilemap;
    uint32_t tick;
    Entity entities[GAME_MAX_ENTITIES];
} Game;

// Returns a zeroed Game if the map does not parse.
Game game_create(const char *map_text);

void game_tick(Game *game, uint8_t buttons);

void game_draw(const Game *game);
