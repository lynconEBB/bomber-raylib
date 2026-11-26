#include "game.h"

#include "movement.h"

Game game_create(const char *map_text)
{
    Game game = { .tilemap = tilemap_from_text(map_text) };
    if (game.tilemap.width == 0) {
        return (Game){ 0 };
    }

    if (game.tilemap.spawn_count > 0) {
        GridPos spawn = game.tilemap.spawns[0];
        game.entities[0] = (Entity){
            .kind = ENTITY_PLAYER,
            .x = (int16_t)grid_cell_center_px(spawn.x),
            .y = (int16_t)grid_cell_center_px(spawn.y),
            .speed = PLAYER_START_SPEED,
        };
    }
    return game;
}

void game_tick(Game *game, uint8_t buttons)
{
    for (int index = 0; index < GAME_MAX_ENTITIES; index++) {
        Entity *entity = &game->entities[index];
        if (entity->kind == ENTITY_PLAYER) {
            movement_tick(entity, &game->tilemap, buttons);
        }
    }
    game->tick++;
}

void game_draw(const Game *game)
{
    tilemap_draw(&game->tilemap);
    for (int index = 0; index < GAME_MAX_ENTITIES; index++) {
        entity_draw(&game->entities[index]);
    }
}
