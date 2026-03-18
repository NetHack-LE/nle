Using NetHack's tiles for image observations
============================================

Tiles
*****

NetHack as we know and love is a text based game with characters representing the dungeon 
levels and objects. The RL Environment represents these in an observation numpy array:

.. code-block:: python

    obs[0]["chars"]

Each character is also associated with a unique glyph id, which is represented in the "glyph" observation:

.. code-block:: python

    obs[0]["glyph"]

NetHack also contains a set of tile descriptor files which can be used to generate
the equivalent RGB values so that the game can be rendered as an image-based display.

The source for the descriptor files are here:

.. code-block:: console

    win/share/monsters.txt
    win/share/objects.txt
    win/share/other.txt

When converted to RGB, the full set of tiles looks like this:

.. image:: https://github.com/NetHack-LE/nle/raw/main/dat/nle/tileset.png
    :alt: NetHack tileset
    :align: center
\

Installation
************

The tile descriptor files are included in the distribution and are installed in the 
`nethackdir/tiles` directory.


Initialisation
**************

To get NLE to render the tiles as an observation set, you must set the render_mode to
"pixel" when the environment is created. For example:

.. code-block:: python

    env = gym.make("NetHack-v0", render_mode="pixel")

The next step is to add the Gymnasium RenderObservationWrapper to the environment. This 
ensures that every time the envrionment is rendered, the observations will include the
RGB tile observations automatically.

.. code-block:: python

    env = gym.wrappers.AddRenderObservation(
        env, render_only=False, render_key="pixel", obs_key="glyphs")

RGB observations
****************

The RGB tiles representing the underlying dungeon can be accessed using the "pixel"
key in the observations dictionary.

.. code-block:: python
    
    rgb_frame = obs[0]["pixel"]

This frame is a 3D numpy array, each 2D slice represents all the pixels in the
rendered game screen, and the 3rd dimension represents the RGB values for each pixel.

Example
*******

Here's a short example of how to set up the environment to use the tile-based RGB observations:

(Note that you need to install the Pillow library to run this example, which can be done with `pip install Pillow`)

.. code-block:: python
    
    import gymnasium as gym
    from PIL import Image
    import nle

    env = gym.make("NetHack-v0", render_mode="pixel")
    env = gym.wrappers.AddRenderObservation(
        env, render_only=False, render_key="pixel", obs_key="glyphs")
    env.unwrapped.seed(1234, 5678, False, 1)

    obs, _ = env.reset()  # each reset generates a new dungeon
    rgb_frame = obs["pixel"]

    # Convert the RGB frame to an image and display it
    img = Image.fromarray(rgb_frame)
    img.show()


Here's an animated example of what the tile-based rendering looks like
after a few steps in the environment:

.. image:: https://github.com/NetHack-LE/nle/raw/main/dat/nle/nethack_tiles_animation.gif
    :alt: NetHack tileset
    :align: center
\
