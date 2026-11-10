"""Step 4 — district A (round the ground) v1: Marcel's town sketch (2026-11-10) as the base, worked out at real sizes by Claude.
python3 tools/plan/village_district_A_v1.py -> design/world/village_district_A_v1.png (+ _vs_marcel.png overlay)

Marcel (2026-11-10): his hand-drawn sketch is the base, not stadium plan v5; v5's streets go where they differ, and the gates,
pubs, coach bay and car-park entrance are placed again. Claude reports the pinch points that are left.
Street types (Claude, Marcel: "wat het beste past bij de wijk"): this is the match-day district, so the streets that carry the
crowd round the ground (the ring + the road-bridge street) are 10.5 m (6.5 m carriageway, 2 m pavements); the terrace streets
8.5 m (5.5 + 1.5); no houses front the main roads (as in the core). Terraces as in the core: front 1.5 m, house 9 m,
yard 8-10 m, back alley 3 m -> two rows back to back need ~42 m between street edges.
Names: v5 names where a street is plainly the same street; new streets are A1, A2, ... (names: Marcel).
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
from shapely.ops import unary_union, nearest_points

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L
import world_plan_v5 as W

OUT = os.path.join(HERE, "../../design/world/village_district_A_v1.png")
VIEW = (-260, -275, 245, 165)
ch = L._chaikin
RING, TERR = 10.5, 8.5
MAIN = unary_union(L.MAIN_ROADS)
PLOT = W.PLOT


def S(pts, n=3):
    return LineString(ch(pts, n)) if len(pts) > 2 else LineString(pts)


def to_main(p, toward):
    """End a street on the main road: run on from p in the direction of `toward` until it meets the main road's centre line."""
    ln = LineString([p, (p[0] + (toward[0] - p[0]) * 3, p[1] + (toward[1] - p[1]) * 3)])
    x = ln.intersection(MAIN)
    if x.is_empty:
        return toward
    pts = [x] if x.geom_type == "Point" else list(x.geoms)
    q = min(pts, key=lambda g: g.distance(Point(p)))
    return (q.x, q.y)


# ---------------------------------------------------------------- streets (name, line, width, kind), traced from Marcel's sketch
_A1_w = to_main((-180, 109), (-230, 105))
_A2_w = to_main((-180, 45), (-220, 38))
_NS_w = to_main((-180, -46), (-209, -57))
_A3_s = to_main((-118, -186), (-125, -198))
_A4_s = to_main((80, -215), (72, -254))
_BY_s = to_main((204, -215), (203, -242))
STREETS = [
    # the ring round the ground (match-day streets)
    ("North Street", S([(-146.5, 113), (-146.5, 51), (-146.5, -6), (-149, -32), (-160, -42), (-185, -50), _NS_w], 2), RING, "ring"),
    ("High Road", S([_A3_s, (-116, -184), (-109, -172), (-98, -152), (-86, -140), (-70, -136), (0, -136), (29, -136)], 2), RING, "ring"),
    ("Lower Road", S([(34, -185), (86, -185), (150, -185), (205, -185)], 1), RING, "ring"),
    ("South Street", S([(206, 69), (184, 61), (166, 50), (155, 36), (151, 20), (150.5, -84), (150.5, -185)], 2), RING, "ring"),
    ("Shelley Street", S([(206, 147), (206, 70), (205.5, 25), (205, -33), (205, -85)], 1), RING, "ring"),     # from the road bridge
    ("Byron Street", S([(205, -85), (205, -185), _BY_s], 1), RING, "ring"),
    # terrace streets
    ("Green Road", S([_A1_w, (-180, 109), (-146.5, 113)], 1), TERR, "street"),
    ("Turnstile Lane", S([(-146.5, 51), (-180, 45), _A2_w], 1), TERR, "street"),
    ("Car Park Lane", S([(29, -136), (33, -139), (34, -148), (34, -185)], 2), TERR, "street"),
    ("Albert Street", S([(-109, -172), (-96, -178), (-80, -182), (-40, -184), (34, -185)], 2), TERR, "street"),
    ("Fenton Road", S([(86, -185), (82, -205), (78, -228), _A4_s], 2), TERR, "street"),
    ("Lock Lane", S([(150.5, -84), (205, -85)], 1), TERR, "street"),
]
# district B starts east of Shelley / Byron Street: its streets only shown as stubs (no houses drawn on them here)
STUBS = [LineString([(206, 70), (216, 74), (240, 82)]), LineString([(205.5, 25), (245, 25)]), LineString([(205, -33), (245, -33)]),
         LineString([(205, -85), (245, -85)]), LineString([(205, -185), (245, -186)])]

WATER = unary_union([LineString(L.CANAL_PTS).buffer(L.RIVER_W / 2), L.GOIT.buffer(3)])
STREET_U = unary_union([ln.buffer(w / 2) for nm, ln, w, k in STREETS] + [s.buffer(TERR / 2) for s in STUBS])
# kerb radii at the junctions (~6 m): close the union (grow then shrink), so corners are rounded, not bitten
STREET_U = STREET_U.buffer(6, join_style=1).buffer(-6, join_style=1).union(STREET_U)
# district A is the land inside the main roads: street ends stop at the far kerb of the main road, not beyond it
A_REGION = Polygon([(-233, 200)] + list(L.MAIN_ROADS[5].coords) + list(L.MAIN_ROADS[9].coords) + [(260, -240), (260, 200)]).buffer(0)
STREET_U = STREET_U.intersection(A_REGION.union(MAIN.buffer(5.0)))
ROADS = unary_union([STREET_U, MAIN.buffer(5.0)])
GREEN = unary_union([L.QUAY_WALK, L.LOOP_PARK])
OPEN = unary_union([PLOT.buffer(1.0), WATER.buffer(4), GREEN])
VIEWBOX = box(*VIEW)
A_ZONE = Polygon([(-232, 128), (206, 128), (212, 150), (212, -245), (-240, -245), (-240, 128)])     # rough frame, the main road cuts it
BLOCKS_ALL = VIEWBOX.difference(ROADS).difference(OPEN)
TOWN = unary_union([ln.buffer(w / 2 + 32, cap_style=2) for nm, ln, w, k in STREETS])
BLOCKS = [g for g in getattr(BLOCKS_ALL, "geoms", [BLOCKS_ALL]) if g.geom_type == "Polygon" and g.area > 200 and g.intersects(TOWN)]
# district A only: west of Shelley / Byron Street and north-east of the main road
_east = box(207, -400, 400, 400)
_south = Polygon(list(L.MAIN_ROADS[9].coords) + [(260, -400), (-300, -400), (-300, -133)])
BLOCKS = [b.difference(_east).difference(_south) for b in BLOCKS]
BLOCKS = [q for g in BLOCKS for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and q.area > 200]
BLOCKS = [b for b in BLOCKS if b.centroid.x > -232]

# houses one by one (Marcel 2026-11-10: "huizen die schuin eindigen bouwen we niet"): each house is a cell 5.5 m wide along
# the street, 9 m deep, its side walls square to the street (on a bend the cells become slight wedges, as real terraces do).
# A house is built only if the whole house fits: not on another street, the plot (+8 m yard), the park, the water or a main
# road, and not on a house already standing (ring streets are built first, so at a corner the side street's house goes)
# main-road frontage, only where Marcel allows it (2026-11-10): opposite North Street and opposite Lower Road.
# (houses only; the road itself is drawn as the main road). Smoothed, so the traced wobble doesn't reach the house fronts
_mr5 = LineString(ch(list(L.MAIN_ROADS[5].simplify(3).coords), 3))
_mr9 = LineString(ch(list(L.MAIN_ROADS[9].simplify(3).coords), 3))
MAIN_FRONT = [("main road (opposite North Street)", _mr5.intersection(box(-260, -57, -190, 110)), 14.0, "mainfront"),
              ("main road (opposite Lower Road)", _mr9.intersection(box(34, -260, 205, -200)), 14.0, "mainfront")]
MAIN_FRONT = [(n_, g_ if g_.geom_type == "LineString" else max(g_.geoms, key=lambda q_: q_.length), w_, k_) for n_, g_, w_, k_ in MAIN_FRONT]
ALLOWED = unary_union(BLOCKS).difference(PLOT.buffer(8.0)).difference(MAIN.buffer(5 + 1.0)).difference(OPEN)
HOUSE_W, HOUSE_D, FRONT_SET = 5.5, 9.0, 1.5
HOUSES = []
_order = sorted(STREETS, key=lambda s_: 0 if s_[3] == "ring" else 1) + MAIN_FRONT
for nm, ln, w, k in _order:
    r0, r1 = w / 2 + FRONT_SET, w / 2 + FRONT_SET + HOUSE_D
    others = unary_union([l2.buffer(w2 / 2 + 1.0) for n2, l2, w2, k2 in STREETS if n2 != nm])
    if k == "mainfront":
        others = unary_union([l2.buffer(w2 / 2 + 1.0) for n2, l2, w2, k2 in STREETS])
    for side in (1, -1):
        def edge(d):
            p = ln.interpolate(d); q = ln.interpolate(min(d + 0.5, ln.length)) if d + 0.5 <= ln.length else ln.interpolate(d)
            if d + 0.5 > ln.length:
                q0 = ln.interpolate(d - 0.5); tx, ty = p.x - q0.x, p.y - q0.y
            else:
                tx, ty = q.x - p.x, q.y - p.y
            T = math.hypot(tx, ty) or 1
            nx_, ny_ = -ty / T * side, tx / T * side
            return (p.x + nx_ * r0, p.y + ny_ * r0), (p.x + nx_ * r1, p.y + ny_ * r1)
        d = 0.0
        while d + HOUSE_W <= ln.length:
            (f0, b0), (f1, b1) = edge(d), edge(d + HOUSE_W)
            cell = Polygon([f0, f1, b1, b0])
            ok = (cell.is_valid and ALLOWED.contains(cell.buffer(-0.15)) and not cell.intersects(others)
                  and all(cell.intersection(h).area < 0.3 for h in HOUSES if h.distance(cell) < 1))
            if ok:
                HOUSES.append(cell)
            d += HOUSE_W
# a lone house is no terrace: drop houses with no neighbour in their row
HOUSES = [h for h in HOUSES if sum(1 for g in HOUSES if g is not h and g.distance(h) < 0.3) >= 1]
# corner houses (Marcel: akkoord): where two rows stop short of a corner, one house turns the corner and closes the gap.
# Its plot is what is left of the two frontage bands between the row ends; built only if it fits whole (no slivers)
_bands = []
for nm, ln, w, k in STREETS + MAIN_FRONT:
    r0, r1 = w / 2 + FRONT_SET, w / 2 + FRONT_SET + HOUSE_D
    _bands.append((nm, ln.buffer(r1, cap_style=2).difference(ln.buffer(r0, cap_style=2))))
_built = unary_union(HOUSES)
_gap = unary_union([b_ for n_, b_ in _bands]).intersection(ALLOWED).difference(_built.buffer(0.05))
_gap = _gap.difference(unary_union([ln.buffer(w / 2 + 1.0) for nm, ln, w, k in STREETS]))
CORNERS = []
for g in getattr(_gap, "geoms", [_gap]):
    if g.geom_type != "Polygon" or not (30 < g.area < 260) or g.buffer(-1.4).is_empty:      # >= ~3 m wide everywhere
        continue
    streets_ = [n_ for n_, b_ in _bands if b_.intersection(g).area > 8]
    rows_ = sum(1 for h in HOUSES if h.distance(g) < 0.2)
    if len(streets_) >= 2 and rows_ >= 2:                       # between two streets and closing two row ends
        CORNERS.append(g.buffer(0.05).intersection(ALLOWED))
HOUSES += CORNERS
FRONT = HOUSES

# ---------------------------------------------------------------- the land round the plot (Marcel 2026-11-10: green, gathering
# places and fitting important buildings; Claude's proposal accepted): SW = the club square at the main-stand side with the
# clubhouse and the hard-core pub on the corner of North Street; NE = a small green with the war memorial and a church hall;
# the strip along the river side of the plot joins the quay walk
_left = A_REGION.difference(ROADS).difference(PLOT.buffer(1)).difference(OPEN).difference(unary_union(HOUSES).buffer(9))
def _part(bx):
    g = _left.intersection(bx)
    return max([q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon"], key=lambda q: q.area)
CLUB_SQUARE = _part(box(-215, -200, -95, -45))
NE_GREEN = _part(box(139, 40, 207, 130))
RIVER_STRIP = _part(box(-235, 113, 206, 140))
CLUBHOUSE = box(-193, -126, -180, -96)                     # 13 x 30 m, two storeys, its back to the plot's west fence
_pubcells = [h for h in HOUSES if h.centroid.x < -185 and -78 < h.centroid.y < -55]
HOUSES = [h for h in HOUSES if not any(h is c for c in _pubcells)]
PUB = unary_union(_pubcells) if _pubcells else None        # the hard-core pub: the corner of North Street and the square
MEMORIAL = (NE_GREEN.representative_point().x, NE_GREEN.representative_point().y)
def _fit(region, w_, h_):
    best = None
    x0_, y0_, x1_, y1_ = region.bounds
    for yy in np.arange(y1_ - h_ - 1, y0_, -2.0):
        for xx in np.arange(x0_ + 1, x1_ - w_, 2.0):
            r_ = box(xx, yy, xx + w_, yy + h_)
            if region.buffer(-1.5).contains(r_):
                return r_
    return best
CHURCH_HALL = _fit(NE_GREEN, 20, 11)
HOUSE_LINES = [LineString(h.exterior.coords) for h in HOUSES]
FRONT_U = unary_union(FRONT)


# ---------------------------------------------------------------- checks (pinch points for Marcel)
def _depth(b):
    """How far the middle of a block is from its edge (half its 'thickness')."""
    lo, hi = 0.0, 80.0
    for _ in range(14):
        m = (lo + hi) / 2
        if b.buffer(-m).is_empty:
            hi = m
        else:
            lo = m
    return 2 * lo


def checks():
    out = []
    out.append(("streets on the ground's plot", [nm for nm, ln, w, k in STREETS if ln.buffer(w / 2).intersection(PLOT).area > 1]))
    out.append(("streets in the water / park", [nm for nm, ln, w, k in STREETS if ln.buffer(w / 2).intersection(unary_union([WATER, GREEN])).area > 2
                                                and nm != "Shelley Street"]))
    loose = []
    for nm, ln, w, k in STREETS:
        for e in (Point(ln.coords[0]), Point(ln.coords[-1])):
            others = unary_union([l2 for n2, l2, w2, k2 in STREETS if n2 != nm] + STUBS + list(L.MAIN_ROADS))
            if others.distance(e) > 3 and Point(L.BRIDGES[0][2]).distance(e) > 0 and min(Point(b[2]).distance(e) for b in L.BRIDGES) > 6:
                loose.append(f"{nm} at ({e.x:.0f}, {e.y:.0f})")
    out.append(("loose street ends", loose))
    gap = []
    for nm, ln, w, k in STREETS:
        dd = ln.buffer(w / 2).distance(PLOT)
        if 0 < dd < 1.5 and ln.distance(PLOT) < 15:
            gap.append(f"{nm}: {dd:.1f} m from the plot fence")
    out.append(("street kerb < 1.5 m from the plot", gap))
    thin, tight, deep = [], [], []
    for b in BLOCKS:
        t = _depth(b)
        c = f"({b.centroid.x:.0f}, {b.centroid.y:.0f}) {t:.0f} m"
        if t < 12:
            thin.append(c)
        elif 21 < t < 40:
            tight.append(c)
        elif t > 52:
            deep.append(c)
    out.append(("blocks too thin for a row of houses", thin))
    out.append(("blocks with two rows but short yards (21-40 m deep)", tight))
    out.append(("blocks deeper than two rows (backland)", deep))
    steep = []
    for nm, ln, w, k in STREETS:
        ds = np.linspace(0, ln.length, max(3, int(ln.length / 10)))
        P_ = np.array([ln.interpolate(d).coords[0] for d in ds])
        h = L.height(P_[:, 0], P_[:, 1])
        g = np.abs(np.diff(h)) / np.diff(ds)
        if g.max() > 0.08:
            steep.append(f"{nm} 1:{1 / g.max():.0f}")
    out.append(("steeper than 1:12", steep))
    return out


# ---------------------------------------------------------------- drawing
def main(path=OUT, for_overlay=False, sketch=False):
    x0, y0, x1, y1 = VIEW
    nx, ny = int((x1 - x0) / 1.5), int((y1 - y0) / 1.5)
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    H = L.height(X, Y)
    fig, ax = plt.subplots(figsize=(20, 20 * (y1 - y0) / (x1 - x0)), dpi=150)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks(np.arange(-250, x1, 50)); ax.set_yticks(np.arange(-250, y1, 50)); ax.tick_params(labelsize=7, colors="#777")
    ax.grid(color="#999", lw=0.3, alpha=0.4, zorder=0.5)
    cmap = LinearSegmentedColormap.from_list("land", ["#f3f5ea", "#e6ecd3", "#d6e0bb", "#c4d1a2", "#aebd88", "#97a674"])
    ax.imshow(LightSource(azdeg=315, altdeg=45).shade(H, cmap=cmap, vert_exag=3, blend_mode="soft", vmin=0, vmax=max(40, H.max())),
              extent=(x0, x1, y0, y1), origin="lower", zorder=0)
    cs = ax.contour(X, Y, H, levels=np.arange(1, 60, 1), colors="#6b5a45", linewidths=0.3, alpha=0.35, zorder=1)

    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def fill(g, fc, ec="none", lw=0.6, z=2, alpha=1.0, hatch=None, ls="-"):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and not q.is_empty:
                verts, codes = [], []
                for ring in [q.exterior] + list(q.interiors):
                    cs_ = list(ring.coords)
                    verts += cs_
                    codes += [MPath.MOVETO] + [MPath.LINETO] * (len(cs_) - 2) + [MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, hatch=hatch, ls=ls))

    fill(WATER, "#9cc7dc", "#3f7fa8", 0.8, 3)
    fill(GREEN, "#a9d08e", "#4f7a3a", 0.5, 3)
    fill(PLOT, "#dfeccf", "#2f5a2a", 1.2, 3.5)
    for b in BLOCKS:
        fill(b, "#efe8d6", "#c9bea6", 0.4, 4)
    fill(FRONT_U, "#c4a27a", "#5b4a36", 0.5, 5)
    hl = unary_union(HOUSE_LINES).intersection(FRONT_U)
    for q in getattr(hl, "geoms", [hl]):
        if q.geom_type == "LineString":
            xx, yy = q.xy
            ax.plot(xx, yy, color="#5b4a36", lw=0.35, zorder=5.1)
    fill(RIVER_STRIP, "#a9d08e", "none", 0, 4.3)
    fill(NE_GREEN, "#8DBF73", "#4f7a3a", 0.8, 4.2)
    fill(CLUB_SQUARE, "#d8cfbf", "#8a7a5a", 0.8, 4.2)
    g_ = np.random.default_rng(4)
    for zone, n_ in ((CLUB_SQUARE.buffer(-4).difference(CLUBHOUSE.buffer(4)), 14), (NE_GREEN.buffer(-3).difference(CHURCH_HALL.buffer(3) if CHURCH_HALL else Point(0, 0)), 10)):
        pts_ = []
        while len(pts_) < n_:
            p_ = Point(g_.uniform(*zone.bounds[0::2]), g_.uniform(*zone.bounds[1::2]))
            if zone.contains(p_) and all(p_.distance(q_) > 7 for q_ in pts_):
                pts_.append(p_)
        ax.scatter([p.x for p in pts_], [p.y for p in pts_], s=60, c="#5f8f4a", edgecolors="#2f5a2a", linewidths=0.6, zorder=8)
    fill(CLUBHOUSE, "#7a5230", "#222", 0.9, 8)
    if PUB is not None:
        fill(PUB, "#a0522d", "#222", 0.9, 8)
    if CHURCH_HALL is not None:
        fill(CHURCH_HALL, "#8a7f70", "#222", 0.9, 8)
    ax.plot([MEMORIAL[0]], [MEMORIAL[1]], marker="P", ms=11, mfc="#555", mec="#111", zorder=9)
    fill(STREET_U, "#e3dccb", "#6b5a45", 0.6, 6.5)
    for s in STUBS:
        xx, yy = s.xy
        ax.plot(xx, yy, color="#9a8a70", lw=1.0, ls=(0, (3, 2)), zorder=6.6)
    fill(MAIN.buffer(5.0).intersection(VIEWBOX.buffer(20)), "#f2d27a", "#222", 0.9, 7)     # main roads at their real 10 m
    for name_, kind_, (bx, by) in L.BRIDGES:
        if x0 < bx < x1 and y0 < by < y1:
            ax.plot([bx], [by], marker="s", ms=9 if kind_ != "foot" else 6, mfc="#d9d9d9" if kind_ == "modern" else "#8a5a2b", mec="#222", zorder=9)
    if sketch:
        import json
        for p_ in json.load(open(os.path.join(HERE, "marcel_districtA_raw.json"))):
            xx, yy = zip(*p_)
            ax.plot(xx, yy, color="#ff7a00", lw=2.2, zorder=12, alpha=0.9)
    if not for_overlay:
        for nm, ln, w, k in STREETS:
            p = ln.interpolate(0.5, normalized=True)
            q = ln.interpolate(min(0.5 * ln.length + 2, ln.length))
            ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
            ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
            ax.text(p.x, p.y, nm, rotation=ang, fontsize=7 if k == "street" else 8, ha="center", va="center", zorder=10, color="#3a2a1e",
                    weight="bold" if k == "ring" else "normal")
        for t_, (x_, y_) in (("CLUB SQUARE", (CLUB_SQUARE.centroid.x + 8, CLUB_SQUARE.centroid.y - 30)), ("clubhouse", CLUBHOUSE.centroid.coords[0]),
                             ("green +\nwar memorial", (MEMORIAL[0], MEMORIAL[1] - 9))) + ((("pub", PUB.centroid.coords[0]),) if PUB is not None else ()) + \
                            ((("church hall", CHURCH_HALL.centroid.coords[0]),) if CHURCH_HALL is not None else ()):
            ax.text(x_, y_, t_, fontsize=7.5, ha="center", va="center", zorder=11, rotation=90 if t_ == "clubhouse" else 0,
                    weight="bold" if t_.isupper() else "normal", bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
        ax.text(0, 0, "THE GROUND (plot)", fontsize=12, ha="center", va="center", color="#2f5a2a", zorder=10, weight="bold")
        ax.text(225, 100, "district B →", fontsize=8, color="#7a6a50", zorder=10, ha="center")
        res = checks()
        txt = "\n".join(f"{k}: {len(v)}" + (f" — {'; '.join(v[:5])}" if v else "") for k, v in res)
        ax.set_title("DISTRICT A v1 — Marcel's town sketch as the base, at real sizes. Bold = ring streets 10.5 m, others 8.5 m; "
                     "brown = terraced houses (9 m deep), cream = yards", fontsize=10.5, loc="left")
        ax.text(x0 + 4, y0 + 4, "CHECK\n" + txt, fontsize=7, zorder=30, va="bottom", ha="left",
                bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.4"))
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("saved", os.path.relpath(path))


if __name__ == "__main__":
    for k, v in checks():
        print(f"{k}: {len(v)}", v[:8])
    main()
    main(OUT.replace(".png", "_vs_marcel.png"), sketch=True)
