"""Quick sketch, not a new version: how the brooks should meet the water. A (brooks into the canal, joining with the flow)
vs B (a small river in the valley beside the canal; the brooks join the river, Mill Brook passes under the canal).
python3 tools/plan/village_water_sketch.py -> design/world/village_water_sketch.png
Marcel, 2026-11-09: "rivieren lopen nooit op 90 graden op elkaar af of wel" -> "Kan je een snelle schets van beide maken?"
"""
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import LineString, Point

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L
import world_plan_v5 as W

OUT = os.path.join(HERE, "../../design/world/village_water_sketch.png")
R = L.R
sm = L._chaikin

# A: the brooks bend with the canal's flow (west -> east, i.e. to the right) and join at a sharp angle
MILL_A = list(L.BROOK.coords)
MILL_A = [c for c in MILL_A if c[1] < 120] + [(-445, 140), (-432, 168), (-412, 186), (-388, 196)]          # past the mill, into the canal
HOLME_A = [c for c in L.BROOK2.coords if c[1] > 320] + [(258, 290), (272, 250), (296, 220), (330, 205)]

# B: a small river on the low side of the valley beyond the canal (between canal and railway), meandering, west -> east
_cy = lambda x: float(np.interp(x, [c[0] for c in L.CANAL_PTS], [c[1] for c in L.CANAL_PTS]))
RIVER = LineString(sm([(-R, _cy(-R) + 150)] + [(x, _cy(x) + 70 + 40 * math.sin(x / 140.0) + 20 * math.sin(x / 47.0))
                                               for x in np.linspace(-950, 950, 24)] + [(R, _cy(R) + 120)], 3))
MILL_B = [c for c in L.BROOK.coords if c[1] < 120] + [(-445, 140), (-430, 175), (-418, 200), (-410, 230)]
MILL_B += [(-395, _cy(-395) + 50), (-370, _cy(-370) + 75)]          # under the canal (culvert) then into the river, with the flow
_rx = lambda x: float(np.interp(x, [c[0] for c in RIVER.coords], [c[1] for c in RIVER.coords]))
HOLME_B = [c for c in L.BROOK2.coords if c[1] > _rx(c[0]) + 90] + [(272, _rx(272) + 55), (296, _rx(296) + 25), (325, _rx(325) + 6)]


def panel(ax, title, brooks, river=None, culvert=None):
    n = 260
    xs = np.linspace(-R, R, n)
    X, Y = np.meshgrid(xs, xs)
    H = L.height_raw(X, Y)
    cmap = LinearSegmentedColormap.from_list("land", ["#e6edd3", "#d3dfb4", "#bccb92", "#a9b97f", "#8d966c"])
    rgb = LightSource(azdeg=315, altdeg=40).shade(H, cmap=cmap, vert_exag=6, blend_mode="soft", vmin=0, vmax=150)
    ax.imshow(rgb, extent=(-R, R, -R, R), origin="lower", zorder=0)
    ax.set_xlim(-R, R); ax.set_ylim(-R, R); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    cx, cy = L.CANAL.buffer(6).exterior.xy
    ax.fill(cx, cy, fc="#9cc7dc", ec="#3f7fa8", lw=0.8, zorder=5)
    rx, ry = L.RAIL.xy
    ax.plot(rx, ry, color="#444", lw=2.4, zorder=6)
    ax.plot(rx, ry, color="white", lw=1.0, zorder=6, ls=(0, (3, 3)))
    gx, gy = W.PLOT.exterior.xy
    ax.fill(gx, gy, fc="#E3EFD9", ec="#2F5B3F", lw=1.0, zorder=7)
    ax.text(0, 0, "ground", ha="center", va="center", fontsize=8, zorder=8)
    if river is not None:
        vx, vy = river.buffer(7).exterior.xy
        ax.fill(vx, vy, fc="#7fb6d6", ec="#2f6f98", lw=0.8, zorder=5)
        p = river.interpolate(0.3, normalized=True)
        ax.text(p.x, p.y + 45, "small river (name later)", fontsize=8.5, weight="bold", color="#1d4f7a", zorder=20, ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    for pts, name in brooks:
        ln = LineString(sm(pts, 2))
        bx, by = ln.buffer(3).exterior.xy
        ax.fill(bx, by, fc="#7fb6d6", ec="#2f6f98", lw=0.5, zorder=6)
        # zoom box on the mouth
        e = Point(ln.coords[-1])
        ax.add_patch(plt.Circle((e.x, e.y), 70, fc="none", ec="#c0392b", lw=1.4, zorder=12))
    ax.plot([-420], [205], marker="s", ms=8, color="#7A6A5A", mec="#222", zorder=13)
    ax.text(-470, 250, "mill", fontsize=8, zorder=20)
    if culvert is not None:
        ax.plot([culvert[0]], [culvert[1]], marker="o", ms=9, mfc="white", mec="#222", zorder=14)
        ax.text(culvert[0] + 25, culvert[1] - 40, "culvert under\nthe canal", fontsize=8, zorder=20)
    # flow arrows on the canal
    for x in (-600, 0, 600):
        y = _cy(x)
        ax.annotate("", xy=(x + 90, _cy(x + 90)), xytext=(x, y), arrowprops=dict(arrowstyle="->", color="#1d4f7a", lw=1.6), zorder=15)
    ax.text(-560, _cy(-560) - 45, "canal flows ->", fontsize=8, color="#1d4f7a", zorder=20)
    ax.set_title(title, fontsize=11, loc="left")


fig, axs = plt.subplots(1, 2, figsize=(22, 11.6), dpi=95)
panel(axs[0], "A — brooks bend with the flow and join the canal at a sharp angle (red circles)",
      [(MILL_A, "Mill Brook"), (HOLME_A, "Holme Beck")])
panel(axs[1], "B — a small river beside the canal; brooks join the river with the flow,\n     Mill Brook drives the mill, passes under the canal, then joins the river",
      [(MILL_B, "Mill Brook"), (HOLME_B, "Holme Beck")], river=RIVER, culvert=(-412, _cy(-412)))
fig.suptitle("QUICK SKETCH — not a new version · where the water goes", fontsize=13, x=0.02, ha="left")
fig.savefig(OUT, bbox_inches="tight", pad_inches=0.1)
print("saved", os.path.relpath(OUT))
