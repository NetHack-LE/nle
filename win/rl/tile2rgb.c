/* Converts the tile text descriptions in monsters.txt, objects.txt, and 
   other.txt into RGB pixels */

#include <string.h>
#include "hack.h"

#include "tile2rgb.h"

/* defined in tile.c, a generated file */
extern short glyph2tile[];
extern int total_tiles_used;

/* Basically want to open the files, read the pixels and be done with it */

int init_tiles(const char *filenames[], int filecount, tile_t *tileset) {

   if(!tileset) {
      // function was called without memory being allocated
      return 0;
   }

   pixel tile[TILE_Y][TILE_X];
   tile_t *tile_ptr = tileset;

   for(int f=0; f<filecount; f++) {
      if(!fopen_text_file(filenames[f], "r")) {
         /* can't read the tiles, throw the problem back */
         printf("init_tiles: unable to open %s\n", filenames[f]);
         return f; 
      }

      while(read_text_tile(tile)) {
         memccpy(tile_ptr, &(tile), TILE_Y * TILE_X, sizeof(pixel));
         tile_ptr++;
      }

      fclose_text_file();
   }

   return filecount;
}