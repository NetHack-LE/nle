# Copyright (c) Facebook, Inc. and its affiliates.
import os
import random
import timeit
import warnings

import numpy as np
import pytest

from nle import _pynethack
from nle import nethack

# MORE + compass directions + long compass directions.
ACTIONS = [
    13,
    107,
    108,
    106,
    104,
    117,
    110,
    98,
    121,
    75,
    76,
    74,
    72,
    85,
    78,
    66,
    89,
]


class TestNetHack:
    @pytest.fixture
    def game(self):  # Make sure we close even on test failure.
        g = nethack.Nethack(observation_keys=("chars", "blstats"))
        try:
            yield g
        finally:
            g.close()

    def test_close_and_restart(self):
        game = nethack.Nethack()
        game.reset()
        game.close()

        game = nethack.Nethack()
        game.reset()
        game.close()

    def test_run_n_episodes(self, tmpdir, game, episodes=3):
        olddir = tmpdir.chdir()  # tmpdir is a py.path.local object.

        chars, blstats = game.reset()

        assert chars.shape == nethack.DUNGEON_SHAPE
        assert blstats.shape == nethack.BLSTATS_SHAPE

        game.step(ord("y"))
        game.step(ord("y"))
        game.step(ord("\n"))

        steps = 0
        start_time = timeit.default_timer()
        start_steps = steps

        mean_sps = 0
        sps_n = 0

        for episode in range(episodes):
            while True:
                ch = random.choice(ACTIONS)
                _, done = game.step(ch)
                if done:
                    # This will typically be DIED, but could be POISONED, etc.
                    assert int(game.how_done()) < int(nethack.GENOCIDED)
                    break

                steps += 1

                if steps % 1000 == 0:
                    end_time = timeit.default_timer()
                    sps = (steps - start_steps) / (end_time - start_time)
                    sps_n += 1
                    mean_sps += (sps - mean_sps) / sps_n
                    print("%f SPS" % sps)
                    start_time = end_time
                    start_steps = steps
            print("Finished episode %i after %i steps." % (episode + 1, steps))
            game.reset()

        print("Finished after %i steps. Mean sps: %f" % (steps, mean_sps))

        # Resetting the game shouldn't have caused cwd to change.
        assert tmpdir.samefile(os.getcwd())

        if mean_sps < 15000:
            warnings.warn("Mean sps was only %f" % mean_sps, stacklevel=2)
        olddir.chdir()
        # No call to game.close() as fixture will do that for us.

    def test_several_nethacks(self, game):
        game.reset()
        game1 = nethack.Nethack()
        game1.reset()

        try:
            for _ in range(300):
                ch = random.choice(ACTIONS)
                _, done = game.step(ch)
                if done:
                    game.reset()
                _, done = game1.step(ch)
                if done:
                    game1.reset()
        finally:
            game1.close()

    def test_set_initial_seeds(self):
        game = nethack.Nethack(copy=True)
        game.set_initial_seeds(core=42, disp=666)
        obs0 = game.reset()
        try:
            seeds0 = game.get_current_seeds()
            game.set_initial_seeds(core=42, disp=666)
            obs1 = game.reset()
            seeds1 = game.get_current_seeds()
            np.testing.assert_equal(obs0, obs1)
            assert seeds0 == seeds1
        finally:
            game.close()

    def test_set_seed_after_reset(self, game):
        game.reset()
        # Could fail on a system without a good source of randomness:
        assert game.get_current_seeds()[2] is True
        game.set_current_seeds(core=42, disp=666)
        assert game.get_current_seeds() == (42, 666, False, 0)


class TestNetHackFurther:
    def test_run(self):
        game = nethack.Nethack(
            observation_keys=("glyphs", "chars", "colors", "blstats", "program_state")
        )
        _, _, _, _, program_state = game.reset()
        actions = [
            nethack.MiscAction.MORE,
            nethack.MiscAction.MORE,
            nethack.MiscAction.MORE,
            nethack.MiscAction.MORE,
            nethack.MiscAction.MORE,
            nethack.MiscAction.MORE,
        ]

        for action in actions:
            while not program_state[3]:  # in_moveloop.
                obs, done = game.step(nethack.MiscAction.MORE)
                _, _, _, _, program_state = obs

            obs, done = game.step(action)
            if done:
                # Only the good die young.
                obs = game.reset()

            glyphs, chars, colors, blstats, _ = obs

            x, y = blstats[:2]

            assert np.count_nonzero(chars == ord("@")) == 1

            # That's where you're @.
            assert chars[y, x] == ord("@")

            # You're bright (4th bit, 8) white (7), too.
            assert colors[y, x] == 8 ^ 7

            mon = nethack.permonst(nethack.glyph_to_mon(glyphs[y][x]))
            assert mon.mname == "monk"
            assert mon.mlevel == 10

            class_sym = nethack.class_sym.from_mlet(mon.mlet)
            assert class_sym.sym == "@"
            assert class_sym.explain == "human or elf"

        game.close()
        assert os.path.isfile(
            os.path.join(os.getcwd(), "nle.ttyrec%i.bz2" % nethack.TTYREC_VERSION)
        )

    def test_illegal_filename(self):
        with pytest.raises(IOError):
            nethack.Nethack(ttyrec="")
        game = nethack.Nethack()
        with pytest.raises(IOError):
            game.reset("")

    def test_set_buffers_after_reset(self):
        game = nethack.Nethack()
        game.reset()
        with pytest.raises(RuntimeError, match=r"set_buffers called after reset()"):
            game._pynethack.set_buffers()

    def test_nethack_random_character(self):
        game = nethack.Nethack(playername="Hugo-@")
        assert "race:random" in game.options
        assert "gender:random" in game.options
        assert "align:random" in game.options

        game = nethack.Nethack(playername="Jurgen-wiz-gno-cha-mal")
        assert "race:random" not in game.options
        assert "gender:random" not in game.options
        assert "align:random" not in game.options

        game = nethack.Nethack(
            playername="Albert-@",
            options=list(nethack.NETHACKOPTIONS) + ["align:lawful"],
        )
        assert "race:random" in game.options
        assert "gender:random" in game.options
        assert "align:random" not in game.options
        assert "align:lawful" in game.options

        game = nethack.Nethack(
            playername="Rachel",
            options=list(nethack.NETHACKOPTIONS) + ["gender:female"],
        )
        assert "race:random" not in game.options
        assert "gender:random" not in game.options
        assert "align:random" not in game.options
        assert "gender:female" in game.options


class TestNethackSomeObs:
    @pytest.fixture
    def game(self):  # Make sure we close even on test failure.
        g = nethack.Nethack(observation_keys=("program_state", "message", "internal"))
        try:
            yield g
        finally:
            g.close()

    def test_message(self, game):
        messages = []

        program_state, message, _ = game.reset()
        messages.append(message)
        while not program_state[3]:  # in_moveloop.
            (program_state, message, _), done = game.step(nethack.MiscAction.MORE)
            messages.append(message)

        greeting = (
            b"Hello Agent, welcome to NetHack!  You are a neutral male human Monk."
        )
        saw_greeting = True
        for message in messages:
            # `greeting` is often the last message, but not always -- e.g.,
            # it could also be "Be careful!  New moon tonight.".
            assert len(message) == 256
            if (
                memoryview(message)[: len(greeting)] == greeting
                and memoryview(message)[len(greeting)] == 0
            ):
                saw_greeting = True
        assert saw_greeting

    def test_internal(self, game):
        program_state, _, internal = game.reset()
        while not program_state[3]:  # in_moveloop.
            # We are not in moveloop. We might still be in "normal game"
            # if something_worth_saving is true. Example: Startup with
            # "--More--", "Be careful!  New moon tonight."
            assert game.in_normal_game() == program_state[5]  # something_worth_saving.
            (program_state, _, internal), done = game.step(nethack.MiscAction.MORE)

        assert game.in_normal_game()
        assert internal[0] == 1  # deepest_lev_reached.

        (_, _, internal), done = game.step(nethack.Command.INVENTORY)
        assert internal[3] == 1  # xwaitforspace


def get_object(name):
    for index in range(nethack.NUM_OBJECTS):
        obj = nethack.objclass(index)
        if nethack.OBJ_NAME(obj) == name:
            return obj
    else:
        raise ValueError("'%s' not found!" % name)


class TestNethackFunctionsAndConstants:
    def test_permonst_and_class_sym(self):
        glyph = 155  # Lichen.

        mon = nethack.permonst(nethack.glyph_to_mon(glyph))

        assert mon.mname == "lichen"

        cs = nethack.class_sym.from_mlet(mon.mlet)

        assert cs.sym == "F"
        assert cs.explain == "fungus or mold"

        assert nethack.NHW_MESSAGE == 1
        assert hasattr(nethack, "MAXWIN")

        # Slightly irritating to need `chr` here.
        cs = nethack.class_sym.from_oc_class(chr(nethack.WAND_CLASS))
        assert cs.sym == "/"
        assert cs.explain == "wand"

        obj = nethack.objclass(0)
        cs = nethack.class_sym.from_oc_class(obj.oc_class)
        assert cs.sym == "]"
        assert cs.explain == "strange object"

    def test_permonst(self):
        mon = nethack.permonst(0)
        assert mon.mname == "giant ant"
        del mon

        mon = nethack.permonst(1)
        assert mon.mname == "killer bee"

    def test_some_constants(self):
        assert nethack.GLYPH_MON_OFF == 0
        assert nethack.NUMMONS > 300

    def test_illegal_numbers(self):
        with pytest.raises(
            IndexError,
            match=r"should be between 0 and NUMMONS \(%i\) but got %i"
            % (nethack.NUMMONS, nethack.NUMMONS),
        ):
            nethack.permonst(nethack.NUMMONS)

        with pytest.raises(
            IndexError,
            match=r"should be between 0 and NUMMONS \(%i\) but got %i"
            % (nethack.NUMMONS, -1),
        ):
            nethack.permonst(-1)

        with pytest.raises(
            IndexError,
            match=r"should be between 0 and MAXMCLASSES \(%i\) but got 127"
            % nethack.MAXMCLASSES,
        ):
            nethack.class_sym.from_mlet("\x7f")

    def test_objclass(self):
        obj = nethack.objclass(0)
        assert nethack.OBJ_NAME(obj) == "strange object"

        food_ration = get_object("food ration")
        assert food_ration.oc_weight == 20

        elven_dagger = get_object("elven dagger")
        assert nethack.OBJ_DESCR(elven_dagger) == "runed dagger"

    def test_objdescr(self):
        od = nethack.objdescr.from_idx(0)
        assert od.oc_name == "strange object"
        assert od.oc_descr is None

        elven_dagger = get_object("elven dagger")
        od = nethack.objdescr.from_idx(elven_dagger.oc_name_idx)
        assert od.oc_name == "elven dagger"
        assert od.oc_descr == "runed dagger"

        # Example of how to do this with glyphs.
        glyph = nethack.GLYPH_OBJ_OFF + elven_dagger.oc_name_idx
        idx = nethack.glyph_to_obj(glyph)
        assert idx == elven_dagger.oc_name_idx
        assert nethack.objdescr.from_idx(idx) is od

    def test_symdef(self):
        tree_cmap_offset = 18  # Cf. drawing.c.
        tree_glyph = nethack.GLYPH_CMAP_OFF + tree_cmap_offset
        tree_symdef = nethack.symdef.from_idx(tree_cmap_offset)

        assert tree_cmap_offset == nethack.glyph_to_cmap(tree_glyph)
        assert tree_symdef.sym == ord("#")
        assert tree_symdef.explanation == "tree"
        assert tree_symdef.color == 2  # CLR_GREEN.
        assert str(tree_symdef) == "<nethack.symdef sym='#' explanation='tree'>"

        darkroom_glyph = nethack.GLYPH_CMAP_OFF
        assert nethack.glyph_to_cmap(darkroom_glyph) == 0
        darkroom_symdef = nethack.symdef.from_idx(0)
        assert darkroom_symdef.sym == ord(" ")
        assert darkroom_symdef.explanation == "dark part of a room"
        assert darkroom_symdef.color == 8  # NO_COLOR

    def test_glyph2tile(self):
        assert nethack.glyph2tile[nethack.GLYPH_MON_OFF] == 0
        assert nethack.glyph2tile[nethack.GLYPH_PET_OFF] == 0
        assert nethack.glyph2tile[nethack.GLYPH_DETECT_OFF] == 0

    def test_glyph_is(self):
        assert nethack.glyph_is_monster(nethack.GLYPH_MON_OFF)
        assert nethack.glyph_is_pet(nethack.GLYPH_PET_OFF)
        assert nethack.glyph_is_invisible(nethack.GLYPH_INVIS_OFF)
        assert nethack.glyph_is_detected_monster(nethack.GLYPH_DETECT_OFF)
        assert nethack.glyph_is_body(nethack.GLYPH_BODY_OFF)
        assert nethack.glyph_is_ridden_monster(nethack.GLYPH_RIDDEN_OFF)
        assert nethack.glyph_is_object(nethack.GLYPH_OBJ_OFF)
        assert nethack.glyph_is_cmap(nethack.GLYPH_CMAP_OFF)
        # No glyph_is_explode, glyph_is_zap in NH.
        assert nethack.glyph_is_swallow(nethack.GLYPH_SWALLOW_OFF)
        assert nethack.glyph_is_warning(nethack.GLYPH_WARNING_OFF)
        assert nethack.glyph_is_statue(nethack.GLYPH_STATUE_OFF)

        vec = np.array(
            [
                nethack.GLYPH_MON_OFF,
                nethack.GLYPH_PET_OFF,
                nethack.GLYPH_INVIS_OFF,
                nethack.GLYPH_DETECT_OFF,
                nethack.GLYPH_BODY_OFF,
                nethack.GLYPH_RIDDEN_OFF,
                nethack.GLYPH_OBJ_OFF,
                nethack.GLYPH_CMAP_OFF,
                nethack.GLYPH_EXPLODE_OFF,
                nethack.GLYPH_ZAP_OFF,
                nethack.GLYPH_SWALLOW_OFF,
                nethack.GLYPH_WARNING_OFF,
                nethack.GLYPH_STATUE_OFF,
            ],
            dtype=np.int32,
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_monster(vec),
            np.isin(
                vec,
                [
                    nethack.GLYPH_MON_OFF,
                    nethack.GLYPH_PET_OFF,
                    nethack.GLYPH_DETECT_OFF,
                    nethack.GLYPH_RIDDEN_OFF,
                ],
            ),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_pet(vec),
            np.isin(vec, [nethack.GLYPH_PET_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_invisible(vec),
            np.isin(vec, [nethack.GLYPH_INVIS_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_normal_object(vec),
            np.isin(vec, [nethack.GLYPH_OBJ_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_detected_monster(vec),
            np.isin(vec, [nethack.GLYPH_DETECT_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_body(vec),
            np.isin(vec, [nethack.GLYPH_BODY_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_ridden_monster(vec),
            np.isin(vec, [nethack.GLYPH_RIDDEN_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_object(vec),
            np.isin(
                vec,
                [
                    nethack.GLYPH_BODY_OFF,
                    nethack.GLYPH_OBJ_OFF,
                    nethack.GLYPH_STATUE_OFF,
                ],
            ),
        )
        assert np.all(nethack.glyph_is_trap(vec) == 0)
        for idx in range(nethack.MAXPCHARS):  # Find an actual trap.
            if "trap" in nethack.symdef.from_idx(idx).explanation:
                assert nethack.glyph_is_trap(nethack.GLYPH_CMAP_OFF + idx)
                break
        np.testing.assert_array_equal(  # Explosions are cmaps?
            nethack.glyph_is_cmap(vec),
            np.isin(vec, [nethack.GLYPH_CMAP_OFF, nethack.GLYPH_EXPLODE_OFF]),
        )
        # No glyph_is_explode, glyph_is_zap in NH.
        np.testing.assert_array_equal(
            nethack.glyph_is_swallow(vec),
            np.isin(vec, [nethack.GLYPH_SWALLOW_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_warning(vec),
            np.isin(vec, [nethack.GLYPH_WARNING_OFF]),
        )
        np.testing.assert_array_equal(
            nethack.glyph_is_statue(vec),
            np.isin(vec, [nethack.GLYPH_STATUE_OFF]),
        )

        # Test some non-offset value too.
        assert nethack.glyph_is_warning(
            (nethack.GLYPH_WARNING_OFF + nethack.GLYPH_STATUE_OFF) // 2
        )

    def test_glyph_to(self):
        assert np.all(
            nethack.glyph_to_mon(
                np.array(
                    [
                        nethack.GLYPH_MON_OFF,
                        nethack.GLYPH_PET_OFF,
                        nethack.GLYPH_DETECT_OFF,
                        nethack.GLYPH_RIDDEN_OFF,
                        nethack.GLYPH_STATUE_OFF,
                    ]
                )
            )
            == 0
        )

        # STATUE and CORPSE from onames.h (generated by makedefs).
        # Returned by glyph_to_obj.
        corpse = get_object("corpse").oc_name_idx
        statue = get_object("statue").oc_name_idx
        np.testing.assert_array_equal(
            nethack.glyph_to_obj(
                np.array(
                    [
                        nethack.GLYPH_BODY_OFF,
                        nethack.GLYPH_STATUE_OFF,
                        nethack.GLYPH_OBJ_OFF,
                    ]
                )
            ),
            np.array([corpse, statue, 0]),
        )

        for idx in range(nethack.MAXPCHARS):  # Find the arrow trap.
            if nethack.symdef.from_idx(idx).explanation == "arrow trap":
                np.testing.assert_array_equal(
                    nethack.glyph_to_trap(
                        np.array([nethack.GLYPH_CMAP_OFF, nethack.GLYPH_CMAP_OFF + idx])
                    ),
                    # Traps are one-indexed in defsym_to_trap as per rm.h.
                    np.array([nethack.NO_GLYPH, 1]),
                )
                break

        np.testing.assert_array_equal(
            nethack.glyph_to_cmap(
                np.array(
                    [
                        nethack.GLYPH_CMAP_OFF,
                        nethack.GLYPH_STATUE_OFF,
                    ]
                )
            ),
            np.array([0, nethack.NO_GLYPH]),
        )

        assert nethack.glyph_to_swallow(nethack.GLYPH_SWALLOW_OFF) == 0

        np.testing.assert_array_equal(
            nethack.glyph_to_warning(
                np.arange(nethack.GLYPH_WARNING_OFF, nethack.GLYPH_STATUE_OFF)
            ),
            np.arange(nethack.WARNCOUNT),
        )


class TestNethackGlanceObservation:
    @pytest.fixture
    def game(self):  # Make sure we close even on test failure.
        g = nethack.Nethack(
            playername="MonkBot-mon-hum-neu-mal",
            observation_keys=("screen_descriptions", "glyphs", "chars"),
        )
        try:
            yield g
        finally:
            g.close()

    def test_new_observation_shapes(self, game):
        screen_descriptions, glyphs, *_ = game.reset()

        assert len(screen_descriptions.shape) == 3
        rows, cols, descr_len = screen_descriptions.shape
        assert tuple(glyphs.shape) == (rows, cols)
        assert _pynethack.nethack.NLE_SCREEN_DESCRIPTION_LENGTH == descr_len

    def test_glance_descriptions(self, game):
        episodes = 6
        for _ in range(episodes):
            desc, glyphs, chars = game.reset()
            row, col = glyphs.shape
            for i in range(row):
                for j in range(col):
                    glyph = glyphs[i][j]
                    char = chars[i][j]
                    letter = chr(char)
                    glance = "".join(chr(c) for c in desc[i][j] if c != 0)
                    if char == 32:  # no text
                        assert glance == ""
                        assert (desc[i][j] == 0).all()
                    elif glyph == 2378 and letter == ".":
                        assert glance == "floor of a room"
                    elif glyph == 333 and letter == "@":  # us!
                        assert glance == "human monk called MonkBot"
                    elif glyph == 413:  # pet cat
                        assert glance == "tame kitten"
                    elif glyph == 397:  # pet dog
                        assert glance == "tame little dog"
                    elif letter in "-":  # illustrate same char, diff descrip
                        if glyph == 2378:
                            assert glance == "grave"
                        elif glyph == 2363:
                            assert glance == "wall"
                        elif glyph == 2372:
                            assert glance == "open door"


class TestNethackTerminalObservation:
    @pytest.fixture
    def game(self):  # Make sure we close even on test failure.
        g = nethack.Nethack(
            playername="MonkBot-mon-hum-neu-mal",
            observation_keys=(
                "tty_chars",
                "tty_colors",
                "tty_cursor",
                "chars",
                "colors",
            ),
        )
        try:
            yield g
        finally:
            g.close()

    def test_new_observation_shapes(self, game):
        tty_chars, tty_colors, tty_cursor, *_ = game.reset()

        assert tty_colors.shape == tty_chars.shape
        assert tty_cursor.shape == (2,)
        terminal_shape = tty_chars.shape
        assert _pynethack.nethack.NLE_TERM_LI == terminal_shape[0]
        assert _pynethack.nethack.NLE_TERM_CO == terminal_shape[1]

    def test_observations(self, game):
        tty_chars, tty_colors, *_ = game.reset()

        top_line = "".join(chr(c) for c in tty_chars[0])
        bottom_sub1_line = "".join(chr(c) for c in tty_chars[-2])
        bottom_line = "".join(chr(c) for c in tty_chars[-1])
        assert top_line.startswith(
            "Hello MonkBot, welcome to NetHack!  You are a neutral male human Monk."
        )
        assert bottom_sub1_line.startswith("MonkBot the Candidate")
        assert bottom_line.startswith("Dlvl:1")

        for c, font in zip(tty_chars.reshape(-1), tty_colors.reshape(-1)):
            if chr(c) == "@":
                assert font == 15  # BRIGHT_WHITE
            if chr(c) == " ":
                assert font == 0  # NO_COLOR

    def test_crop(self, game):
        tty_chars, tty_colors, _, chars, colors = game.reset()

        # DUNGEON is [21, 79], TTY is [24, 80]. Crop to get alignment.
        np.testing.assert_array_equal(chars, tty_chars[1:-2, :-1])
        np.testing.assert_array_equal(colors, tty_colors[1:-2, :-1])


class TestNethackMiscObservation:
    @pytest.fixture
    def game(self):  # Make sure we close even on test failure.
        g = nethack.Nethack(
            playername="MonkBot-mon-hum-neu-mal", observation_keys=("misc", "internal")
        )
        try:
            yield g
        finally:
            g.close()

    def test_misc_yn_question(self, game):
        misc, internal = game.reset()
        while misc[2]:
            (misc, internal), done = game.step(ord(" "))
            assert not done

        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])

        game.step(nethack.M("p"))  # pray
        np.testing.assert_array_equal(misc, np.array([1, 0, 0]))
        np.testing.assert_array_equal(misc, internal[1:4])

        game.step(ord("n"))
        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])

    def test_misc_getline(self, game):
        misc, internal = game.reset()
        while misc[2]:
            (misc, internal), done = game.step(ord(" "))
            assert not done

        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])

        game.step(nethack.M("n"))  # name ..
        game.step(ord("a"))  # ... the current level
        np.testing.assert_array_equal(misc, np.array([0, 1, 0]))
        np.testing.assert_array_equal(misc, internal[1:4])

        for let in "Gehennom":
            game.step(ord(let))
            np.testing.assert_array_equal(misc, np.array([0, 1, 0]))
            np.testing.assert_array_equal(misc, internal[1:4])

        game.step(ord("\r"))
        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])

    def test_misc_wait_for_space(self, game):
        misc, internal = game.reset()
        while misc[2]:
            (misc, internal), done = game.step(ord(" "))
            assert not done

        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])

        game.step(ord("i"))
        np.testing.assert_array_equal(misc, np.array([0, 0, 1]))
        np.testing.assert_array_equal(misc, internal[1:4])

        game.step(ord(" "))
        assert np.all(misc == 0)
        np.testing.assert_array_equal(misc, internal[1:4])


class TestAuxillaryFunctions:
    def test_tty_render(self):
        text = ["DE", "HV"]
        chars = np.array([[ord(c) for c in line] for line in text])
        colors = np.array([[1, 2], [3, 14]])
        cursor = (0, 1)

        expected = (
            "\n\033[0;31mD\033[4m\033[0;32mE\033[0m\n\033[0;33mH\033[1;36mV\033[0m"
        )
        assert expected == nethack.tty_render(chars, colors, cursor)


class TestNethackActions:
    def test_all_ascii(self):
        for c in range(32, 127):
            if chr(c) in "%]{|}~":  # Not a NetHack command.
                continue
            nethack.action_id_to_type(c)
