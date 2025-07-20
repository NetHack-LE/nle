/* Converts the tile text descriptions in monsters.txt, objects.txt, and 
   other.txt into RGB pixels */

#include <string.h>
#include "hack.h"
#include "tile.h"

#define NUM_TILES 1082 /* TODO figure out how to not hard code this */

/* defined in tile.c, a generated file */
extern short glyph2tile[];
extern int total_tiles_used;

typedef struct tile_s {
   pixel tile[TILE_Y][TILE_X];
} tile_t;

tile_t tileset[NUM_TILES]; 

/* Basically want to open the files, read the pixels and be done with it */

int init_tiles(const char *filenames[], int filecount) {

   memset(tileset, 0, sizeof(tileset));

   pixel tile[TILE_Y][TILE_X];
   tile_t *tile_ptr = tileset;

   for(int f=0; f<filecount; f++) {
      if(!fopen_text_file(filenames[f], "r")) {
         /* can't read the tiles, throw the problem back */
         return f+1; 
      }

      while(read_text_tile(tile)) {
         memccpy(tile_ptr, &(tile), NUM_TILES, TILE_Y * TILE_X * sizeof(pixel));
         tile_ptr++;
      }

      fclose_text_file();
   }

   return 0;
}