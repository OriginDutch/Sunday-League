"""Glue the --hair-sheet renders into design/3d/player/hairstyles.png + beards.png (then deletes the frames)."""
import glob, os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(__file__), "..", "..", "design", "3d", "player")
idx = open(os.path.join(D, "_sheet_index.txt")).read().split("\n#\n")
hairs, beards = idx[0].split("\n"), idx[1].split("\n")
W, cols = 200, 10
rows = (len(hairs) + cols - 1) // cols
im = Image.new("RGB", (cols * W, rows * W * 2), (40, 40, 40))
for i, h in enumerate(hairs):
    c, r = i % cols, i // cols
    for j, s in enumerate("ab"):
        im.paste(Image.open(os.path.join(D, f"_h_{h}_{s}.png")), (c * W, (r * 2 + j) * W))
    ImageDraw.Draw(im).text((c * W + 4, r * 2 * W + 4), h[5:], fill=(255, 255, 255))
im.save(os.path.join(D, "hairstyles.png"))
im = Image.new("RGB", (3 * W, (len(beards) // 3) * W))
for i, b in enumerate(beards):
    im.paste(Image.open(os.path.join(D, f"_b_{b}.png")), ((i % 3) * W, (i // 3) * W))
    ImageDraw.Draw(im).text(((i % 3) * W + 4, (i // 3) * W + 4), b[6:], fill=(255, 255, 255))
im.save(os.path.join(D, "beards.png"))
for f in glob.glob(os.path.join(D, "_h_*")) + glob.glob(os.path.join(D, "_b_*")) + [os.path.join(D, "_sheet_index.txt")]:
    os.remove(f)
