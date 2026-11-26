#pragma once

#include <stdint.h>

#include "entity.h"
#include "tilemap.h"

void movement_tick(Entity *entity, const Tilemap *tilemap, uint8_t buttons);
