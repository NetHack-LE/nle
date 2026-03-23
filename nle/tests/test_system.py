# Copyright (c) Facebook, Inc. and its affiliates.

import ctypes
import functools
import multiprocessing as mp
import queue
import random
import threading

import gymnasium as gym
import pytest

import nle  # noqa: F401

START_METHODS = [m for m in ("fork", "spawn") if m in mp.get_all_start_methods()]


def new_env_one_step():
    env = gym.make("NetHackScore-v0")
    env.reset()
    obs, reward, terminated, _, _ = env.step(0)
    return terminated


@functools.cache
def is_asan():
    """Checks if the process is running with ASAN.

    See if the __asan_init symbol is present in the current process.
    """

    current_process = ctypes.CDLL(None)
    return hasattr(current_process, "__asan_init")


@pytest.mark.parametrize(
    "ctx", [mp.get_context(m) for m in START_METHODS], ids=START_METHODS
)
class TestEnvSubprocess:
    def test_env_in_subprocess(self, ctx):
        if ctx.get_start_method() == "spawn" and is_asan():
            pytest.skip("ASAN crashes on spawn on this environment")
        p = ctx.Process(target=new_env_one_step)
        p.start()
        p.join()
        assert p.exitcode == 0

    def test_env_before_and_in_subprocess(self, ctx):
        if ctx.get_start_method() == "spawn" and is_asan():
            pytest.skip("ASAN crashes on spawn on this environment")
        new_env_one_step()
        p = ctx.Process(target=new_env_one_step)
        p.start()
        p.join()
        assert p.exitcode == 0


ACTIONS = [0, 1, 2]


class TestParallelEnvs:
    def test_two_nles(self):
        envs = [gym.make("NetHackScore-v0") for _ in range(2)]

        env, *queue = envs
        env.reset()

        num_resets = 1

        while num_resets < 4:
            _, _, terminated, _, _ = env.step(random.choice(ACTIONS))
            if terminated:
                queue.append(env)
                env = queue.pop(0)
                env.reset()
                num_resets += 1

    def test_threaded_nles(self, num_envs=10, num_threads=3):
        readyqueue = queue.Queue()
        resetqueue = queue.Queue()

        def target():
            while True:
                env = resetqueue.get()
                if env is None:
                    return
                env.reset()
                readyqueue.put(env)

        threads = [threading.Thread(target=target) for _ in range(num_threads)]
        for t in threads:
            t.start()

        envs = [gym.make("NetHackScore-v0") for _ in range(num_envs)]
        for env in envs:
            resetqueue.put(env)
        env = readyqueue.get()

        num_resets = 1

        while num_resets < 4:
            a = random.choice(ACTIONS)
            _, _, terminated, _, _ = env.step(a)
            if terminated:
                resetqueue.put(env)
                env = readyqueue.get()
                num_resets += 1

        for _ in threads:
            resetqueue.put(None)

        for t in threads:
            t.join()
