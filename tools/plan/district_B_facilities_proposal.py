"""District B — facilities proposal (Claude, 2026-11-11, for Marcel to judge; Marcel: "ja, er is ruimte voor").
A district of ~1,200 houses gets: a board school (with its playground) taking one whole block, a chapel on the green square,
two pubs (one by the new river green, one on the corner by the main-road junction) and five corner shops.
python3 tools/plan/district_B_facilities_proposal.py -> design/world/village_district_B_facilities_proposal.png
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Point, box
from shapely.ops import unary_union
import village_district_B_v1 as B
import district_lib as D

OUT = os.path.join(HERE, "../../design/world/village_district_B_facilities_proposal.png")


def corner_at(x, y):
    return min(B.CORNERS, key=lambda c: c.distance(Point(x, y)))


SCHOOL_BLOCK = [q for q in B.BLOCKS if q.contains(Point(330, -80))][0]          # ~0.58 ha: school + walled playground
SCHOOL_HOUSES = [h for h in B.HOUSES if h.intersects(SCHOOL_BLOCK)]
SCHOOL = box(282, -95, 318, -55).intersection(SCHOOL_BLOCK)                       # two-storey board school, ~36 x 40 m
CHAPEL_BLOCK = [q for q in B.BLOCKS if q.contains(Point(470, 85))][0]
# the chapel faces the green: it takes 3 row houses on the green side of the block and runs 17 m back (~16.5 x 17 m)
_row = sorted([h for h in B.HOUSES if h.intersects(CHAPEL_BLOCK) and len(h.exterior.coords) == 5 and h not in B.CORNERS],
              key=lambda h: h.centroid.distance(Point(470, 62)))[:3]
CHAPEL_HOUSES = _row
_r = unary_union(_row).minimum_rotated_rectangle
_cs = list(_r.exterior.coords)[:4]
_e = sorted([(_cs[i], _cs[(i + 1) % 4]) for i in range(4)], key=lambda e: Point((e[0][0] + e[1][0]) / 2, (e[0][1] + e[1][1]) / 2).distance(B.GREEN_SQ))
(_a, _b) = _e[0]                                                                  # front edge, facing the green
import math as _m
_tx, _ty = _b[0] - _a[0], _b[1] - _a[1]
_n = (-_ty, _tx); _nl = _m.hypot(*_n); _n = (_n[0] / _nl, _n[1] / _nl)
if Point(_a[0] + _n[0], _a[1] + _n[1]).distance(B.GREEN_SQ) < Point(_a).distance(B.GREEN_SQ):
    _n = (-_n[0], -_n[1])
from shapely.geometry import Polygon
CHAPEL_SITE = Polygon([_a, _b, (_b[0] + _n[0] * 17, _b[1] + _n[1] * 17), (_a[0] + _n[0] * 17, _a[1] + _n[1] * 17)])
PUBS = [(corner_at(495, 165), "pub by the river green"), (corner_at(400, -185), "pub on the corner\nby the junction")]
SHOPS = [(corner_at(*p), "shop") for p in ((262, 25), (440, 60), (520, 40), (600, 100), (650, 30))]

if __name__ == "__main__":
    _orig = plt.Figure.savefig

    def _hook(fig, path, *a, **k):
        ax = fig.axes[0]

        def fillp(g, fc, ec="#222", lw=0.9, z=40, alpha=1.0, hatch=None):
            for q in getattr(g, "geoms", [g]):
                if q.geom_type == "Polygon":
                    xs, ys = q.exterior.xy
                    ax.fill(xs, ys, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch)
        fillp(SCHOOL_BLOCK, "#e9e3d3", "#1f5fa8", 1.6, 38, 0.95)
        for h in SCHOOL_HOUSES:
            fillp(h, "none", "#c0392b", 0.6, 39, hatch="xx")
        fillp(SCHOOL, "#8a4b3a", z=40)
        ax.text(SCHOOL_BLOCK.centroid.x + 8, SCHOOL_BLOCK.centroid.y - 18, "BOARD SCHOOL\n+ playground\n(replaces this block's houses)",
                fontsize=7.5, color="#1f5fa8", weight="bold", ha="center", zorder=41, bbox=dict(fc="white", ec="#1f5fa8", alpha=0.9, pad=0.25))
        for h in CHAPEL_HOUSES:
            fillp(h, "none", "#c0392b", 0.6, 39, hatch="xx")
        fillp(CHAPEL_SITE, "#b3aa96", z=40)
        ax.text(CHAPEL_SITE.centroid.x, CHAPEL_SITE.centroid.y + 22, "CHAPEL\n(on the green)", fontsize=7.5, color="#4a4030", weight="bold",
                ha="center", zorder=41, bbox=dict(fc="white", ec="#4a4030", alpha=0.9, pad=0.25))
        for g, t in PUBS:
            fillp(g, "#a0522d")
            ax.annotate(t, g.centroid.coords[0], (g.centroid.x + 12, g.centroid.y + 14), fontsize=7, color="#7a3010", zorder=41,
                        arrowprops=dict(arrowstyle="-", color="#7a3010", lw=0.8), bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        for g, t in SHOPS:
            fillp(g, "#d9a23a")
            ax.annotate(t, g.centroid.coords[0], (g.centroid.x + 8, g.centroid.y - 12), fontsize=7, color="#7a5a10", zorder=41,
                        arrowprops=dict(arrowstyle="-", color="#7a5a10", lw=0.8), bbox=dict(fc="white", ec="none", alpha=0.85, pad=0.2))
        ax.set_title(f"DISTRICT B — FACILITIES PROPOSAL (Claude): school (blue), chapel, 2 pubs (brown), 5 corner shops (ochre); "
                     f"red cross-hatch = houses that would go ({len(SCHOOL_HOUSES) + len(CHAPEL_HOUSES)})", fontsize=10.5, loc="left")
        return _orig(fig, path, *a, **k)

    plt.Figure.savefig = _hook
    B.main(OUT)
