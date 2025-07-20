import gymnasium as gym
import nle

env=gym.make("NetHack-v0", render_mode="pixel")
env2=gym.wrappers.AddRenderObservation(env, render_only=False, render_key="pixel", obs_key="glyphs")

obs=env2.reset()

print(obs)