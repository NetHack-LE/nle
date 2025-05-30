
#ifndef NLETYPES_H
#define NLETYPES_H

#include <fcontext/fcontext.h>
#include <stdbool.h>
#include <stdio.h>

#define NLE_MESSAGE_SIZE 256
#define NLE_BLSTATS_SIZE 27
#define NLE_PROGRAM_STATE_SIZE 6
#define NLE_INTERNAL_SIZE 9
#define NLE_MISC_SIZE 3
#define NLE_INVENTORY_SIZE 55
#define NLE_INVENTORY_STR_LENGTH 80
#define NLE_SCREEN_DESCRIPTION_LENGTH 80
#define NLE_TERM_CO 80
#define NLE_TERM_LI 24

/* blstats indices, see also botl.c and statusfields in botl.h. */
#define NLE_BL_X 0
#define NLE_BL_Y 1
#define NLE_BL_STR25 2  /* strength 3..25 */
#define NLE_BL_STR125 3 /* strength 3..125   */
#define NLE_BL_DEX 4
#define NLE_BL_CON 5
#define NLE_BL_INT 6
#define NLE_BL_WIS 7
#define NLE_BL_CHA 8
#define NLE_BL_SCORE 9
#define NLE_BL_HP 10
#define NLE_BL_HPMAX 11
#define NLE_BL_DEPTH 12
#define NLE_BL_GOLD 13
#define NLE_BL_ENE 14
#define NLE_BL_ENEMAX 15
#define NLE_BL_AC 16
#define NLE_BL_HD 17  /* monster level, "hit-dice" */
#define NLE_BL_XP 18  /* experience level */
#define NLE_BL_EXP 19 /* experience points */
#define NLE_BL_TIME 20
#define NLE_BL_HUNGER 21 /* hunger state */
#define NLE_BL_CAP 22    /* carrying capacity */
#define NLE_BL_DNUM 23
#define NLE_BL_DLEVEL 24
#define NLE_BL_CONDITION 25 /* condition bit mask */
#define NLE_BL_ALIGN 26

/* #define NLE_USE_TILES 1 */ /* Set in CMakeLists.txt. */

/* NetHack defines boolean as follows:
    typedef xchar boolean;      (global.h:80)
    typedef schar xchar;        (global.h:73)
    typedef signed char schar;  (config.h:420)

So we'll do the same to avoid having to include all of NetHack's types
*/
typedef signed char boolean;

typedef struct TMT TMT;

typedef struct nle_observation {
    int action;
    int done;
    char in_normal_game;     /* Bool indicating if other obs are set. */
    int how_done;            /* If game is really_done, how it ended. */
    short *glyphs;           /* Size ROWNO * (COLNO - 1) */
    unsigned char *chars;    /* Size ROWNO * (COLNO - 1) */
    unsigned char *colors;   /* Size ROWNO * (COLNO - 1) */
    unsigned char *specials; /* Size ROWNO * (COLNO - 1) */
    long *blstats;           /* Size NLE_BLSTATS_SIZE */
    unsigned char *message;  /* Size NLE_MESSAGE_SIZE */
    int *program_state;      /* Size NLE_PROGRAM_STATE_SIZE */
    int *internal;           /* Size NLE_INTERNAL_SIZE */
    short *inv_glyphs;       /* Size NLE_INVENTORY_SIZE */
    unsigned char
        *inv_strs; /* Size NLE_INVENTORY_SIZE * NLE_INVENTORY_STR_LENGTH */
    unsigned char *inv_letters;         /* Size NLE_INVENTORY_SIZE */
    unsigned char *inv_oclasses;        /* Size NLE_INVENTORY_SIZE */
    unsigned char *screen_descriptions; /* Size ROWNO * (COLNO - 1) *
                                           NLE_SCREEN_DESCRIPTION_LENGTH */
    unsigned char *tty_chars;           /* Size NLE_TERM_LI * NLE_TERM_CO */
    signed char *tty_colors;            /* Size NLE_TERM_LI * NLE_TERM_CO */
    unsigned char *tty_cursor;          /* Size 2 */
    int *misc;                          /* Size NLE_MISC_SIZE */
} nle_obs;

typedef struct {
    unsigned long seeds[2]; /* core, disp */
    char reseed; /* boolean: use NetHack's anti-TAS reseed mechanism? */
    bool use_init_seeds;     /* bool to tell NLE if seeds were provided */
    unsigned long lgen_seed; /* seed for level generation RNG */
    bool use_lgen_seed; /* bool to tell NLE to use level generation RNG */
} nle_seeds_init_t;

typedef struct nle_globals {
    fcontext_stack_t stack;
    fcontext_t returncontext;
    fcontext_t generatorcontext;

    FILE *ttyrec;
    TMT *vterminal;
    char outbuf[BUFSIZ];
    char *outbuf_write_ptr;
    char *outbuf_write_end;

#ifdef NLE_BZ2_TTYRECS
    void *ttyrec_bz2;
#endif

    boolean done;
    nle_obs *observation;
} nle_ctx_t;

typedef struct nle_settings {
    /*
     *  Path to NetHack's game files.
     */
    char hackdir[4096];
    char scoreprefix[4096];
    char options[32768];
    char wizkit[4096];
    /*
     * Bool indicating whether to spawn monsters randomly after every step
     * with some probability (1 by def). For more info, see
     * https://nethackwiki.com/wiki/Monster_creation#Random_generation
     */
    int spawn_monsters;
    /*
     * Filename for nle's ttyrec*.bz2.
     */
    char ttyrecname[4096];

    /* Initial seeds for the RNGs */
    nle_seeds_init_t initial_seeds;

} nle_settings;

#endif /* NLETYPES_H */
