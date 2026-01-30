# import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from nle import _pynethack

nh = _pynethack.Nethack(".", ".", "", False)

tile_paths = [
    "/Users/stephenoman/Development/nle/win/share/monsters.txt",
    "/Users/stephenoman/Development/nle/win/share/objects.txt",
    "/Users/stephenoman/Development/nle/win/share/other.txt",
]
nh.setup_tiles(tile_paths)

frame = np.zeros((432, 640, 3), dtype=np.uint8)
nh.get_tileset(frame)
print(frame)

img = Image.fromarray(frame, "RGB")
img.save("tileset.png")
