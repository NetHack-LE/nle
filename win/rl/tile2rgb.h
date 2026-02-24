/* Interface for converting the text-defined tiles to rgb array */

#ifndef TILE2RGB_H
#define TILE2RGB_H

#include "tile.h"

#define TILE_Z 3 /* RGB */

typedef struct tile_s {
    pixel tile[TILE_Y][TILE_X];
} tile_t;

int init_rgb_tileset(const char *[], int, tile_t *);

#endif /* TILE2RGB */