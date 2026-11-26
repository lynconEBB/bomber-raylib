#pragma once

#include <stdint.h>

#include "entity.h"
#include "tilemap.h"

#define SCENE_TICKS_PER_SECOND 60
#define SCENE_MAX_ENTITIES 64

typedef enum : uint8_t {
    SCENE_NONE,
    SCENE_ARENA,
    SCENE_UI
} SceneType;

typedef struct {
    Tilemap tilemap;
    SceneType type;
    Entity entities[SCENE_MAX_ENTITIES];
} Scene;

// Returns a zeroed Scene if the map does not parse.
Scene scene_create_arena(const char *map_text);

void scene_tick(Scene *scene, uint8_t buttons);

void scene_draw(const Scene *scene);
