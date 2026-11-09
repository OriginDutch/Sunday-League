"""Village skeleton v1 — the town planned on purpose before anything is filled in. No houses.
python3 tools/plan/village_skeleton_v1.py  ->  design/world/village_skeleton_v1.png (+ zooms)

Marcel, 2026-11-09, after village plan v4: "opnieuw tekenen vanaf wat we al hadden, dan kan je het beter opvullen
en plannen ipv pleisters plakken". Order: fixed things (ground v5, canal, railway, main roads) -> skeleton
(districts, district streets, parks, industry, landmarks with their own grounds) -> Marcel reviews -> fill.

Marcel's answers:
  park 1 behind / next to the church, together with the cemetery;
  park 2 on the canal, behind the terraces at the south stand, east of them (= where v4 had the big green east of the estate);
  industry below the railway, at the bottom of the picture (= towards game-west), not in the town;
  garden depth: Victorian 10-15 m, 1930s 20-30 m, new build 8-12 m;
  districts: Claude proposes.
Picture orientation as before: right = South (+x), up = East (+y), down = West.
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Ellipse
from matplotlib.path import Path
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import world_plan_v5 as W
import village_plan_v1 as V

OUT = os.path.join(HERE, "../../design/world")
R = 750
WORLD = box(-R, -R, R, R)

# ---------------------------------------------------------------- districts (proposal)
# name -> (colour, polygon, garden depth m, note)
D_VIC, D_CORE, D_30S, D_NEW, D_EST, D_EDW, D_IND = ("Victorian terraces", "old core", "1930s semis", "new build",
                                                    "post-war estate", "Edwardian + infill", "industrial estate")
DCOL = {D_VIC: "#C77B60", D_CORE: "#B8956A", D_30S: "#E2B48A", D_NEW: "#EBD9BE", D_EST: "#9FAAB6", D_EDW: "#D6A98A",
        D_IND: "#8E8A84"}
GARDEN = {D_VIC: "10-15 m", D_CORE: "10-15 m", D_30S: "20-30 m", D_NEW: "8-12 m", D_EST: "communal green", D_EDW: "15-20 m",
          D_IND: "yards"}
IND_POLY = Polygon([(352, -478), (500, -455), (750, -375), (750, -750), (375, -750)])
DISTRICTS = [   # later ones sit on top
    (D_EDW, Polygon([(-R, -R), (R, -R), (R, R), (-R, R)])),
    (D_30S, Polygon(V.LAYERS[1][2])),
    (D_30S, Polygon(V.LAYERS[2][2])),
    (D_NEW, Polygon(V.LAYERS[3][2])),
    (D_NEW, Polygon(V.LAYERS[4][2])),
    (D_NEW, Polygon(V.LAYERS[5][2]).difference(IND_POLY)),
    (D_VIC, Polygon(V.LAYERS[6][2])),
    (D_CORE, Polygon(V.LAYERS[7][2])),
    (D_EST, Polygon(V.LAYERS[8][2])),
    (D_IND, IND_POLY),
]

# ---------------------------------------------------------------- fixed: main roads, canal, railway
MAIN = {n: (LineString(p), w, k) for n, (p, w, k) in V.ROADS.items()}

# ---------------------------------------------------------------- district streets (new, proposal)
# the second layer: they link the main roads so no block is bigger than a district can fill sensibly
DSTREETS = {
    "Brickfield Road": [(-266, 335), (-100, 338), (100, 333), (312, 335)],
    "Grove Road": [(-263, 600), (-80, 604), (120, 598), (353.4, 600)],
    "Kingsway": [(20, 335), (24, 470), (20, 600), (16, 750)],
    "Park Avenue": [(-750, 432), (-560, 436), (-268, 430)],
    "Moorside": [(-600, 434), (-604, 600), (-598, 750)],
    "School Lane": [(353.4, 600), (480, 603), (621, 600)],
    "Lock Lane": [(415, 289), (418, 450), (414, 601)],
    "Back Lane": [(-640, -245), (-643, -150), (-640, -55)],
    "Railway Terrace": [(-40.5, -390), (100, -392), (180, -390), (322, -395)],
    "Foundry Lane": [(480, -243), (492, -330), (500, -392), (600, -370), (680, -345), (700, -211)],
    "Southfield Road": [(-750, -640), (-420, -642), (-83, -640), (120, -632), (350, -620)],
    "Rectory Road": [(-420, -642), (-418, -700), (-420, -750)],
}
# industrial estate: one way in off Moor Lane, a loop round the yards
EST_IN = [(346.1, -585), (430, -585)]
EST_LOOP = [(430, -540), (480, -515), (600, -495), (700, -455), (715, -600), (690, -690), (560, -700), (450, -680), (430, -640), (430, -540)]
DSTREETS["Moor Lane Ind. Estate"] = EST_IN
LOOP = LineString(EST_LOOP)

# ---------------------------------------------------------------- landmarks (moved / new ones marked)
LMK = {}
for name, (x, y), size, col, shape in V.LANDMARKS:
    if shape == "rect":
        LMK[name.splitlines()[0]] = [box(x - size[0] / 2, y - size[1] / 2, x + size[0] / 2, y + size[1] / 2), col]
LMK.pop("cemetery")                       # moves to the church (park 1)
LMK["petrol station"][0] = box(600, -285, 640, -260)      # on London Road, in the Foundry Lane loop corner

# ---------------------------------------------------------------- park 1: church, churchyard, cemetery, park to the canal
PARK1 = Polygon([(-488, -26), (-488, 40), (-530, 118), (-600, 135), (-730, 128), (-730, -30), (-600, -46)])
CEMETERY = Polygon([(-492, -24), (-492, 52), (-610, 52), (-610, -44), (-600, -44)])
P1_PATHS = [
    [(-610, 20), (-650, 40), (-700, 80), (-728, 95)],                       # cemetery gate -> towpath corner
    [(-492, 45), (-530, 80), (-560, 112), (-575, 132)],                     # church -> canal
    [(-725, -25), (-680, 10), (-640, 60), (-600, 100), (-575, 132)],        # Back Lane corner -> canal (diagonal)
    [(-730, 60), (-690, 70), (-650, 40)],
]
P1_CEM_PATHS = [[(-551, -40), (-551, 52)], [(-610, 4), (-492, 4)]]          # cross of paths through the cemetery
P1_POND = (-665, 95, 50, 26)
P1_FEAT = [("playground", (-700, 0)), ("pond", (-665, 95)), ("lychgate", (-492, 20))]

# ---------------------------------------------------------------- park 2: on the canal, east of the estate
PARK2 = Polygon([(487, 214), (600, 250), (668, 266), (688, 170), (703, 40), (640, 22), (598, 95)])
P2_PATHS = [
    [(495, 212), (540, 200), (600, 160), (650, 150), (680, 160)],
    [(600, 248), (610, 200), (600, 160), (612, 110), (640, 30)],
    [(495, 212), (560, 238), (660, 262)],                                   # along the canal
    [(598, 95), (612, 110)],
]
P2_POND = (632, 225, 40, 22)
P2_FEAT = [("bandstand", (600, 160)), ("pond", (632, 225)), ("playground", (560, 175)), ("kickabout pitch", (665, 85)),
           ("bowling green", (625, 120))]
P2_PITCH = box(645, 60, 690, 112)
P2_BOWLS = box(615, 112, 640, 132)

# ---------------------------------------------------------------- green buffer between industry and houses
BUFFER = Polygon([(337, -478), (352, -478), (375, -750), (360, -750)]).buffer(0)       # Moor Lane west verge widened
BUFFER = LineString([(352, -478), (375, -750)]).buffer(14, cap_style=2).difference(IND_POLY).difference(
    LineString(V.ROADS["Moor Lane"][0]).buffer(4.5))

# ---------------------------------------------------------------- extra green: OPTIONS for Marcel (not decided)
CANAL_GREEN = V.CANAL.buffer(24).difference(V.CANAL.buffer(9)).difference(unary_union(
    [l.buffer(40) for l, w, k in MAIN.values()] + [box(-285, -320, 315, 250), PARK1, PARK2] +     # not in the v5 area: houses there
    [LMK[k][0].buffer(5) for k in ("old mill (canal)",)]))
OPTIONS = {
    "a: canal greenway (15 m strip both banks)": CANAL_GREEN,
    "b: rec ground below the railway": box(-620, -740, -470, -665),
    "c: rec ground in the north new build": box(-560, 640, -400, 735),
    "e: cricket ground + pavilion (old cemetery site)": box(-600, -455, -420, -300),
    "d: park 2 grows down to London Road side": Polygon([(640, 22), (703, 40), (712, -60), (720, -150), (640, -160), (610, -60)]),
}


# ---------------------------------------------------------------- self-check
GREEN_KEYS = ("village green", "Victoria Park", "playing fields", "allotments", "secondary school")


def all_lines():
    out = {n: (l, w) for n, (l, w, k) in MAIN.items()}
    for n, pts in DSTREETS.items():
        out[n] = (LineString(pts), 6.5 if "Estate" not in n else 7.0)
    out["estate loop"] = (LOOP, 7.0)
    return out


def tangent(line, d):
    a = line.interpolate(max(d - 2, 0))
    b = line.interpolate(min(d + 2, line.length))
    L = math.hypot(b.x - a.x, b.y - a.y) or 1
    return ((b.x - a.x) / L, (b.y - a.y) / L)


def check():
    errs, notes = [], []
    lines = all_lines()
    hard = unary_union([V.CANAL.buffer(9), V.RAIL.buffer(7), W.PLOT])
    # 1. every district street ends on another street (or the map edge) at 60-120 degrees
    for n, pts in DSTREETS.items():
        ln = LineString(pts)
        for end, prev in ((0, 1), (-1, -2)):
            p = Point(pts[end])
            if WORLD.exterior.distance(p) < 3:
                continue
            hosts = [(o, l) for o, (l, w) in lines.items() if o != n and l.distance(p) < 3]
            if not hosts:
                errs.append(f"{n}: loose end at {tuple(round(v) for v in pts[end])}")
                continue
            q = Point(pts[prev])
            dx, dy = q.x - p.x, q.y - p.y
            L = math.hypot(dx, dy) or 1
            angs = []
            for o, l in hosts:
                tt = tangent(l, l.project(p))
                angs.append((math.degrees(math.acos(min(1, abs(tt[0] * dx / L + tt[1] * dy / L)))), o))
            ang, o = max(angs)
            if ang < 60:
                errs.append(f"{n} meets {o} at {ang:.0f} deg")
    # 2. no district street over the canal, the railway or the ground
    for n, pts in DSTREETS.items():
        if LineString(pts).buffer(3).intersects(hard):
            errs.append(f"{n}: over canal / railway / ground")
    # 3. no landmark, park or the industry loop on a street
    roads = unary_union([l.buffer(w / 2 + 1.5) for l, w in lines.values()])
    things = {k: g for k, (g, c) in LMK.items() if k != "STATION"}
    things.update({"park 1": PARK1, "park 2": PARK2})
    for k, g in things.items():
        if g.intersects(roads):
            errs.append(f"{k}: on a street")
        if g.intersects(V.CANAL.buffer(9)) and not k.startswith("old mill"):     # the mill stands on the water on purpose
            errs.append(f"{k}: in the canal")
    # 4. junctions not within 30 m of a bridge (main road x canal / railway)
    bridges = []
    for l, w, k in MAIN.values():
        for wl in (V.CANAL, V.RAIL):
            x = l.intersection(wl)
            bridges += list(getattr(x, "geoms", [x])) if not x.is_empty else []
    for n, pts in DSTREETS.items():
        for e in (pts[0], pts[-1]):
            for b in bridges:
                if Point(e).distance(b) < 30:
                    errs.append(f"{n}: junction {Point(e).distance(b):.0f} m from a bridge")
    # 5. biggest leftover block per district (the fill step must be able to handle it)
    roads = roads.union(unary_union([r.buffer(3) for r in W.roads.values()]))
    blocks = WORLD.difference(unary_union([roads, V.CANAL.buffer(9), V.RAIL.buffer(7), W.PLOT.buffer(2)]))
    big = sorted([g for g in blocks.geoms if g.area > 1000], key=lambda g: -g.area)
    for g in big[:6]:
        c = g.representative_point()
        notes.append(f"block {g.area / 1e4:.1f} ha at ({c.x:.0f}, {c.y:.0f})")
    return errs, notes, bridges


def green_area():
    g = [PARK1, PARK2, BUFFER] + [LMK[k][0] for k in GREEN_KEYS]
    return unary_union(g).area


# ---------------------------------------------------------------- drawing
def geom_patch(ax, g, fc, ec, lw, z, alpha=1.0, ls="-", hatch=None):
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon":
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls, hatch=hatch))


def label(ax, x, y, t, fs=8, col="#222", w="bold", rot=0, bg="white", z=60, style="normal"):
    ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=col, weight=w, rotation=rot, zorder=z, style=style, clip_on=True,
            bbox=dict(fc=bg, ec="none", alpha=0.85, pad=0.5) if bg else None)


def line_label(ax, ln, name, at, fs, col_bg):
    p = ln.interpolate(at, normalized=True)
    q = ln.interpolate(min(at * ln.length + 1, ln.length))
    ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
    ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
    ax.text(p.x, p.y, name, rotation=ang, ha="center", va="center", fontsize=fs, color="white", weight="bold", zorder=40, clip_on=True,
            bbox=dict(fc=col_bg, ec="none", pad=0.35))


def draw(path, view=None, size=15, dpi=120, title=True):
    x0, y0, x1, y1 = view or (-R, -R, R, R)
    zoom = view is not None
    k = 1.0 if not zoom else min(3.0, 1500 / (x1 - x0) * 0.75)
    fig, ax = plt.subplots(figsize=(size, size * (y1 - y0) / (x1 - x0)), dpi=dpi)
    ax.set_aspect("equal")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor("#F4F2EC")
    # districts, light
    for n, g in DISTRICTS:
        geom_patch(ax, g, DCOL[n], "white", 1.2, 1, alpha=0.55)
    # the ground (v5 area)
    geom_patch(ax, W.PLOT, "#E3EFD9", "#2F5B3F", 1.2, 5)
    geom_patch(ax, box(-W.HL, -W.HW, W.HL, W.HW), "#7DB36A", "#2F5B3F", 0.8, 6)
    for r in W.roads.values():
        xs, ys = r.xy
        ax.plot(xs, ys, color="#9a958c", lw=1.4 * k, zorder=7, solid_capstyle="round")
    # canal + towpath, railway
    geom_patch(ax, V.CANAL.buffer(6), "#BFD9E6", "#5f95b3", 0.8, 8)
    xs, ys = V.RAIL.xy
    ax.plot(xs, ys, color="#444", lw=3.4 * k, zorder=9)
    ax.plot(xs, ys, color="white", lw=1.4 * k, zorder=9, ls=(0, (3, 3)))
    # green
    green_c = "#8DBF73"
    geom_patch(ax, BUFFER, "#A9CF8E", "#6c8f55", 0.6, 10, hatch="..")
    for key in GREEN_KEYS:
        g, c = LMK[key]
        geom_patch(ax, g, "#B5CF8A" if key == "allotments" else green_c, "#4f7a3a", 0.8, 10)
    for P, paths, pond, feats in ((PARK1, P1_PATHS, P1_POND, P1_FEAT), (PARK2, P2_PATHS, P2_POND, P2_FEAT)):
        geom_patch(ax, P, green_c, "#4f7a3a", 1.0, 10)
        geom_patch(ax, P.exterior.buffer(2.0).intersection(P), "#e9e2cf", "none", 0, 11)      # perimeter path
        for pts in paths:
            ln = LineString(pts).intersection(P.buffer(1))
            for s in getattr(ln, "geoms", [ln]):
                if s.geom_type == "LineString":
                    xs, ys = s.xy
                    ax.plot(xs, ys, color="#e9e2cf", lw=2.2 * k, zorder=11, solid_capstyle="round")
        ax.add_patch(Ellipse((pond[0], pond[1]), pond[2], pond[3], fc="#9cc7dc", ec="#5f95b3", lw=0.8, zorder=12))
        if zoom:
            for t, (x, y) in feats:
                label(ax, x, y, t, fs=7.5, w="normal", style="italic", col="#2f4f23", bg="#eef6e6")
    geom_patch(ax, CEMETERY, "#A7B89A", "#4f5f45", 1.0, 12)
    for pts in P1_CEM_PATHS:
        xs, ys = LineString(pts).xy
        ax.plot(xs, ys, color="#e9e2cf", lw=1.8 * k, zorder=13)
    if zoom:
        import random
        rr = random.Random(3)
        for _ in range(260):              # headstones, so it reads as a cemetery and not a lawn
            x, y = rr.uniform(-606, -496), rr.uniform(-40, 48)
            if CEMETERY.buffer(-3).contains(Point(x, y)) and abs(x + 551) > 4 and abs(y - 4) > 4:
                ax.plot([x], [y], marker="s", ms=1.6, color="#5d6156", zorder=13)
    geom_patch(ax, P2_PITCH, "#7DB36A", "white", 1.0, 12)
    geom_patch(ax, P2_BOWLS, "#6aa457", "white", 0.8, 12)
    # green options, dashed
    for i, (n, g) in enumerate(OPTIONS.items()):
        geom_patch(ax, g, "#cfe6bf", "#3d7a2a", 1.2, 10, alpha=0.9, ls="--")
        c = g.representative_point() if i else Point(-620, 190)
        if x0 < c.x < x1 and y0 < c.y < y1:
            label(ax, c.x, c.y, f"option {n.split(':')[0]}", fs=7 if not zoom else 9, col="#1d3b14", bg="#ffffffcc")
    # industry: yards along the loop, one way in
    yards = []
    for i in range(len(EST_LOOP) - 1):
        a, b = EST_LOOP[i], EST_LOOP[i + 1]
        seg = LineString([a, b])
        for side in (1, -1):
            off = seg.parallel_offset(30 * side, "left")
            if off.is_empty:
                continue
            y_ = off.buffer(24, cap_style=2).intersection(IND_POLY.buffer(-6)).difference(LOOP.buffer(8))
            yards.append(y_)
    YARDS = unary_union(yards)
    geom_patch(ax, YARDS, "#bdb8ae", "#77736b", 0.6, 12, ls="--")
    # main roads
    for n, (l, w, kd) in MAIN.items():
        xs, ys = l.xy
        ax.plot(xs, ys, color="#2f3337" if kd == "a" else "#4d5258", lw={"a": 5.5, "b": 4.2, "c": 3.0}[kd] * k, zorder=20,
                solid_capstyle="round")
    # district streets
    for n, pts in DSTREETS.items():
        xs, ys = LineString(pts).xy
        ax.plot(xs, ys, color="#D9822B", lw=2.6 * k, zorder=21, solid_capstyle="round")
    xs, ys = LOOP.xy
    ax.plot(xs, ys, color="#D9822B", lw=2.6 * k, zorder=21)
    # landmarks
    for key, (g, c) in LMK.items():
        if key in GREEN_KEYS:
            continue
        geom_patch(ax, g, c, "#333", 0.8, 22)
    # labels
    fs = 6.8 if not zoom else 9
    for n, (l, w, kd) in MAIN.items():
        line_label(ax, l, n, 0.62 if n != "Moor Lane" else 0.35, fs, "#2f3337")
    for n, pts in DSTREETS.items():
        line_label(ax, LineString(pts), n, 0.5 if n not in ("Southfield Road",) else 0.25, fs, "#B5651D")
    line_label(ax, LOOP, "estate loop", 0.15, fs, "#B5651D")
    for key, (g, c) in LMK.items():
        cx, cy = g.centroid.x, g.centroid.y
        if x0 < cx < x1 and y0 < cy < y1:
            label(ax, cx, cy, key, fs=fs)
    for t, (x, y) in (("PARK 1\nchurch + cemetery park", (-640, 90)), ("PARK 2\ncanal park", (545, 225)),
                      ("cemetery", (-551, 30)), ("INDUSTRIAL ESTATE\n(one way in, off Moor Lane)", (570, -600)),
                      ("green buffer", (395, -680)), ("THE GROUND\n(plan v5)", (0, 0)), ("canal", (-150, 182)),
                      ("railway", (-300, -475))):
        if x0 < x < x1 and y0 < y < y1:
            label(ax, x, y, t, fs=fs + 0.5, col="#1d3b14" if "PARK" in t or "green" in t else "#222")
    if not zoom:
        for n, g in DISTRICTS[1:]:
            c = g.representative_point()
            if n == D_IND:
                continue
            label(ax, c.x, c.y - 22, f"{n}\ngardens {GARDEN[n]}", fs=6.2, w="normal", col="#3a2a1e", bg="#ffffffaa", style="italic")
        label(ax, 640, 680, f"{D_EDW}\ngardens {GARDEN[D_EDW]}", fs=6.2, w="normal", col="#3a2a1e", bg="#ffffffaa", style="italic")
    if title:
        errs, notes, _ = check()
        gp = 100 * green_area() / WORLD.area
        ax.text(x0 + 12, y1 - 12,
                "VILLAGE SKELETON v1 — planned first, filled later (no houses yet)\n"
                "dark = main roads (fixed) · orange = district streets (new, proposal) · green = public green\n"
                f"public green {gp:.1f} % (target 10-15 %) · dashed = green OPTIONS, not decided · check: {len(errs)} errors",
                ha="left", va="top", fontsize=9 if not zoom else 10, zorder=70,
                bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    sb = 200 if not zoom else 50
    ax.plot([x1 - 30 - sb, x1 - 30], [y0 + 25, y0 + 25], color="#222", lw=3, zorder=70)
    ax.text(x1 - 30 - sb / 2, y0 + 40, f"{sb} m", ha="center", fontsize=9, zorder=70)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print("saved", os.path.relpath(path))


if __name__ == "__main__":
    errs, notes, bridges = check()
    print(f"public green: {100 * green_area() / WORLD.area:.1f} %  ({green_area() / 1e4:.1f} ha of {WORLD.area / 1e4:.0f} ha)")
    print(f"errors: {len(errs)}")
    for e in errs:
        print("   ", e)
    for n, g in OPTIONS.items():
        print(f"   option {n}: +{g.area / 1e4:.1f} ha = +{100 * g.area / WORLD.area:.1f} %")
    print("biggest blocks:")
    for n in notes:
        print("   ", n)
    draw(os.path.join(OUT, "village_skeleton_v1.png"))
    draw(os.path.join(OUT, "village_skeleton_v1_zoom_park1.png"), view=(-750, -120, -400, 200), size=11)
    draw(os.path.join(OUT, "village_skeleton_v1_zoom_park2.png"), view=(440, -20, 760, 300), size=11)
    draw(os.path.join(OUT, "village_skeleton_v1_zoom_industry.png"), view=(280, -760, 760, -330), size=11)
