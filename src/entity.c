#include "entity.h"

#include "raylib.h"

void entity_draw(const Entity *entity)
{
    switch (entity->kind) {
    case ENTITY_NONE:
        break;
    case ENTITY_PLAYER:
        DrawCircleLinesV((Vector2){ (float)entity->x, (float)entity->y }, BODY_RADIUS, WHITE);
        DrawRectangle(entity->x - 1, entity->y - 1, 2, 2, WHITE);
        break;
    }
}
