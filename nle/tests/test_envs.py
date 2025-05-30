#!/usr/bin/env python
#
# Copyright (c) Facebook, Inc. and its affiliates.
import os
import pathlib
import random
import sys
import tempfile

import gymnasium as gym
import numpy as np
import pytest

import nle
import nle.env
from nle import nethack


def get_nethack_env_ids():
    specs = gym.envs.registry.keys()
    # Ignoring base environment, since we can't handle random actions yet with
    # the full action space, and this requires a whole different set of tests.
    # For now this is OK, since NetHackScore-v0 is very similar.
    return [
        spec for spec in specs if spec.startswith("NetHack") and spec != "NetHack-v0"
    ]


def rollout_env(env, max_rollout_len):
    """Produces a rollout and asserts step outputs.

    Returns final reward. Does not assume that the environment has already been
    reset.
    """
    obs, reset_info = env.reset()
    assert env.observation_space.contains(obs)

    for _ in range(max_rollout_len):
        a = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(a)
        assert env.observation_space.contains(obs)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(info, dict)
        if terminated:
            assert not info["is_ascended"]
            break
    env.close()
    return reward


def term_screen(obs):
    return "\n".join("".join(chr(c) for c in row) for row in obs["tty_chars"])


def compare_rollouts(env0, env1, max_rollout_len):
    """Checks that two active environments return the same rollout.

    Assumes that the environments have already been reset.
    """
    step = 0
    while True:
        a = env0.action_space.sample()
        obs0, reward0, terminated0, truncated0, info0 = env0.step(a)
        obs1, reward1, terminated1, truncated1, info1 = env1.step(a)
        step += 1

        s0, s1 = term_screen(obs0), term_screen(obs1)
        top_ten_msg = "You made the top ten list!"
        if top_ten_msg in s0:
            assert top_ten_msg in s1
        else:
            np.testing.assert_equal(obs0, obs1)
        assert reward0 == reward1
        assert terminated0 == terminated1
        assert truncated0 == truncated1
        assert info0 == info1

        if terminated0 or step >= max_rollout_len:
            return


@pytest.mark.parametrize("env_name", get_nethack_env_ids())
@pytest.mark.parametrize("wizard", [False, True])
class TestGymEnv:
    @pytest.fixture(autouse=True)  # will be applied to all tests in class
    def make_cwd_tmp(self, tmpdir):
        """Makes cwd point to the test's tmpdir."""
        with tmpdir.as_cwd():
            yield

    def test_init(self, env_name, wizard):
        """Tests default initialization given standard env specs."""
        env = gym.make(env_name, wizard=wizard)
        del env

    def test_reset(self, env_name, wizard):
        """Tests default initialization given standard env specs."""
        env = gym.make(env_name, wizard=wizard)
        obs, reset_info = env.reset()
        assert env.observation_space.contains(obs)

    def test_chars_colors_specials(self, env_name, wizard):
        env = gym.make(
            env_name, observation_keys=("chars", "colors", "specials", "blstats")
        )
        obs, reset_info = env.reset()

        assert "specials" in obs
        x, y = obs["blstats"][:2]

        # That's where you're @.
        assert obs["chars"][y, x] == ord("@")

        # You're bright (4th bit, 8) white (7), too.
        assert obs["colors"][y, x] == 8 ^ 7

    def test_default_wizard_mode(self, env_name, wizard):
        if wizard:
            if env_name.startswith("NetHackChallenge-"):
                pytest.skip("No wizard mode in NetHackChallenge")
            env = gym.make(env_name, wizard=wizard)
            assert "playmode:debug" in env.unwrapped.nethack.options
        else:
            # do not send a parameter to test a default
            env = gym.make(env_name)
            assert "playmode:debug" not in env.unwrapped.nethack.options


class TestWizardMode:
    def test_wizlevelport(self):
        actions = (
            list(nethack.USEFUL_ACTIONS)
            + list(nethack.TextCharacters)
            + list(nethack.WizardCommand)
        )

        env = gym.make(
            "NetHack-v0",
            wizard=True,
            actions=actions,
            allow_all_yn_questions=True,
            allow_all_modes=True,
        )
        env.reset()
        env.step(actions.index(nethack.WizardCommand.WIZLEVELPORT))
        for c in b"10\r":
            env.step(actions.index(c))


class TestWizkit:
    @pytest.fixture(autouse=True)  # will be applied to all tests in class
    def make_cwd_tmp(self, tmpdir):
        """Makes cwd point to the test's tmpdir."""
        with tmpdir.as_cwd():
            yield

    def test_meatball_exists(self):
        """Test loading stuff via wizkit"""
        env = gym.make("NetHack-v0", wizard=True)
        found = dict(meatball=0)
        obs, reset_info = env.reset(options={"wizkit_items": list(found.keys())})
        for line in obs["inv_strs"]:
            if np.all(line == 0):
                break
            for key in found:
                if key in line.tobytes().decode("utf-8"):
                    found[key] += 1
        for key, count in found.items():
            assert key == key and count > 0
        del env

    def test_wizkit_no_wizard_mode(self):
        env = gym.make("NetHack-v0", wizard=False)
        with pytest.raises(ValueError) as e_info:
            env.reset(options={"wizkit_items": ["meatball"]})
        assert e_info.value.args[0] == "Set wizard=True to use the wizkit option."

    def test_wizkit_file(self):
        env = gym.make("NetHack-v0", wizard=True)
        req_items = ["meatball", "apple"]
        env.reset(options={"wizkit_items": req_items})

        # TODO: Test inventory here.
        env.reset(options={"wizkit_items": req_items})
        del env


@pytest.mark.parametrize("env_name", [e for e in get_nethack_env_ids() if "Score" in e])
class TestBasicGymEnv:
    def test_inventory(self, env_name):
        env = gym.make(
            env_name,
            observation_keys=(
                "chars",
                "inv_glyphs",
                "inv_strs",
                "inv_letters",
                "inv_oclasses",
            ),
        )
        obs, reset_info = env.reset()

        found = dict(spellbook=0, apple=0)
        for line in obs["inv_strs"]:
            if np.all(line == 0):
                break
            for key in found:
                if key in line.tobytes().decode("utf-8"):
                    found[key] += 1

        for key, count in found.items():
            assert key == key and count > 0

        assert "inv_strs" in obs

        index = 0
        if obs["inv_letters"][index] != ord("a"):
            # We autopickedup some gold.
            assert obs["inv_letters"][index] == ord("$")
            assert obs["inv_oclasses"][index] == nethack.COIN_CLASS
            index = 1

        assert obs["inv_letters"][index] == ord("a")
        assert obs["inv_oclasses"][index] == nethack.ARMOR_CLASS


@pytest.mark.parametrize("env_name", get_nethack_env_ids())
@pytest.mark.parametrize("rollout_len", [500])
class TestGymEnvRollout:
    @pytest.fixture(autouse=True)  # will be applied to all tests in class
    def make_cwd_tmp(self, tmpdir):
        """Makes cwd point to the test's tmpdir."""
        with tmpdir.as_cwd():
            yield

    def test_rollout(self, env_name, rollout_len):
        """Tests rollout_len steps (or until termination) of random policy."""
        with tempfile.TemporaryDirectory() as savedir:
            env = gym.make(env_name, save_ttyrec_every=1, savedir=savedir)
            rollout_env(env, rollout_len)
            env.close()

            assert os.path.exists(
                os.path.join(
                    savedir,
                    "nle.%i.0.ttyrec%i.bz2" % (os.getpid(), nethack.TTYREC_VERSION),
                )
            )
            assert os.path.exists(
                os.path.join(savedir, "nle.%i.xlogfile" % os.getpid())
            )

    def test_rollout_no_archive(self, env_name, rollout_len):
        """Tests rollout_len steps (or until termination) of random policy."""
        env = gym.make(env_name, savedir=None)
        assert env.unwrapped.savedir is None
        rollout_env(env, rollout_len)

    def test_seed_interface_output(self, env_name, rollout_len):
        """Tests whether env.seed output can be reused correctly."""
        if env_name.startswith("NetHackChallenge"):
            pytest.skip("Not running seed test on NetHackChallenge")

        env0 = gym.make(env_name)
        env1 = gym.make(env_name)

        seed_list0 = env0.unwrapped.seed()
        env0.reset()

        assert env0.unwrapped.get_seeds() == seed_list0

        seed_list1 = env1.unwrapped.seed(*seed_list0)
        assert seed_list0 == seed_list1

    def test_seed_rollout_seeded(self, env_name, rollout_len):
        """Tests that two seeded envs return same step data."""
        if env_name.startswith("NetHackChallenge"):
            pytest.skip("Not running seed test on NetHackChallenge")

        env0 = gym.make(env_name)
        env1 = gym.make(env_name)

        env0.unwrapped.seed(123456, 789012)
        obs0 = env0.reset()
        seeds0 = env0.unwrapped.get_seeds()

        assert seeds0 == (123456, 789012, False, None)

        env1.unwrapped.seed(*seeds0)
        obs1 = env1.reset()
        seeds1 = env1.unwrapped.get_seeds()

        assert seeds0 == seeds1

        np.testing.assert_equal(obs0, obs1)
        compare_rollouts(env0, env1, rollout_len)

    def test_seed_rollout_seeded_int(self, env_name, rollout_len):
        """Tests that two seeded envs return same step data."""
        if env_name.startswith("NetHackChallenge"):
            pytest.skip("Not running seed test on NetHackChallenge")

        env0 = gym.make(env_name)
        env1 = gym.make(env_name)

        initial_seeds = (
            random.randrange(sys.maxsize),
            random.randrange(sys.maxsize),
            False,
            random.randrange(sys.maxsize),
        )
        env0.unwrapped.seed(*initial_seeds)
        obs0 = env0.reset()
        seeds0 = env0.unwrapped.get_seeds()

        env1.unwrapped.seed(*seeds0)
        obs1 = env1.reset()
        seeds1 = env1.unwrapped.get_seeds()

        assert seeds0 == seeds1 == initial_seeds

        np.testing.assert_equal(obs0, obs1)
        compare_rollouts(env0, env1, rollout_len)

    def test_seed_lgen(self, env_name, rollout_len):
        """Tests that the lgen seed returns deterministic dungeon structure"""
        if env_name.startswith("NetHackChallenge"):
            pytest.skip("Not running seed test on NetHackChallenge")

        env = gym.make(env_name)
        env.unwrapped.seed(lgen=1)
        obs = env.reset()

        assert env.unwrapped.get_seeds()[3] == 1

        # check for the first room the agent appears.
        assert obs[0]["chars"][3][61] == ord("-")
        assert obs[0]["chars"][4][51] == ord(".")
        assert obs[0]["chars"][5][59] == ord(".")
        assert obs[0]["chars"][7][65] == ord("|")
        assert obs[0]["chars"][7][51] == ord("@")

    def test_seeds_with_lgen(self, env_name, rollout_len):
        """Tests that the lgen seed returns deterministic dungeon structure,
        when passed alongside other NetHack seed values"""
        if env_name.startswith("NetHackChallenge"):
            pytest.skip("Not running seed test on NetHackChallenge")

        env = gym.make(env_name)
        env.unwrapped.seed(1234, 5678, False, 1)
        obs = env.reset()

        assert env.unwrapped.get_seeds()[3] == 1

        # check for the first room the agent appears.
        assert obs[0]["chars"][3][61] == ord("-")
        assert obs[0]["chars"][4][51] == ord(".")
        assert obs[0]["chars"][5][59] == ord(".")
        assert obs[0]["chars"][7][65] == ord("|")
        assert obs[0]["chars"][7][51] == ord("@")

    # Further level-generation tests:
    # There should be a test that compares level two in multiple
    # rollouts. That requires an agent that can successfully and
    # always find the stairs and descend to the second level. To
    # say nothing about deeper levels of the dungeon! For now it
    # doesn't exist, and so remains an active area of research.
    #
    # Left as an exercise for the student?

    def test_render_ansi(self, env_name, rollout_len):
        env = gym.make(env_name, render_mode="ansi")
        env.reset()
        for _ in range(rollout_len):
            action = env.action_space.sample()
            _, _, terminated, _, _ = env.step(action)
            if terminated:
                env.reset()
            output = env.render()
            assert isinstance(output, str)
            assert len(output.replace("\n", "")) == np.prod(nle.env.DUNGEON_SHAPE)


class TestGymDynamics:
    """Tests a few game dynamics."""

    @pytest.fixture(autouse=True)  # Will be applied to all tests in class.
    def make_cwd_tmp(self, tmpdir):
        """Makes cwd point to the test's tmpdir."""
        with tmpdir.as_cwd():
            yield

    @pytest.fixture
    def env(self):
        e = gym.make("NetHackScore-v0")
        try:
            yield e
        finally:
            e.close()

    def test_kick_and_quit(self, env):
        env.reset()
        kick = env.unwrapped.actions.index(nethack.Command.KICK)
        obs, reward, terminated, _, _ = env.step(kick)
        assert b"In what direction? " in bytes(obs["message"])
        env.step(nethack.MiscAction.MORE)

        # Hack to quit.
        env.unwrapped.nethack.step(nethack.M("q"))
        obs, reward, terminated, _, _ = env.step(env.unwrapped.actions.index(ord("y")))

        assert terminated
        assert reward == 0.0

    def test_final_reward(self, env):
        obs, reset_info = env.reset()

        for _ in range(100):
            obs, reward, terminated, _, info = env.step(env.action_space.sample())
            if terminated:
                break

        if terminated:
            assert reward == 0.0
            return

        # Hopefully, we got some positive reward by now.

        # Get out of any menu / yn_function.
        env.step(env.unwrapped.actions.index(ord("\r")))

        # Hack to quit.
        env.unwrapped.nethack.step(nethack.M("q"))
        _, reward, terminated, _, info = env.step(env.unwrapped.actions.index(ord("y")))

        assert terminated
        assert reward == 0.0

    def test_ttyrec_every(self):
        path = pathlib.Path(".")
        env = gym.make("NetHackChallenge-v0", save_ttyrec_every=2, savedir=str(path))
        pid = os.getpid()
        for episode in range(10):
            env.reset()
            for c in [ord(" "), ord(" "), ord("<"), ord("y")]:
                _, _, terminated, *_ = env.step(env.unwrapped.actions.index(c))
            assert terminated

            if episode % 2 != 0:
                continue
            contents = {str(p) for p in path.iterdir()}
            # `contents` includes xlogfile and ttyrecs.
            assert len(contents) - 1 == episode // 2 + 1
            assert (
                "nle.%i.%i.ttyrec%i.bz2" % (pid, episode, nethack.TTYREC_VERSION)
                in contents
            )
            assert "nle.%i.xlogfile" % pid in contents

        with open("nle.%i.xlogfile" % pid, "r") as f:
            entries = f.readlines()

        assert len(entries) == 10

    def test_env_truncation(self):
        test_horizon = 10

        env = gym.make("NetHack-v0", max_episode_steps=test_horizon)
        env.reset()
        for _steps in range(test_horizon - 1):
            obs, reward, termination, truncation, info = env.step(
                nethack.MiscDirection.WAIT
            )
            assert not termination
            assert not truncation

        obs, reward, termination, truncation, info = env.step(
            nethack.MiscDirection.WAIT
        )
        assert not termination
        assert truncation


class TestEnvMisc:
    """Tests miscellaneous enviroment behavior."""

    @pytest.fixture
    def env(self):
        if sys.version_info < (3, 8):
            e = gym.make("NetHackScore-v0")
        else:
            # gym 0.24+ doesnt like the shape of our observations.
            e = gym.make("NetHackScore-v0")
        try:
            yield e
        finally:
            e.close()

    def test_no_reset(self, env):
        with pytest.raises(RuntimeError, match="step called without reset()"):
            env.step(0)


class TestNetHackChallenge:
    def test_no_seed_setting(self):
        env = gym.make("NetHackChallenge-v0")
        with pytest.raises(
            RuntimeError, match="NetHackChallenge doesn't allow seed changes"
        ):
            env.unwrapped.seed()

        with pytest.raises(RuntimeError, match="Should not try changing seeds"):
            env.unwrapped.nethack.set_initial_seeds(0, 0, True)
