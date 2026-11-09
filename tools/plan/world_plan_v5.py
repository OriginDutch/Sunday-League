"""Line plan v5: the home ground at its minimum (13th division) and at its maximum (1st division), same village round it.
python3 tools/plan/world_plan_v5.py [--five]   ->  design/world/plan_v5_min.png, plan_v5_max.png (+ _five variants)

Orientation as the top-down renders: right = South (+x), left = North (home end), up = East, down = West (camera side,
main stand). Fans come out of the streets: junctions on the ground's edge are approach routes.
The script checks itself before drawing: nothing on a street, in a house or over a path; every path connects.
"""
import math
import os
import random
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "../../design/world")
SIX = "--five" not in sys.argv          # 6 sections per end (Marcel, 2026-11-09)
SUFFIX = "" if SIX else "_five"

# ---------------------------------------------------------------- dimensions (m)
HL, HW = 52.5, 34.0
SW = 11.5
FRONT = 2.9
N_LONG, N_END = 9, (6 if SIX else 5)
LONG_HALF, END_HALF = N_LONG * SW / 2, N_END * SW / 2
SIDE_FRONT, END_FRONT = HW + FRONT, HL + FRONT          # 36.9, 55.4
STAND_MAX_X, STAND_MAX_Y = 125.0, 105.0                  # stands at their biggest (every shape fits)
FACADE = {"W": 20.0, "E": 10.0, "N": 10.0, "S": 10.0}   # facade zone beyond the stands (Marcel: ok)
MAXL = box(-STAND_MAX_X - FACADE["N"], -STAND_MAX_Y - FACADE["W"], STAND_MAX_X + FACADE["S"], STAND_MAX_Y + FACADE["E"])
MAST_D = 15.0
ST, PV = 7.0, 1.8
EDGE = ST / 2 + PV                                       # centreline -> back of pavement
# terrace plot, from the back of the pavement: front garden, house, back yard (outrigger in it), alley
FG, HD, YD, AL, HWID, OUTW, OUTD = 1.5, 8.0, 8.0, 1.5, 5.0, 2.6, 3.5
PLOT_D = FG + HD + YD + AL

C = {"bg": "#EEF3E8", "pitch": "#7DB36A", "stand": "#9AA3AD", "standmax": "#8C96A1", "away": "#D9534F",
     "max": "#3B6FB6", "fac": "#E8A33D", "facedge": "#8a5a12", "road": "#555B61", "pave": "#C8C2B5",
     "hard": "#D8D2C4", "house": "#B5654A", "out": "#9C5440", "yard": "#E4EDD9", "front": "#C9DDB5", "alley": "#BDB6A6",
     "water": "#6FA8C7", "ground": "#CFE5C0", "tow": "#B9A27A", "tree": "#4F8A3F", "path": "#E2D6B8", "pub": "#E9DFC6",
     "fence": "#2F5B3F", "pay": "#1d4f91"}

# ---------------------------------------------------------------- the ground's plot (irregular, holds the max line)
PLOT = Polygon([(-139, 119), (139, 119), (139, -129), (139, -178), (40, -178), (40, -129), (-176, -129),
                (-176, -55), (-139, -40)])
def _kink(poly, keep, seed=5):
    r = random.Random(seed)
    pts = list(poly.exterior.coords)[:-1]
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        out.append(a)
        L = math.dist(a, b)
        k = int(L // 15)
        for j in range(1, k + 1):
            t = j / (k + 1)
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if any(math.hypot(x - kx, y - ky) < kr for kx, ky, kr in keep):
                out.append((x, y))            # keep the fence straight at gates
                continue
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            if not poly.contains(Point(x + nx, y + ny)):
                nx, ny = -nx, -ny
            d = r.uniform(0.0, 1.3) if j % 2 else r.uniform(0.0, 0.5)
            out.append((x + nx * d, y + ny * d))
    return Polygon(out)


GATES_KEEP = [(-10, -129, 30), (137, 100, 20), (-139, 20, 26), (-150, -125, 30), (40, -162, 12)]
PLOT = _kink(PLOT, GATES_KEEP)
assert PLOT.buffer(0.01).contains(MAXL), "max line must fit inside the plot"

# ---------------------------------------------------------------- streets (centrelines)
STREETS = {
    "High Road": [(-265, -138), (-182, -135.5), (-120, -135), (-10, -135), (18, -135)],
    "Car Park Lane": [(18, -135), (25, -135.6), (30.5, -138.2), (33.4, -143), (34, -150), (34, -184)],
    "Lower Road": [(34, -184), (153.5, -184), (265, -188)],
    "Gate Street": [(-10, -135), (-13, -190), (-19, -265)],
    "Albert Street": [(-265, -187), (-120, -184), (-13, -183), (34, -184)],
    "Victoria Street": [(-265, -236), (-120, -232), (-17.5, -232)],
    "Raglan Street": [(-17.5, -232), (34, -233), (150, -236), (265, -241)],
    "Mill Lane": [(-182, -135.5), (-205, -190), (-232, -265)],
    "North Street": [(-182, -135.5), (-182, -50), (-145.5, -30), (-145.5, 20), (-145.5, 146), (-145, 215)],
    "Chapel Row": [(-145.5, 20), (-200, 24), (-265, 16)],
    "Moor Street": [(-200, 24), (-197, 146)],
    "Hope Street": [(-243, 19), (-244, 146)],
    "Hope Street South": [(-243, 19), (-238, -136.5)],
    "Canal Street": [(-265, 147), (-145.5, 146), (0, 145), (153.5, 146), (265, 150)],
    "South Street": [(153.5, -184), (153.5, -60), (154, 60), (153.5, 146), (154, 218)],
    "Lock Lane": [(153.5, -60), (210, -66), (265, -52)],
    "Byron Street": [(202, -186), (203, -64)],
    "Shelley Street": [(203, -64), (201, 147)],
    "Keats Street": [(246, -188), (244, -57), (243, 149)],
    "Wharf Street": [(-265, 214), (0, 216), (265, 220)],
}
def _run_on(streets, d=4.5):
    lines = {k: LineString(v) for k, v in streets.items()}
    out = {}
    for k, pts in streets.items():
        pts = list(pts)
        for end in (0, -1):
            p = Point(pts[end])
            if any(o.distance(p) < 1.0 for kk, o in lines.items() if kk != k):
                q = pts[1] if end == 0 else pts[-2]
                dx, dy = pts[end][0] - q[0], pts[end][1] - q[1]
                L = math.hypot(dx, dy) or 1
                # only straight-on T-ends: a street that continues another one (same direction) is joined smoothly instead
                ext = (pts[end][0] + dx / L * d, pts[end][1] + dy / L * d)
                if end == 0:
                    pts.insert(0, ext)
                else:
                    pts.append(ext)
        out[k] = pts
    return out


SMOOTH_JOINS = {("High Road", "Car Park Lane")}
_ext = _run_on({k: v for k, v in STREETS.items() if k not in ("Car Park Lane",)})
_ext["Car Park Lane"] = STREETS["Car Park Lane"][:-1] + [(34, -184), (34, -188.5)]
_ext["High Road"] = [p for p in _ext["High Road"] if p[0] <= 18.01]       # High Road flows into Car Park Lane: no run-on there
roads = {k: LineString(_ext[k]) for k in STREETS}
# natural: every street its own width (main roads wider, back streets narrower), pavements vary too
MAIN = {"High Road", "Canal Street", "South Street", "North Street", "Lower Road", "Wharf Street"}
_rw = random.Random(11)
RW = {n: ((_rw.uniform(7.0, 7.4), _rw.uniform(1.4, 2.2)) if n in MAIN else (_rw.uniform(5.8, 6.6), _rw.uniform(1.2, 1.9)))
      for n in STREETS}


def edge_of(n):
    return RW[n][0] / 2 + RW[n][1]


road_area = unary_union([r.buffer(edge_of(k), cap_style=2, join_style=2) for k, r in roads.items()])
carriage = unary_union([r.buffer(RW[k][0] / 2, cap_style=2, join_style=2) for k, r in roads.items()])
canal = LineString([(-270, 179), (-120, 177), (0, 175), (120, 178), (270, 182)])
water = canal.buffer(6.0, cap_style=2)
tow = canal.buffer(9.5, cap_style=2).difference(water)
VIEW = box(-262, -262, 262, 228)
PUB_CORNERS = [(-182, -135.5, "hard core"), (-10, -135, ""), (153.5, 146, "away"), (-145.5, 20, ""), (34, -184, "")]

# ---------------------------------------------------------------- village: terraces along every street side
class Grid:
    def __init__(self, cell=20.0):
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


def frame_poly(p, t, n, u0, u1, v0, v1):
    """Quad in a street frame: u along the street (t), v away from it (n)."""
    pts = []
    for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        pts.append((p[0] + t[0] * u + n[0] * v, p[1] + t[1] * u + n[1] * v))
    return Polygon(pts)


HOUSES = []      # dicts: front, house, outrigger, yard, alley, pub, frame (for the 3D mockup)
RUN_ID = [0]
blocked = unary_union([PLOT.buffer(0.5), road_area.buffer(-0.05), water.buffer(3.6), tow]).intersection(box(-400, -400, 400, 400))
occ = Grid()
pubs_used = set()
rr = random.Random(7)
for name, line in roads.items():
    L = line.length
    for side in (1, -1):
        s, k, run = 6.0, 0, 0
        EDGE_N = edge_of(name)
        while s < L - 6:
            if run == 0:           # natural: each terrace its own width, front garden, house depth and yard
                hw_run = rr.uniform(4.6, 5.8)
                fg_run = rr.choice([0.0, 0.6, 1.2, 1.8, 2.5])
                hd_run = rr.uniform(7.5, 9.0)
                yd_run = rr.uniform(5.0, 10.0)
            p = line.interpolate(s)
            q = line.interpolate(min(s + 1.0, L))
            tx, ty = q.x - p.x, q.y - p.y
            d = math.hypot(tx, ty) or 1.0
            t = (tx / d, ty / d)
            n = (-t[1] * side, t[0] * side)
            o = (p.x + n[0] * EDGE_N, p.y + n[1] * EDGE_N)
            # pub on a chosen corner: wider plot, first house at the junction
            width = hw_run
            pub = None
            FG, HD = fg_run, hd_run
            for (jx, jy, tag) in PUB_CORNERS:
                key = (jx, jy, name, side)
                if (jx, jy) not in [(a, b) for (a, b, *_ ) in pubs_used] and math.hypot(o[0] - jx, o[1] - jy) < 22:
                    width, pub = 10.0, tag
                    break
            for depth in (FG + HD + yd_run + AL, FG + HD + 5.0 + AL, FG + HD + 3.0):
                cand = frame_poly(o, t, n, 0.0, width, 0.25, depth)
                if cand.intersects(blocked) or occ.hits(cand.buffer(-0.35)) or not VIEW.buffer(30).contains(cand):
                    continue
                break
            else:
                s += 2.0
                run = 0
                continue
            occ.add(cand)
            h = {"pub": pub}
            h["front"] = frame_poly(o, t, n, 0, width, 0, FG)
            h["house"] = frame_poly(o, t, n, 0, width, FG, FG + HD)
            yd = depth - FG - HD - (AL if depth >= FG + HD + 5 + AL else 0)
            h["yard"] = frame_poly(o, t, n, 0, width, FG + HD, FG + HD + yd)
            if pub is None and yd >= OUTD + 1:
                u0 = 0 if k % 2 == 0 else width - OUTW
                h["out"] = frame_poly(o, t, n, u0, u0 + OUTW, FG + HD, FG + HD + OUTD)
            if depth >= FG + HD + 5 + AL:
                h["alley"] = frame_poly(o, t, n, 0, width, depth - AL, depth)
            if pub is not None:
                pubs_used.add((jx, jy, name, side))
                h["pubpos"] = h["house"].centroid
            if run == 0:
                RUN_ID[0] += 1
            h["frame"] = {"o": o, "t": t, "n": n, "w": width, "fg": FG, "hd": HD, "yd": yd, "depth": depth,
                          "run": RUN_ID[0], "street": name}
            if "out" in h:
                h["frame"]["out_u0"] = 0 if k % 2 == 0 else width - OUTW
            HOUSES.append(h)
            s += width
            k += 1
            run += 1
            if run >= rr.randint(9, 13):        # a ginnel through the terrace
                s += 1.6
                run = 0

# ---------------------------------------------------------------- terrain (metres relative to the levelled ground)
def terrain(x, y):
    import numpy as np
    t = np.clip((y + 262) / (175 + 262), 0, 1)
    base = 3.2 * (1 - t) ** 1.2 - 1.2 * t                # higher in the West, down towards the canal
    return base + 0.6 * np.sin(x / 70.0 + 0.8) * (1 - t) - 0.004 * np.clip(x, 0, None)


# canal water levels: the lock steps the water down to the East; both stay well below the banks
import numpy as _np
_tw = [float(terrain(_np.array(x), _np.array(canal.interpolate(canal.project(Point(x, 175))).y - 8.0))) for x in range(-262, 50, 8)]
_te = [float(terrain(_np.array(x), _np.array(canal.interpolate(canal.project(Point(x, 175))).y - 8.0))) for x in range(66, 262, 8)]
WATER_W = round(min(_tw) - 0.6, 1)
WATER_E = round(min(min(_te) - 0.6, WATER_W - 1.8), 1)


# ---------------------------------------------------------------- canal crossings: two humpback bridges + a footbridge at the lock
BRIDGES = [n for n, r in roads.items() if r.intersects(water)]
LOCK_X = 60.0
lock_p = canal.interpolate(canal.project(Point(LOCK_X, 175)))
FOOTBRIDGE = LineString([(LOCK_X - 6, lock_p.y - 9.5), (LOCK_X - 6, lock_p.y + 9.5)])

# ---------------------------------------------------------------- backland: empty block middles become courts with
# garages / workshops, reached through an arch in the terrace (Marcel: ok)
from shapely.ops import nearest_points
taken = unary_union([h["front"].union(h["house"]).union(h["yard"]).union(h.get("alley", Polygon())) for h in HOUSES])
free = VIEW.buffer(-2).difference(unary_union([taken.buffer(0.3), road_area, PLOT.buffer(2.0), water.buffer(3.6), tow.buffer(1)]))
COURTS = []
for g in getattr(free, "geoms", [free]):
    g2 = g.buffer(-2.0).buffer(1.0, join_style=2)
    for c in getattr(g2, "geoms", [g2]):
        if c.is_empty or c.geom_type != "Polygon" or c.area < 450:
            continue
        mrr = list(c.minimum_rotated_rectangle.exterior.coords)
        e1, e2 = math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2])
        if min(e1, e2) < 12:
            continue
        pc, pr = nearest_points(c, carriage)
        lane_line = LineString([(pc.x, pc.y), (pr.x, pr.y)])
        lane = lane_line.buffer(1.7, cap_style=2)
        HOUSES[:] = [h for h in HOUSES if not h["house"].union(h["yard"]).union(h["front"]).intersects(lane)]
        # a row of garages / workshops along the long side
        if e1 >= e2:
            a, b = mrr[0], mrr[1]
        else:
            a, b = mrr[1], mrr[2]
        L = math.dist(a, b)
        t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        boxes = []
        for nsign in (1, -1):
            n = (-t[1] * nsign, t[0] * nsign)
            u = 1.0
            while u < L - 4:
                for v0 in (1.0,):
                    q = frame_poly(a, t, n, u, u + 3.0, v0, v0 + 6.0)
                    if c.buffer(-0.4).contains(q) and not any(q.intersects(o) for o in boxes):
                        boxes.append(q)
                u += 3.2
        COURTS.append({"area": c, "lane": lane, "boxes": boxes})

# ---------------------------------------------------------------- the ground
MASTS = [box(sx * (HL + MAST_D / math.sqrt(2)) - 2, sy * (HW + MAST_D / math.sqrt(2)) - 2,
             sx * (HL + MAST_D / math.sqrt(2)) + 2, sy * (HW + MAST_D / math.sqrt(2)) + 2) for sx in (-1, 1) for sy in (-1, 1)]


def stand_rects(west, east, north, south, wsecs=None, esecs=None, corners=False):
    """Stand footprints by depth beyond the stand front lines. wsecs/esecs = (first, last) section index along the side."""
    out = []
    def span(secs):
        if secs is None:
            return -LONG_HALF, LONG_HALF
        return (secs[0] - 4.5) * SW, (secs[1] - 3.5) * SW
    if west:
        a, b = span(wsecs)
        out.append(box(a, -SIDE_FRONT - west, b, -SIDE_FRONT))
    if east:
        a, b = span(esecs)
        out.append(box(a, SIDE_FRONT, b, SIDE_FRONT + east))
    if north:
        out.append(box(-END_FRONT - north, -END_HALF, -END_FRONT, END_HALF))
    if south:
        out.append(box(END_FRONT, -END_HALF, END_FRONT + south, END_HALF))
    if corners:
        for sx in (-1, 1):
            for sy in (-1, 1):
                out.append(box(min(sx * END_FRONT, sx * STAND_MAX_X), min(sy * SIDE_FRONT, sy * STAND_MAX_Y),
                               max(sx * END_FRONT, sx * STAND_MAX_X), max(sy * SIDE_FRONT, sy * STAND_MAX_Y)))
    return out


def ground(stage):
    """Everything inside the plot fence for 'min' (13th division) or 'max' (1st division)."""
    G = {"buildings": [], "paths": [], "hard": [], "green": [], "trees": [], "plots": [], "turnstiles": [],
         "fence_pay": None, "stands": [], "masts": [], "notes": [], "bays": [], "lines": []}
    B = G["buildings"]

    def bld(name, geom, col=C["fac"], label=None, fs=7.5):
        B.append({"name": name, "g": geom, "col": col, "label": label if label is not None else name, "fs": fs})

    pr = random.Random(hash(stage) % 1000 + 3)

    def path(name, pts, w=5.0):
        line = LineString(pts)
        if line.length < 12:
            G["paths"].append({"name": name, "line": line, "g": line.buffer(w / 2, cap_style=2, join_style=2)})
            return
        ph = pr.uniform(0, 6.28)
        ds = [i * 2.5 for i in range(int(line.length / 2.5) + 1)] + [line.length]
        cs, lefts, rights = [], [], []
        for d in ds:
            p0 = line.interpolate(max(d - 0.5, 0))
            p1 = line.interpolate(min(d + 0.5, line.length))
            tl = math.hypot(p1.x - p0.x, p1.y - p0.y) or 1
            nx, ny = -(p1.y - p0.y) / tl, (p1.x - p0.x) / tl
            env = math.sin(math.pi * d / line.length)                 # 0 at both ends: they stay where they connect
            off = env * 1.3 * math.sin(d / 16 + ph)
            wd = w * (1 + env * 0.2 * math.sin(d / 9 + ph * 1.7))
            pt = line.interpolate(d)
            c = (pt.x + nx * off, pt.y + ny * off)
            cs.append(c)
            lefts.append((c[0] + nx * wd / 2, c[1] + ny * wd / 2))
            rights.append((c[0] - nx * wd / 2, c[1] - ny * wd / 2))
        g = Polygon(lefts + rights[::-1]).buffer(0)
        G["paths"].append({"name": name, "line": LineString(cs), "g": g})

    gate_main = (-10, -129)
    cpl_edge = 34 + RW["Car Park Lane"][0] / 2
    G["drives"] = [box(cpl_edge, -167, 41.5, -157)]           # car park entrance from Car Park Lane (dropped kerb + gate)
    if stage == "min":
        G["stands"] = stand_rects(11, 6, 6, 3, wsecs=(3, 5), esecs=(3, 5))      # local index 0..8 along the side (West 12-14)
        G["masts"] = MASTS
        pay = box(-80, -58, 68, 52)
        G["fence_pay"] = pay
        # turnstiles on the paying fence
        T = {"W": box(-16, -60, -4, -56), "NW": box(-82, -36, -78, -24), "N": box(-82, 14, -78, 26), "A": box(66, 18, 70, 30)}
        for k, g in T.items():
            G["turnstiles"].append((k, g))
        # players' gate + changing rooms (grows), tunnel at section 13 (x = 0)
        G["plots"].append(("changing rooms", box(14, -78, 42, -60)))
        bld("changing rooms", box(14, -72, 28, -62))
        path("players", [(21, -61.8), (21, -58), (0, -48.6)], w=2.4)
        # main approach from Gate Street
        bld("gate arch + sign + flags", box(-18, -129, -2, -125), label="gate arch\n+ sign, flags")
        path("main", [(-10, -125), (-10, -60)], w=6)
        G["plots"].append(("ticket office", box(-36, -127, -20, -111)))
        bld("tickets", box(-28, -120, -22, -114))
        G["plots"].append(("club shop", box(4, -127, 34, -103)))
        for i in range(3):
            bld(f"merch {i}", box(6 + i * 7, -112, 11 + i * 7, -107), col="#F2D6A2", label="")
        G["notes"].append((20, -100, "merch tents", 7))
        bld("programmes", box(-4.5, -112, -1.5, -110), col="#F2D6A2", label="")
        G["notes"].append((3, -116, "progr.", 6))
        bld("bikes", box(-36, -108, -26, -105), col="#888", label="")
        G["notes"].append((-31, -102, "bikes", 6))
        # service road from the car-park lobe to the bus bay by the changing rooms
        G["hard"].append(box(40, -178, 92, -150))             # car park (min, ~30)
        G["plots"].append(("car park", box(40, -178, 139, -133)))
        path("service", [(60, -150), (60, -82), (46, -82)], w=6)
        G["bays"].append(box(40, -88, 52, -76))
        G["notes"].append((46, -93, "team bus", 6.5))
        G["plots"].append(("offices", box(66, -114, 96, -92)))
        bld("offices (portakabin)", box(66, -100, 80, -95), label="offices")
        G["plots"].append(("groundsman", box(102, -176, 137, -152)))
        bld("groundsman", box(102, -166, 112, -158), label="groundsman")
        path("groundsman", [(60, -150), (60, -146), (102, -146), (107, -157.5)], w=4)
        # clubhouse on the home plaza (North-West bulge, outside the max line: it stays)
        G["hard"].append(Polygon([(-176, -129), (-120, -129), (-120, -110), (-176, -110)]))
        G["plots"].append(("clubhouse", box(-174, -106, -141, -66)))
        bld("CLUBHOUSE + bar", box(-168, -100, -148, -88), label="CLUBHOUSE\n+ bar", fs=8)
        path("home NW", [(-140, -118), (-112, -100), (-82, -30)], w=5)
        path("clubhouse", [(-158, -110), (-158, -100)], w=3)
        # home approach from Chapel Row
        path("home N", [(-139, 20), (-82, 20)], w=5)
        # inside the paying fence: home end kiosks
        bld("chip van", box(-76, 30, -70, 42), label="chip van", fs=6.5)
        bld("tea hut", box(-76, -20, -70, -12), label="tea", fs=6.5)
        bld("toilets", box(-76, -46, -68, -38), label="wc", fs=6.5)
        # away: gate in the South-East, walk to the away turnstile, kiosk + wc inside the pen
        path("away", [(134.6, 100), (126, 100), (100, 60), (70.6, 24)], w=4)
        yseg = (N_END / 2 - 2) * SW
        G["lines"].append(([(58.4, yseg), (68, yseg)], C["away"]))          # segregation inside (away = 2 East-most South sections)
        bld("away kiosk", box(60, 32, 64, 36), col="#F4C7C5", label="")
        G["notes"].append((88, 40, "away kiosk + wc", 6.5))
        bld("away wc", box(60, yseg + 2, 64, yseg + 7), col="#F4C7C5", label="")
        bld("away gate", box(135, 94, 139, 106), col=C["away"], label="")
        # healthy fill
        G["green"].append(("kickabout", box(-40, 66, 40, 104)))
        G["green"].append(("training pitch", box(80, -40, 120, 24)))
        tree_zones = [box(-134, 60, -50, 114), box(50, 62, 134, 114), box(-134, -36, -92, 56), box(76, -122, 134, -50),
                      box(-120, -96, -86, -62)]
        G["trees"] = tree_zones
    else:
        G["stands"] = [box(-STAND_MAX_X, -STAND_MAX_Y, STAND_MAX_X, STAND_MAX_Y).difference(
            box(-END_FRONT, -SIDE_FRONT, END_FRONT, SIDE_FRONT))]
        G["fence_pay"] = None                     # the facade is the fence
        # facade zone: West = club building (offices, club shop, ticket office, changing rooms, bar), stair cores elsewhere
        bld("club building", box(-42, -123, 42, -105), col=C["standmax"], label="CLUB BUILDING\noffices · shop · tickets · lounges", fs=7)
        for x in (-95, 95):
            bld(f"stair W{x}", box(x - 6, -115, x + 6, -105), col=C["standmax"], label="")
        for x in (-80, -25, 25, 80):
            bld(f"stair E{x}", box(x - 5, 105, x + 5, 112), col=C["standmax"], label="")
        for y in (-55, 0, 55):
            bld(f"stair N{y}", box(-132, y - 5, -125, y + 5), col=C["standmax"], label="")
            bld(f"stair S{y}", box(125, y - 5, 132, y + 5), col=C["standmax"], label="")
        # 1st division: every stand has its own turnstiles (in the facade, on the outer line of the max zone)
        for x in (-62, 62):
            G["turnstiles"].append(("W", box(x - 3, -125, x + 3, -121)))
        for x in (-52, 52):
            G["turnstiles"].append(("E", box(x - 3, 111, x + 3, 115)))
        for y in (-28, 28):
            G["turnstiles"].append(("N", box(-135, y - 3, -131, y + 3)))
        G["turnstiles"].append(("S", box(131, -31, 135, -25)))
        G["turnstiles"].append(("A", box(131, 25, 135, 31)))
        bld("gate arch + sign + flags", box(-18, -129, -2, -126), label="")
        path("main", [(-10, -126), (-10, -123)], w=6)
        # forecourt ring between the facade and the fence
        G["hard"].append(PLOT.difference(MAXL).intersection(box(-176, -129, 139, 119)).difference(box(40, -178, 139, -129)))
        G["hard"].append(MAXL.difference(box(-STAND_MAX_X, -STAND_MAX_Y, STAND_MAX_X, STAND_MAX_Y)))
        # car park full, groundsman yard full, service road to the club building
        G["hard"].append(box(40, -178, 98, -133))
        G["plots"].append(("car park (~120)", box(40, -178, 139, -133)))
        bld("groundsman", box(102, -176, 137, -152), label="groundsman yard")
        path("service", [(60, -150), (60, -129), (44, -123)], w=6)
        G["bays"].append(box(43, -129, 55, -125))
        # clubhouse at full size on the home plaza
        G["hard"].append(Polygon([(-176, -129), (-120, -129), (-120, -110), (-176, -110)]))
        bld("CLUBHOUSE + bar", box(-174, -106, -141, -66), label="CLUBHOUSE\n+ bar (full size)", fs=8)
        bld("away gate", box(135, 94, 139, 106), col=C["away"], label="")
        G["notes"].append((0, 0, "1st division: everything in the stands\nkiosks, wc's, changing rooms, offices\nown turnstiles per stand · masts → roof light bars", 8))
        G["trees"] = []
    return G


# ---------------------------------------------------------------- self-check
_ss = 153.5 - RW["South Street"][0] / 2
COACH_BAY = box(_ss - 3.5, 55, _ss, 120)


def check(G, stage):
    errs = []
    houses_all = unary_union([h["house"] for h in HOUSES] + [h.get("out", Polygon()) for h in HOUSES])
    plots_all = unary_union([h["front"].union(h["house"]).union(h["yard"]) for h in HOUSES])
    # village
    if plots_all.intersects(PLOT.buffer(-0.01)):
        errs.append("a house plot is inside the ground's plot")
    if houses_all.intersection(road_area).area > 0.5:
        errs.append("a house stands on a street")
    if plots_all.intersects(water):
        errs.append("a house is in the canal")
    # ground
    road_or_out = road_area.union(VIEW.difference(PLOT))
    pathgeo = [p["g"] for p in G["paths"]]
    stands = unary_union(G["stands"]) if G["stands"] else Polygon()
    for b in G["buildings"]:
        g = b["g"]
        if not PLOT.buffer(0.01).contains(g):
            errs.append(f"{b['name']}: outside the plot")
        if g.intersects(road_area):
            errs.append(f"{b['name']}: on a street")
        for p in G["paths"]:
            if g.buffer(-0.3).intersects(p["g"]):
                errs.append(f"{b['name']}: over path '{p['name']}'")
        for o in G["buildings"]:
            if o is not b and g.buffer(-0.2).intersects(o["g"]):
                errs.append(f"{b['name']}: overlaps {o['name']}")
        for m in G["masts"]:
            if g.intersects(m):
                errs.append(f"{b['name']}: on a mast")
        if g.buffer(-0.2).intersects(stands):
            errs.append(f"{b['name']}: inside a stand")
    for p in G["paths"]:
        for m in G["masts"]:
            if p["g"].intersects(m):
                errs.append(f"path '{p['name']}': through a mast")
        if p["g"].buffer(-0.3).intersects(stands):
            if p["name"] != "players":
                errs.append(f"path '{p['name']}': through a stand")
        if not PLOT.buffer(0.01).contains(p["g"]):
            errs.append(f"path '{p['name']}': outside the plot")
        # both ends must touch something: plot edge (a gate), another path, a building, a turnstile, a bay, a stand, hard standing
        anchors = [PLOT.exterior.buffer(1.2)] + [o["g"] for o in G["paths"] if o is not p] + [b["g"] for b in G["buildings"]] + \
                  [g for _, g in G["turnstiles"]] + G["bays"] + G["stands"] + G["hard"]
        for end in (Point(p["line"].coords[0]), Point(p["line"].coords[-1])):
            if not any(a.buffer(1.0).contains(end) for a in anchors):
                errs.append(f"path '{p['name']}': loose end at ({end.x:.0f}, {end.y:.0f})")
    for dv in G["drives"]:
        if dv.intersects(plots_all) or dv.distance(carriage) > 0.2 or dv.intersection(PLOT).area < 1:
            errs.append("car park entrance doesn't join street and car park (or hits a house)")
    # the plot itself against the streets (this hole let North Street through in v3)
    a = PLOT.intersection(road_area).area
    if a > 0.5:
        errs.append(f"the ground's plot overlaps a street ({a:.0f} m2)")
    # the away coach bay: on the ground side, never on houses or the carriageway
    if COACH_BAY.intersects(plots_all) or COACH_BAY.intersection(carriage).area > 0.1 or COACH_BAY.intersection(PLOT).area > 0.1:
        errs.append("away coach bay hits houses, the carriageway or the ground")
    # pubs are houses: already in the house checks; courts + lanes
    for ct in COURTS:
        if ct["lane"].intersection(unary_union([h["house"] for h in HOUSES])).area > 0.1:
            errs.append("a court lane goes through a house")
    # canal: every crossing is a bridge, the towpath has a footbridge; every street is reachable from High Road
    for n, r in roads.items():
        if r.intersects(water) and n not in BRIDGES:
            errs.append(f"{n} crosses the canal without a bridge")
    names = list(roads)
    seen, todo = {"High Road"}, ["High Road"]
    while todo:
        cur = todo.pop()
        for n in names:
            if n not in seen and roads[cur].buffer(0.5).intersects(roads[n]):
                seen.add(n)
                todo.append(n)
    for n in names:
        if n not in seen:
            errs.append(f"{n} can't be reached from High Road")
    return errs


# ---------------------------------------------------------------- drawing
def draw_poly(ax, g, fc, ec="none", lw=0.4, z=1, alpha=1.0, ls="-", hatch=None):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        if p.geom_type in ("MultiPolygon", "GeometryCollection"):
            draw_poly(ax, p, fc, ec, lw, z, alpha, ls, hatch)
            continue
        if p.geom_type != "Polygon":
            continue
        # real holes (a ring of streets round the canal must not paint over it)
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls, hatch=hatch))


def label(ax, x, y, text, fs=7.5, col="#222", w="bold", rot=0):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=col, weight=w, rotation=rot, zorder=60,
            bbox=dict(fc="white", ec="none", alpha=0.78, pad=0.5))


def trees(ax, zones, avoid, seed=3):
    r = random.Random(seed)
    for z in zones:
        x0, y0, x1, y1 = z.bounds
        y = y0 + 3
        while y < y1 - 2:
            x = x0 + 3 + r.random() * 3
            while x < x1 - 2:
                px, py = x + r.uniform(-1.5, 1.5), y + r.uniform(-1.5, 1.5)
                c = Point(px, py).buffer(3.0)
                if z.contains(Point(px, py)) and not c.intersects(avoid):
                    ax.add_patch(Circle((px, py), r.uniform(2.3, 3.3), fc=C["tree"], ec="#3a6a2e", lw=0.3, alpha=0.9, zorder=12))
                x += 8.0
            y += 7.0


def draw(stage, G):
    fig, ax = plt.subplots(figsize=(15, 14.2), dpi=125)
    ax.set_aspect("equal")
    ax.set_facecolor(C["bg"])
    ax.set_xlim(VIEW.bounds[0], VIEW.bounds[2])
    ax.set_ylim(VIEW.bounds[1], VIEW.bounds[3])
    ax.set_xticks([]); ax.set_yticks([])
    # village
    draw_poly(ax, tow.intersection(VIEW), C["tow"], z=2)
    draw_poly(ax, water.intersection(VIEW), C["water"], z=3)
    draw_poly(ax, road_area.intersection(VIEW), C["pave"], z=4)
    for ct in COURTS:
        draw_poly(ax, ct["area"], C["hard"], ec="#a89f8c", lw=0.4, z=5)
        draw_poly(ax, ct["lane"], C["alley"], z=5)
        for q in ct["boxes"]:
            draw_poly(ax, q, "#8E8378", ec="#5e554c", lw=0.3, z=6)
    draw_poly(ax, carriage.intersection(VIEW), C["road"], z=5)
    for h in HOUSES:
        draw_poly(ax, h["front"], C["front"], ec="#a9bf98", lw=0.2, z=6)
        draw_poly(ax, h["yard"], C["yard"], ec="#b9c7ab", lw=0.2, z=6)
        if "alley" in h:
            draw_poly(ax, h["alley"], C["alley"], z=6)
        draw_poly(ax, h["house"], C["pub"] if h["pub"] is not None else C["house"], ec="#7a3f2d", lw=0.35, z=7)
        if "out" in h:
            draw_poly(ax, h["out"], C["out"], ec="#6b3526", lw=0.25, z=7)
    for n in BRIDGES:
        seg = roads[n].intersection(water.buffer(2.5))
        for sd in (-1, 1):
            edge = seg.parallel_offset(EDGE - 0.6, "left" if sd > 0 else "right") if seg.geom_type == "LineString" else None
            if edge is not None and not edge.is_empty:
                xs, ys = edge.xy
                ax.plot(xs, ys, color="#6b6257", lw=2.2, zorder=9)
        c = seg.centroid
        label(ax, c.x + 16, c.y, "bridge", fs=6, w="normal")
    ax.plot(*FOOTBRIDGE.xy, color="#6b6257", lw=2.5, zorder=9)
    for dx in (-10, 4):
        gate = LineString([(LOCK_X + dx, lock_p.y - 6), (LOCK_X + dx, lock_p.y + 6)])
        ax.plot(*gate.xy, color="#3b2f22", lw=2.0, zorder=9)
    label(ax, LOCK_X - 2, lock_p.y + 13, "lock + footbridge", fs=6, w="normal")
    big = sorted(COURTS, key=lambda ct: -ct["area"].area)[:5]
    for ct in big:
        cc = ct["area"].representative_point()
        label(ax, cc.x, cc.y, "garages /\nworkshops", fs=5.5, w="normal")
    for h in HOUSES:
        if h["pub"] is not None:
            c = h["pubpos"]
            label(ax, c.x, c.y, "PUB" + (f"\n({h['pub']})" if h["pub"] else ""), fs=6.5)
    for name, line in roads.items():
        p = line.interpolate(0.5, normalized=True)
        q = line.interpolate(min(line.length, line.length * 0.5 + 1))
        ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
        ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
        if VIEW.contains(p):
            ax.text(p.x, p.y, name.upper(), rotation=ang, ha="center", va="center", fontsize=5.5, color="white", weight="bold", zorder=8)
    # ground
    draw_poly(ax, PLOT, C["ground"], ec=C["fence"], lw=2.2, z=9)
    for h in G["hard"]:
        draw_poly(ax, h, C["hard"], ec="#b8b0a0", lw=0.4, z=10)
    for name, g in G["green"]:
        draw_poly(ax, g, "#8FBF7A", ec="white", lw=0.8, z=10)
        label(ax, g.centroid.x, g.centroid.y, name, fs=7, w="normal")
    avoid = unary_union([p["g"] for p in G["paths"]] + [b["g"] for b in G["buildings"]] + G["stands"] + G["hard"] +
                        [g for _, g in G["green"]] + G["masts"] + [g for _, g in G["plots"]])
    trees(ax, G["trees"], avoid)
    for name, g in G["plots"]:
        draw_poly(ax, g, "none", ec="#8a5a12", lw=0.9, z=11, ls=(0, (3, 2)))
    draw_poly(ax, MAXL, "none", ec=C["max"], lw=1.6, z=40, ls=(0, (6, 4)))
    # pitch + stands
    draw_poly(ax, box(-HL - 3, -HW - 3, HL + 3, HW + 3), C["pitch"], z=13)
    draw_poly(ax, box(-HL, -HW, HL, HW), "none", ec="white", lw=1.1, z=14)
    ax.plot([0, 0], [-HW, HW], color="white", lw=0.9, zorder=14)
    ax.add_patch(Circle((0, 0), 9.15, fc="none", ec="white", lw=0.9, zorder=14))
    for g in G["stands"]:
        draw_poly(ax, g, C["stand"] if stage == "min" else C["standmax"], ec="#6d757d", lw=0.6, z=15)
    if stage == "min":
        # section ticks on the ends + away pen
        for k in range(N_END):
            y0 = (N_END / 2 - 1 - k) * SW
            draw_poly(ax, box(END_FRONT, y0, END_FRONT + 3, y0 + SW), "#F4C7C5" if k <= 1 else "none",
                      ec=C["away"] if k <= 1 else "#6d757d", lw=0.6, z=16)
            draw_poly(ax, box(-END_FRONT - 6, y0, -END_FRONT, y0 + SW), "none", ec="#6d757d", lw=0.4, z=16)
        label(ax, -END_FRONT - 13, -2, "HOME END", fs=7, col=C["pay"])
        label(ax, 0, -SIDE_FRONT - 5.5, "MAIN STAND", fs=6.5)
        label(ax, END_FRONT + 11, 14, "away", fs=6.5, col=C["away"])
    else:
        label(ax, 0, 70, "STADIUM (max, corners closed)", fs=9)
    for m in G["masts"]:
        draw_poly(ax, m, "#222", z=41)
    if G["fence_pay"] is not None:
        draw_poly(ax, G["fence_pay"], "none", ec=C["pay"], lw=1.6, z=42, ls=(0, (2, 1.5)))
        label(ax, -40, 55.5, "paying area fence", fs=6.5, col=C["pay"], w="normal")
    for p in G["paths"]:
        draw_poly(ax, p["g"], C["path"], ec="#c8b98f", lw=0.4, z=17 if p["name"] != "players" else 43)
    for b in G["bays"]:
        draw_poly(ax, b, "#3B6FB6", alpha=0.5, z=18)
    for b in G["buildings"]:
        draw_poly(ax, b["g"], b["col"], ec=C["facedge"] if b["col"] != C["standmax"] else "#5f666d", lw=0.8, z=44)
        if b["label"]:
            c = b["g"].centroid
            label(ax, c.x, c.y, b["label"], fs=b["fs"])
    for k, g in G["turnstiles"]:
        draw_poly(ax, g, C["pay"], z=45)
    for pts, col in G["lines"]:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=col, lw=1.8, zorder=46)
    for x, y, t, fs in G["notes"]:
        label(ax, x, y, t, fs=fs, w="normal")
    for name, g in G["plots"]:
        x0, y0, x1, y1 = g.bounds
        ax.text(x0 + 1, y1 - 1, name, ha="left", va="top", fontsize=5.5, color="#8a5a12", zorder=47, style="italic")
    # coach bay (pavement side of South Street, ground side)
    draw_poly(ax, COACH_BAY, "#F4C7C5", ec=C["away"], lw=0.8, z=8)
    for dv in G["drives"]:
        draw_poly(ax, dv, C["hard"], ec="#8f8778", lw=0.6, z=10)
    label(ax, 58, -162, "car park entrance", fs=6, w="normal")
    # contours: the land falls gently towards the canal (the lock steps it down); the ground is levelled
    import numpy as np
    xs = np.linspace(VIEW.bounds[0], VIEW.bounds[2], 220)
    ys = np.linspace(VIEW.bounds[1], VIEW.bounds[3], 200)
    X, Y = np.meshgrid(xs, ys)
    Z = terrain(X, Y)
    from matplotlib.path import Path as MPath
    inside = MPath(list(PLOT.buffer(4).exterior.coords)).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
    Z = np.ma.masked_where(inside | (Y > 168), Z)
    cs = ax.contour(X, Y, Z, levels=np.arange(-1.5, 4.01, 0.5), colors="#6b4a26", linewidths=1.0, alpha=0.85, zorder=8.5)
    ax.clabel(cs, fmt="%+.1f m", fontsize=5.5, inline=True)
    label(ax, 0, -22 if stage == "min" else -60, "ground levelled at ±0.0 m", fs=6, col="#7a5c3a", w="normal")
    label(ax, LOCK_X - 40, lock_p.y, f"{WATER_W:+.1f} m water", fs=5.5, col="#245", w="normal")
    label(ax, LOCK_X + 30, lock_p.y, f"{WATER_E:+.1f} m water", fs=5.5, col="#245", w="normal")
    label(ax, 157, 87, "away\ncoaches", fs=6.5, col=C["away"])
    # compass, key, scale
    title = "PLAN v5 — MIN (13th division)" if stage == "min" else "PLAN v5 — MAX (1st division)"
    for t, (x, y, rot) in {"EAST": (0, 224, 0), "WEST (camera)": (0, -257, 0), "NORTH = HOME": (-257, -60, 90),
                           "SOUTH": (257, 0, 90)}.items():
        ax.text(x, y, t, ha="center", va="center", fontsize=10, weight="bold", rotation=rot, zorder=70,
                bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.plot([180, 230], [-252, -252], color="#222", lw=3, zorder=70)
    ax.text(205, -246, "50 m", ha="center", fontsize=9, zorder=70)
    key = (f"{title}\n{N_END} sections per end\n"
           "dashed blue = max line (stands + facade)\n"
           "dashed brown = growth plot of a facility\n"
           + ("dotted blue = paying area: free to walk round,\n  only the away pen is fenced off\n" if stage == "min" else "facade = fence, own turnstiles per stand\n") +
           "houses: front · house + outrigger · yard · alley\n"
           "brown lines = height (m), ground levelled")
    ax.text(-258, -205, key, fontsize=7.5, va="top", zorder=70, bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    plt.tight_layout()
    out = os.path.join(OUTDIR, f"plan_v5_{stage}{SUFFIX}.png")
    plt.savefig(out, dpi=125)
    plt.close(fig)
    return out


if __name__ == "__main__":
    bad = False
    for stage in ("min", "max"):
        G = ground(stage)
        errs = check(G, stage)
        print(f"[{stage}] houses: {len(HOUSES)}, pubs: {sum(1 for h in HOUSES if h['pub'] is not None)}, errors: {len(errs)}")
        for e in errs:
            print("   ", e)
        bad |= bool(errs)
        print("   saved", draw(stage, G))
    sys.exit(1 if bad else 0)
