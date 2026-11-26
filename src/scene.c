#include "scene.h"

#include "movement.h"

Scene scene_create_arena(const char *map_text)
{
    Scene scene = {
        .tilemap = tilemap_from_text(map_text),
        .type = SCENE_ARENA,
    };

    if (scene.tilemap.width == 0) {
        return (Scene){ 0 };
    }

    if (scene.tilemap.spawn_count > 0) {
        GridPos spawn = scene.tilemap.spawns[0];
        scene.entities[0] = (Entity){
            .kind = ENTITY_PLAYER,
            .x = (int16_t)grid_cell_center_px(spawn.x),
            .y = (int16_t)grid_cell_center_px(spawn.y),
            .speed = PLAYER_START_SPEED,
        };
    }
    return scene;
}

void scene_tick(Scene *scene, uint8_t buttons)
{
    for (int index = 0; index < SCENE_MAX_ENTITIES; index++) {
        Entity *entity = &scene->entities[index];
        if (entity->kind == ENTITY_PLAYER) {
            movement_tick(entity, &scene->tilemap, buttons);
        }
    }
}

void scene_draw(const Scene *scene)
{
    if (scene->type == SCENE_ARENA)
        tilemap_draw(&scene->tilemap);

    for (int index = 0; index < SCENE_MAX_ENTITIES; index++) {
        entity_draw(&scene->entities[index]);
    }
}
