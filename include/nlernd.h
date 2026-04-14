/*

Set of functions to manipulate NetHack's Random Number Generators

*/

#ifndef NLERND_H
#define NLERND_H

#include "nletypes.h"
#include <time.h>

void nle_init_lgen_rng();
void nle_swap_to_lgen(int);
void nle_swap_to_core(int);

void nle_set_seed(nle_ctx_t *, unsigned long, unsigned long, boolean,
                  unsigned long);
void nle_get_seed(nle_ctx_t *, unsigned long *, unsigned long *, boolean *,
                  unsigned long *, bool *);

/* Fill struct tm with deterministic values from seed via ISAAC64. */
void nle_fill_fixed_tm(struct tm *, unsigned long);

#endif