Getting Started
===============

Dependencies
************

NLE requires `python>=3.10`, `cmake>=3.28` and some NetHack dependencies
(e.g. `libncurses`) to be installed and available both when building the
package, and at runtime.

On **MacOS**, one can use `Homebrew` as follows:

.. code-block:: console

    $ brew install ncurses cmake


On a plain **Ubuntu 18.04** distribution, `cmake` and other dependencies
can be installed by doing:

.. code-block:: console

    # Python and most build deps
    $ sudo apt-get install -y build-essential autoconf libtool pkg-config \
        python3-dev python3-pip python3-numpy git libncurses5-dev flex bison

    # recent cmake version
    $ wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | sudo apt-key add -
    $ sudo apt-add-repository 'deb https://apt.kitware.com/ubuntu/ bionic main'
    $ sudo apt-get update && apt-get --allow-unauthenticated install -y \
        cmake \
        kitware-archive-keyring


Installation
************

To then install nle, simply do:

.. code-block:: bash

   $ conda activate nledev
   $ pip install nle


Optionally, one can clone the repository and install the package manually.

.. code-block:: bash

   $ git clone https://github.com/NetHack-LE/nle
   $ conda activate nledev
   $ pip install .


Trying it out
*************

After installation, one can try out any of the provided tasks as follows:

.. code-block:: python
    
    import gymnasium as gym
    import nle
    env = gym.make("NetHackScore-v0")
    env.reset()  # each reset generates a new dungeon
    env.step(1)  # move agent '@' north
    env.render()

NLE also comes with a few scripts that allow to get some environment rollouts, and
play with the action space:

.. code-block:: bash

    $ python -m nle.scripts.play
    $ python -m nle.scripts.random_agent
    $ python -m nle.scripts.play_random_games


Additionally, a `TorchBeast <https://github.com/facebookresearch/torchbeast>`_
agent is bundled in ``nle.agent`` together with a simple model to provide a
starting point for experiments:

.. code-block:: bash

    $ pip install ".[agent]"
    $ python -m nle.agent.agent --help
