
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "nledl.h"

static void
fail_with_dlerror(const char *symbol, const char *error)
{
    fprintf(stderr, "failure in nledl: symbol '%s': %s\n", symbol,
            error ? error : "unresolved symbol");
    exit(EXIT_FAILURE);
}

static void *
nledl_dlsym_checked(nledl_ctx *nledl, const char *symbol)
{
    dlerror(); /* Clear any existing error. */
    void *sym = dlsym(nledl->dlhandle, symbol);
    char *error = dlerror();
    if (error != NULL || sym == NULL) {
        fail_with_dlerror(symbol, error);
    }
    return sym;
}

void
nledl_init(nledl_ctx *nledl, nle_obs *obs, nle_settings *settings)
{
    void *handle = dlopen(nledl->dlpath, RTLD_LAZY | RTLD_NOLOAD);
    if (handle) {
        dlclose(handle);
        fprintf(stderr,
                "failure in nledl_init: library %s is already loaded\n",
                nledl->dlpath);
        exit(EXIT_FAILURE);
    }

    nledl->dlhandle = dlopen(nledl->dlpath, RTLD_LAZY);

    if (!nledl->dlhandle) {
        fprintf(stderr, "%s\n", dlerror());
        exit(EXIT_FAILURE);
    }

    void *(*start)(nle_obs *, FILE *, nle_settings *);
    start = nledl_dlsym_checked(nledl, "nle_start");
    nledl->nle_ctx = start(obs, nledl->ttyrec, settings);
    if (!nledl->nle_ctx) {
        fprintf(stderr, "failure in nledl_init: nle_start returned NULL\n");
        exit(EXIT_FAILURE);
    }

    nledl->step = nledl_dlsym_checked(nledl, "nle_step");
}

void
nledl_close(nledl_ctx *nledl)
{
    if (!nledl || !nledl->dlhandle) {
        fprintf(stderr, "failure in nledl_close: invalid context\n");
        exit(EXIT_FAILURE);
    }
    if (!nledl->nle_ctx) {
        fprintf(stderr, "failure in nledl_close: missing nle_ctx\n");
        exit(EXIT_FAILURE);
    }

    void (*end)(void *);
    end = nledl_dlsym_checked(nledl, "nle_end");
    end(nledl->nle_ctx);
    nledl->nle_ctx = NULL;

    if (dlclose(nledl->dlhandle)) {
        fprintf(stderr, "Error in dlclose: %s\n", dlerror());
        exit(EXIT_FAILURE);
    }
    nledl->dlhandle = NULL;
}

nledl_ctx *
nle_start(const char *dlpath, nle_obs *obs, FILE *ttyrec,
          nle_settings *settings)
{
    /* TODO: Consider getting ttyrec path from caller? */
    struct nledl_ctx *nledl = malloc(sizeof(struct nledl_ctx));
    if (!nledl) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    nledl->ttyrec = ttyrec;
    strncpy(nledl->dlpath, dlpath, sizeof(nledl->dlpath));

    nledl_init(nledl, obs, settings);
    return nledl;
};

nledl_ctx *
nle_step(nledl_ctx *nledl, nle_obs *obs)
{
    if (!nledl || !nledl->dlhandle || !nledl->nle_ctx) {
        fprintf(stderr, "Illegal nledl_ctx\n");
        exit(EXIT_FAILURE);
    }

    nledl->step(nledl->nle_ctx, obs);

    return nledl;
}

/* TODO: For a standard reset, we don't need the full close in nle.c.
 * E.g., we could re-use the stack buffer and the nledl_ctx. */
void
nle_reset(nledl_ctx *nledl, nle_obs *obs, FILE *ttyrec,
          nle_settings *settings)
{
    nledl_close(nledl);
    /* Reset file only if not-NULL. */
    if (ttyrec)
        nledl->ttyrec = ttyrec;

    // TODO: Consider refactoring nledl.h such that we expose this init
    // function but drop reset.
    nledl_init(nledl, obs, settings);
}

void
nle_end(nledl_ctx *nledl)
{
    nledl_close(nledl);
    free(nledl);
}

void
nle_set_seed(nledl_ctx *nledl, unsigned long core, unsigned long disp,
             char reseed, unsigned long lgen)
{
    void (*set_seed)(void *, unsigned long, unsigned long, char,
                     unsigned long);

    set_seed = dlsym(nledl->dlhandle, "nle_set_seed");

    char *error = dlerror();
    if (error != NULL) {
        fprintf(stderr, "%s\n", error);
        exit(EXIT_FAILURE);
    }

    set_seed(nledl->nle_ctx, core, disp, reseed, lgen);
}

void
nle_get_seed(nledl_ctx *nledl, unsigned long *core, unsigned long *disp,
             char *reseed, unsigned long *lgen, bool *lgen_in_use)
{
    void (*get_seed)(void *, unsigned long *, unsigned long *, char *,
                     unsigned long *, bool *);

    get_seed = dlsym(nledl->dlhandle, "nle_get_seed");

    char *error = dlerror();
    if (error != NULL) {
        fprintf(stderr, "%s\n", error);
        exit(EXIT_FAILURE);
    }

    /* Careful here. NetHack has different ideas of what a boolean is
     * than C++ (see global.h and SKIP_BOOLEAN). But one byte should be fine.
     */
    get_seed(nledl->nle_ctx, core, disp, reseed, lgen, lgen_in_use);
}
