"""Step 4 — district B v1 (east of Shelley Street, between the river and the main roads): Marcel's town sketch (2026-11-10),
worked out at real sizes by Claude with district A's rules (district_lib.py). Marcel: B in one go (B1 grid + B2 diagonal).
python3 tools/plan/village_district_B_v1.py -> design/world/village_district_B_v1.png (+ _vs_marcel.png)

Streets traced from the sketch (marcel_districtB_raw.json -> trace_streets.merge), split where a traced chain turned a sharp
corner. All B streets are terrace streets, 10 m (7 m carriageway + 2 x 1.5 m pavements, as Marcel chose for A); the long
through streets build first. Shelley / Byron Street (district A) get B's houses on their east side. No houses on the main
roads (A's rule: only where Marcel says); the river side of the riverside street is built for now (open question). Marcel's green
square is a small park. Names: B1, B2, ... until Marcel names them.
"""
import json
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource, LinearSegmentedColormap
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union, polygonize, nearest_points

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import village_land_v1 as L
import village_district_A_v1 as A
import district_lib as D
import trace_streets as T

OUT = os.path.join(HERE, "../../design/world/village_district_B_v1.png")
VIEW = (195, -265, 800, 240)
TERR = 10.0
MAIN = unary_union(L.MAIN_ROADS)
RIVER = LineString(L.CANAL_PTS)
WATER = unary_union([RIVER.buffer(L.RIVER_W / 2)])

# ---------------------------------------------------------------- the district: the land between Shelley Street, the river and the main roads
_frame = box(195, -300, 860, 300)
_cut = unary_union([MAIN.intersection(_frame.buffer(50)), RIVER.intersection(_frame.buffer(50)), LineString([(206, 150), (206, -300)]),
                    _frame.exterior])
REGION = [f for f in polygonize(_cut) if f.contains(Point(450, 0))][0].intersection(box(206, -300, 800, 300))

# ---------------------------------------------------------------- streets
_raw = T.merge(json.load(open(os.path.join(HERE, "marcel_districtB_raw.json"))))
_lines = [q for ln in _raw for q in D.split_sharp(ln)]


def _to_main(ln):
    """A traced street that stops just short of a main road runs on to its centre line."""
    cs = list(ln.coords)
    for end in (0, -1):
        p = Point(cs[end])
        if 0 < MAIN.distance(p) < 25:
            q = nearest_points(MAIN, p)[0]
            if end == 0:
                cs.insert(0, (q.x, q.y))
            else:
                cs.append((q.x, q.y))
    return LineString(cs)


_lines = [_to_main(LineString(L._chaikin(list(l.simplify(1.0).coords), 2))) for l in _lines]
_lines = sorted(_lines, key=lambda l: -l.length)
STREETS = [(f"B{i + 1}", ln, TERR, "ring" if ln.length > 400 else "street") for i, ln in enumerate(_lines)]
# district A's border streets (their east side is B's frontage)
A_BORDER = [s for s in A.STREETS if s[0] in ("Shelley Street", "Byron Street")]
ALL = STREETS + A_BORDER
STREET_U = D.street_union(ALL, REGION, MAIN)

# ---------------------------------------------------------------- open land
GREEN_SQ = Polygon(json.load(open(os.path.join(HERE, "marcel_districtB_green.json")))[0]).buffer(0)
GREEN_SQ = D.clean(GREEN_SQ.difference(STREET_U.buffer(0.5)), 50)       # drawn to the street centres: the streets cut out
RIVER_STRIP = Point(0, 0).buffer(0)   # houses on the river side of the riverside street: built for now, open question for Marcel
OPEN = unary_union([WATER.buffer(4), GREEN_SQ, RIVER_STRIP.buffer(0.5)])
ROADS = unary_union([STREET_U, MAIN.buffer(5.0)])
BLOCKS = D.blocks(VIEW, ROADS, OPEN, REGION)
ALLOWED = unary_union(BLOCKS).difference(MAIN.buffer(6.0)).difference(OPEN)

# ---------------------------------------------------------------- houses, corners, backs
# houses on the main roads wherever they fit (Marcel 2026-11-10: "waar het past, mogen huizen aan de hoofdweg"); set 9 m back
# from the road's centre line like district A's main-road rows
MAIN_FRONT = []
for i_, r_ in enumerate(L.MAIN_ROADS):
    if i_ == 4:          # the bypass along the top right (south-east): no houses on it in this district (Marcel: too tight)
        continue
    g_ = r_.intersection(REGION.buffer(15))
    for q_ in getattr(g_, "geoms", [g_]):
        if q_.geom_type == "LineString" and q_.length > 30:
            MAIN_FRONT.append((f"main road {i_}", LineString(L._chaikin(list(q_.simplify(3).coords), 3)), 14.0, "mainfront"))
HOUSES = D.build_houses(ALL, ALLOWED, MAIN_FRONT)
HOUSES = [h for h in HOUSES if h.centroid.x > 206]          # Shelley / Byron west side is district A

# the river side of the riverside street (Marcel): in the middle there is a gap without houses; the 6 houses either side of it
# (tiny yards, the river comes close) go, and the gap + their land become a green by the water
RIVERSIDE = STREETS[0][1]
_land = REGION.difference(STREET_U)
_north_pt = None
_rs_houses = []
for h in HOUSES:
    c_ = h.centroid
    pr = RIVERSIDE.project(c_)
    q_ = RIVERSIDE.interpolate(pr)
    q2 = RIVERSIDE.interpolate(min(pr + 1, RIVERSIDE.length))
    side = (q2.x - q_.x) * (c_.y - q_.y) - (q2.y - q_.y) * (c_.x - q_.x)
    if side > 0 and c_.distance(RIVERSIDE) < 15 and RIVER.distance(c_) < 60:
        _rs_houses.append((pr, h))
_rs_houses.sort(key=lambda t: t[0])
_gaps = [(_rs_houses[k + 1][0] - _rs_houses[k][0], k) for k in range(len(_rs_houses) - 1)]
_gw, _gk = max(_gaps)
_drop = [h for pr, h in _rs_houses[max(0, _gk - 5):_gk + 7]]
RS_GAP = (_rs_houses[_gk][0], _rs_houses[_gk + 1][0])
_s0 = _rs_houses[max(0, _gk - 5)][0] - 3
_s1 = _rs_houses[min(len(_rs_houses) - 1, _gk + 6)][0] + 3
def _perp(sv, ln=120):
    p_ = RIVERSIDE.interpolate(sv); q_ = RIVERSIDE.interpolate(min(sv + 1, RIVERSIDE.length))
    tx, ty = q_.x - p_.x, q_.y - p_.y; T_ = math.hypot(tx, ty) or 1
    return LineString([(p_.x + ty / T_ * ln, p_.y - tx / T_ * ln), (p_.x - ty / T_ * ln, p_.y + tx / T_ * ln)])
_mid = RIVERSIDE.interpolate((_s0 + _s1) / 2)
_pieces = list(polygonize(unary_union([_land.boundary, _perp(_s0), _perp(_s1)])))
RIVER_GREEN = [f for f in _pieces if f.representative_point().within(_land) and f.distance(RIVER) < 30
               and f.distance(_mid) < 25 and _land.contains(f.representative_point())]
RIVER_GREEN = D.clean(unary_union(RIVER_GREEN).intersection(_land).difference(WATER), 100) if RIVER_GREEN else None
HOUSES = [h for h in HOUSES if not any(h is d_ for d_ in _drop)]
if RIVER_GREEN is not None:
    OPEN = unary_union([OPEN, RIVER_GREEN])
    ALLOWED = ALLOWED.difference(RIVER_GREEN)
    HOUSES = [h for h in HOUSES if not h.intersects(RIVER_GREEN.buffer(-0.5))]
CORNERS = D.corner_houses(ALL, HOUSES, ALLOWED, MAIN_FRONT)
HOUSES += CORNERS
BK = D.backs(HOUSES, CORNERS, BLOCKS, STREET_U, MAIN, unary_union([OPEN, GREEN_SQ]), VIEW)
YARDS, OUTRIGGERS, GINNEL_U, TUNNELS = BK["yards"], BK["outriggers"], BK["ginnel"], BK["tunnels"]
# the green square: a few trees round its edge
SQ_TREES = [GREEN_SQ.buffer(-4).exterior.interpolate(d) for d in np.arange(3, GREEN_SQ.buffer(-4).exterior.length, 11.0)]


# ---------------------------------------------------------------- checks
def _depth(b):
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
    out.append(("streets in the water / green", [nm for nm, ln, w, k in STREETS if ln.buffer(w / 2).intersection(unary_union([WATER, GREEN_SQ])).area > 2]))
    loose = []
    net = unary_union([l for n, l, w, k in ALL] + list(L.MAIN_ROADS))
    for nm, ln, w, k in STREETS:
        for e in (Point(ln.coords[0]), Point(ln.coords[-1])):
            others = unary_union([l2 for n2, l2, w2, k2 in ALL if n2 != nm] + list(L.MAIN_ROADS))
            if others.distance(e) > 3:
                loose.append(f"{nm} at ({e.x:.0f}, {e.y:.0f})")
    out.append(("loose street ends", loose))
    thin = [f"({b.centroid.x:.0f}, {b.centroid.y:.0f}) {_depth(b):.0f} m" for b in BLOCKS if _depth(b) < 12]
    out.append(("blocks too thin for a row of houses", thin))
    hs = HOUSES
    ov = sum(1 for i in range(len(hs)) for j in range(i + 1, len(hs)) if hs[i].distance(hs[j]) < 0.01 and hs[i].intersection(hs[j]).area > 0.5)
    out.append(("overlapping houses", [str(ov)] if ov else []))
    steep = []
    for nm, ln, w, k in STREETS:
        ds = np.linspace(0, ln.length, max(3, int(ln.length / 10)))
        P_ = np.array([ln.interpolate(d).coords[0] for d in ds])
        h = L.height(P_[:, 0], P_[:, 1])
        g = np.abs(np.diff(h)) / np.diff(ds)
        if g.max() > 0.08:
            steep.append(f"{nm} 1:{1 / g.max():.0f}")
    out.append(("steeper than 1:12", steep))
    comps = [g for g in getattr(GINNEL_U, "geoms", [GINNEL_U]) if g.geom_type == "Polygon"]
    closed = [g for g in comps if not g.intersects(BK["open_to"]) and not any(t[1].distance(g) < 1.2 for t in TUNNELS)]
    out.append(("ginnels with no way in", [f"({g.centroid.x:.0f}, {g.centroid.y:.0f})" for g in closed]))
    return out


# ---------------------------------------------------------------- drawing
def main(path=OUT, sketch=False):
    x0, y0, x1, y1 = VIEW
    nx, ny = int((x1 - x0) / 1.5), int((y1 - y0) / 1.5)
    X, Y = np.meshgrid(np.linspace(x0, x1, nx), np.linspace(y0, y1, ny))
    H = L.height(X, Y)
    fig, ax = plt.subplots(figsize=(20, 20 * (y1 - y0) / (x1 - x0)), dpi=150)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_xticks(np.arange(200, x1, 50)); ax.set_yticks(np.arange(-250, y1, 50)); ax.tick_params(labelsize=7, colors="#777")
    ax.grid(color="#999", lw=0.3, alpha=0.4, zorder=0.5)
    cmap = LinearSegmentedColormap.from_list("land", ["#f3f5ea", "#e6ecd3", "#d6e0bb", "#c4d1a2", "#aebd88", "#97a674"])
    ax.imshow(LightSource(azdeg=315, altdeg=45).shade(H, cmap=cmap, vert_exag=3, blend_mode="soft", vmin=0, vmax=max(40, H.max())),
              extent=(x0, x1, y0, y1), origin="lower", zorder=0)
    ax.contour(X, Y, H, levels=np.arange(1, 60, 1), colors="#6b5a45", linewidths=0.3, alpha=0.35, zorder=1)
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def fill(g, fc, ec="none", lw=0.6, z=2, alpha=1.0):
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "Polygon" and not q.is_empty:
                verts, codes = [], []
                for ring in [q.exterior] + list(q.interiors):
                    cs_ = list(ring.coords)
                    verts += cs_
                    codes += [MPath.MOVETO] + [MPath.LINETO] * (len(cs_) - 2) + [MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))

    fill(WATER, "#9cc7dc", "#3f7fa8", 0.8, 3)
    fill(RIVER_STRIP, "#cfe3c0", "#4f7a3a", 0.4, 3.2)
    fill(GREEN_SQ, "#8DBF73", "#4f7a3a", 0.8, 4.2)
    if RIVER_GREEN is not None:
        fill(RIVER_GREEN, "#8DBF73", "#4f7a3a", 0.8, 4.2)
    for b in BLOCKS:
        fill(b, "#efe8d6", "#c9bea6", 0.4, 4)
    fill(GINNEL_U, "#b9b2a3", "#8a8274", 0.3, 4.6)
    for y_ in YARDS:
        fill(y_, "#e2d6bd", "#7e4a3a", 0.35, 4.7)
    for o_ in OUTRIGGERS:
        fill(o_, "#b08f68", "#5b4a36", 0.35, 4.8)
    fill(unary_union(HOUSES), "#c4a27a", "#5b4a36", 0.5, 5)
    for h in HOUSES:
        xx, yy = h.exterior.xy
        ax.plot(xx, yy, color="#5b4a36", lw=0.3, zorder=5.1)
    for h_, ln_ in TUNNELS:
        fill(ln_.buffer(0.75, cap_style=2).intersection(h_.buffer(0.3)), "#6b6458", "none", 0, 5.2)
    fill(STREET_U, "#e3dccb", "#6b5a45", 0.6, 6.5)
    fill(MAIN.buffer(5.0).intersection(box(*VIEW).buffer(20)), "#f2d27a", "#222", 0.9, 7)
    ax.scatter([p.x for p in SQ_TREES], [p.y for p in SQ_TREES], s=60, c="#5f8f4a", edgecolors="#2f5a2a", linewidths=0.6, zorder=8)
    for name_, kind_, (bx, by) in L.BRIDGES:
        if x0 < bx < x1 and y0 < by < y1:
            ax.plot([bx], [by], marker="s", ms=8, mfc="#8a5a2b", mec="#222", zorder=9)
    if sketch:
        for p_ in json.load(open(os.path.join(HERE, "marcel_districtB_raw.json"))):
            xx, yy = zip(*p_)
            ax.plot(xx, yy, color="#ff7a00", lw=2.2, zorder=12, alpha=0.9)
    for nm, ln, w, k in ALL:
        p = ln.interpolate(0.5, normalized=True)
        q = ln.interpolate(min(0.5 * ln.length + 2, ln.length))
        ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
        ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
        ax.text(p.x, p.y, nm, rotation=ang, fontsize=7.5, ha="center", va="center", zorder=10, color="#3a2a1e",
                weight="bold" if k == "ring" else "normal", clip_on=True)
    ax.text(GREEN_SQ.centroid.x, GREEN_SQ.centroid.y, "green\n(Marcel)", fontsize=7.5, ha="center", va="center", zorder=11,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    ax.text(214, 0, "← district A", fontsize=8, color="#7a6a50", zorder=10)
    res = checks()
    txt = "\n".join(f"{k}: {len(v)}" + (f" — {'; '.join(v[:5])}" if v else "") for k, v in res)
    ax.set_title(f"DISTRICT B v1 — Marcel's sketch at real sizes (district A's rules). Streets 10 m; {len(HOUSES)} houses "
                 f"({len(CORNERS)} corner), {len(YARDS)} yards, {len(TUNNELS)} tunnel backs; grey = ginnels", fontsize=10.5, loc="left")
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
