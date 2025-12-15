# import matplotlib.pyplot as plt
import numpy as np

from nle import _pynethack

nh = _pynethack.Nethack(".", ".", "", False)
nh.setup_tiles()

frame = np.zeros(16 * 16 * 3, dtype=np.uint8)
print(frame)
nh.get_tileset(frame)
print(frame)
