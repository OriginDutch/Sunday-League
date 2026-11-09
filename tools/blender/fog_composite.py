"""Put the game's depth fog over a town render: python3 fog_composite.py beauty.png mist.png out.png
The mist pass holds (distance - 120) / 280 clamped, written through the sRGB transform; the game uses curve 1.6
and fog colour (0.75, 0.82, 0.9) (main.gd: FOG_BEGIN 120, FOG_END 400)."""
import sys
import numpy as np
from PIL import Image

beauty = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32) / 255
m = np.asarray(Image.open(sys.argv[2]).convert("L")).astype(np.float32) / 255
t = np.where(m <= 0.04045, m / 12.92, ((m + 0.055) / 1.055) ** 2.4)      # back to linear
f = np.clip(t, 0, 1) ** 1.6
fog = np.array([0.75, 0.82, 0.9], np.float32)
out = beauty * (1 - f[..., None]) + fog * f[..., None]
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(sys.argv[3])
