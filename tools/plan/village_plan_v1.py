"""Village plan v1 — step 1: layers (how the town grew), main roads, canal, railway, landmarks. No houses yet.
python3 tools/plan/village_plan_v1.py  ->  design/world/village_v1.png

~1.5 x 1.5 km round the ground (Marcel, 2026-11-09). The ground sits fairly central: it "happened" to grow there,
on the land of an old brickworks between the old core and the Victorian terraces. Orientation as before:
right = South (+x), left = North, up = East, down = West. The stadium area of world plan v5 is drawn in light lines.
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import world_plan_v5 as W

OUT = os.path.join(HERE, "../../design/world/village_v1.png")
R = 750

LAYERS = [   # (name, colour, polygon) — later layers sit on top of earlier ones
    ("Edwardian + mixed infill", "#D6A98A", [(-750, -750), (750, -750), (750, 750), (-750, 750)]),
    ("1930s semis", "#E2B48A", [(-750, -250), (-575, -255), (-560, 40), (-575, 235), (-750, 280)]),
    ("1930s semis", "#E2B48A", [(-330, 425), (300, 430), (310, 335), (-200, 335), (-290, 230)]),
    ("new build (cul-de-sacs)", "#EBD9BE", [(-750, 280), (-575, 235), (-560, 425), (-330, 425), (-300, 750), (-750, 750)]),
    ("new build (cul-de-sacs)", "#EBD9BE", [(600, 120), (750, 150), (750, 750), (-300, 750), (-330, 425), (300, 430), (480, 250)]),
    ("new build (cul-de-sacs)", "#EBD9BE", [(-750, -750), (750, -750), (750, -380), (500, -455), (200, -495), (-100, -480),
                                           (-400, -495), (-750, -585)]),
    ("Victorian terraces", "#C77B60", [(-280, -305), (280, -300), (320, -185), (305, 200), (310, 335), (-200, 335), (-290, 230),
                                       (-275, -60)]),
    ("old core", "#B8956A", [(-520, -285), (-330, -305), (-280, -200), (-272, -60), (-290, 60), (-330, 150), (-470, 175),
                             (-560, 40), (-580, -150)]),
    ("post-war estate + flats", "#9FAAB6", [(320, -185), (560, -205), (600, 120), (480, 250), (305, 200)]),
    ("industrial", "#8E8A84", [(350, -425), (720, -365), (720, -285), (560, -255), (350, -305)]),
]

CANAL = LineString([(-750, 150), (-500, 186), (-270, 179), (-120, 177), (0, 175), (120, 178), (270, 182), (480, 245), (750, 292)])
RAIL = LineString([(-750, -560), (-400, -472), (-100, -458), (200, -472), (500, -432), (750, -352)])
ROADS = {   # (points, carriageway m, kind)
    "London Road (A-road)": ([(-750, -250), (-430, -235), (-300, -292), (-150, -335), (100, -335), (300, -305), (500, -235), (750, -205)], 9, "a"),
    "High Street": ([(-430, -235), (-405, -160), (-392, -60), (-352, 20), (-300, 118), (-272, 175), (-262, 260), (-270, 420), (-255, 750)], 7, "b"),
    "Mill Road": ([(300, -305), (305, -185), (300, 60), (300, 180), (318, 400), (380, 750)], 7.5, "b"),
    "Station Road": ([(-19, -265), (-30, -350), (-55, -445)], 6.5, "c"),
    "Church Road": ([(-392, -60), (-480, -40), (-600, -60), (-750, -40)], 6.5, "c"),
    "North Road": ([(-575, 235), (-470, 175), (-352, 20)], 6.5, "c"),
    "Estate Road": ([(305, -100), (430, -120), (560, -60), (590, 60), (480, 200), (305, 120)], 6.5, "c"),
    "Canal Road": ([(305, 200), (450, 300), (600, 360), (750, 380)], 6.5, "c"),
    "Bypass": ([(750, -205), (720, 100), (650, 400), (600, 750)], 9, "a"),
}

LANDMARKS = [   # (label, centre, size (w, h) or radius, colour, shape)
    ("village green", (-447, -110), (50, 45), "#8FC27A", "rect"),
    ("church + churchyard", (-462, 0), (45, 34), "#7D7466", "rect"),
    ("library", (-345, -25), (14, 12), "#E8A33D", "rect"),
    ("village hall", (-360, -125), (22, 14), "#E8A33D", "rect"),
    ("GP + pharmacy", (-385, -205), (18, 12), "#E8A33D", "rect"),
    ("High St shops, pubs,\nfish & chips, takeaways", (-385, -150), None, None, "text"),
    ("SUPERMARKET\n+ car park", (-195, -385), (95, 55), "#5C8FC9", "rect"),
    ("petrol station", (560, -275), (40, 25), "#5C8FC9", "rect"),
    ("fire station", (150, -365), (35, 22), "#C0392B", "rect"),
    ("STATION", (-60, -470), (70, 12), "#444", "rect"),
    ("old mill (canal)", (-420, 205), (60, 25), "#7A6A5A", "rect"),
    ("Victoria Park\n+ bandstand", (-440, 320), (180, 140), "#8FC27A", "rect"),
    ("cemetery", (-660, -380), (130, 110), "#A7B89A", "rect"),
    ("primary school", (440, 40), (60, 45), "#E8A33D", "rect"),
    ("secondary school\n+ sports fields", (520, 520), (170, 130), "#8FC27A", "rect"),
    ("allotments", (240, -420), (110, 35), "#A9C47F", "rect"),
    ("flats (4–5 storeys)", (430, -170), None, None, "text"),
    ("industrial estate", (540, -330), None, None, "text"),
    ("playing fields", (-120, 520), (140, 90), "#8FC27A", "rect"),
    ("parade: shops + takeaway", (390, -60), (40, 12), "#E8A33D", "rect"),
]
BUS_STOPS = [("London Road (A-road)", f) for f in (0.15, 0.32, 0.5, 0.7, 0.88)] + [("High Street", f) for f in (0.12, 0.3, 0.5)] + \
            [("Mill Road", f) for f in (0.2, 0.45, 0.7)] + [("Estate Road", 0.5)]


def poly(ax, pts, fc, ec="none", lw=0.6, z=1, alpha=1.0, ls="-"):
    ax.add_patch(MPoly(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls))


def label(ax, x, y, t, fs=8, col="#222", w="bold", rot=0):
    ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=col, weight=w, rotation=rot, zorder=60,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.6))


def check():
    """Landmarks never on a main road, the canal or the railway."""
    errs = []
    blocked = unary_union([LineString(p).buffer(w / 2 + 2) for p, w, _ in ROADS.values()] + [CANAL.buffer(8), RAIL.buffer(6)])
    for name, (x, y), size, col, shape in LANDMARKS:
        if shape != "rect":
            continue
        g = box(x - size[0] / 2, y - size[1] / 2, x + size[0] / 2, y + size[1] / 2)
        if name == "STATION":
            continue
        if g.intersects(blocked):
            errs.append(f"{name.splitlines()[0]}: on a road / canal / railway")
    return errs


def draw():
    fig, ax = plt.subplots(figsize=(14, 14.6), dpi=120)
    ax.set_aspect("equal")
    ax.set_facecolor("#E9EFE2")
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R + 60)
    ax.set_xticks([]); ax.set_yticks([])
    seen = []
    for name, col, pts in LAYERS:
        poly(ax, pts, col, ec="white", lw=1.2, z=2, alpha=0.95)
    # the stadium area of plan v5 in light lines
    for r in W.roads.values():
        xs, ys = r.xy
        ax.plot(xs, ys, color="#fff", lw=1.0, alpha=0.8, zorder=5)
    poly(ax, list(W.PLOT.exterior.coords), "#CFE5C0", ec="#2F5B3F", lw=1.4, z=6)
    poly(ax, [(-W.HL, -W.HW), (W.HL, -W.HW), (W.HL, W.HW), (-W.HL, W.HW)], "#7DB36A", ec="white", lw=0.8, z=7)
    label(ax, 0, 0, "THE GROUND\n(plan v5)", fs=8, col="#1d4f91")
    # canal, railway, roads
    xs, ys = CANAL.buffer(6).exterior.xy
    ax.fill(xs, ys, color="#6FA8C7", zorder=8)
    for x0 in (60, 520):
        p = CANAL.interpolate(CANAL.project(Point(x0, 200)))
        ax.plot([p.x, p.x], [p.y - 7, p.y + 7], color="#3b2f22", lw=2.2, zorder=9)
    label(ax, 560, 300, "canal + 2 locks", fs=7, w="normal", col="#245")
    xs, ys = RAIL.xy
    ax.plot(xs, ys, color="#333", lw=3.2, zorder=10)
    ax.plot(xs, ys, color="white", lw=1.6, zorder=11, ls=(0, (4, 4)))
    label(ax, 380, -455, "railway", fs=7, w="normal")
    for name, (pts, w, kind) in ROADS.items():
        xs, ys = LineString(pts).xy
        ax.plot(xs, ys, color="#2f3337" if kind == "a" else "#4d5258", lw={"a": 5.5, "b": 4.0, "c": 2.6}[kind], zorder=12,
                solid_capstyle="round")
        ln = LineString(pts)
        p = ln.interpolate(0.62, normalized=True)
        q = ln.interpolate(0.62 * ln.length + 1)
        ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x))
        ang = ang - 180 if ang > 90 else (ang + 180 if ang < -90 else ang)
        ax.text(p.x, p.y, name, rotation=ang, ha="center", va="center", fontsize=6.5, color="white", weight="bold", zorder=13,
                bbox=dict(fc="#2f3337", ec="none", pad=0.4))
    # landmarks
    for name, (x, y), size, col, shape in LANDMARKS:
        if shape == "rect":
            poly(ax, [(x - size[0] / 2, y - size[1] / 2), (x + size[0] / 2, y - size[1] / 2), (x + size[0] / 2, y + size[1] / 2),
                      (x - size[0] / 2, y + size[1] / 2)], col, ec="#333", lw=0.8, z=20)
            label(ax, x, y + size[1] / 2 + 12, name, fs=7)
        else:
            label(ax, x, y, name, fs=7, w="normal")
    for name, f in BUS_STOPS:
        p = LineString(ROADS[name][0]).interpolate(f, normalized=True)
        ax.add_patch(Circle((p.x, p.y), 7, fc="#F2C230", ec="#333", lw=0.8, zorder=21))
    # what the match camera can see: fog closes at 400 m
    ax.add_patch(Circle((0, 0), 400, fc="none", ec="#666", lw=1.4, ls=(0, (6, 4)), zorder=30))
    label(ax, 0, 410, "fog closes here (400 m) — beyond: only from the air / later", fs=7, col="#555", w="normal")
    # legend
    handles = []
    names = []
    for name, col, _ in LAYERS:
        if name not in names:
            names.append(name)
            handles.append(plt.Rectangle((0, 0), 1, 1, fc=col, ec="white"))
    handles += [plt.Line2D([], [], color="#2f3337", lw=5), plt.Line2D([], [], color="#333", lw=3),
                plt.Line2D([], [], marker="o", color="none", markerfacecolor="#F2C230", markeredgecolor="#333", markersize=8)]
    names += ["main road", "railway", "bus stop"]
    ax.legend(handles, names, loc="upper left", fontsize=8, framealpha=0.92, title="VILLAGE PLAN v1 — layers", title_fontsize=9)
    for t, (x, y, rot) in {"EAST": (0, R + 40, 0), "WEST": (0, -R + 18, 0), "NORTH": (-R + 18, -140, 90), "SOUTH": (R - 18, 0, 90)}.items():
        ax.text(x, y, t, ha="center", va="center", fontsize=10, weight="bold", rotation=rot, zorder=70,
                bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.plot([520, 720], [-725, -725], color="#222", lw=3, zorder=70)
    ax.text(620, -710, "200 m", ha="center", fontsize=9, zorder=70)
    plt.tight_layout()
    plt.savefig(OUT, dpi=120)


if __name__ == "__main__":
    errs = check()
    print("errors:", len(errs))
    for e in errs:
        print("  ", e)
    draw()
    print("saved", OUT)
