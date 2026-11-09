"""Line plan v2 of the home ground + its edge of the village (2D top view, metres).
python3 tools/plan/world_plan_v2.py  ->  design/world/plan_v2.png + design/world/plan_v2_growth.png

Orientation as the top-down renders: right = South (+x), left = North, up = East (far side), down = West (camera side,
main stand). North = home end / hard core (Marcel). Fans come out of the streets: every junction on the edge of the
ground is an approach route (Marcel). Sections: 0..8 East, 9..17 West, 18..22 North (18 = East-most), 23..27 South.
"""
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon as MPoly
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "../../design/world")

HL, HW = 52.5, 34.0
SW = 11.5
FRONT = 2.9
MAX_X, MAX_Y = 125.0, 105.0
MAST_D = 15.0
ST, PV = 7.0, 1.8            # carriageway, pavement
HOUSE, YARD, ALLEY = 8.0, 7.0, 2.0

C = {"bg": "#EEF3E8", "pitch": "#7DB36A", "stand": "#9AA3AD", "away": "#D9534F", "max": "#3B6FB6", "fac": "#E8A33D",
     "facedge": "#8a5a12", "road": "#555B61", "pave": "#C8C2B5", "hard": "#D8D2C4", "house": "#B5654A", "yard": "#DCE9CF",
     "water": "#6FA8C7", "ground": "#CFE5C0", "tow": "#B9A27A", "tree": "#4F8A3F", "path": "#E2D6B8"}

# ---------------------------------------------------------------- the ground's plot: irregular, holds the max footprint
PLOT = Polygon([(-118, -116), (38, -112), (44, -150), (140, -150), (140, -112), (132, -100), (130, 70), (140, 82),
                (138, 112), (118, 111), (-60, 110), (-136, 106), (-140, 40), (-152, 0), (-136, -60), (-136, -95)])
assert PLOT.contains(sbox(-MAX_X, -MAX_Y, MAX_X, MAX_Y))

# ---------------------------------------------------------------- streets (centrelines); junctions on the edge = approach routes
STREETS = {
    "High Road": [(-260, -128), (-128, -126), (0, -123), (30, -122), (40, -140), (60, -162), (147, -166), (260, -170)],
    "Gate Street": [(0, -123), (-4, -190), (-16, -265)],
    "Mill Lane": [(-128, -126), (-168, -186), (-196, -265)],
    "North Street": [(-128, -126), (-146, -62), (-161, 0), (-153, 60), (-150, 122), (-162, 200)],
    "Chapel Row": [(-161, 0), (-210, 6), (-265, -4)],
    "Canal Street": [(-150, 122), (-60, 128), (60, 131), (151, 133), (260, 140)],
    "South Street": [(147, -265), (147, -166), (150, -40), (151, 60), (151, 133), (146, 200)],
    "Lock Lane": [(147, -60), (205, -66), (265, -50)],
}
roads = {k: LineString(v) for k, v in STREETS.items()}
road_area = unary_union([r.buffer(ST / 2 + PV, cap_style=2, join_style=2) for r in roads.values()])
carriage = unary_union([r.buffer(ST / 2, cap_style=2, join_style=2) for r in roads.values()])
canal = LineString([(-265, 182), (-120, 172), (0, 168), (110, 176), (200, 190), (265, 186)])
canal_area = canal.buffer(6.0, cap_style=2)
tow_area = canal.buffer(10.0, cap_style=2, single_sided=False).difference(canal_area)
VIEW = sbox(-265, -265, 265, 230)

# houses: a band on both sides of every street (fronts on the pavement), yards behind, with ginnels every ~45 m
house_bands, yard_bands = [], []
for r in roads.values():
    for side in (1, -1):
        f = r.offset_curve(side * (ST / 2 + PV + HOUSE / 2), join_style=2)
        y = r.offset_curve(side * (ST / 2 + PV + HOUSE + YARD / 2), join_style=2)
        hb = f.buffer(HOUSE / 2, cap_style=2, join_style=2)
        yb = y.buffer(YARD / 2, cap_style=2, join_style=2)
        # ginnels
        L = r.length
        cuts = []
        d = 22.0
        while d < L:
            p = r.interpolate(d)
            p2 = r.interpolate(min(d + 1, L))
            ang = math.atan2(p2.y - p.y, p2.x - p.x)
            nx, ny = -math.sin(ang), math.cos(ang)
            cuts.append(LineString([(p.x - nx * 40, p.y - ny * 40), (p.x + nx * 40, p.y + ny * 40)]).buffer(1.5))
            d += 45.0
        cut = unary_union(cuts)
        house_bands.append(hb.difference(cut))
        yard_bands.append(yb.difference(cut))
blocked = unary_union([PLOT.buffer(1.0), road_area, canal.buffer(12.0)])
houses = unary_union(house_bands).difference(blocked).intersection(VIEW)
yards = unary_union(yard_bands).difference(blocked).difference(unary_union(house_bands)).intersection(VIEW)

# ---------------------------------------------------------------- drawing helpers
def poly(ax, g, fc, ec="none", lw=0.5, z=1, alpha=1.0, ls="-", hatch=None):
    gs = getattr(g, "geoms", [g])
    for p in gs:
        if p.is_empty or p.geom_type != "Polygon":
            continue
        ax.add_patch(MPoly(list(p.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls, hatch=hatch))
        for hole in p.interiors:
            ax.add_patch(MPoly(list(hole.coords), closed=True, fc=C["bg"], ec="none", zorder=z))


def rect(ax, x0, y0, x1, y1, fc, ec="none", lw=1, z=1, ls="-", alpha=1.0, hatch=None):
    ax.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0), fc=fc, ec=ec, lw=lw, zorder=z,
                           ls=ls, alpha=alpha, hatch=hatch))


def fac(ax, x0, y0, x1, y1, text, tx=None, ty=None, fs=9.5, ha="center", col=None, z=14):
    rect(ax, x0, y0, x1, y1, col or C["fac"], ec=C["facedge"], lw=1, z=z)
    if text:
        ax.text((x0 + x1) / 2 if tx is None else tx, (y0 + y1) / 2 if ty is None else ty, text, ha=ha, va="center",
                fontsize=fs, zorder=30, weight="bold", color="#222",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))


def note(ax, x, y, text, fs=9, col="#333", ha="center", w="bold"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=col, zorder=31, weight=w,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))


def trees(ax, region, spacing=7.5, seed=1, z=9):
    import random
    rr = random.Random(seed)
    minx, miny, maxx, maxy = region.bounds
    y = miny
    from shapely.geometry import Point
    while y < maxy:
        x = minx + (rr.random() * spacing)
        while x < maxx:
            px, py = x + rr.uniform(-2, 2), y + rr.uniform(-2, 2)
            if region.contains(Point(px, py)):
                ax.add_patch(Circle((px, py), rr.uniform(2.4, 3.6), fc=C["tree"], ec="#3a6a2e", lw=0.4, alpha=0.9, zorder=z))
            x += spacing
        y += spacing * 0.87


def pitch(ax, z=6):
    rect(ax, -HL - 3, -HW - 3, HL + 3, HW + 3, C["pitch"], z=z)
    rect(ax, -HL, -HW, HL, HW, "none", ec="white", lw=1.2, z=z + 1)
    ax.plot([0, 0], [-HW, HW], color="white", lw=1.0, zorder=z + 1)
    ax.add_patch(Circle((0, 0), 9.15, fc="none", ec="white", lw=1.0, zorder=z + 1))
    for s in (-1, 1):
        rect(ax, s * HL, -20.16, s * (HL - 16.5), 20.16, "none", ec="white", lw=1.0, z=z + 1)


def stands(ax, west, east, north, south, z=8, sections=False):
    """Stand bands by depth (m) per side, from the stand front line outwards."""
    yW, yE, xN, xS = -HW - FRONT, HW + FRONT, -HL - FRONT, HL + FRONT
    L = 4.5 * SW
    S = 2.5 * SW
    if west:
        rect(ax, -L, yW, L, yW - west, C["stand"], ec="#6d757d", lw=0.8, z=z)
    if east:
        rect(ax, -L, yE, L, yE + east, C["stand"], ec="#6d757d", lw=0.8, z=z)
    if north:
        rect(ax, xN, -S, xN - north, S, C["stand"], ec="#6d757d", lw=0.8, z=z)
    if south:
        rect(ax, xS, -S, xS + south, S, C["stand"], ec="#6d757d", lw=0.8, z=z)


def masts(ax, z=15, roof=False):
    dd = MAST_D / math.sqrt(2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mx, my = sx * (HL + dd), sy * (HW + dd)
            if roof:
                continue
            rect(ax, mx - 2, my - 2, mx + 2, my + 2, "#222", z=z)


def base(ax, xlim, ylim):
    ax.set_aspect("equal")
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.set_yticks([])


# ================================================================ MAIN PLAN (early stage)
fig, ax = plt.subplots(figsize=(15, 13.6), dpi=125)
base(ax, (-250, 250), (-255, 215))

poly(ax, yards, C["yard"], ec="#a9bf98", lw=0.3, z=2)
poly(ax, houses, C["house"], ec="#7a3f2d", lw=0.4, z=3)
poly(ax, road_area, C["pave"], z=4)
poly(ax, carriage, C["road"], z=5)
poly(ax, tow_area.intersection(VIEW), C["tow"], z=3)
poly(ax, canal_area.intersection(VIEW), C["water"], z=4)
note(ax, -200, 175, "canal", fs=9, col="#245")
for name, pts in STREETS.items():
    r = roads[name]
    p = r.interpolate(0.5, normalized=True)
    p2 = r.interpolate(0.5 + 0.01, normalized=True)
    ang = math.degrees(math.atan2(p2.y - p.y, p2.x - p.x))
    if ang > 90:
        ang -= 180
    if ang < -90:
        ang += 180
    if name in ("Gate Street", "Mill Lane", "Chapel Row", "Lock Lane", "High Road"):
        p = r.interpolate(0.78 if name != "High Road" else 0.2, normalized=True)
    ax.text(p.x, p.y, name.upper(), rotation=ang, ha="center", va="center", fontsize=6.5, color="white", weight="bold", zorder=6)

# the plot
poly(ax, PLOT, C["ground"], ec="#2F5B3F", lw=2.4, z=6)
rect(ax, -MAX_X, -MAX_Y, MAX_X, MAX_Y, "none", ec=C["max"], lw=1.8, z=20, ls=(0, (6, 4)))
note(ax, -60, MAX_Y - 5, "max stadium line (every shape fits) — inside it everything is temporary", fs=8, col=C["max"], w="normal")

pitch(ax, z=7)
stands(ax, west=16, east=8, north=4, south=4, z=8)
# away sections 23 + 24 and the SE corner
for k in (0, 1):
    y0 = (1.5 - k) * SW
    rect(ax, HL + FRONT, y0, HL + FRONT + 4, y0 + SW, "#F4C7C5", ec=C["away"], lw=1.4, z=9)
rect(ax, HL + FRONT, HW + FRONT, HL + FRONT + 12, HW + FRONT + 12, "#F4C7C5", ec=C["away"], lw=1.2, z=9, ls="--", alpha=0.8)
note(ax, HL + 10, 8, "away\n23–24\n+ corner", fs=7.5, col=C["away"])
note(ax, 0, -44, "MAIN STAND (tunnel)", fs=7.5)
note(ax, 0, 41, "SHED", fs=7.5)
note(ax, -HL - 12, -2, "HOME\nEND", fs=8, col="#1d4f91")

# ---- hard standing + walkways (approach routes from the junctions)
walk = unary_union([
    LineString([(0, -118), (0, -60)]).buffer(4),                                    # main approach (Gate Street junction)
    LineString([(-124, -112), (-96, -84), (-72, -40)]).buffer(4),                    # home approach (Mill Lane / High Road junction)
    LineString([(-146, 0), (-72, 0)]).buffer(4),                                     # home approach 2 (Chapel Row junction)
    LineString([(-72, -50), (-72, 46), (-40, 50), (40, 50)]).buffer(3),              # concourse round the home end, behind the Shed
    LineString([(-60, -60), (60, -60)]).buffer(3.5),                                 # concourse behind the main stand
])
poly(ax, walk.intersection(PLOT), C["path"], ec="#c8b98f", lw=0.5, z=10)
away_walk = LineString([(136, 97), (110, 92), (80, 64), (68, 46), (62, 30)]).buffer(3)
poly(ax, away_walk.intersection(PLOT), "#F7D9D7", ec=C["away"], lw=1.0, z=10)
ax.plot([138, 104, 74, 64], [104, 100, 72, 50], color=C["away"], lw=1.5, ls="--", zorder=11)    # segregation fence

# ---- facilities (early)
# West: the club's front door
fac(ax, -9, -118, 9, -111, "gate arch + club sign + flags", ty=-108, fs=8)
fac(ax, -16, -104, -11, -99, "tickets", tx=-26, ty=-101.5, fs=8)
fac(ax, -18, -114, -13, -111, "", col="#777")
note(ax, -30, -113, "bikes", fs=7.5, w="normal")
for i in range(3):
    fac(ax, 8 + i * 8, -96, 14 + i * 8, -90, "", col="#F2D6A2")
note(ax, 26, -86, "merch tents", fs=8)
note(ax, 9, -103, "programmes", fs=7.5, w="normal")
fac(ax, -9, -70, -2, -63, "", )
fac(ax, 2, -70, 9, -63, "")
note(ax, 0, -75, "home turnstiles", fs=7.5)
fac(ax, -34, -70, -18, -62, "changing rooms", ty=-74, fs=7.5)
fac(ax, 18, -70, 32, -64, "boardroom", ty=-74, fs=7.5)
rect(ax, -6, -57, 6, -54, "#3B6FB6", z=14)
note(ax, 0, -51, "team bus", fs=7.5, w="normal")
# clubhouse between the two home approaches, beer garden
fac(ax, -70, -100, -44, -86, "CLUBHOUSE\n+ bar", fs=8)
rect(ax, -44, -100, -32, -88, C["path"], ec="#c8b98f", lw=0.5, z=12)
note(ax, -38, -105, "beer garden", fs=6.5, w="normal")
# North: home end catering + turnstiles
fac(ax, -82, -6, -76, 6, "chip van", tx=-92, ty=12, fs=8)
fac(ax, -82, -30, -76, -22, "tea hut", tx=-92, ty=-26, fs=8)
fac(ax, -84, 24, -76, 34, "toilets", tx=-94, ty=29, fs=8)
fac(ax, -70, -46, -62, -40, "", )
note(ax, -58, -46, "home end\nturnstiles", fs=7, ha="left")
fac(ax, -66, -4, -62, 4, "")
# South-West: car park lobe (outside the max line: permanent) + service road to the tunnel
rect(ax, 50, -146, 136, -118, C["hard"], ec="#777", lw=1, z=12)
for i in range(30):
    ax.plot([52 + i * 2.8] * 2, [-145, -139], color="white", lw=0.5, zorder=13)
    ax.plot([52 + i * 2.8] * 2, [-125, -119], color="white", lw=0.5, zorder=13)
note(ax, 93, -132, "CAR PARK (~55)  — outside the max line, stays", fs=8)
rect(ax, 42, -118, 50, -60, C["hard"], ec="#999", lw=0.5, z=11)
rect(ax, 6, -60, 50, -54, C["hard"], ec="#999", lw=0.5, z=11)
note(ax, 64, -88, "service road\n(bus, groundsman)", fs=7, w="normal", ha="left")
fac(ax, 62, -60, 76, -50, "groundsman", ty=-45, fs=7.5)
# South: training pitch (temporary) + East: kickabout green with trees
rect(ax, 78, -44, 118, 20, "#8FBF7A", ec="white", lw=1, z=9)
note(ax, 98, -12, "training\npitch", fs=8)
note(ax, -30, 80, "kickabout green + trees", fs=8, w="normal")
trees(ax, Polygon([(-120, 58), (-30, 58), (-20, 100), (-128, 100)]), spacing=9, seed=3)
trees(ax, Polygon([(24, 58), (64, 58), (64, 100), (24, 100)]), spacing=9, seed=4)
trees(ax, Polygon([(-134, -58), (-120, -58), (-120, 100), (-138, 100)]), spacing=7, seed=5)
trees(ax, Polygon([(118, -100), (130, -100), (128, 64), (118, 64)]), spacing=7, seed=6)
# away: gate in the SE notch, kiosk + toilets as a question, coach bay on South Street
fac(ax, 132, 88, 140, 104, "", col=C["away"])
note(ax, 118, 118, "AWAY GATE", fs=8, col=C["away"])
rect(ax, 96, 74, 106, 82, "none", ec=C["away"], lw=1, ls="--", z=12)
note(ax, 101, 64, "away kiosk + wc ?", fs=7, col=C["away"], w="normal")
rect(ax, 154.5, 60, 158, 128, "#F4C7C5", ec=C["away"], lw=1, z=7)
note(ax, 170, 96, "away\ncoaches", fs=7.5, col=C["away"])
# ad boards on the street fences
for x0 in range(-112, 36, 10):
    if not (-14 < x0 < 12):
        rect(ax, x0, -114.5 + (x0 + 112) * 0.026, x0 + 8, -113.3 + (x0 + 112) * 0.026, "#C0392B", z=13)
note(ax, -60, -108, "ad boards", fs=7, col="#C0392B", w="normal")
masts(ax)
note(ax, -HL - 22, HW + 16, "mast", fs=7, w="normal")
# pub at the home junction
pub = Polygon([(-150, -150), (-132, -146), (-136, -132), (-153, -137)])
poly(ax, pub, "#E9DFC6", ec="#8a7b5a", lw=1, z=8)
note(ax, -160, -152, "PUB (hard core)", fs=8)

# approach arrows from the junctions
def arrow(x0, y0, x1, y1, col):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=32,
                arrowprops=dict(arrowstyle="-|>", color=col, lw=2.6, mutation_scale=18))
arrow(-2, -150, -2, -119, "#1d4f91")
arrow(-150, -125, -126, -113, "#1d4f91")
arrow(-185, 2, -150, 0, "#1d4f91")
arrow(178, 140, 142, 100, C["away"])

# compass, scale, key
for t, (x, y) in {"EAST": (0, 208), "WEST (camera)": (0, -248), "NORTH = HOME": (-242, -70), "SOUTH": (242, 0)}.items():
    ax.text(x, y, t, ha="center", va="center", fontsize=11, weight="bold", color="#333",
            rotation=90 if abs(x) > 200 else 0, zorder=40, bbox=dict(fc="white", ec="none", alpha=0.85))
ax.plot([150, 200], [-240, -240], color="#222", lw=3, zorder=40)
ax.text(175, -234, "50 m", ha="center", fontsize=10, zorder=40)
ax.text(-245, -212, "PLAN v2 (early stage)\nblue arrows = home fans from the junctions\nred = away route  ·  beige = walkways\n"
        "dashed blue = max stadium line\nvillage edge = schematic, next round",
        fontsize=8.5, va="top", zorder=40, bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "plan_v2.png"), dpi=125)
plt.close(fig)

# ================================================================ GROWTH STRIP
fig, axs = plt.subplots(1, 3, figsize=(18, 7.2), dpi=110)
titles = ["1. EARLY — facilities round the ground", "2. SECOND RING (~35 m stands)", "3. MAX (every shape)"]
depths = [(16, 8, 4, 4), (35, 35, 35, 35), (MAX_Y - HW - FRONT, MAX_Y - HW - FRONT, MAX_X - HL - FRONT, MAX_X - HL - FRONT)]
for i, ax in enumerate(axs):
    base(ax, (-170, 170), (-200, 145))
    poly(ax, PLOT, C["ground"], ec="#2F5B3F", lw=1.8, z=2)
    rect(ax, -MAX_X, -MAX_Y, MAX_X, MAX_Y, "none", ec=C["max"], lw=1.2, z=20, ls=(0, (5, 4)))
    rect(ax, 50, -146, 136, -118, C["hard"], ec="#777", lw=0.8, z=3)
    pitch(ax, z=4)
    stands(ax, *depths[i], z=6)
    if i < 2:
        masts(ax, z=8)
    ax.set_title(titles[i], fontsize=12, weight="bold")
    if i == 0:
        for (x0, y0, x1, y1) in ((-70, -100, -44, -86), (-34, -70, -18, -62), (18, -70, 32, -64), (-82, -6, -76, 6),
                                 (-82, -30, -76, -22), (-84, 24, -76, 34), (62, -60, 76, -50), (8, -96, 30, -90)):
            rect(ax, x0, y0, x1, y1, C["fac"], ec=C["facedge"], lw=0.8, z=9)
        rect(ax, 78, -44, 118, 20, "#8FBF7A", ec="white", z=5)
        note(ax, 0, -178, "all facilities outside, on the ground", fs=9, w="normal")
    elif i == 1:
        # what survives outside a 35 m ring: clubhouse, merch at the gate, chip van on the approach
        for (x0, y0, x1, y1) in ((-70, -100, -44, -86), (8, -96, 30, -90), (-104, -6, -98, 6)):
            rect(ax, x0, y0, x1, y1, C["fac"], ec=C["facedge"], lw=0.8, z=9)
        note(ax, 0, -178, "into the stands: turnstiles, changing rooms,\nboardroom, kiosks, toilets, groundsman · training pitch gone\n"
             "still outside: clubhouse, merch, chip van (moves out)", fs=8.5, w="normal")
    else:
        for sx in (-1, 1):
            for sy in (-1, 1):
                rect(ax, sx * (HL + FRONT), sy * (HW + FRONT), sx * MAX_X, sy * MAX_Y, "#C3C8CE", ec="#8d949b", lw=0.6, z=5, ls="--", alpha=0.6)
        note(ax, 0, -178, "light corners = only if the shape closes them\neverything inside the stands (clubhouse = bar in the main stand)\n"
             "outside: car park, away coach bay, the village · masts → roof bars", fs=8.5, w="normal")
    note(ax, 93, -132, "car park", fs=7.5, w="normal")
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "plan_v2_growth.png"), dpi=110)
print("saved plan_v2.png + plan_v2_growth.png")
