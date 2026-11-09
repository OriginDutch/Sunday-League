"""Village plan v4 — the town GROWS from what is already there (Marcel on v2: "it feels like you built the rest round
what we had; no regard for where roads already are, how roads join, how houses stand").
python3 tools/plan/village_plan_v4.py  ->  design/world/village_v4.png (+ zooms)
v4 (panel on v3): no junction on or near a bridge; every block gets a use (split -> mews court -> park / playing
field / allotments / garages / play area), coverage measured per block; ~10-15 % public green, marked as green;
landmarks with their own grounds; denser estate + industrial; no street doubling a main road.

How it grows:
 1. Start from the main roads (village plan v1) and every street of world plan v5 (the area round the ground, unchanged).
 2. v5 streets that stop at the edge of that area carry straight on until they meet another street.
 3. Every block between streets is split by a new street only if that street meets streets at BOTH ends, at a real
    T-junction (65-115 deg), at least 28 m from other junctions (or lined up with one: a crossroads). The split runs
    across the long side when the block is too long, along it when it is too deep — until the block holds exactly
    two rows of plots back to back (per layer). New build may end in a cul-de-sac with a turning head.
 4. Houses face the street; the layer at each plot decides the house type (so the High Street gets old core shops).
Self-check (does it read as a village, not only "nothing collides"): junction angles, junction spacing, no street
crossing another without a junction, no loose ends (except cul-de-sacs), no building on a street / canal / railway /
landmark / the ground.
"""
import math
from shapely.ops import substring
import os
import random
import sys
from collections import defaultdict, Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from shapely.geometry import LineString, Polygon, Point, box, MultiLineString
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import world_plan_v5 as W
import village_plan_v1 as V

OUTDIR = os.path.join(HERE, "../../design/world")
R = 750
WORLD = box(-R, -R, R, R)
V5_BOX = box(-262, -262, 262, 228)
rng = random.Random(31)

# ---------------------------------------------------------------- layers
CORE, VIC, EDW, S30, POST, NEW, IND = ("old core", "Victorian terraces", "Edwardian + mixed infill", "1930s semis",
                                       "post-war estate + flats", "new build (cul-de-sacs)", "industrial")
REG = {}
_cov = Polygon()
for nm, col, pts in reversed(V.LAYERS):
    REG[nm] = REG.get(nm, Polygon()).union(Polygon(pts).intersection(WORLD).difference(_cov))
    _cov = _cov.union(Polygon(pts))
REG_P = {k: prep(v) for k, v in REG.items()}


def layer_at(x, y):
    p = Point(x, y)
    for nm in (IND, POST, CORE, VIC, NEW, S30, EDW):
        if nm in REG_P and REG_P[nm].contains(p):
            return nm
    return EDW


# block depth = two plots back to back (+ alley); max block length; street; wiggle; house rule
RULE = {
    CORE: dict(depth=58, maxlen=120, w=5.4, pv=1.3, wig=11.0, house=("cottage", 4.5, 9.0, 0.4, 0.6, 7.0, 11.0, 8.5)),
    VIC:  dict(depth=40, maxlen=170, w=6.2, pv=1.6, wig=2.0, house=("terrace", 4.6, 5.8, 0.4, 1.5, 6.0, 8.5, 8.0)),
    EDW:  dict(depth=48, maxlen=190, w=6.6, pv=1.8, wig=3.0, house=("terrace", 5.6, 6.6, 2.0, 3.0, 8.0, 10.0, 9.0)),
    S30:  dict(depth=58, maxlen=230, w=6.6, pv=1.8, wig=16.0, house=("semi", 13.0, 13.0, 5.0, 6.5, 9.0, 13.0, 9.0)),
    POST: dict(depth=150, maxlen=260, w=6.4, pv=1.8, wig=5.0, house=("terrace", 5.5, 5.5, 3.0, 4.0, 8.0, 10.0, 8.5)),
    NEW:  dict(depth=52, maxlen=210, w=5.6, pv=1.6, wig=20.0, house=("detached", 9.0, 11.0, 5.0, 6.5, 8.0, 11.0, 9.0)),
    IND:  dict(depth=95, maxlen=300, w=7.5, pv=1.5, wig=0.0, house=None),
}
GAP = {"terrace": 0.0, "cottage": 0.0, "semi": 3.0, "detached": 3.5}

# ---------------------------------------------------------------- the network
class Street:
    def __init__(self, line, w, pv, kind, layer=None, culdesac=False):
        self.line, self.w, self.pv, self.kind, self.layer, self.cul = line, w, pv, kind, layer, culdesac


STREETS = []
for n, (pts, w, k) in V.ROADS.items():
    STREETS.append(Street(LineString(pts), w, 2.0, "main"))
for n, r in W.roads.items():
    seg = r.intersection(V5_BOX)
    for s in getattr(seg, "geoms", [seg]):
        if s.geom_type == "LineString" and s.length > 2:
            STREETS.append(Street(s, W.RW[n][0], W.RW[n][1], "v5"))
LMK = [(nm, box(x - sz[0] / 2, y - sz[1] / 2, x + sz[0] / 2, y + sz[1] / 2), col)
       for nm, (x, y), sz, col, shape in V.LANDMARKS if shape == "rect"]
lmk_area = unary_union([g for _, g, _ in LMK])
canal_block = V.CANAL.buffer(12.0)
rail_block = V.RAIL.buffer(9.0)
HARD = unary_union([canal_block, rail_block, lmk_area.buffer(3), W.PLOT.buffer(1)])
HARD_P = prep(HARD)
HARD2_P = prep(unary_union([canal_block, rail_block, W.PLOT.buffer(1)]))
JUNCTIONS = []          # points where a street meets another
# where main roads cross the canal or the railway: no junction within 30 m of these (bridges + ramps)
BRIDGE_PTS = []
for s_ in STREETS:
    if s_.kind == "main":
        for base in (V.CANAL, V.RAIL):
            x_ = s_.line.intersection(base)
            for g_ in getattr(x_, "geoms", [x_]):
                if g_.geom_type == "Point":
                    BRIDGE_PTS.append(g_)


def net_lines(exclude=None):
    return unary_union([s.line for s in STREETS if s is not exclude])


def edge_of(s):
    return s.w / 2 + s.pv


def nearest_street(pt, exclude=None):
    best, bd = None, 1e9
    for s in STREETS:
        if s is exclude:
            continue
        d = s.line.distance(pt)
        if d < bd:
            best, bd = s, d
    return best, bd


def tangent(line, d):
    a = line.interpolate(max(d - 1, 0))
    b = line.interpolate(min(d + 1, line.length))
    L = math.hypot(b.x - a.x, b.y - a.y) or 1
    return (b.x - a.x) / L, (b.y - a.y) / L


def junction_angle(host, pt, direction):
    t = tangent(host.line, host.line.project(pt))
    c = abs(t[0] * direction[0] + t[1] * direction[1])
    return math.degrees(math.acos(min(1.0, c)))           # 90 = square T


def junction_ok(pt):
    if any(b.distance(pt) < 30.0 for b in BRIDGE_PTS):
        return False
    for j in JUNCTIONS:
        d = j.distance(pt)
        if 4.0 < d < 28.0:
            return False
    return True


# ---------------------------------------------------------------- step 2: v5 streets carry on out of the v5 area
for s in [s for s in STREETS if s.kind == "v5"]:
    for end in (0, -1):
        cs = list(s.line.coords)
        p = Point(cs[end])
        if V5_BOX.exterior.distance(p) > 2.0:
            continue
        q = Point(cs[1] if end == 0 else cs[-2])
        dx, dy = p.x - q.x, p.y - q.y
        L = math.hypot(dx, dy) or 1
        dx, dy = dx / L, dy / L
        pts = [(p.x, p.y)]
        hit = None
        for k in range(1, 120):
            x, y = p.x + dx * 3 * k, p.y + dy * 3 * k
            pt = Point(x, y)
            if not WORLD.contains(pt) or HARD_P.contains(pt) or V5_BOX.buffer(-0.5).contains(pt):
                break
            pts.append((x, y))
            host, d = nearest_street(pt, exclude=s)
            if k > 2 and host is not None and host.kind != "v5" and d < 1.5:
                hit = (host, pt)
                break
        if hit and len(pts) > 3:
            host, pt = hit
            ang = junction_angle(host, pt, (dx, dy))
            if ang > 60:
                ln = LineString(pts)
                lay = layer_at(*ln.interpolate(0.5, normalized=True).coords[0])
                r = RULE[lay]
                STREETS.append(Street(ln, r["w"], r["pv"], "ext", lay))
                JUNCTIONS.append(Point(pts[-1]))
                JUNCTIONS.append(p)


# ---------------------------------------------------------------- step 2b: streets along the canal and the railway
main_cut = unary_union([s.line.buffer(edge_of(s) + 0.5) for s in STREETS if s.kind == "main"])
for base, off in ((V.CANAL, 12.0 + 3.4), (V.RAIL, 9.0 + 3.4)):
    for side in ("left", "right"):
        ln = base.parallel_offset(off, side, join_style=2)
        for part in getattr(ln, "geoms", [ln]):
            rest = part.difference(main_cut).difference(V5_BOX.buffer(6)).difference(lmk_area.buffer(8)).intersection(WORLD)
            for seg in getattr(rest, "geoms", [rest]):
                if seg.geom_type != "LineString" or seg.length < 60:
                    continue
                # no street doubling a main road: drop stretches that run alongside one within 45 m
                good = []
                dd = 0.0
                while dd <= seg.length:
                    pt_ = seg.interpolate(dd)
                    tt = tangent(seg, dd)
                    ok_ = True
                    for m_ in STREETS:
                        if m_.kind != "main" or m_.line.distance(pt_) > 45:
                            continue
                        mt = tangent(m_.line, m_.line.project(pt_))
                        if abs(mt[0] * tt[0] + mt[1] * tt[1]) > 0.9 and m_.line.distance(pt_) > edge_of(m_) + 3:
                            ok_ = False
                    good.append((dd, ok_))
                    dd += 5.0
                runs, cur_ = [], []
                for dd, ok_ in good:
                    if ok_:
                        cur_.append(dd)
                    elif cur_:
                        runs.append(cur_)
                        cur_ = []
                if cur_:
                    runs.append(cur_)
                pieces = [LineString([seg.interpolate(x).coords[0] for x in r_]) for r_ in runs if len(r_) > 1 and r_[-1] - r_[0] >= 60]
                for piece in pieces:
                    cs = list(piece.coords)
                    for end in (0, -1):
                        p0 = Point(cs[end])
                        host, d = nearest_street(p0)
                        if host is None or host.kind != "main" or d > edge_of(host) + 2:
                            continue
                        X = min(BRIDGE_PTS, key=lambda b: b.distance(p0)) if BRIDGE_PTS else None
                        if X is not None and X.distance(p0) < 45 and host.line.distance(X) < 1:
                            # bend away from the bridge: meet the main road square-on ~32 m from the crossing
                            dX = host.line.project(X)
                            cands = [host.line.interpolate(min(max(dX + k, 0), host.line.length)) for k in (-32, 32)]
                            T = min(cands, key=lambda q: q.distance(p0))
                            tm = tangent(host.line, host.line.project(T))
                            nm = (-tm[1], tm[0])
                            if (p0.x - T.x) * nm[0] + (p0.y - T.y) * nm[1] < 0:
                                nm = (-nm[0], -nm[1])
                            A = (T.x + nm[0] * 14, T.y + nm[1] * 14)
                            line_ = LineString(cs)
                            keep = line_.difference(host.line.buffer(30))
                            keep = max(getattr(keep, "geoms", [keep]), key=lambda g: g.length) if not keep.is_empty else None
                            if keep is None or keep.length < 40:
                                continue
                            kc = list(keep.coords)
                            # orient so the end we fix is last
                            if Point(kc[0]).distance(p0) < Point(kc[-1]).distance(p0):
                                kc = kc[::-1]
                            kc += [A, (T.x, T.y)]
                            cs = kc if end == -1 else kc[::-1]
                            JUNCTIONS.append(T)
                        else:
                            snap = host.line.interpolate(host.line.project(p0))
                            if end == 0:
                                cs.insert(0, (snap.x, snap.y))
                            else:
                                cs.append((snap.x, snap.y))
                            JUNCTIONS.append(snap)
                    lay = layer_at(*LineString(cs).interpolate(0.5, normalized=True).coords[0])
                    r = RULE[lay]
                    STREETS.append(Street(LineString(cs), r["w"], r["pv"], "edge", lay))
                continue



# loose ends of the canal / railway streets: join them to the nearest street with a short square link, or cut them back
for st in [x for x in STREETS if x.kind == "edge"]:
    cs = list(st.line.coords)
    for end in (0, -1):
        p0 = Point(cs[end])
        if WORLD.exterior.distance(p0) < 6 or lmk_area.distance(p0) < 12:
            continue
        host, d = nearest_street(p0, exclude=st)
        if host is not None and d < 1.5:
            continue
        if host is not None and d < 60:
            snap = host.line.interpolate(host.line.project(p0))
            link = LineString([(p0.x, p0.y), (snap.x, snap.y)])
            dx, dy = snap.x - p0.x, snap.y - p0.y
            L_ = math.hypot(dx, dy) or 1
            if not HARD2_P.intersects(link.buffer(3)) and junction_angle(host, snap, (dx / L_, dy / L_)) >= 65 and junction_ok(snap):
                if end == 0:
                    cs.insert(0, (snap.x, snap.y))
                else:
                    cs.append((snap.x, snap.y))
                JUNCTIONS.append(snap)
                continue
        # no good link: cut this end back to where the street last met another one
        line_ = LineString(cs)
        best = None
        for o in STREETS:
            if o is st:
                continue
            x_ = line_.intersection(o.line)
            if not x_.is_empty:
                for q in getattr(x_, "geoms", [x_]):
                    for c_ in q.coords:
                        dd = line_.project(Point(c_))
                        if best is None or (dd > best if end == -1 else dd < best):
                            best = dd
        if best is not None and ((end == -1 and line_.length - best > 1) or (end == 0 and best > 1)):
            seg_ = line_.interpolate(best)
            if end == -1:
                cs = [c_ for c_ in cs if line_.project(Point(c_)) < best] + [(seg_.x, seg_.y)]
            else:
                cs = [(seg_.x, seg_.y)] + [c_ for c_ in cs if line_.project(Point(c_)) > best]
    if len(cs) >= 2 and LineString(cs).length > 20:
        st.line = LineString(cs)
    else:
        STREETS.remove(st)


# ---------------------------------------------------------------- step 3: split blocks
def road_area(streets):
    return unary_union([s.line.buffer(edge_of(s), cap_style=2, join_style=2) for s in streets] +
                       [Point(s.line.coords[-1]).buffer(9) for s in streets if s.cul])


def frame_of(P):
    mrr = list(P.minimum_rotated_rectangle.exterior.coords)
    e1, e2 = math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2])
    a, b = (mrr[0], mrr[1]) if e1 >= e2 else (mrr[1], mrr[2])
    L = math.dist(a, b)
    t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    c = P.minimum_rotated_rectangle.centroid
    return (c.x, c.y), t, (-t[1], t[0]), max(e1, e2), min(e1, e2)


def try_split(P, lay):
    """A new street across block P that meets streets at both ends with proper junctions; returns Street or None."""
    r = RULE[lay]
    c, t, n, L, Wd = frame_of(P)
    options = []
    if L > r["maxlen"]:
        for f in (0.5, 0.42, 0.58, 0.35, 0.65):
            options.append(("across", (f - 0.5) * L))
    if Wd > r["depth"] * 1.55:
        for f in (0.0, -0.08, 0.08, -0.16, 0.16):
            options.append(("along", f * Wd))
    for mode, off in options:
        if mode == "across":
            o = (c[0] + t[0] * off, c[1] + t[1] * off)
            d = n
            span = Wd
        else:
            o = (c[0] + n[0] * off, c[1] + n[1] * off)
            d = t
            span = L
        if lay == CORE:
            a_ = math.atan2(d[1], d[0]) + rng.uniform(-0.3, 0.3)
            d = (math.cos(a_), math.sin(a_))
        raw = LineString([(o[0] - d[0] * (span + 40), o[1] - d[1] * (span + 40)), (o[0] + d[0] * (span + 40), o[1] + d[1] * (span + 40))])
        seg = raw.intersection(P)
        if seg.geom_type != "LineString" or seg.length < 25:
            continue
        a, b = Point(seg.coords[0]), Point(seg.coords[-1])
        ends = []
        for pt in (a, b):
            if WORLD.exterior.distance(pt) < 3.0 or lmk_area.distance(pt) < 6.0:
                ends.append(pt)
                continue
            host, dist = nearest_street(pt)
            near_v5 = V5_BOX.exterior.distance(pt) < 3.0 and host is not None and dist < 16
            if host is None or (dist > edge_of(host) + 2.5 and not near_v5):
                break
            snap = host.line.interpolate(host.line.project(pt))
            ang = junction_angle(host, snap, d)
            if ang < 65 or not junction_ok(snap):
                break
            ends.append(snap)
        if len(ends) != 2:
            continue
        # gentle bend in the middle, ends stay put
        A, B = ends
        pts = []
        steps = max(4, int(A.distance(B) / 8))
        ph = rng.uniform(0, 6.3)
        nx, ny = -d[1], d[0]
        for i in range(steps + 1):
            f = i / steps
            x, y = A.x + (B.x - A.x) * f, A.y + (B.y - A.y) * f
            off_ = r["wig"] * math.sin(math.pi * f) ** 2 * math.sin(ph)      # flat at both ends: square junctions
            pts.append((x + nx * off_, y + ny * off_))
        ln = LineString(pts)
        if HARD2_P.intersects(ln.buffer(r["w"] / 2)):          # canal / railway / the ground; a park or station may be touched
            continue
        # it must not run along / through another street except at its two ends
        others = net_lines()
        inner = LineString(pts[1:-1]) if len(pts) > 3 else ln
        trimmed = inner.difference(A.buffer(8)).difference(B.buffer(8))
        if not trimmed.is_empty and trimmed.distance(others) < edge_of(Street(ln, r["w"], r["pv"], "x")) + 3:
            continue
        return Street(ln, r["w"], r["pv"], "gen", lay)
    return None


def culdesac(P, lay):
    r = RULE[lay]
    c, t, n, L, Wd = frame_of(P)
    if Wd < 70:
        return None
    for f in (0.5, 0.35, 0.65):
        o = (c[0] + t[0] * (f - 0.5) * L, c[1] + t[1] * (f - 0.5) * L)
        for sd in (1, -1):
            raw = LineString([o, (o[0] + n[0] * sd * Wd, o[1] + n[1] * sd * Wd)])
            seg = raw.intersection(P)
            if seg.geom_type != "LineString" or seg.is_empty:
                continue
            far = Point(seg.coords[-1])
            host, dist = nearest_street(far)
            if host is None or dist > edge_of(host) + 2.5:
                continue
            snap = host.line.interpolate(host.line.project(far))
            if junction_angle(host, snap, (-n[0] * sd, -n[1] * sd)) < 65 or not junction_ok(snap):
                continue
            length = min(Wd * 0.62, 95)
            end = (snap.x - n[0] * sd * length, snap.y - n[1] * sd * length)
            ln = LineString([(snap.x, snap.y), end])
            if HARD_P.intersects(Point(end).buffer(10)) or not P.buffer(1).contains(Point(end).buffer(9.5)):
                continue
            return Street(ln, r["w"], r["pv"], "gen", lay, culdesac=True)
    return None


blocks = WORLD.difference(unary_union([road_area(STREETS), HARD, V5_BOX]))
queue = [g for g in getattr(blocks, "geoms", [blocks]) if g.geom_type == "Polygon" and g.area > 600]
LEAVES = []
guard = 0
while queue and guard < 4000:
    guard += 1
    P = queue.pop(0)
    rp = P.representative_point()
    lay = layer_at(rp.x, rp.y)
    s = try_split(P, lay)
    if s is None and lay in (NEW,) and P.area > 6000:
        s = culdesac(P, lay)
    if s is None:
        LEAVES.append((P, lay))
        continue
    STREETS.append(s)
    JUNCTIONS.append(Point(s.line.coords[0]))
    if not s.cul:
        JUNCTIONS.append(Point(s.line.coords[-1]))
    cut = s.line.buffer(edge_of(s), cap_style=2, join_style=2)
    if s.cul:
        cut = cut.union(Point(s.line.coords[-1]).buffer(9))
    parts = P.difference(cut)
    for g in getattr(parts, "geoms", [parts]):
        if g.geom_type == "Polygon" and g.area > 600:
            queue.append(g)
LEAVES += [(P, layer_at(P.representative_point().x, P.representative_point().y)) for P in queue]


# canal / railway streets that still end nowhere, or meet a street at a sharp angle: that end becomes a cul-de-sac
def _end_state(st, end):
    cs = list(st.line.coords)
    p = Point(cs[end])
    if WORLD.exterior.distance(p) < 6.0 or lmk_area.distance(p) < 12.0:
        return "ok"
    host, d = nearest_street(p, exclude=st)
    if host is None or d > 1.5:
        return "loose"
    q = Point(cs[1 if end == 0 else -2])
    dx, dy = p.x - q.x, p.y - q.y
    L_ = math.hypot(dx, dy) or 1
    return "sharp" if junction_angle(host, p, (dx / L_, dy / L_)) < 60 else "ok"


for st in [x for x in STREETS if x.kind == "edge"]:
    a0, a1 = _end_state(st, 0), _end_state(st, -1)
    if a0 == "ok" and a1 == "ok":
        continue
    if a0 != "ok" and a1 != "ok":
        STREETS.remove(st)            # connected nowhere: drop it, the blocks either side merge on the next run
        continue
    if a0 != "ok":
        st.line = LineString(list(st.line.coords)[::-1])
        a1 = a0
    if a1 == "sharp":                 # pull the end back off the other street
        st.line = substring(st.line, 0, st.line.length - 22)
    st.cul = True

ROADS_ALL = road_area(STREETS)
CARR = unary_union([s.line.buffer(s.w / 2, cap_style=2, join_style=2) for s in STREETS] +
                   [Point(s.line.coords[-1]).buffer(7) for s in STREETS if s.cul])


# ---------------------------------------------------------------- step 4: buildings
class Grid:
    def __init__(self, cell=25.0):
        self.c, self.d = cell, defaultdict(list)

    def _keys(self, g):
        x0, y0, x1, y1 = g.bounds
        for i in range(int(math.floor(x0 / self.c)), int(math.floor(x1 / self.c)) + 1):
            for j in range(int(math.floor(y0 / self.c)), int(math.floor(y1 / self.c)) + 1):
                yield i, j

    def add(self, g):
        for k in self._keys(g):
            self.d[k].append(g)

    def hits(self, g):
        seen = set()
        for k in self._keys(g):
            for o in self.d[k]:
                if id(o) not in seen:
                    seen.add(id(o))
                    if o.intersects(g):
                        return True
        return False


def fpoly(o, t, n, u0, u1, v0, v1):
    return Polygon([(o[0] + t[0] * u + n[0] * v, o[1] + t[1] * u + n[1] * v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))])


BLOCKED = prep(unary_union([ROADS_ALL.buffer(-0.02), canal_block, rail_block, lmk_area.buffer(2), V5_BOX.buffer(1), W.PLOT.buffer(1)]))
occ = Grid()
BUILD, FLATS, SHEDS = [], [], []

# flats + sheds first, in the middle of estate / industrial blocks
for P, lay in LEAVES:
    if lay not in (POST, IND):
        continue
    c, t, n, L, Wd = frame_of(P)
    sx, sy, gx, gy = (48, 13, 60, 30) if lay == POST else (44, 30, 50, 38)
    u = -L / 2 + gx / 2
    while u < L / 2 - gx / 2 + 1:
        v = -Wd / 2 + gy / 2
        while v < Wd / 2 - gy / 2 + 1:
            o = (c[0] + t[0] * u + n[0] * v, c[1] + t[1] * u + n[1] * v)
            g = fpoly(o, t, n, -sx / 2, sx / 2, -sy / 2, sy / 2)
            need = 10 if lay == POST else 8
            if P.contains(g) and g.distance(ROADS_ALL) >= need and not occ.hits(g.buffer(6)):
                occ.add(g.buffer(4))
                (FLATS if lay == POST else SHEDS).append(g)
            v += gy
        u += gx


def place_along(st, rr):
    line = st.line
    L = line.length
    edge = edge_of(st)
    for side in (1, -1):
        s = rr.uniform(3, 7)
        run, cur = 0, None
        while s < L - 4:
            p = line.interpolate(s)
            q = line.interpolate(min(s + 1.0, L))
            tx, ty = q.x - p.x, q.y - p.y
            d = math.hypot(tx, ty) or 1.0
            t = (tx / d, ty / d)
            n = (-t[1] * side, t[0] * side)
            o = (p.x + n[0] * edge, p.y + n[1] * edge)
            lay = layer_at(o[0] + n[0] * 10, o[1] + n[1] * 10)
            hr = RULE[lay]["house"]
            if hr is None:
                s += 6
                run = 0
                continue
            if lay != cur or run == 0:
                cur = lay
                kind, wmin, wmax, fgmin, fgmax, ydmin, ydmax, hd = hr
                w_run, fg_run, yd_run = rr.uniform(wmin, wmax), max(rr.uniform(fgmin, fgmax), 0.4), rr.uniform(ydmin, ydmax)
                run = 0
            w = w_run if kind != "cottage" else rr.uniform(wmin, wmax)
            ok = None
            for depth in (fg_run + hd + yd_run, fg_run + hd + 4.0):
                cand = fpoly(o, t, n, 0.0, w, 0.4, depth)
                if BLOCKED.intersects(cand) or occ.hits(cand.buffer(-0.4)) or not WORLD.contains(cand):
                    continue
                ok = depth
                break
            if ok is None:
                s += 2.0
                run = 0
                continue
            occ.add(cand)
            plot = fpoly(o, t, n, 0, w, 0, ok)
            if kind == "semi":
                hs = [fpoly(o, t, n, 0.6, w / 2, fg_run, fg_run + hd), fpoly(o, t, n, w / 2, w - 0.6, fg_run, fg_run + hd)]
            elif kind == "detached":
                hs = [fpoly(o, t, n, 1.2, w - 1.2, fg_run, fg_run + hd)]
            else:
                hs = [fpoly(o, t, n, 0, w, fg_run, fg_run + hd)]
                if kind == "terrace" and ok - fg_run - hd > 5:
                    u0 = 0 if run % 2 == 0 else w - 2.6
                    hs.append(fpoly(o, t, n, u0, u0 + 2.6, fg_run + hd, fg_run + hd + 3.5))
            shop = lay == CORE and st.kind == "main"
            BUILD.append({"plot": plot, "houses": hs, "layer": lay, "kind": kind, "shop": shop})
            s += w + GAP[kind]
            run += 1
            if kind in ("terrace", "cottage") and run >= rr.randint(9, 15):
                s += 1.6
                run = 0


rr = random.Random(5)
order = [s for s in STREETS if s.kind == "main"] + [s for s in STREETS if s.kind in ("ext", "edge")] + [s for s in STREETS if s.kind == "gen"]
for st in order:
    if st.kind == "main":
        segs = st.line.difference(V5_BOX.buffer(2))
        for g in getattr(segs, "geoms", [segs]):
            if g.geom_type == "LineString" and g.length > 15:
                place_along(Street(g, st.w, st.pv, "main"), rr)
    else:
        place_along(st, rr)


# ---------------------------------------------------------------- step 5: every block gets a use
GREEN_KINDS = ("park", "playing field", "allotments", "play area")
GREEN_LMK = [g for nm, g, col in LMK if any(k in nm.lower() for k in ("park", "green", "cemetery", "sports", "playing", "allotments"))]
TOWN = WORLD.area
USES = []          # (geom, kind)
MEWS = []          # lanes into block middles
green_area = sum(g.area for g in GREEN_LMK)


def used_now():
    return unary_union([b["plot"] for b in BUILD] + [f.buffer(8) for f in FLATS] + [f.buffer(6) for f in SHEDS] +
                       [g for g, k in USES])


rr2 = random.Random(9)
used = used_now()
left = []
for P, lay in LEAVES:
    rest = P.difference(used).buffer(-1.0).buffer(1.0, join_style=2)
    for g in getattr(rest, "geoms", [rest]):
        if g.geom_type == "Polygon" and g.area > 300:
            left.append((g, lay))
left.sort(key=lambda x: -x[0].area)
small_cycle = ["garages", "allotments", "play area", "allotments"]
k_small = 0
LEFT2 = []
for g, lay in left:
    c, t, n, L, Wd = frame_of(g)
    if g.area >= 3500 and Wd >= 30 and green_area < 0.13 * TOWN:
        kind = "playing field" if g.area > 9000 else "park"
        USES.append((g, kind))
        green_area += g.area
        continue
    if g.area >= 1200 and Wd >= 26 and lay not in (IND,):
        # a mews / court: a lane from the nearest street into the block, houses along it
        rp = g.representative_point()
        a_, b_ = nearest_points(rp, CARR)
        lane = LineString([(b_.x, b_.y), (rp.x, rp.y)])
        if lane.length < 120 and not HARD2_P.intersects(lane.buffer(2.5)):
            cut = lane.buffer(2.6)
            BUILD[:] = [b for b in BUILD if not b["plot"].intersects(cut)]
            ext = LineString([(b_.x, b_.y), (rp.x + (rp.x - b_.x) / max(lane.length, 1) * (L * 0.35), rp.y + (rp.y - b_.y) / max(lane.length, 1) * (L * 0.35))])
            inner = ext.intersection(g.buffer(-4))
            inner = max(getattr(inner, "geoms", [inner]), key=lambda q: q.length) if not inner.is_empty else None
            MEWS.append(ext.intersection(g.buffer(2)).union(lane) if inner is not None else lane)
            if inner is not None and inner.geom_type == "LineString" and inner.length > 20:
                before = len(BUILD)
                place_along(Street(inner, 4.4, 0.8, "mews"), rr2)
                for b in BUILD[before:]:
                    b["mews"] = True
            continue
    if g.area >= 300:
        LEFT2.append(g)
# leftovers behind houses become their back gardens (as in a real town): split by nearest house, glued onto that plot.
# Only pieces with no houses around them get a small named use.
used = used_now()
for P, lay in LEAVES:
    rest = P.difference(used).difference(unary_union([m.buffer(2.5) for m in MEWS]) if MEWS else Polygon()).buffer(-1.0).buffer(1.0, join_style=2)
    for g in getattr(rest, "geoms", [rest]):
        if g.geom_type == "Polygon" and g.area > 60:
            LEFT2.append(g)
LEFT2 = [g for g in unary_union(LEFT2).geoms] if LEFT2 and unary_union(LEFT2).geom_type == "MultiPolygon" else ([unary_union(LEFT2)] if LEFT2 else [])
from shapely import STRtree, voronoi_polygons
from shapely.geometry import MultiPoint
PLOTS_TREE = STRtree([b["plot"] for b in BUILD])
for g in LEFT2:
    near = [int(i) for i in PLOTS_TREE.query(g.buffer(3.0)) if BUILD[int(i)]["plot"].distance(g) < 3.0 and BUILD[int(i)]["houses"]]
    if near:
        pts, seen = [], set()
        for i in near:
            c_ = BUILD[i]["plot"].centroid
            k_ = (round(c_.x, 1), round(c_.y, 1))
            if k_ not in seen:
                seen.add(k_)
                pts.append((i, c_))
        cells = [g] if len(pts) == 1 else list(voronoi_polygons(MultiPoint([c_ for i, c_ in pts]), extend_to=g.buffer(50)).geoms)
        for cell in cells:
            piece = cell.intersection(g)
            if piece.is_empty or piece.area < 1:
                continue
            i = min(near, key=lambda j: BUILD[j]["plot"].distance(piece))
            BUILD[i]["plot"] = BUILD[i]["plot"].union(piece.buffer(0.05))
            BUILD[i]["garden"] = True
        continue
    if g.area < 300:
        continue
    kind = small_cycle[k_small % len(small_cycle)]
    k_small += 1
    if kind in GREEN_KINDS and green_area + g.area > 0.13 * TOWN:
        kind = "garages"
    USES.append((g, kind))
    if kind in GREEN_KINDS:
        green_area += g.area
GREEN_PCT = 100 * green_area / TOWN


def coverage():
    """Share of each block that is built on or has a named use."""
    used = used_now().union(unary_union([m.buffer(2.5) for m in MEWS]) if MEWS else Polygon())
    low, tot, tot_used = 0, 0.0, 0.0
    for P, lay in LEAVES:
        u = P.intersection(used).area
        tot += P.area
        tot_used += u
        if u / P.area < 0.85 and P.area > 1500:
            low += 1
    return low, 100 * tot_used / max(tot, 1)


# ---------------------------------------------------------------- self-check
DIAG = []
COVER = [0, 0.0]


def check():
    errs = []
    # 1. junction angles + loose ends for every street we made
    made = [s for s in STREETS if s.kind in ("ext", "gen", "edge")]
    bad_angle, loose = 0, 0
    for s in made:
        cs = list(s.line.coords)
        for end, prev in ((0, 1), (-1, -2)):
            if s.cul and end == -1:
                continue
            if s.kind == "ext" and end == 0:
                continue                      # the v5 street carrying straight on, not a junction
            p = Point(cs[end])
            if WORLD.exterior.distance(p) < 6.0 or lmk_area.distance(p) < 12.0:
                continue                      # runs off the map (the town carries on) or ends at a park / station / mill
            host, d = nearest_street(p, exclude=s)
            if host is None or d > 1.5:
                if not (s.kind == "ext" and V5_BOX.exterior.distance(p) < 2.5):
                    loose += 1
                    DIAG.append(("loose", s.kind, round(p.x), round(p.y), round(d, 1)))
                continue
            q = Point(cs[prev])
            dx, dy = p.x - q.x, p.y - q.y
            L = math.hypot(dx, dy) or 1
            if junction_angle(host, p, (dx / L, dy / L)) < 60:
                bad_angle += 1
                DIAG.append(("angle", s.kind, round(p.x), round(p.y)))
    if bad_angle:
        errs.append(f"{bad_angle} junctions sharper than 60 deg")
    if loose:
        errs.append(f"{loose} loose street ends")
    # 2. junction spacing
    close = 0
    for i, a in enumerate(JUNCTIONS):
        for b in JUNCTIONS[i + 1:]:
            if 4.0 < a.distance(b) < 25.0:
                close += 1
                DIAG.append(("close", round(a.x), round(a.y), round(a.distance(b), 1)))
    if close:
        errs.append(f"{close} junction pairs closer than 25 m")
    # 3. no street crossing / running along another without a junction (ends excluded)
    cross = 0
    for s in made:
        core = s.line.difference(Point(s.line.coords[0]).buffer(9)).difference(Point(s.line.coords[-1]).buffer(9))
        if core.is_empty:
            continue
        for o in STREETS:
            if o is s:
                continue
            # a street that ENDS on this one is a T-junction, not a crossing: leave its end zone out
            o_core = o.line.difference(Point(o.line.coords[0]).buffer(9)).difference(Point(o.line.coords[-1]).buffer(9))
            if o_core.is_empty:
                continue
            if core.distance(o_core) < (s.w + o.w) / 2:
                cross += 1
                q = nearest_points(core, o.line)[0]
                DIAG.append(("cross", s.kind, o.kind, round(q.x), round(q.y)))
                break
    if cross:
        errs.append(f"{cross} streets cross or run along another without a junction")
    # 3b. no junction on or next to a bridge
    nb = sum(1 for j in JUNCTIONS if any(b.distance(j) < 25 for b in BRIDGE_PTS))
    if nb:
        errs.append(f"{nb} junctions within 25 m of a bridge")
    # 3c. every block used (>= 85 %)
    low, pct = coverage()
    COVER[:] = [low, pct]
    if low:
        errs.append(f"{low} blocks less than 85 % used (overall {pct:.0f} %)")
    # 4. buildings
    allb = unary_union([h for b in BUILD for h in b["houses"]] + FLATS + SHEDS)
    for nm, g in (("a street", ROADS_ALL), ("the canal", canal_block.buffer(-3)), ("the railway", rail_block.buffer(-3)),
                  ("a landmark", lmk_area), ("the ground", W.PLOT)):
        a = allb.intersection(g).area
        if a > 0.05:
            errs.append(f"buildings on {nm}: {a:.1f} m2")
    return errs


# ---------------------------------------------------------------- drawing
LAYER_COL = {nm: col for nm, col, _ in V.LAYERS}


def draw_geom(ax, g, fc, ec, lw, z, alpha=1.0):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        if p.geom_type in ("MultiPolygon", "GeometryCollection"):
            draw_geom(ax, p, fc, ec, lw, z, alpha)
            continue
        if p.geom_type != "Polygon":
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))


def draw(path, view=None, title="", scale=(200, "200 m"), size=14.5, dpi=130):
    x0, y0, x1, y1 = view or (-R, -R, R, R)
    fig, ax = plt.subplots(figsize=(size, size * (y1 - y0) / (x1 - x0)), dpi=dpi)
    ax.set_aspect("equal")
    ax.set_facecolor("#F6F5F0")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([]); ax.set_yticks([])
    lw = 0.25 if view is None else 0.6
    draw_geom(ax, V.CANAL.buffer(6), "#BFD9E6", "#5f95b3", lw, 2)
    xs, ys = V.RAIL.xy
    ax.plot(xs, ys, color="#555", lw=2.4 if view is None else 4, zorder=3)
    ax.plot(xs, ys, color="white", lw=1.0 if view is None else 2, zorder=3, ls=(0, (3, 3)))
    draw_geom(ax, ROADS_ALL, "#DCDAD3", "#8d8a82", lw, 4)
    draw_geom(ax, CARR, "#C9C6BE", "none", 0, 5)
    for b in BUILD:
        draw_geom(ax, b["plot"], "none", "#b8b3a7", lw * 0.7, 6)
        col = "#C9A44C" if b["shop"] else LAYER_COL.get(b["layer"], "#ccc")
        for h in b["houses"]:
            draw_geom(ax, h, col, "#3d3a36", lw, 7)
    for h in W.HOUSES:
        if V5_BOX.contains(h["house"]):
            draw_geom(ax, h["front"].union(h["house"]).union(h["yard"]), "none", "#b8b3a7", lw * 0.7, 6)
            draw_geom(ax, h["house"], LAYER_COL[VIC], "#3d3a36", lw, 7)
            if "out" in h:
                draw_geom(ax, h["out"], LAYER_COL[VIC], "#3d3a36", lw, 7)
    USE_COL = {"park": "#9FCB86", "playing field": "#8DBF73", "allotments": "#B5CF8A", "play area": "#C3DE9F", "garages": "#B9B2A6"}
    for g, k in USES:
        draw_geom(ax, g, USE_COL[k], "#6c8f55" if k in GREEN_KINDS else "#8d8a82", lw, 6.5)
        c = g.representative_point()
        if x0 < c.x < x1 and y0 < c.y < y1 and (g.area > (1500 if view is None else 300)):
            ax.text(c.x, c.y, k, ha="center", va="center", fontsize=4.8 if view is None else 7.5, color="#2f4f23" if k in GREEN_KINDS else "#444",
                    zorder=19, style="italic")
    for m in MEWS:
        draw_geom(ax, m.buffer(2.2, cap_style=2), "#DCDAD3", "#8d8a82", lw, 4.5)
    for f in FLATS:
        draw_geom(ax, f, LAYER_COL[POST], "#3d3a36", lw * 1.4, 7)
    for f in SHEDS:
        draw_geom(ax, f, LAYER_COL[IND], "#3d3a36", lw * 1.4, 7)
    draw_geom(ax, W.PLOT, "#E3EFD9", "#2F5B3F", lw * 3, 8)
    draw_geom(ax, box(-W.HL, -W.HW, W.HL, W.HW), "#7DB36A", "#2F5B3F", lw * 2, 9)
    for name, g, col in LMK:
        draw_geom(ax, g, col, "#333", lw * 2, 9, alpha=0.85)
        x0_, y0_, x1_, y1_ = g.bounds
        if name.startswith("SUPERMARKET"):     # its own grounds: the shop at the back, a car park with bays
            draw_geom(ax, box(x0_ + 4, y0_ + 4, x0_ + 74, y0_ + 40), "#3f6fa8", "#222", lw * 1.5, 10)
            draw_geom(ax, box(x0_ + 4, y0_ + 44, x1_ - 4, y1_ - 4), "#C9C6BE", "#777", lw, 10)
            xx = x0_ + 8
            while xx < x1_ - 8:
                ax.plot([xx, xx], [y0_ + 46, y0_ + 52], color="white", lw=lw, zorder=11)
                ax.plot([xx, xx], [y1_ - 12, y1_ - 6], color="white", lw=lw, zorder=11)
                xx += 2.8
        elif "school" in name:
            draw_geom(ax, box(x0_ + 4, y0_ + 4, x0_ + (x1_ - x0_) * 0.45, y0_ + (y1_ - y0_) * 0.4), "#c98a2c", "#222", lw * 1.5, 10)
            draw_geom(ax, box(x0_ + (x1_ - x0_) * 0.5, y0_ + 4, x1_ - 4, y0_ + (y1_ - y0_) * 0.4), "#C9C6BE", "#777", lw, 10)
        c = g.centroid
        if x0 < c.x < x1 and y0 < c.y < y1:
            ax.text(c.x, c.y, name.splitlines()[0], ha="center", va="center", fontsize=5.5 if view is None else 8, weight="bold",
                    zorder=20, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    ax.add_patch(plt.Circle((0, 0), 400, fc="none", ec="#777", lw=1.0, ls=(0, (6, 4)), zorder=25))
    sl, st = scale
    sx, sy = x1 - (x1 - x0) * 0.04 - sl, y0 + (y1 - y0) * 0.03
    ax.plot([sx, sx + sl], [sy, sy], color="#222", lw=3, zorder=30)
    ax.text(sx + sl / 2, sy + (y1 - y0) * 0.012, st, ha="center", fontsize=9, zorder=30)
    if title:
        ax.text(x0 + (x1 - x0) * 0.015, y1 - (y1 - y0) * 0.015, title, ha="left", va="top", fontsize=9, zorder=30,
                bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    errs = check()
    homes = sum(2 if b["kind"] == "semi" else 1 for b in BUILD) + sum(1 for h in W.HOUSES if V5_BOX.contains(h["house"]))
    kinds = Counter(s.kind for s in STREETS)
    print(f"streets: {dict(kinds)}, cul-de-sacs: {sum(1 for s in STREETS if s.cul)}, leaves: {len(LEAVES)}")
    print(f"homes: {homes}, shops on the High St: {sum(1 for b in BUILD if b['shop'])}, flats: {len(FLATS)}, sheds: {len(SHEDS)}")
    print(f"green: {GREEN_PCT:.1f} %, coverage: {COVER[1]:.1f} % (blocks < 85 %: {COVER[0]}), uses: {Counter(k for g, k in USES)}, mews: {len(MEWS)}")
    print("errors:", len(errs))
    for e in errs:
        print("   ", e)
    for d in DIAG[:40]:
        print("      ", d)
    title = (f"VILLAGE PLAN v4 — grown from the existing roads, every block used\n~{homes} homes · {len(FLATS)} blocks of flats · {len(SHEDS)} sheds · "
             f"{len(MEWS)} mews courts\npublic green {GREEN_PCT:.0f} % (green = park, playing field, allotments, play area)\n"
             f"blocks used: {COVER[1]:.0f} % · gold = High Street shops · dashed circle = fog 400 m")
    draw(os.path.join(OUTDIR, "village_v4.png"), title=title)
    draw(os.path.join(OUTDIR, "village_v4_zoom_core.png"), view=(-620, -360, -220, 40), title="zoom: old core + High Street",
         scale=(50, "50 m"), size=12)
    draw(os.path.join(OUTDIR, "village_v4_zoom_canal.png"), view=(150, 60, 550, 420), title="zoom: Mill Road canal bridge + estate",
         scale=(50, "50 m"), size=12)
    print("saved")
