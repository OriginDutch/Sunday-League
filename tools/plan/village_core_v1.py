"""Step 3 — the old core, first sketch (Claude's proposal for Marcel, 2026-11-09).
python3 tools/plan/village_core_v1.py -> design/world/village_core_v1.png

Built on the land + main roads of village_land_v1. Rules we agreed: nothing floating (everything on a road), no square
blocks / parks, shapes follow the streets, the church on the highest point of the dry rise, park 1 = churchyard +
cemetery park next to the church, the mill is NOT here (it is across from the ground), the old stone bridge is the start.
Variant A (market street) with a small green where the old road north forks off (a touch of B).
Medieval logic: long narrow burgage plots behind the frontages, ending in back lanes; ginnels between houses.
"""
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, substring

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L

OUT = os.path.join(HERE, "../../design/world/village_core_v1.png")
VIEW = (-760, -250, -150, 240)
ch = L._chaikin

# ---------------------------------------------------------------- High Street: from the old bridge up the dry rise
HS = LineString(ch([(-497, 98), (-472, 74), (-444, 47), (-414, 20), (-382, -9), (-350, -40), (-312, -73)], 3))


def frame(line, s):
    d = s * line.length
    p = line.interpolate(d)
    a = line.interpolate(max(d - 2, 0)); b = line.interpolate(min(d + 2, line.length))
    tx, ty = b.x - a.x, b.y - a.y
    T = math.hypot(tx, ty) or 1
    return p, (tx / T, ty / T), (-ty / T, tx / T)


def half_width(s):
    """The street is ~10 m wide and swells to a ~34 m market place in its middle (lens shape, no straight edges)."""
    base = 5.0
    if 0.33 <= s <= 0.78:
        f = (s - 0.33) / 0.45
        return base + 12.0 * math.sin(math.pi * f) ** 1.3
    return base


left, right = [], []
for s in np.linspace(0, 1, 120):
    p, t, n = frame(HS, s)
    hw = half_width(s)
    left.append((p.x + n[0] * hw, p.y + n[1] * hw))
    right.append((p.x - n[0] * hw, p.y - n[1] * hw))
STREET = Polygon(left + right[::-1]).buffer(0)
MARKET = STREET.difference(HS.buffer(5.5))
_mp, _mt, _mn = frame(HS, 0.56)
MARKET_HALL = Polygon([(_mp.x + _mt[0] * a + _mn[0] * b, _mp.y + _mt[1] * a + _mn[1] * b)
                       for a, b in ((-10, -4.5), (10, -4.5), (10, 4.5), (-10, 4.5))])
_cp, _, _ = frame(HS, 0.43)
MARKET_CROSS = (_cp.x, _cp.y)

# which side of the street the dry rise / church is on
_p, _t, _n = frame(HS, 0.7)
RISE = (-395, -62)
CHURCH_SIDE = 1 if ((RISE[0] - _p.x) * _n[0] + (RISE[1] - _p.y) * _n[1]) > 0 else -1

# ---------------------------------------------------------------- church on the top of the rise, churchyard round it
CHURCH_C = (-405, -70)
# a church lies east-west (altar east): east = +y in plan
CHURCH = Polygon([(CHURCH_C[0] - 6, CHURCH_C[1] - 16), (CHURCH_C[0] + 6, CHURCH_C[1] - 16), (CHURCH_C[0] + 6, CHURCH_C[1] + 14),
                  (CHURCH_C[0] + 4, CHURCH_C[1] + 18), (CHURCH_C[0] - 4, CHURCH_C[1] + 18), (CHURCH_C[0] - 6, CHURCH_C[1] + 14)]).union(
    box(CHURCH_C[0] - 4, CHURCH_C[1] - 24, CHURCH_C[0] + 4, CHURCH_C[1] - 16))          # west tower
CHURCHYARD = Polygon(ch([(-372, -48), (-390, -32), (-420, -36), (-446, -58), (-448, -90), (-430, -112), (-398, -114),
                         (-374, -96), (-364, -72)], 3))
_gp, _, _ = frame(HS, 0.82)
CHURCH_LANE = LineString(ch([(_gp.x, _gp.y), (-360, -50), (-372, -48)], 2))
# park 1: the cemetery park behind the churchyard, down to Mill Brook's clough (follows the brook, not a box)
CEMETERY_PARK = Polygon(ch([(-446, -58), (-470, -40), (-505, -30), (-545, -45), (-580, -20), (-598, 20), (-590, 55),
                            (-560, 40), (-530, 5), (-498, -8), (-470, -10), (-452, -30)], 2)).buffer(0).difference(
    L.BROOK.buffer(5)).union(Polygon(ch([(-448, -90), (-470, -110), (-520, -112), (-555, -80), (-545, -45), (-505, -30),
                                         (-470, -40), (-446, -58)], 2)).buffer(0))
CEM_GRAVES = Polygon(ch([(-452, -92), (-470, -104), (-512, -104), (-538, -80), (-530, -55), (-500, -42), (-470, -50)], 2))
CEM_PATHS = [LineString(ch([(-448, -74), (-500, -70), (-540, -62), (-570, -20), (-590, 30)], 2)),
             LineString(ch([(-500, -104), (-500, -40), (-490, -12)], 1))]

# ---------------------------------------------------------------- the old road north: forks off at a small green
_fp, _ft, _fn = frame(HS, 0.28)
FORK = (_fp.x, _fp.y)
OLD_NORTH = LineString(ch([FORK, (FORK[0] - 40, FORK[1] - 12), (-540, 18), (-585, 10), (-625, 4), (-680, -4), (-760, -18)], 3))
_g1 = OLD_NORTH.interpolate(28)
_hp, _, _ = frame(HS, 0.38)
GREEN = Polygon(ch([FORK, (_g1.x, _g1.y), (_hp.x - 30, _hp.y - 30), (_hp.x, _hp.y)], 2)).buffer(-4).buffer(4)
GREEN = GREEN.difference(STREET.buffer(2)).difference(OLD_NORTH.buffer(6))
PACKHORSE = OLD_NORTH.intersection(L.BROOK)           # a little bridge where it crosses Mill Brook

# ---------------------------------------------------------------- back lanes + burgage plots + frontages
PLOT_DEPTH = 52.0
BACK_LANES, PLOTS, FRONTS = [], [], []
blocked = unary_union([CHURCHYARD.buffer(3), CEMETERY_PARK.buffer(3), GREEN.buffer(3), OLD_NORTH.buffer(6),
                       L.BROOK.buffer(8), LineString(L.CANAL_PTS).buffer(L.RIVER_W / 2 + 6), CHURCH_LANE.buffer(5)])
rng = np.random.default_rng(5)
for side in (1, -1):
    lane = []
    s = 0.06
    while s < 0.97:
        p, t, n = frame(HS, s)
        hw = half_width(s)
        w = rng.uniform(5.5, 8.5)                     # frontage width
        d0 = hw + 1.0
        dep = PLOT_DEPTH * rng.uniform(0.85, 1.1)
        q = [(p.x + side * n[0] * d0, p.y + side * n[1] * d0), (p.x + t[0] * w + side * n[0] * d0, p.y + t[1] * w + side * n[1] * d0),
             (p.x + t[0] * w + side * n[0] * (d0 + dep), p.y + t[1] * w + side * n[1] * (d0 + dep)),
             (p.x + side * n[0] * (d0 + dep), p.y + side * n[1] * (d0 + dep))]
        plot = Polygon(q).difference(blocked)
        if not plot.is_empty and plot.area > 120:
            plot = max(getattr(plot, "geoms", [plot]), key=lambda g: g.area)
            PLOTS.append(plot)
            fr = Polygon([q[0], q[1], (q[1][0] + side * n[0] * 10, q[1][1] + side * n[1] * 10),
                          (q[0][0] + side * n[0] * 10, q[0][1] + side * n[1] * 10)]).intersection(plot)
            if not fr.is_empty:
                FRONTS.append(fr)
            lane.append((p.x + t[0] * w / 2 + side * n[0] * (d0 + PLOT_DEPTH + 4), p.y + t[1] * w / 2 + side * n[1] * (d0 + PLOT_DEPTH + 4)))
        else:
            if len(lane) > 4:
                BACK_LANES.append(LineString(ch(lane, 2)))
            lane = []
        s += w / HS.length
    if len(lane) > 4:
        BACK_LANES.append(LineString(ch(lane, 2)))
# ginnels: narrow footpaths from the street to the back lanes, every ~8 plots
GINNELS = []
for i in range(4, len(FRONTS), 9):
    c = FRONTS[i].centroid
    pr = HS.interpolate(HS.project(c))
    dx, dy = c.x - pr.x, c.y - pr.y
    L_ = math.hypot(dx, dy) or 1
    GINNELS.append(LineString([(pr.x + dx / L_ * 6, pr.y + dy / L_ * 6), (pr.x + dx / L_ * (PLOT_DEPTH + 10), pr.y + dy / L_ * (PLOT_DEPTH + 10))]))

# ---------------------------------------------------------------- landmarks in the core
_ip, _it, _in = frame(HS, 0.1)
_iside = -CHURCH_SIDE
INN = Polygon([(_ip.x + _it[0] * a + _iside * _in[0] * b, _ip.y + _it[1] * a + _iside * _in[1] * b)
               for a, b in ((-12, 6), (14, 6), (14, 18), (4, 18), (4, 34), (-12, 34))])          # L-shaped coaching inn + yard
PUBS = [frame(HS, 0.3)[0], frame(HS, 0.62)[0], frame(HS, 0.97)[0]]
SCHOOL = Polygon(ch([(-356, -56), (-340, -66), (-346, -82), (-362, -76)], 1))


# ---------------------------------------------------------------- drawing
def main():
    x0, y0, x1, y1 = VIEW
    xs = np.linspace(x0, x1, 300)
    ys = np.linspace(y0, y1, 240)
    X, Y = np.meshgrid(xs, ys)
    H = L.height(X, Y)
    fig, ax = plt.subplots(figsize=(15, 15 * (y1 - y0) / (x1 - x0)), dpi=120)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    cmap = LinearSegmentedColormap.from_list("land", ["#eef2df", "#dfe8c8", "#cfdcab", "#bccb92", "#a9b97f"])
    ax.imshow(LightSource(azdeg=315, altdeg=40).shade(H, cmap=cmap, vert_exag=4, blend_mode="soft", vmin=0, vmax=60),
              extent=(x0, x1, y0, y1), origin="lower", zorder=0)
    cs = ax.contour(X, Y, H, levels=np.arange(2, 60, 2), colors="#6b5a45", linewidths=0.4, alpha=0.5, zorder=1)
    ax.clabel(cs, levels=np.arange(4, 60, 4), fmt="%d m", fontsize=7)

    def fill(g, fc, ec="none", lw=0.6, z=2, alpha=1.0, ls="-"):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and not q.is_empty:
                xx, yy = q.exterior.xy
                ax.fill(xx, yy, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls)

    def line(g, col, lw, z, ls="-"):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "LineString":
                xx, yy = q.xy
                ax.plot(xx, yy, color=col, lw=lw, zorder=z, ls=ls, solid_capstyle="round")

    # water
    fill(LineString(L.CANAL_PTS).buffer(L.RIVER_W / 2), "#9cc7dc", "#3f7fa8", 0.8, 3)
    fill(L.BROOK.buffer(3.5), "#9cc7dc", "#3f7fa8", 0.5, 3)
    # green
    fill(CEMETERY_PARK, "#9fcb86", "#4f7a3a", 0.8, 4)
    fill(CEM_GRAVES, "#b9c7ad", "#4f5f45", 0.6, 4.2)
    gx = np.random.default_rng(3)
    pts = [(a, b) for a, b in zip(gx.uniform(-540, -450, 900), gx.uniform(-106, -40, 900)) if CEM_GRAVES.buffer(-3).contains(Point(a, b))]
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], marker="s", s=2, c="#5d6156", zorder=4.3, linewidths=0)
    for pth in CEM_PATHS:
        line(pth.intersection(CEMETERY_PARK), "#e9e2cf", 1.6, 4.4)
    fill(CHURCHYARD, "#b9c7ad", "#4f5f45", 1.0, 4.5)
    fill(GREEN, "#8DBF73", "#4f7a3a", 0.8, 4.5)
    # plots, back lanes, ginnels
    for pl in PLOTS:
        fill(pl, "#efe6d2", "#b3a68c", 0.4, 5)
    for bl in BACK_LANES:
        line(bl, "#d8d2c4", 3.2, 5.5)
    for gi in GINNELS:
        line(gi, "#8a7a5a", 0.9, 6, ls=(0, (2, 1.5)))
    # roads
    for rd in L.MAIN_ROADS:
        line(rd, "#222", 6.0, 6.5); line(rd, "#f2d27a", 4.0, 6.6)
    fill(STREET, "#e3dccb", "#6b5a45", 0.8, 6.7)
    fill(MARKET, "#d9cfb8", "none", 0, 6.8)
    line(OLD_NORTH, "#6b5a45", 6.5, 6.5); line(OLD_NORTH, "#e3dccb", 4.8, 6.6)
    line(CHURCH_LANE, "#6b5a45", 4.5, 6.5); line(CHURCH_LANE, "#e3dccb", 3.2, 6.6)
    # buildings
    for fr in FRONTS:
        fill(fr, "#b8956a", "#3d3a36", 0.5, 7)
    fill(CHURCH, "#7d7466", "#222", 0.9, 8)
    fill(INN, "#a0522d", "#222", 0.8, 8)
    fill(MARKET_HALL, "#c98a2c", "#222", 0.8, 8)
    fill(SCHOOL, "#e8a33d", "#222", 0.8, 8)
    ax.plot([MARKET_CROSS[0]], [MARKET_CROSS[1]], marker="+", ms=10, mew=2, color="#222", zorder=9)
    for p in PUBS:
        ax.plot([p.x], [p.y], marker="o", ms=7, mfc="#a0522d", mec="#222", zorder=9)
    # bridges: old stone bridge + packhorse bridge over Mill Brook
    for name_, kind_, (bx, by) in L.BRIDGES:
        if x0 < bx < x1 and y0 < by < y1 and kind_ in ("stone", "modern", "foot", "road"):
            ax.plot([bx], [by], marker="s", ms=9 if kind_ != "foot" else 5, mfc="#b49a74" if kind_ == "stone" else "#8a5a2b", mec="#222", zorder=9)
    for q in getattr(PACKHORSE, "geoms", [PACKHORSE]):
        if q.geom_type == "Point":
            ax.plot([q.x], [q.y], marker="s", ms=6, mfc="#b49a74", mec="#222", zorder=9)
            ax.text(q.x - 10, q.y + 14, "packhorse bridge", fontsize=8, zorder=20, ha="right", bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.2))
    # labels

    def lab(x, y, t, fs=9, w="bold", col="#222", style="normal"):
        ax.text(x, y, t, fontsize=fs, weight=w, color=col, style=style, ha="center", va="center", zorder=20,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.3))
    lab(-500, 135, "old stone bridge", fs=8.5)
    lab(_mp.x + 40, _mp.y + 38, "MARKET STREET\n(High Street widens)", fs=9)
    lab(MARKET_HALL.centroid.x - 4, MARKET_HALL.centroid.y - 18, "market hall", fs=8, w="normal")
    lab(MARKET_CROSS[0] - 30, MARKET_CROSS[1] + 14, "market cross", fs=8, w="normal")
    lab(CHURCH_C[0] + 2, CHURCH_C[1] - 44, "parish church\n(top of the rise)", fs=8.5)
    lab(-520, -20, "cemetery park\n(park 1)", fs=8.5, col="#1d3b14")
    lab(GREEN.centroid.x - 6, GREEN.centroid.y - 4, "green", fs=8, col="#1d3b14", style="italic")
    lab(INN.centroid.x + 36, INN.centroid.y + 8, "coaching inn\n+ yard", fs=8, w="normal")
    lab(SCHOOL.centroid.x + 32, SCHOOL.centroid.y - 10, "old school", fs=8, w="normal")
    lab(-690, 8, "old road north\n(to the next village)", fs=8, w="normal")
    lab(-262, -60, "main road\n(west of the ground)", fs=8, w="normal")
    lab(-610, 140, "the river", fs=8.5, col="#245", w="normal")
    lab(-640, -150, "Mill Brook\n(wooded clough)", fs=8, col="#245", w="normal")
    lab(-250, 60, "burgage plots: long narrow gardens behind\nthe houses, ending in back lanes; - - ginnels", fs=8, w="normal")
    ax.text(x0 + 8, y1 - 8, "OLD CORE v1 — Claude's first sketch (variant A: market street, with a small green at the fork)\n"
            "brown dots = pubs · + = market cross · plots and frontages are the medieval pattern, not final houses",
            ha="left", va="top", fontsize=10, zorder=30, bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.4"))
    ax.plot([x1 - 130, x1 - 30], [y0 + 15, y0 + 15], color="#222", lw=3, zorder=30)
    ax.text(x1 - 80, y0 + 25, "100 m", ha="center", fontsize=9, zorder=30)
    cx, cy = x1 - 50, y0 + 90
    for t_, (dx, dy) in (("N", (-1, 0)), ("S", (1, 0)), ("E", (0, 1)), ("W", (0, -1))):
        ax.annotate("", xy=(cx + dx * 22, cy + dy * 22), xytext=(cx, cy), arrowprops=dict(arrowstyle="->", color="#222"), zorder=30)
        ax.text(cx + dx * 32, cy + dy * 32, t_, ha="center", va="center", fontsize=9, weight="bold", zorder=30)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.1)
    print("saved", os.path.relpath(OUT), "plots", len(PLOTS), "frontages", len(FRONTS), "back lanes", len(BACK_LANES))


if __name__ == "__main__":
    main()
