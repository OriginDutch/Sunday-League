"""Clean, detailed base map for Marcel to draw on (no proposals on it, only what is decided).
python3 tools/plan/village_basemap.py [x0 y0 x1 y1] [name]  ->  design/world/basemap_<name>.png
Default: the old core area. Contours every 1 m, a light 50 m grid with coordinates, decided water / bridges / main roads.
"""
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import LineString

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L
import world_plan_v5 as W

args = sys.argv[1:]
VIEW = tuple(float(a) for a in args[:4]) if len(args) >= 4 else (-760, -260, -140, 260)
NAME = args[4] if len(args) >= 5 else "core"
OUT = os.path.join(HERE, f"../../design/world/basemap_{NAME}.png")


def view_has(g, x0, y0, x1, y1):
    from shapely.geometry import box as _b
    return g.intersects(_b(x0, y0, x1, y1))


def main(view=None, out=None, title=None):
    x0, y0, x1, y1 = view or VIEW
    nx = int((x1 - x0) / 1.5)
    ny = int((y1 - y0) / 1.5)
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    H = L.height(X, Y)
    fig, ax = plt.subplots(figsize=(20, 20 * (y1 - y0) / (x1 - x0)), dpi=150)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    cmap = LinearSegmentedColormap.from_list("land", ["#f3f5ea", "#e6ecd3", "#d6e0bb", "#c4d1a2", "#aebd88", "#97a674"])
    ax.imshow(LightSource(azdeg=315, altdeg=45).shade(H, cmap=cmap, vert_exag=3, blend_mode="soft", vmin=0, vmax=max(40, H.max())),
              extent=(x0, x1, y0, y1), origin="lower", zorder=0)
    lv1 = np.arange(1, 200, 1)
    ax.contour(X, Y, H, levels=lv1, colors="#8a7a60", linewidths=0.25, alpha=0.45, zorder=1)
    cs = ax.contour(X, Y, H, levels=np.arange(5, 200, 5), colors="#6b5a45", linewidths=0.6, alpha=0.7, zorder=1)
    ax.clabel(cs, fmt="%d m", fontsize=7)
    # 50 m grid with coordinates (handy to talk about places)
    for gx in np.arange(math.ceil(x0 / 50) * 50, x1, 50):
        ax.axvline(gx, color="#999", lw=0.3, alpha=0.5, zorder=1.5)
    for gy in np.arange(math.ceil(y0 / 50) * 50, y1, 50):
        ax.axhline(gy, color="#999", lw=0.3, alpha=0.5, zorder=1.5)
    ax.set_xticks(np.arange(math.ceil(x0 / 100) * 100, x1, 100)); ax.set_yticks(np.arange(math.ceil(y0 / 100) * 100, y1, 100))
    ax.tick_params(labelsize=7, colors="#777")

    def fill(g, fc, ec, lw, z):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon":
                xx, yy = q.exterior.xy
                ax.fill(xx, yy, fc=fc, ec=ec, lw=lw, zorder=z)

    # water (decided)
    fill(LineString(L.CANAL_PTS).buffer(L.RIVER_W / 2), "#9cc7dc", "#3f7fa8", 0.8, 3)
    fill(L.BROOK.buffer(3.5), "#9cc7dc", "#3f7fa8", 0.5, 3)
    fill(L.BROOK2.buffer(3.0), "#9cc7dc", "#3f7fa8", 0.5, 3)
    fill(L.GOIT.buffer(3.0), "#9cc7dc", "#3f7fa8", 0.5, 3)
    fill(L.QUARRY_POND, "#9cc7dc", "#3f7fa8", 0.5, 3)
    L._draw_tram(ax)
    for f_ in L.FALLS:
        ax.plot([f_.x - 5, f_.x + 5], [f_.y, f_.y], color="white", lw=2, zorder=3.5)
    # the ground plot + loop park + quay walk (decided)
    fill(W.PLOT, "#e3efd9", "#2F5B3F", 1.0, 2.5)
    fill(L.LOOP_PARK, "#a9d08e", "#4f7a3a", 0.6, 2.6)
    fill(L.QUAY_WALK, "#a9d08e", "#4f7a3a", 0.6, 2.6)
    fill(L.MILL_BOX, "#7A6A5A", "#222", 0.8, 6)
    # the old core (decided): its streets, church, churchyard, market, inn + green
    import village_core_v2 as C
    for nm_, ln_, w_, k_ in C.STREETS:
        fill(ln_.buffer(w_ / 2), "#e3dccb", "#6b5a45", 0.6, 4.5)
        if view_has(ln_, x0, y0, x1, y1):
            p_ = ln_.interpolate(0.5, normalized=True)
            ax.text(p_.x, p_.y, nm_, fontsize=6.5, ha="center", va="center", zorder=8, color="#3a2a1e", clip_on=True)
    for fp_ in C.FOOTPATHS:
        xx, yy = fp_.xy
        ax.plot(xx, yy, color="#8a7a5a", lw=1.2, ls=(0, (2, 1.5)), zorder=4.6)
    fill(C.CHURCHYARD, "#a9d08e", "#4f7a3a", 0.6, 4.4)
    fill(C.CHURCH, "#7d7466", "#222", 0.8, 6)
    fill(C.MARKET, "#d9cfb8", "#8a7a5a", 0.6, 4.4)
    fill(C.INN, "#a0522d", "#222", 0.8, 6)
    # main roads (decided) + roundabout + bridges
    for rd in L.MAIN_ROADS:
        xx, yy = rd.xy
        ax.plot(xx, yy, color="#222", lw=7, zorder=5, solid_capstyle="round")
        ax.plot(xx, yy, color="#f2d27a", lw=5, zorder=5.1, solid_capstyle="round")
    ax.add_patch(plt.Circle(L.ROUNDABOUT, 16, fc="#f2d27a", ec="#222", lw=1.4, zorder=5.2))
    rx, ry = L.RAIL.xy
    ax.plot(rx, ry, color="#444", lw=3, zorder=5); ax.plot(rx, ry, color="white", lw=1.2, zorder=5, ls=(0, (3, 3)))
    for name_, kind_, (bx, by) in L.BRIDGES:
        if x0 < bx < x1 and y0 < by < y1:
            ax.plot([bx], [by], marker="s", ms=9 if kind_ != "foot" else 6, mfc={"stone": "#b49a74", "modern": "#d9d9d9", "road": "#c8c3b8",
                    "rail": "#555", "foot": "#8a5a2b"}[kind_], mec="#222", zorder=7)
            ax.text(bx + 8, by + 8, name_, fontsize=7, zorder=8, clip_on=True, bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.15))
    ax.text(L.MILL[0], L.MILL[1] + 16, "mill", fontsize=7, ha="center", zorder=8, clip_on=True)
    if title:
        ax.set_title(title, fontsize=11, loc="left")
        return fig, ax
    ax.set_title(f"BASE MAP ({NAME}) — only what is decided. Contours 1 m (bold 5 m), grid 50 m, coordinates in metres. "
                 "Draw in purple / orange, not black, red or blue.", fontsize=11, loc="left")
    cx, cy = x1 - 40, y0 + 60
    for t_, (dx, dy) in (("N", (-1, 0)), ("S", (1, 0)), ("E", (0, 1)), ("W", (0, -1))):
        ax.annotate("", xy=(cx + dx * 18, cy + dy * 18), xytext=(cx, cy), arrowprops=dict(arrowstyle="->", color="#222"), zorder=30)
        ax.text(cx + dx * 27, cy + dy * 27, t_, ha="center", va="center", fontsize=9, weight="bold", zorder=30,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.1))
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.1)
    print("saved", os.path.relpath(OUT))


if __name__ == "__main__":
    main()
