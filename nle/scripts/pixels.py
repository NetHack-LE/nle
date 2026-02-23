import gymnasium as gym
from PIL import Image

import nle  # noqa: F401

env = gym.make("NetHack-v0", render_mode="pixel")
# env = gym.wrappers.AddRenderObservation(
#     env, render_only=False, render_key="pixel", obs_key="glyphs"
# )
env.unwrapped.seed(1234, 5678, False, 1)


frames = []

obs = env.reset()
frame = obs[0]["pixel"]
img = Image.fromarray(frame, "RGB")
frames.append(img)

NORTH = 0
WEST = 3
SOUTH = 2
EAST = 1

# Get out of starting room
steps = [EAST, EAST, NORTH, NORTH, WEST, WEST, WEST, WEST, WEST]
# Go to room two
steps += [
    SOUTH,
    SOUTH,
    SOUTH,
    SOUTH,
    SOUTH,
    WEST,
    SOUTH,
    WEST,
    SOUTH,
    SOUTH,
    SOUTH,
    SOUTH,
    SOUTH,
    WEST,
    SOUTH,
    WEST,
    WEST,
]
# Traverse room two
steps += [WEST, WEST, WEST, WEST, NORTH, NORTH, NORTH, NORTH]
# Go to room three
steps += [
    WEST,
    NORTH,
    NORTH,
    WEST,
    WEST,
    NORTH,
    NORTH,
    WEST,
    WEST,
    NORTH,
    NORTH,
    WEST,
    WEST,
    WEST,
    WEST,
    WEST,
    WEST,
    WEST,
    WEST,
    NORTH,
]
# Traverse room three
steps += [NORTH, NORTH]
# Go back towards room two and kill the monster
steps += [SOUTH, SOUTH, SOUTH, EAST, EAST, EAST, EAST, EAST]
# Continue to room two
steps += [
    EAST,
    EAST,
    EAST,
    SOUTH,
    SOUTH,
    EAST,
    EAST,
    SOUTH,
    SOUTH,
    EAST,
    EAST,
    SOUTH,
    SOUTH,
    EAST,
    SOUTH,
    SOUTH,
]
# Traverse room two to other exit
steps += [WEST, WEST, WEST, WEST, WEST, WEST, WEST, WEST, WEST, NORTH]
# Go to room four
steps += [NORTH, NORTH, NORTH, NORTH]

for action in range(len(steps)):
    obs = env.step(steps[action])
    env.unwrapped.nethack.draw_frame(frame)
    img = Image.fromarray(frame, "RGB")
    frames.append(img)

print(f"Saving animation with {len(frames)} frames...")
frames[0].save(
    "nethack_tiles_animation.gif",
    save_all=True,
    append_images=frames[1:],
    duration=400,
    loop=0,
)
