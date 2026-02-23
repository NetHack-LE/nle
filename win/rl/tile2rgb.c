/* Converts the tile text descriptions in monsters.txt, objects.txt, and
   other.txt into RGB pixels */

#include "hack.h"
#include <string.h>

#include "tile2rgb.h"

/* defined in tile.c, a generated file */
extern short glyph2tile[];
extern int total_tiles_used;

/*
Basically want to open the files, read the pixels and be done with it.
Returns the number of files read sucessfully, so 0 == failure.
*/
int
init_rgb_tileset(const char *filenames[], int filecount, tile_t *tileset)
{
    if (!filenames || filecount <= 0) {
        // no files to read, return 0
        return 0;
    }

    if (!tileset) {
        // function was called without memory being allocated
        return 0;
    }

    pixel tile[TILE_Y][TILE_X];
    tile_t *tile_ptr = tileset;

    for (int f = 0; f < filecount; f++) {
        /* file handles are static variables in tiletext.c so
           we don't have to manage them - except that we call
           the open and close management functions.
        */
        if (!fopen_text_file(filenames[f], "r")) {
            /* can't read the tiles, throw the problem back */
            fprintf(stderr, "init_tiles: unable to open %s\n", filenames[f]);
            return f;
        }

        while (read_text_tile(tile)) {
            memcpy(tile_ptr, &(tile), TILE_Y * TILE_X * sizeof(pixel));
            tile_ptr++;
        }

        fclose_text_file();
    }

    return filecount;
}