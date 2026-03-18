import gymnasium as gym
import numpy as np
import pytest

import nle


class TestTileset:
    # Test that the tile files can be read successfully
    # with the default paths & that the tileset is correctly
    # generated.
    def test_tile_setup_repo(self):
        nh = nle.nethack.Nethack()
        nh.setup_tiles()
        tileset = np.zeros((432, 640, 3), dtype=np.uint8)
        nh.get_tileset(tileset)

        assert tileset[0][0][0] == 71
        assert tileset[431][638][2] == 108

    # Test that invalid tile paths raise an error.
    def test_tile_setup_invalid_path(self):
        nh = nle.nethack.Nethack()
        with pytest.raises(RuntimeError):
            nh.setup_tiles(
                [
                    "invalid/path/monsters.txt",
                    "invalid/path/objects.txt",
                    "invalid/path/other.txt",
                ]
            )

    # Stupid test but am doing it anyway :-)
    # Test that the tileset cannot be retrieved if the frame is too big
    def test_tileset_too_large(self):
        nh = nle.nethack.Nethack()
        nh.setup_tiles()
        tileset = np.zeros((1000, 1000, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError):
            nh.get_tileset(tileset)

    # Alternatively, test that the tileset can be retrieved if the frame is too small.
    def test_tileset_too_small(self):
        nh = nle.nethack.Nethack()
        nh.setup_tiles()
        tileset = np.zeros((100, 100, 3), dtype=np.uint8)
        nh.get_tileset(tileset)

        assert tileset[0][0][0] == 71
        assert tileset[99][99][2] == 0


class TestDrawingFrame:
    def test_drawing_frame_before_tileset_setup(self):
        nh = nle.nethack.Nethack()
        frame = np.zeros(nle.nethack.TILE_RENDER_SHAPE, dtype=np.uint8)
        with pytest.raises(RuntimeError):
            nh.draw_frame(frame)

    def test_drawing_frame_with_invalid_frame_size(self):
        nh = nle.nethack.Nethack()
        nh.setup_tiles()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            nh.draw_frame(frame)


class TestTileObservations:
    def test_observation_contains_pixels(self):
        env = gym.make("NetHack-v0", render_mode="pixel")
        env = gym.wrappers.AddRenderObservation(
            env, render_only=False, render_key="pixel", obs_key="glyphs"
        )
        obs = env.reset()

        assert "pixel" in obs[0]

    # Test that the observation contains the correct pixel data for the starting location of the hero.
    def test_hero_pixel_values(self):
        env = gym.make("NetHack-v0", render_mode="pixel")
        env = gym.wrappers.AddRenderObservation(
            env, render_only=False, render_key="pixel", obs_key="glyphs"
        )
        env.unwrapped.seed(1234, 5678, False, 1)

        obs = env.reset()

        # The monk hero should be at location (7,51) with this seed.
        assert obs[0]["chars"][7][51] == ord("@")
        assert obs[0]["glyphs"][7][51] == 333

        # The pixel location corresponding to (7,51) is (7*16, 51*16) = (112, 816).
        # Pick out the R values of the piles a few rows down to check that the correct tiles are being rendered.
        assert obs[0]["pixel"][115][822][0] == 145
        assert obs[0]["pixel"][115][823][0] == 255
        assert obs[0]["pixel"][115][824][0] == 145
