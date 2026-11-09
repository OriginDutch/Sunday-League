"""Step 3 — the old core v2: Marcel's drawing (2026-11-09) as the inspiration, worked out at real sizes by Claude.
python3 tools/plan/village_core_v2.py -> design/world/village_core_v2.png (+ _vs_marcel.png overlay)

Kept from Marcel: the old bridge with a triangle place on the north bank, the old road north (up the valley), the road NE to the
bypass, a riverside street on both banks, the High Street from the bridge to the main road, the market on BOTH sides of the High
Street in front of the church, the churchyard (partly a park) on the rise with the church east-west and its tower west, the
curving road along the hill (with the lane up to the viewpoint), cross streets climbing the slope (the Victorian terraces), a
fan of streets on the north bank.
Real sizes (Claude): High Street 12 m, riverside streets 10 m, the hill road 9 m, terrace streets 8 m, lanes 5 m. Terraces:
front 1.5 m, house 8-9 m, yard 8-10 m, back alley 3 m -> two rows back to back need ~40 m between street centrelines.
So the north-bank fan has 3 streets ~48 m apart instead of 5 at ~29 m, and no parallel streets inside the wedge (too thin).
Claude's suggestions, marked in the drawing: the two long cross streets end at the main road as footpaths (no rat-run);
the churchyard's hill-side edge follows the hill road; round lines everywhere a street bends.
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
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L

OUT = os.path.join(HERE, "../../design/world/village_core_v2.png")
VIEW = (-760, -260, -140, 260)          # the same frame as basemap_core.png, so Marcel's drawing can be laid over it
ch = L._chaikin


def S(pts, n=3):
    return LineString(ch(pts, n))


# ---------------------------------------------------------------- streets (name, line, width, kind)
CROSS = (-488, 146)                                              # plain crossroads north of the old bridge (Marcel)
PLACE = Point(CROSS).buffer(7)
STREETS = [
    # south bank
    ("Bridge Street", S([CROSS, (-498, 130), (-503, 113), (-508, 99), (-524, 86), (-545, 70), (-564, 53)]), 10, "old"),
    ("High Street", S([(-564, 53), (-540, 41), (-522, 32), (-492, 16), (-465, 2), (-430, -13), (-394, -29), (-368, -42),
                       (-343, -55), (-325, -65), (-307, -75)]), 12, "high"),
    ("Quay Street", S([(-524, 86), (-496, 76), (-463, 69), (-431, 66), (-397, 67), (-364, 71), (-330, 78), (-296, 86),
                       (-262, 95), (-229, 104)]), 10, "old"),
    ("Hill Road", S([(-564, 53), (-578, 34), (-581, 12), (-560, -8), (-528, -24), (-505, -44), (-487, -66), (-476, -86),
                     (-467, -104), (-456, -124), (-447, -141), (-434, -155), (-412, -165), (-382, -166), (-352, -158),
                     (-321, -145), (-287, -126), (-253, -108)]), 9, "old"),
    ("Mill Lane", S([(-496, 76), (-505, 62), (-518, 46), (-534, 37)]), 6, "lane"),
    ("Chapel Street", S([(-431, 66), (-434, 46), (-438, 28), (-448, 13), (-463, 3)]), 8, "street"),
    ("Market Street", S([(-364, 71), (-362, 40), (-362, 10), (-370, -12), (-385, -24), (-394, -29)]), 8, "street"),
    ("Ferry Lane", S([(-296, 86), (-298, 60), (-300, 39), (-308, 18), (-320, -6)]), 8, "street"),
    ("Long Row", S([(-300, 39), (-282, 34), (-264, 32), (-240, 34), (-218, 37)]), 8, "street"),
    ("Church Lane", S([(-528, -24), (-497, -12), (-465, 2)]), 6, "lane"),
    ("Church Walk", S([(-399, -30), (-425, -41), (-452, -52), (-470, -59), (-487, -66)]), 7, "street"),
    ("Kirk Gate", S([(-452, -52), (-440, -68), (-424, -88), (-412, -105), (-400, -122), (-392, -140), (-382, -166)]), 8, "street"),
    ("Low Terrace", S([(-467, -104), (-444, -96), (-420, -87), (-382, -72), (-343, -56), (-300, -40), (-262, -26), (-232, -18)]), 8, "street"),
    ("High Terrace", S([(-447, -141), (-424, -132), (-399, -122), (-360, -106), (-320, -90), (-284, -76), (-253, -64), (-232, -56)]), 8, "street"),
    ("Croft Street", S([(-361, 8), (-340, 2), (-319, -7), (-300, -20), (-283, -35), (-268, -50), (-253, -64)]), 8, "street"),
    ("Beacon Lane", S([(-382, -166), (-378, -195), (-373, -227), (-366, -245), (-360, -260)]), 5, "lane"),     # up to the viewpoint
    # north bank
    ("Old North Road", S([CROSS, (-500, 152), (-516, 166), (-542, 182), (-570, 203), (-599, 226), (-630, 246), (-650, 260)]), 9, "old"),
    ("Moor Road", S([CROSS, (-478, 158), (-462, 166), (-446, 182), (-424, 196), (-402, 208), (-380, 219), (-340, 236), (-300, 252),
                     (-281, 260)]), 9, "old"),
    ("Water Street", S([CROSS, (-472, 138), (-453, 134), (-427, 131), (-398, 131), (-368, 135), (-339, 143), (-300, 160), (-270, 174),
                        (-247, 182)]), 9, "old"),
]
# the fan on the north bank: 3 streets from Water Street up to Moor Road, ~48 m apart (Marcel's 5 at ~29 m don't fit terraces)
STREETS += [("Fan Street 2", S([(-397, 131), (-398, 170), (-393, 210)], 3), 8, "street"),
            ("Fan Street 3", S([(-350, 141), (-352, 190), (-347, 233)], 3), 8, "street")]
# the inn (coaching inn: house at the front, yard + stables behind) in the wedge, a village green in front of it (Marcel)
INN_PLOT = Polygon(ch([(-454, 168), (-447, 136), (-401, 135), (-402, 185)], 1))
INN = Polygon([(-452, 160), (-444, 140), (-432, 145), (-440, 165)])                     # the inn, facing the green
INN_YARD = INN_PLOT.difference(INN.buffer(1))
INN_GREEN = Polygon([(-490, 146), (-470, 175), (-452, 190), (-454, 168), (-447, 136), (-480, 132)]).difference(INN_PLOT)   # the whole wedge in front of the inn
INN_PLOT = INN_PLOT.union(Polygon([(-402, 185), (-401, 135), (-447, 136), (-454, 168), (-452, 190), (-420, 205)])).difference(INN_GREEN)
# Claude's suggestion: the two long cross streets don't reach the main road as streets; their last stretch is a footpath
FOOTPATHS = [S([(-232, -18), (-212, -13)], 1), S([(-232, -56), (-212, -48)], 1)]
# joins to the main roads that already exist
JOINS = [S([(-307, -75), (-302, -78)], 1), S([(-229, 104), (-226, 104)], 1)]

# ---------------------------------------------------------------- places
CHURCHYARD = Polygon(ch([(-528, -24), (-465, 2), (-399, -28), (-452, -52), (-487, -66), (-505, -44)], 1)).buffer(-5)
# the hill-side edge follows Hill Road (it was a straight line in the sketch)
CHURCHYARD = CHURCHYARD.difference(STREETS[3][1].buffer(4.5 + 3)).difference(STREETS[1][1].buffer(6 + 3)).difference(
    STREETS[9][1].buffer(3 + 3))
CHURCH_C = (-466, -27)
CHURCH = Polygon([(CHURCH_C[0] - 6, CHURCH_C[1] - 14), (CHURCH_C[0] + 6, CHURCH_C[1] - 14), (CHURCH_C[0] + 6, CHURCH_C[1] + 13),
                  (CHURCH_C[0] + 3, CHURCH_C[1] + 17), (CHURCH_C[0] - 3, CHURCH_C[1] + 17), (CHURCH_C[0] - 6, CHURCH_C[1] + 13)]).union(
    box(CHURCH_C[0] - 4.5, CHURCH_C[1] - 23, CHURCH_C[0] + 4.5, CHURCH_C[1] - 14))       # nave east-west, tower at the west end
from shapely.affinity import rotate as _rot
# Marcel drew the church diagonal, along the contours; an exact east-west church stood across the slope -> his angle
# measured from Marcel's drawing: tower end (-459, -43) -> east end (-471, -12) = 111 deg; my plan is 90 deg -> +21
# (I first rotated -50: the wrong way and too far)
CHURCH = _rot(CHURCH, 21, origin=CHURCH_C)
GRAVES = CHURCHYARD.intersection(Polygon([(-470, -10), (-420, -20), (-430, -45), (-490, -60), (-500, -40)])).buffer(-3)
CHURCH_PARK = CHURCHYARD.difference(GRAVES.buffer(2))
MARKET_LOW = Polygon(ch([(-449, -50), (-399, -31), (-345, -58), (-420, -84)], 1)).buffer(-5)
MARKET_UP = Polygon(ch([(-397, -24), (-374, -6), (-318, -38), (-338, -56)], 1)).buffer(-4)
MARKET = unary_union([MARKET_LOW, MARKET_UP, STREETS[1][1].buffer(6).intersection(unary_union([MARKET_LOW, MARKET_UP]).convex_hull)])
MARKET_HALL = Polygon([(-372, -40), (-358, -47), (-354, -40), (-368, -33)])
MARKET_CROSS = (-398, -45)

# ---------------------------------------------------------------- geometry: street areas, blocks, frontages
WATER = unary_union([LineString(L.CANAL_PTS).buffer(L.RIVER_W / 2), L.BROOK.buffer(3.5)])
ROADS = unary_union([ln.buffer(w / 2) for nm, ln, w, k in STREETS] + [r.buffer(4.5) for r in L.MAIN_ROADS] + [PLACE] +
                    [j.buffer(4) for j in JOINS])
# the blocks the churchyard and market sit in are theirs entirely (Marcel: "dat moet gewoon park/kerkhof/markt blijven")
_pre = box(*VIEW).difference(unary_union([ln.buffer(w / 2) for nm, ln, w, k in STREETS] + [r.buffer(4.5) for r in L.MAIN_ROADS]))
_cy0, _mk0 = CHURCHYARD, MARKET
for _g in getattr(_pre, "geoms", [_pre]):
    _g = _g.buffer(-1.5)
    has_c, has_m = _g.intersects(_cy0.buffer(-1)), _g.intersection(_mk0).area > 50
    if has_c and has_m:
        # one block shared by both: the churchyard keeps its own shape, the rest of the block is market
        CHURCHYARD = CHURCHYARD.union(_g.intersection(_cy0.buffer(6)))
        MARKET = MARKET.union(_g.difference(_cy0.buffer(6)))
    elif has_c:
        CHURCHYARD = CHURCHYARD.union(_g)
    elif has_m and _g.area < 6000:
        MARKET = MARKET.union(_g)
CHURCH_PARK = CHURCHYARD.difference(GRAVES.buffer(2))
RIVER = LineString(L.CANAL_PTS)
QUAYSIDE = []
from shapely.ops import nearest_points as _np
for _nm in ("Water Street",):          # Marcel: houses along Quay Street; along Water Street it is too tight -> quay
    _ln = [ln for nm, ln, w, k in STREETS if nm == _nm][0]
    _area = _ln.buffer(60, cap_style=2).intersection(RIVER.buffer(60)).difference(_ln.buffer(5)).difference(RIVER.buffer(L.RIVER_W / 2))
    # keep only the pieces BETWEEN the street and the river (a point half-way from the street to the river lies in them)
    _mids = []
    for _f in np.linspace(0.05, 0.95, 19):
        _p = _ln.interpolate(_f, normalized=True)
        _q = _np(_p, RIVER)[1]
        _mids.append(Point((_p.x + _q.x) / 2, (_p.y + _q.y) / 2))
    for _g in getattr(_area, "geoms", [_area]):
        if any(_g.contains(m_) for m_ in _mids):
            QUAYSIDE.append(_g)
QUAYSIDE = unary_union(QUAYSIDE + [RIVER.buffer(L.RIVER_W / 2 + 6).difference(RIVER.buffer(L.RIVER_W / 2)).intersection(
    [ln for nm, ln, w, k in STREETS if nm == "Quay Street"][0].buffer(60))])        # a 6 m walk along the quay wall
BROOKSIDE = L.BROOK.buffer(16).difference(L.BROOK.buffer(3.5))
OPEN = unary_union([INN_PLOT.buffer(1), INN_GREEN.buffer(1), CHURCHYARD.buffer(2), MARKET.buffer(1), WATER.buffer(4), L.QUAY_WALK, L.LOOP_PARK, QUAYSIDE, BROOKSIDE])
VIEWBOX = box(*VIEW)
BLOCKS_ALL = VIEWBOX.difference(ROADS).difference(OPEN)
# the town only: blocks touching our streets (not the empty valley beyond)
TOWN = unary_union([ln.buffer(w / 2 + 32, cap_style=2) for nm, ln, w, k in STREETS])
BLOCKS = [g for g in getattr(BLOCKS_ALL, "geoms", [BLOCKS_ALL]) if g.geom_type == "Polygon" and g.area > 200 and g.intersects(TOWN)]
BLOCKS = [g.intersection(TOWN) for g in BLOCKS]
BLOCKS = [q for g in BLOCKS for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and q.area > 200]
# frontage: terraced houses 9 m deep, 1.5 m back from the street, cut into houses ~5.5 m wide
FRONT, HOUSE_LINES = [], []
for nm, ln, w, k in STREETS:
    band = ln.buffer(w / 2 + 1.5 + 9, cap_style=2).difference(ln.buffer(w / 2 + 1.5, cap_style=2))
    band = band.difference(unary_union([l2.buffer(w2 / 2 + 1.0, cap_style=2) for n2, l2, w2, k2 in STREETS if n2 != nm]))
    for b in BLOCKS:
        f = band.intersection(b)
        if not f.is_empty and f.area > 30:
            FRONT.append(f)
    d = 3.0
    while d < ln.length - 3:
        p = ln.interpolate(d); q = ln.interpolate(min(d + 1, ln.length))
        tx, ty = q.x - p.x, q.y - p.y; T = math.hypot(tx, ty) or 1
        nx_, ny_ = -ty / T, tx / T
        r0, r1 = w / 2 + 1.5, w / 2 + 10.5
        HOUSE_LINES.append(LineString([(p.x - nx_ * r1, p.y - ny_ * r1), (p.x - nx_ * r0, p.y - ny_ * r0)]))
        HOUSE_LINES.append(LineString([(p.x + nx_ * r0, p.y + ny_ * r0), (p.x + nx_ * r1, p.y + ny_ * r1)]))
        d += 5.5
FRONT_U = unary_union(FRONT)


# ---------------------------------------------------------------- checks
def checks():
    out = []
    wet = [nm for nm, ln, w, k in STREETS if ln.buffer(w / 2).intersection(WATER).area > 2 and nm != "Bridge Street"]   # (the old bridge itself)
    out.append(("streets in the water", wet))
    allnet = unary_union([ln for nm, ln, w, k in STREETS] + list(L.MAIN_ROADS) + [PLACE.exterior] + JOINS + FOOTPATHS)
    loose = []
    for nm, ln, w, k in STREETS:
        for e in (Point(ln.coords[0]), Point(ln.coords[-1])):
            if not VIEWBOX.buffer(-3).contains(e):
                continue
            others = unary_union([l2 for n2, l2, w2, k2 in STREETS if n2 != nm] + list(L.MAIN_ROADS) + [PLACE.buffer(1), MARKET.buffer(2)]
                                 + JOINS + FOOTPATHS)
            if others.distance(e) > 3:
                loose.append(f"{nm} at ({e.x:.0f}, {e.y:.0f})")
    out.append(("loose street ends (not at the map edge)", loose))
    thin = [b for b in BLOCKS if b.buffer(-10).is_empty]
    deep = [b for b in BLOCKS if not b.buffer(-24).is_empty]
    out.append(("blocks too thin for one row of houses (become yards / green)", [f"({b.centroid.x:.0f}, {b.centroid.y:.0f})" for b in thin]))
    out.append(("blocks deeper than two rows back to back (backland: gardens, yards, workshops)", [f"({b.centroid.x:.0f}, {b.centroid.y:.0f})" for b in deep]))
    return out


# ---------------------------------------------------------------- drawing
def main(path=OUT, for_overlay=False):
    x0, y0, x1, y1 = VIEW
    nx, ny = int((x1 - x0) / 1.5), int((y1 - y0) / 1.5)
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    H = L.height(X, Y)
    fig, ax = plt.subplots(figsize=(20, 20 * (y1 - y0) / (x1 - x0)), dpi=150)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks(np.arange(-700, x1, 100)); ax.set_yticks(np.arange(-200, y1, 100)); ax.tick_params(labelsize=7, colors="#777")
    cmap = LinearSegmentedColormap.from_list("land", ["#f3f5ea", "#e6ecd3", "#d6e0bb", "#c4d1a2", "#aebd88", "#97a674"])
    ax.imshow(LightSource(azdeg=315, altdeg=45).shade(H, cmap=cmap, vert_exag=3, blend_mode="soft", vmin=0, vmax=max(40, H.max())),
              extent=(x0, x1, y0, y1), origin="lower", zorder=0)
    cs = ax.contour(X, Y, H, levels=np.arange(5, 200, 5), colors="#6b5a45", linewidths=0.5, alpha=0.5, zorder=1)
    ax.clabel(cs, fmt="%d m", fontsize=7)

    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def fill(g, fc, ec="none", lw=0.6, z=2, alpha=1.0, hatch=None):
        """Polygons with their holes (a ring of terraces round a block must not be painted solid)."""
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and not q.is_empty:
                verts, codes = [], []
                for ring in [q.exterior] + list(q.interiors):
                    cs_ = list(ring.coords)
                    verts += cs_
                    codes += [MPath.MOVETO] + [MPath.LINETO] * (len(cs_) - 2) + [MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch))

    fill(WATER, "#9cc7dc", "#3f7fa8", 0.8, 3)
    fill(L.GOIT.buffer(3), "#9cc7dc", "#3f7fa8", 0.5, 3)
    fill(L.QUAY_WALK, "#a9d08e", "#4f7a3a", 0.5, 3)
    fill(L.LOOP_PARK, "#a9d08e", "#4f7a3a", 0.5, 3)
    for b in BLOCKS:
        fill(b, "#efe8d6", "#c9bea6", 0.4, 4)                   # gardens / yards inside the blocks
    fill(FRONT_U, "#c4a27a", "#5b4a36", 0.5, 5)                 # the terraces along the streets
    hl = unary_union(HOUSE_LINES).intersection(FRONT_U)
    for q in getattr(hl, "geoms", [hl]):
        if q.geom_type == "LineString":
            xx, yy = q.xy
            ax.plot(xx, yy, color="#5b4a36", lw=0.35, zorder=5.1)
    fill(CHURCH_PARK, "#a9d08e", "#4f7a3a", 0.8, 4.5)
    fill(QUAYSIDE, "#cfe3c0", "#4f7a3a", 0.5, 4.4)                # quays: tree-lined walk along the water, no houses
    fill(BROOKSIDE.difference(unary_union([ln.buffer(w / 2) for nm, ln, w, k in STREETS])), "#b9d9a0", "#4f7a3a", 0.4, 4.4)
    fill(GRAVES, "#b9c7ad", "#4f5f45", 0.6, 4.6)
    g_ = np.random.default_rng(2)
    pts = [(a, b) for a, b in zip(g_.uniform(-505, -420, 700), g_.uniform(-62, -8, 700)) if GRAVES.buffer(-2).contains(Point(a, b))]
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], marker="s", s=1.5, c="#5d6156", zorder=4.7, linewidths=0)
    fill(MARKET, "#d9cfb8", "#8a7a5a", 0.6, 6)
    # streets
    for nm, ln, w, k in STREETS:
        fill(ln.buffer(w / 2), "#e3dccb", "#6b5a45", 0.6, 6.5)
    fill(PLACE, "#e3dccb", "#6b5a45", 0.6, 6.5)
    _wedge = INN_GREEN.union(INN_PLOT).buffer(15).difference(unary_union([ln.buffer(w / 2 + 0.5) for nm, ln, w, k in STREETS]))
    _wedge = [q for q in getattr(_wedge, "geoms", [_wedge]) if q.contains(Point(-450, 150))][0]
    fill(_wedge.difference(INN_PLOT), "#8DBF73", "#4f7a3a", 0.8, 6.6)
    fill(_wedge.intersection(INN_PLOT.buffer(15)).difference(_wedge.difference(INN_PLOT)).difference(INN.buffer(1)), "#d8cdb5", "#8a7a5a", 0.6, 6.6)
    fill(INN, "#a0522d", "#222", 0.9, 8)
    for j in JOINS:
        fill(j.buffer(4), "#e3dccb", "none", 0, 6.5)
    for fp in FOOTPATHS:
        xx, yy = fp.xy
        ax.plot(xx, yy, color="#c0392b", lw=2.0, ls=(0, (2, 1.5)), zorder=7)
    for rd in L.MAIN_ROADS:
        xx, yy = rd.xy
        ax.plot(xx, yy, color="#222", lw=7, zorder=7, solid_capstyle="round"); ax.plot(xx, yy, color="#f2d27a", lw=5, zorder=7.1, solid_capstyle="round")
    fill(CHURCH, "#7d7466", "#222", 0.9, 8)
    fill(MARKET_HALL, "#c98a2c", "#222", 0.8, 8)
    ax.plot([MARKET_CROSS[0]], [MARKET_CROSS[1]], marker="+", ms=10, mew=2, color="#222", zorder=9)
    for name_, kind_, (bx, by) in L.BRIDGES:
        if x0 < bx < x1 and y0 < by < y1:
            ax.plot([bx], [by], marker="s", ms=9 if kind_ != "foot" else 6, mfc="#b49a74" if kind_ == "stone" else "#d9d9d9" if kind_ == "modern" else "#8a5a2b",
                    mec="#222", zorder=9)
    if not for_overlay:
        for nm, ln, w, k in STREETS:
            p = ln.interpolate(0.5, normalized=True)
            q = ln.interpolate(min(0.5 * ln.length + 2, ln.length))
            ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
            ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
            ax.text(p.x, p.y, nm, rotation=ang, fontsize=6.5 if w < 9 else 7.5, ha="center", va="center", zorder=10, color="#3a2a1e",
                    weight="bold" if k in ("high", "old") else "normal")
        for t, (x, y) in (("MARKET", (-405, -62)), ("MARKET", (-352, -28)), ("church", (CHURCH_C[0] + 22, CHURCH_C[1] + 6)),
                          ("churchyard\n+ park", (-505, -20)), ("inn + yard", (-425, 160)), ("green", (-465, 155)), ("market hall", (-358, -52))):
            ax.text(x, y, t, fontsize=7.5, ha="center", va="center", zorder=11, weight="bold" if t == "MARKET" else "normal",
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
        ax.text(-205, -30, "footpath\n(suggestion:\nno rat-run)", fontsize=7, color="#c0392b", zorder=11, ha="left",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
        res = checks()
        txt = "\n".join(f"{k}: {len(v)}" + (f" — {', '.join(v[:4])}" if v and len(v) <= 4 else "") for k, v in res)
        ax.set_title("OLD CORE v2 — Marcel's drawing as the base, worked out at real sizes. Brown strips = terraced houses (9 m deep), "
                     "cream = gardens / yards, red dashes = Claude's suggestion", fontsize=10.5, loc="left")
        ax.text(x0 + 6, y0 + 6, "CHECK\n" + txt, fontsize=7.5, zorder=30, va="bottom", ha="left",
                bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.4"))
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("saved", os.path.relpath(path))


if __name__ == "__main__":
    for k, v in checks():
        print(f"{k}: {len(v)}", v[:8])
    main()
