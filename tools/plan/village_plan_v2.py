"""Village plan v2 — step 2: the whole town as a line drawing: every street, every house / building outline.
python3 tools/plan/village_plan_v2.py  ->  design/world/village_v2.png (+ village_v2_zoom_*.png)

Built on village plan v1 (layers, main roads, canal, railway, landmarks) and world plan v5 (the area round the ground,
kept as it is). Outside that area the streets are generated per layer, each layer with its own rules:
  old core      lanes that wander off the High Street, cottages of all widths, no front gardens
  Victorian     parallel streets ~45 m apart with a gentle bend, terraces, cross streets
  Edwardian     the same, a little wider: bigger terraces with front gardens
  1930s         curving streets ~55 m apart, semi-detached pairs with front gardens and drives
  post-war      a loop road, slab blocks of flats in open green + short terraces
  new build     a spine with cul-de-sacs and turning heads, detached houses
  industrial    a spine with sheds
The script checks itself: no house on a street / the canal / the railway / a landmark / the ground, no generated
street over the canal or the railway, every generated street joined to the network.
"""
import math
import os
import random
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, PathPatch
from matplotlib.path import Path
from shapely.geometry import LineString, Polygon, Point, box, MultiLineString
from shapely.ops import unary_union, linemerge

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import world_plan_v5 as W
import village_plan_v1 as V

OUTDIR = os.path.join(HERE, "../../design/world")
R = 750
WORLD = box(-R, -R, R, R)
V5_BOX = box(-262, -262, 262, 228)          # the area round the ground: kept exactly as world plan v5

# ---------------------------------------------------------------- the fixed frame from v1
MAIN = {n: (LineString(p), w) for n, (p, w, k) in V.ROADS.items()}
MAIN_PV = 2.0
main_area = unary_union([l.buffer(w / 2 + MAIN_PV, cap_style=2, join_style=2) for l, w in MAIN.values()])
canal_block = V.CANAL.buffer(12.0)
rail_block = V.RAIL.buffer(9.0)
LMK = []
for name, (x, y), size, col, shape in V.LANDMARKS:
    if shape == "rect":
        LMK.append((name, box(x - size[0] / 2, y - size[1] / 2, x + size[0] / 2, y + size[1] / 2), col))
lmk_area = unary_union([g for _, g, _ in LMK])
hard_block = unary_union([canal_block, rail_block, V5_BOX, lmk_area.buffer(3)])


def layer_at(pt):
    name = None
    for nm, col, pts in V.LAYERS:
        if Polygon(pts).contains(pt):
            name = nm
    return name or "Edwardian + mixed infill"


# ---------------------------------------------------------------- layer rules
RULES = {
    "old core":                  dict(street=5.5, pave=1.3, kind="organic", house=("cottage", 4.5, 9.0, 0.0, 0.0, 7.0, 10.0, 8.0)),
    "Victorian terraces":        dict(street=6.2, pave=1.6, kind="parallel", spacing=46, amp=4, cross=170,
                                      house=("terrace", 4.6, 5.8, 0.0, 1.5, 6.0, 9.0, 8.0)),
    "Edwardian + mixed infill":  dict(street=6.6, pave=1.8, kind="parallel", spacing=52, amp=6, cross=190,
                                      house=("terrace", 5.6, 6.6, 2.0, 3.0, 8.0, 12.0, 9.0)),
    "1930s semis":               dict(street=6.6, pave=1.8, kind="curved", spacing=58, amp=14, cross=230,
                                      house=("semi", 13.0, 13.0, 5.0, 7.0, 10.0, 16.0, 9.0)),
    "post-war estate + flats":   dict(street=6.4, pave=1.8, kind="estate", house=("terrace", 5.5, 5.5, 3.0, 4.0, 8.0, 10.0, 8.5)),
    "new build (cul-de-sacs)":   dict(street=5.6, pave=1.6, kind="culdesac", house=("detached", 9.0, 11.0, 5.0, 7.0, 8.0, 12.0, 9.0)),
    "industrial":                dict(street=7.5, pave=1.5, kind="industrial", house=None),
}
GAP = {"terrace": 0.0, "cottage": 0.0, "semi": 3.0, "detached": 3.5}


# ---------------------------------------------------------------- superblocks: the land between main roads, canal, railway
free_land = WORLD.difference(unary_union([main_area, hard_block]))
# each layer's own region (later layers sit on top), so a block between main roads can hold several layers
LAYER_REGION = {}
covered = Polygon()
for nm, col, pts in reversed(V.LAYERS):
    reg = Polygon(pts).intersection(WORLD).difference(covered)
    LAYER_REGION[nm] = LAYER_REGION.get(nm, Polygon()).union(reg)
    covered = covered.union(Polygon(pts))
SUPER = []
BOUNDARY_STREETS = []
for nm, reg in LAYER_REGION.items():
    piece = free_land.intersection(reg)
    for g in getattr(piece, "geoms", [piece]):
        if g.geom_type == "Polygon" and g.area > 2500:
            SUPER.append((g, nm))
# where two layers meet inside a block, a street runs along the seam
for nm, reg in LAYER_REGION.items():
    seam = reg.boundary.intersection(free_land.buffer(-4))
    for s_ in getattr(seam, "geoms", [seam]):
        if s_.geom_type == "LineString" and s_.length > 40:
            BOUNDARY_STREETS.append(s_)


def frame_of(P):
    mrr = list(P.minimum_rotated_rectangle.exterior.coords)
    e1, e2 = math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2])
    a, b = (mrr[0], mrr[1]) if e1 >= e2 else (mrr[1], mrr[2])
    L = math.dist(a, b)
    t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (-t[1], t[0])
    c = P.minimum_rotated_rectangle.centroid
    return (c.x, c.y), t, n, max(e1, e2), min(e1, e2)


def wiggle_line(c, t, n, u0, u1, v, amp, lam, ph, step=12.0):
    pts = []
    u = u0
    while u <= u1:
        off = v + amp * math.sin(u / lam + ph)
        pts.append((c[0] + t[0] * u + n[0] * off, c[1] + t[1] * u + n[1] * off))
        u += step
    return LineString(pts)


def keep_lines(g, minlen):
    out = []
    for s in getattr(g, "geoms", [g]):
        if s.geom_type == "LineString" and s.length >= minlen:
            out.append(s)
        elif s.geom_type == "MultiLineString":
            out += [q for q in s.geoms if q.length >= minlen]
    return out


def gen_streets(P, layer, rng):
    """Local streets for one superblock (they run a few metres into the roads round it, so they join)."""
    r = RULES[layer]
    c, t, n, L, Wd = frame_of(P)
    zone = P.buffer(r["street"] / 2 + MAIN_PV + 3).difference(hard_block.buffer(-0.5))
    out = []
    kind = r["kind"]
    if kind in ("parallel", "curved"):
        sp = r["spacing"]
        v = -Wd / 2 + rng.uniform(0.45, 0.6) * sp
        while v < Wd / 2 - 0.4 * sp:
            ln = wiggle_line(c, t, n, -L / 2 - 30, L / 2 + 30, v, r["amp"], rng.uniform(60, 110), rng.uniform(0, 6.3))
            out += keep_lines(ln.intersection(zone), 40)
            v += sp * rng.uniform(0.92, 1.08)
        u = -L / 2 + rng.uniform(0.4, 0.7) * r["cross"]
        while u < L / 2 - 0.3 * r["cross"]:
            ln = wiggle_line(c, n, (-t[0], -t[1]), -Wd / 2 - 30, Wd / 2 + 30, -u, r["amp"] * 0.5, 80, rng.uniform(0, 6.3))
            out += keep_lines(ln.intersection(zone), 40)
            u += r["cross"] * rng.uniform(0.85, 1.15)
    elif kind == "organic":
        for _ in range(max(3, int(P.area / 3200))):
            b = P.exterior.interpolate(rng.uniform(0, P.exterior.length))
            ang = math.atan2(c[1] - b.y, c[0] - b.x) + rng.uniform(-0.6, 0.6)
            pts = [(b.x, b.y)]
            x, y = b.x, b.y
            for k in range(rng.randint(6, 13)):
                ang += rng.uniform(-0.45, 0.45)
                x, y = x + math.cos(ang) * 14, y + math.sin(ang) * 14
                pts.append((x, y))
            out += keep_lines(LineString(pts).intersection(zone), 30)
    elif kind == "culdesac":
        spine = wiggle_line(c, t, n, -L / 2 - 30, L / 2 + 30, rng.uniform(-Wd * 0.1, Wd * 0.1), 22, rng.uniform(70, 120), rng.uniform(0, 6.3))
        sp = keep_lines(spine.intersection(zone), 40)
        out += sp
        inner = P.buffer(-22)
        for s in sp:
            d = rng.uniform(25, 40)
            side = 1
            while d < s.length - 25:
                p = s.interpolate(d)
                q = s.interpolate(d + 1)
                tx, ty = q.x - p.x, q.y - p.y
                tl = math.hypot(tx, ty) or 1
                a0 = math.atan2(tx / tl * side, -ty / tl * side) + rng.uniform(-0.45, 0.45)
                L1 = rng.uniform(40, 95)
                bend = rng.uniform(-0.5, 0.5)
                mid = (p.x + math.cos(a0) * L1 * 0.5, p.y + math.sin(a0) * L1 * 0.5)
                end = (mid[0] + math.cos(a0 + bend) * L1 * 0.5, mid[1] + math.sin(a0 + bend) * L1 * 0.5)
                ln = LineString([(p.x, p.y), mid, end]).intersection(inner)
                for b in keep_lines(ln, 30):
                    out.append(LineString([(p.x, p.y)] + list(b.coords)[1:]))
                    CULDESAC_ENDS.append(Point(b.coords[-1]))
                d += rng.uniform(38, 70)
                if rng.random() < 0.8:
                    side = -side
    elif kind == "estate":
        ring = P.buffer(-55)
        if not ring.is_empty and ring.geom_type == "Polygon":
            out.append(ring.exterior.simplify(4))
            # spurs from the ring to the edge roads
            for k in range(3):
                p = ring.exterior.interpolate(k / 3, normalized=True)
                q = P.exterior.interpolate(P.exterior.project(p))
                dx, dy = q.x - p.x, q.y - p.y
                dl = math.hypot(dx, dy) or 1
                out += keep_lines(LineString([(p.x, p.y), (q.x + dx / dl * 9, q.y + dy / dl * 9)]).intersection(zone), 5)
    elif kind == "industrial":
        spine = wiggle_line(c, t, n, -L / 2 - 30, L / 2 + 30, 0, 0, 100, 0)
        out += keep_lines(spine.intersection(zone), 40)
    return out


CULDESAC_ENDS = []
rng = random.Random(2026)
GEN = []          # (line, layer, width, pave)
for bl in BOUNDARY_STREETS:
    ext = bl.buffer(0)  # noqa
    GEN.append((bl, layer_at(bl.interpolate(0.5, normalized=True)), 6.4, 1.7))
for P, layer in SUPER:
    for ln in gen_streets(P, layer, rng):
        r = RULES[layer]
        GEN.append((ln, layer, r["street"], r["pave"]))
def _joined(gen):
    joined = unary_union([l.buffer(w / 2 + MAIN_PV) for l, w in MAIN.values()] + [V5_BOX])
    done, changed = set(), True
    while changed:
        changed = False
        for i, (l, lay, w, p) in enumerate(gen):
            if i not in done and l.buffer(w / 2).intersects(joined):
                joined = joined.union(l.buffer(w / 2 + p))
                done.add(i)
                changed = True
    return done


_ok = _joined(GEN)
DROPPED = len(GEN) - len(_ok)
GEN = [g for i, g in enumerate(GEN) if i in _ok]
CULDESAC_ENDS = [e for e in CULDESAC_ENDS if any(e.distance(g[0]) < 1 for g in GEN)]
gen_area = unary_union([l.buffer(w / 2 + p, cap_style=2, join_style=2) for l, _, w, p in GEN] +
                       [e.buffer(9.0) for e in CULDESAC_ENDS])
gen_carr = unary_union([l.buffer(w / 2, cap_style=2, join_style=2) for l, _, w, p in GEN] + [e.buffer(7.0) for e in CULDESAC_ENDS])
all_road = unary_union([main_area, gen_area])

# ---------------------------------------------------------------- buildings
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


blocked = unary_union([all_road.buffer(-0.02), canal_block, rail_block, lmk_area.buffer(2), V5_BOX.buffer(1), W.PLOT.buffer(1)])
from shapely.prepared import prep
blocked_p = prep(blocked)
occ = Grid()
BUILD = []        # dicts: plot, house, layer, kind
FLATS, SHEDS = [], []


def place_along(line, layer, edge, rng):
    r = RULES.get(layer)
    if not r or not r["house"]:
        return
    kind, wmin, wmax, fgmin, fgmax, ydmin, ydmax, hd = r["house"]
    L = line.length
    for side in (1, -1):
        s = rng.uniform(4, 9)
        run = 0
        while s < L - 6:
            if run == 0:
                w_run = rng.uniform(wmin, wmax)
                fg_run = max(rng.uniform(fgmin, fgmax), 0.4)     # never right on the kerb line
                yd_run = rng.uniform(ydmin, ydmax)
            w = w_run if kind != "cottage" else rng.uniform(wmin, wmax)
            p = line.interpolate(s)
            q = line.interpolate(min(s + 1.0, L))
            tx, ty = q.x - p.x, q.y - p.y
            d = math.hypot(tx, ty) or 1.0
            t = (tx / d, ty / d)
            n = (-t[1] * side, t[0] * side)
            o = (p.x + n[0] * edge, p.y + n[1] * edge)
            ok = None
            for depth in (fg_run + hd + yd_run, fg_run + hd + 4.0):
                cand = fpoly(o, t, n, 0.0, w, 0.4, depth)
                if blocked_p.intersects(cand) or occ.hits(cand.buffer(-0.4)) or not WORLD.contains(cand):
                    continue
                ok = depth
                break
            if ok is None:
                s += 2.5
                run = 0
                continue
            occ.add(cand)
            plot = fpoly(o, t, n, 0, w, 0, ok)
            if kind == "semi":
                houses = [fpoly(o, t, n, 0.6, w / 2, fg_run, fg_run + hd), fpoly(o, t, n, w / 2, w - 0.6, fg_run, fg_run + hd)]
            elif kind == "detached":
                houses = [fpoly(o, t, n, 1.2, w - 1.2, fg_run, fg_run + hd)]
            else:
                houses = [fpoly(o, t, n, 0, w, fg_run, fg_run + hd)]
                if kind == "terrace" and ok - fg_run - hd > 5:
                    u0 = 0 if run % 2 == 0 else w - 2.6
                    houses.append(fpoly(o, t, n, u0, u0 + 2.6, fg_run + hd, fg_run + hd + 3.5))
            BUILD.append({"plot": plot, "houses": houses, "layer": layer, "kind": kind})
            s += w + GAP[kind]
            run += 1
            if kind in ("terrace", "cottage") and run >= rng.randint(8, 14):
                s += 1.6
                run = 0


# post-war flats: slab blocks in the open green inside the estate ring; industrial sheds along the spine
for P, layer in SUPER:
    if layer == "post-war estate + flats":
        c, t, n, L, Wd = frame_of(P)
        u = -L / 2 + 30
        while u < L / 2 - 30:
            v = -Wd / 2 + 30
            while v < Wd / 2 - 30:
                o = (c[0] + t[0] * u + n[0] * v, c[1] + t[1] * u + n[1] * v)
                slab = fpoly(o, t, n, -26, 26, -7, 7)
                if P.buffer(-4).contains(slab) and not slab.buffer(7).intersects(all_road) and not occ.hits(slab.buffer(8)):
                    occ.add(slab.buffer(6))
                    FLATS.append(slab)
                v += 34
            u += 66
    if layer == "industrial":
        for ln, lay, w, p in GEN:
            if lay != "industrial":
                continue
            s = 10.0
            while s < ln.length - 30:
                for side in (1, -1):
                    p0 = ln.interpolate(s)
                    q = ln.interpolate(s + 1)
                    tx, ty = q.x - p0.x, q.y - p0.y
                    d = math.hypot(tx, ty) or 1
                    t = (tx / d, ty / d)
                    n = (-t[1] * side, t[0] * side)
                    o = (p0.x + n[0] * 12, p0.y + n[1] * 12)
                    shed = fpoly(o, t, n, 0, 42, 0, 30)
                    if not blocked_p.intersects(shed) and not occ.hits(shed.buffer(3)) and WORLD.contains(shed):
                        occ.add(shed)
                        SHEDS.append(shed)
                s += 50



rng = random.Random(7)
# frontage on the main roads first, then the local streets
for name, (l, w) in MAIN.items():
    segs = keep_lines(l.difference(V5_BOX.buffer(2)), 20)
    for sg in segs:
        mid = sg.interpolate(0.5, normalized=True)
        layer = layer_at(mid)
        if layer == "industrial":
            continue
        place_along(sg, layer, w / 2 + MAIN_PV, rng)
for ln, layer, w, p in GEN:
    place_along(ln, layer, w / 2 + p, rng)

# ---------------------------------------------------------------- self-check
def check():
    errs = []
    houses = unary_union([h for b in BUILD for h in b["houses"]] + FLATS + SHEDS)
    for nm, g in (("a street", all_road), ("the canal", canal_block.buffer(-3)), ("the railway", rail_block.buffer(-3)),
                  ("a landmark", lmk_area), ("the ground", W.PLOT)):
        a = houses.intersection(g).area
        if a > 0.05:
            errs.append(f"buildings on {nm}: {a:.1f} m2")
    for ln, layer, w, p in GEN:
        if ln.intersects(V.CANAL.buffer(6)) or ln.intersects(V.RAIL.buffer(2)):
            errs.append(f"a {layer} street crosses the canal or the railway")
    # every generated street joins the network (main roads + the v5 area), through other streets if need be
    net = [l.buffer(w / 2 + MAIN_PV) for l, w in MAIN.values()] + [V5_BOX]
    joined = unary_union(net)
    todo = list(range(len(GEN)))
    changed = True
    done = set()
    while changed:
        changed = False
        for i in todo:
            if i in done:
                continue
            if GEN[i][0].buffer(GEN[i][2] / 2).intersects(joined):
                joined = joined.union(GEN[i][0].buffer(GEN[i][2] / 2 + GEN[i][3]))
                done.add(i)
                changed = True
    loose = len(GEN) - len(done)
    if loose:
        errs.append(f"{loose} generated streets not joined to the network")
    return errs


# ---------------------------------------------------------------- drawing (wireframe)
LAYER_COL = {nm: col for nm, col, _ in V.LAYERS}


def draw_geom(ax, g, fc, ec, lw, z, alpha=1.0):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        if p.geom_type == "MultiPolygon":
            draw_geom(ax, p, fc, ec, lw, z, alpha)
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha))


def draw(path, view=None, scale_txt="200 m", scale_len=200, title="", dpi=130, size=14.5):
    x0, y0, x1, y1 = view or (-R, -R, R, R)
    fig, ax = plt.subplots(figsize=(size, size * (y1 - y0) / (x1 - x0)), dpi=dpi)
    ax.set_aspect("equal")
    ax.set_facecolor("#F6F5F0")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([]); ax.set_yticks([])
    lw = 0.25 if view is None else 0.6
    # canal, railway
    draw_geom(ax, V.CANAL.buffer(6), "#BFD9E6", "#5f95b3", lw, 2)
    xs, ys = V.RAIL.xy
    ax.plot(xs, ys, color="#555", lw=2.4 if view is None else 4, zorder=3)
    ax.plot(xs, ys, color="white", lw=1.0 if view is None else 2, zorder=3, ls=(0, (3, 3)))
    # roads (main + generated + v5)
    v5_roads = unary_union([r.buffer(W.edge_of(k), cap_style=2, join_style=2) for k, r in W.roads.items()]).intersection(V5_BOX)
    draw_geom(ax, unary_union([main_area, gen_area, v5_roads]), "#DCDAD3", "#8d8a82", lw, 4)
    draw_geom(ax, unary_union([gen_carr, unary_union([l.buffer(w / 2, cap_style=2, join_style=2) for l, w in MAIN.values()]),
                               W.carriage.intersection(V5_BOX)]), "#C9C6BE", "none", 0, 5)
    # plots + houses
    for b in BUILD:
        draw_geom(ax, b["plot"], "none", "#b8b3a7", lw * 0.7, 6)
        for h in b["houses"]:
            draw_geom(ax, h, LAYER_COL.get(b["layer"], "#ccc"), "#3d3a36", lw, 7)
    for h in W.HOUSES:
        if V5_BOX.contains(h["house"]):
            draw_geom(ax, h["front"].union(h["house"]).union(h["yard"]), "none", "#b8b3a7", lw * 0.7, 6)
            draw_geom(ax, h["house"], "#C77B60", "#3d3a36", lw, 7)
            if "out" in h:
                draw_geom(ax, h["out"], "#C77B60", "#3d3a36", lw, 7)
    for f in FLATS:
        draw_geom(ax, f, "#9FAAB6", "#3d3a36", lw * 1.4, 7)
    for f in SHEDS:
        draw_geom(ax, f, "#8E8A84", "#3d3a36", lw * 1.4, 7)
    # the ground (plan v5) + landmarks
    draw_geom(ax, W.PLOT, "#E3EFD9", "#2F5B3F", lw * 3, 8)
    draw_geom(ax, box(-W.HL, -W.HW, W.HL, W.HW), "#7DB36A", "#2F5B3F", lw * 2, 9)
    for name, g, col in LMK:
        draw_geom(ax, g, col, "#333", lw * 2, 9, alpha=0.85)
        c = g.centroid
        if x0 < c.x < x1 and y0 < c.y < y1:
            ax.text(c.x, c.y, name.splitlines()[0], ha="center", va="center", fontsize=5.5 if view is None else 8,
                    weight="bold", zorder=20, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    ax.add_patch(plt.Circle((0, 0), 400, fc="none", ec="#777", lw=1.0, ls=(0, (6, 4)), zorder=25))
    sx = x1 - (x1 - x0) * 0.04 - scale_len
    sy = y0 + (y1 - y0) * 0.03
    ax.plot([sx, sx + scale_len], [sy, sy], color="#222", lw=3, zorder=30)
    ax.text(sx + scale_len / 2, sy + (y1 - y0) * 0.012, scale_txt, ha="center", fontsize=9, zorder=30)
    if title:
        ax.text(x0 + (x1 - x0) * 0.015, y1 - (y1 - y0) * 0.015, title, ha="left", va="top", fontsize=9, zorder=30,
                bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    plt.close(fig)


if __name__ == "__main__":
    errs = check()
    from collections import Counter
    cnt = Counter(b["layer"] for b in BUILD)
    nh = sum(2 if b["kind"] == "semi" else 1 for b in BUILD)
    v5n = sum(1 for h in W.HOUSES if V5_BOX.contains(h["house"]))
    print(f"generated streets: {len(GEN)}, plots: {len(BUILD)}, homes (+v5): {nh + v5n}, flats blocks: {len(FLATS)}, sheds: {len(SHEDS)}")
    for k, v in cnt.most_common():
        print(f"   {k}: {v}")
    print("dropped loose streets:", DROPPED)
    print("errors:", len(errs))
    for e in errs:
        print("   ", e)
    title = (f"VILLAGE PLAN v2 — every street + building\n~{nh + v5n} homes, {len(FLATS)} blocks of flats, {len(SHEDS)} sheds\n"
             "colour = layer (see v1) · dashed circle = fog 400 m")
    draw(os.path.join(OUTDIR, "village_v2.png"), title=title)
    draw(os.path.join(OUTDIR, "village_v2_zoom_core.png"), view=(-620, -360, -220, 40), scale_txt="50 m", scale_len=50,
         title="zoom: old core + High Street", size=12)
    draw(os.path.join(OUTDIR, "village_v2_zoom_east.png"), view=(260, -260, 700, 180), scale_txt="50 m", scale_len=50,
         title="zoom: post-war estate + flats", size=12)
    draw(os.path.join(OUTDIR, "village_v2_zoom_newbuild.png"), view=(-200, 330, 300, 750), scale_txt="50 m", scale_len=50,
         title="zoom: 1930s + new build", size=12)
    print("saved")
