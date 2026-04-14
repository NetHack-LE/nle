Deterministic Seeding
=====================

NLE provides several mechanisms to make game runs reproducible. This is
important for training and evaluating reinforcement learning agents, where
differences between runs should come from agent behaviour, not from hidden
sources of randomness.

Core and Display Seeds
**********************

NetHack 3.6 uses two random number generators (RNGs):

- **core** -- drives gameplay randomness (monster spawns, loot, combat).
- **disp** -- drives display-only randomness (as an anti-TAS measure).

You can fix both seeds before a reset:

.. code-block:: python

    env = NLE()
    env.seed(core=42, disp=42, reseed=False)
    obs, info = env.reset()  # reproducible from here

Setting ``reseed=False`` disables NetHack's periodic reseeding, which would
otherwise inject true randomness during play.

Level Generation Seed
*********************

By default the core RNG is also used when NetHack generates new dungeon
levels, meaning the levels depend on in-game actions taken before reaching
them. The optional **lgen** seed isolates level generation into its own RNG
so that the dungeon layout is fixed regardless of gameplay choices:

.. code-block:: python

    env.seed(core=42, disp=42, reseed=False, lgen=99)

Fixing Time-based Effects (``fix_moon_phase``)
**********************************************

NetHack changes gameplay based on the real-world system clock:

- **Moon phase** -- full moon grants +1 luck; new moon gives -1 luck.
- **Friday the 13th** -- gives -1 luck.
- **Night** (10 pm -- 6 am) -- affects undead behaviour and other events.
- **Midnight** -- triggers special undead/vampire encounters.

These effects are **not** controlled by the core seed and will differ between
runs executed at different times of day or on different dates. This can cause
noticeable score variance (e.g. full moon luck bonuses).

To make these effects deterministic, pass ``fix_moon_phase=True`` when
creating the environment:

.. code-block:: python

    env = NLE(fix_moon_phase=True)
    env.seed(core=42, disp=42, reseed=False)
    obs, info = env.reset()  # time-based effects now derived from the seed

When ``fix_moon_phase=True`` **and** seeds are set, the time values (moon
phase, friday 13th, night, midnight) are derived deterministically from the
core seed using a private ISAAC64 RNG instance -- the same RNG family that
NetHack uses internally.

When ``fix_moon_phase=True`` but no seeds have been set, the real system time
is used as usual.

Putting It All Together
***********************

For fully deterministic runs:

.. code-block:: python

    import gymnasium as gym
    import nle

    env = gym.make("NetHackScore-v0", fix_moon_phase=True)
    env.seed(core=42, disp=42, reseed=False, lgen=99)
    obs, info = env.reset()

    # Every run with these settings will produce identical results
    # regardless of wall-clock time.
