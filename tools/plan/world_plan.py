"""Line plan of the home ground + its surroundings (2D top view, metres).
python3 tools/plan/world_plan.py  ->  design/world/plan_v1.png

Orientation as the top-down renders: right = South (+x), left = North, up = East (far side), down = West (camera side,
main stand, High Road). Sections: 0..8 East (far), 9..17 West (near), 18..22 North end, 23..27 South end (23 = East-most).
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "../../design/world/plan_v1.png")

HL, HW = 52.5, 34.0          # pitch half sizes
SW = 11.5                    # section width
FRONT = 2.9                  # stand front line from the touch/goal line
MAX_X, MAX_Y = 125.0, 105.0  # max stadium footprint (every shape fits), half sizes
MAST_D = 15.0                # floodlight mast, diagonally out from the corner flag

C = {"pitch": "#7DB36A", "line": "white", "stand": "#9AA3AD", "away": "#D9534F", "max": "#3B6FB6",
     "fac": "#E8A33D", "road": "#555B61", "park": "#C8C2B5", "house": "#B5654A", "yard": "#DCE9CF",
     "water": "#6FA8C7", "green": "#CFE5C0", "tow": "#B9A27A"}

fig, ax = plt.subplots(figsize=(16, 13.5), dpi=130)
ax.set_aspect("equal")
ax.set_facecolor("#EEF3E8")


def rect(x0, y0, x1, y1, fc, ec="none", lw=1, z=1, ls="-", alpha=1.0, hatch=None):
    ax.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1 - x0), abs(y1 - y0), fc=fc, ec=ec, lw=lw, zorder=z,
                           ls=ls, alpha=alpha, hatch=hatch))


def label(n, x, y, z=20):
    ax.add_patch(Circle((x, y), 4.2, fc="white", ec="#222", lw=1.2, zorder=z))
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8.5, weight="bold", zorder=z + 1)


# ---------------------------------------------------------------- the village (schematic)
# streets right round the reserve; tight terraces behind them (house 8 m, yard 7 m, alley 2 m, yard, house)
ST = 7.0      # carriageway
PV = 1.8      # pavement
ring_x, ring_y = MAX_X + 8 + PV + ST / 2, MAX_Y + 8 + PV + ST / 2   # 8 m strip of the reserve outside the max footprint
for (x0, y0, x1, y1) in ((-ring_x - 60, -ring_y, ring_x + 60, -ring_y),          # High Road (West)
                         (-ring_x - 60, ring_y, ring_x + 60, ring_y),            # East street (canal side)
                         (-ring_x, -ring_y - 60, -ring_x, ring_y + 60),          # North street
                         (ring_x, -ring_y - 60, ring_x, ring_y + 60)):           # South street
    if y0 == y1:
        rect(x0, y0 - ST / 2 - PV, x1, y0 + ST / 2 + PV, C["park"], z=2)
        rect(x0, y0 - ST / 2, x1, y0 + ST / 2, C["road"], z=3)
    else:
        rect(x0 - ST / 2 - PV, y0, x0 + ST / 2 + PV, y1, C["park"], z=2)
        rect(x0 - ST / 2, y0, x0 + ST / 2, y1, C["road"], z=3)


def terrace_band(x0, x1, y_front, direction, gap_every=11, start=0):
    """Houses facing a horizontal street at y_front, going away in `direction` (+1/-1), then yard, alley, yard, houses."""
    hw, hd, yd, al = 5.0, 8.0, 7.0, 2.0
    x = x0
    k = start
    while x + hw <= x1:
        if k % gap_every == gap_every - 1:      # ginnel
            x += 3.0
            k += 1
            continue
        a = y_front
        b = a + direction * hd
        rect(x, a, x + hw - 0.15, b, C["house"], ec="#7a3f2d", lw=0.3, z=4)
        rect(x, b, x + hw - 0.15, b + direction * yd, C["yard"], ec="#9fb58f", lw=0.3, z=4)
        # back-to-back row across the alley
        c = b + direction * (yd + al)
        rect(x, c, x + hw - 0.15, c + direction * yd, C["yard"], ec="#9fb58f", lw=0.3, z=4)
        rect(x, c + direction * yd, x + hw - 0.15, c + direction * (yd + hd), C["house"], ec="#7a3f2d", lw=0.3, z=4)
        x += hw
        k += 1
    return y_front + direction * (2 * hd + 2 * yd + al)


def terrace_band_v(y0, y1, x_front, direction, gap_every=11):
    hw, hd, yd, al = 5.0, 8.0, 7.0, 2.0
    y = y0
    k = 0
    while y + hw <= y1:
        if k % gap_every == gap_every - 1:
            y += 3.0
            k += 1
            continue
        a = x_front
        b = a + direction * hd
        rect(a, y, b, y + hw - 0.15, C["house"], ec="#7a3f2d", lw=0.3, z=4)
        rect(b, y, b + direction * yd, y + hw - 0.15, C["yard"], ec="#9fb58f", lw=0.3, z=4)
        c = b + direction * (yd + al)
        rect(c, y, c + direction * yd, y + hw - 0.15, C["yard"], ec="#9fb58f", lw=0.3, z=4)
        rect(c + direction * yd, y, c + direction * (yd + hd), y + hw - 0.15, C["house"], ec="#7a3f2d", lw=0.3, z=4)
        y += hw
        k += 1


edge = ST / 2 + PV
# West: houses across the High Road (facing the gate); the pub opposite the gate
terrace_band(-ring_x - 60, -16, -ring_y - edge, -1)
terrace_band(16, ring_x + 60, -ring_y - edge, -1)
rect(-14, -ring_y - edge, 14, -ring_y - edge - 12, "#E9DFC6", ec="#8a7b5a", lw=1, z=4)
ax.text(0, -ring_y - edge - 6, "PUB", ha="center", va="center", fontsize=8, weight="bold", zorder=5)
# North + South: terraces with their fronts on the side streets
terrace_band_v(-ring_y + edge, ring_y - edge, -ring_x - edge, -1)
terrace_band_v(-ring_y + edge, ring_y - edge, ring_x + edge, 1)
# East: one row of houses whose yards back onto the canal towpath
y = ring_y + edge
x = -ring_x - 60
k = 0
while x + 5 <= ring_x + 60:
    if k % 11 != 10:
        rect(x, y, x + 4.85, y + 8, C["house"], ec="#7a3f2d", lw=0.3, z=4)
        rect(x, y + 8, x + 4.85, y + 15, C["yard"], ec="#9fb58f", lw=0.3, z=4)
        x += 5
    else:
        x += 3
    k += 1
rect(-ring_x - 60, y + 15, ring_x + 60, y + 19, C["tow"], z=3)          # towpath
rect(-ring_x - 60, y + 19, ring_x + 60, y + 31, C["water"], z=3)        # canal
ax.text(-ring_x - 30, y + 25, "canal", fontsize=9, color="white", weight="bold", va="center", zorder=5)

# ---------------------------------------------------------------- the reserve
rect(-MAX_X - 8, -MAX_Y - 8, MAX_X + 8, MAX_Y + 8, C["green"], ec="#2F5B3F", lw=2.2, z=5)          # club ground + fence
rect(-MAX_X, -MAX_Y, MAX_X, MAX_Y, "none", ec=C["max"], lw=2, z=12, ls=(0, (6, 4)))                 # max footprint
ax.text(-MAX_X + 2, MAX_Y - 3, "max stadium footprint (every shape fits)", color=C["max"], fontsize=8.5, va="top", zorder=12)

# pitch
rect(-HL - 3, -HW - 3, HL + 3, HW + 3, C["pitch"], z=6)
rect(-HL, -HW, HL, HW, "none", ec=C["line"], lw=1.4, z=7)
ax.plot([0, 0], [-HW, HW], color="white", lw=1.2, zorder=7)
ax.add_patch(Circle((0, 0), 9.15, fc="none", ec="white", lw=1.2, zorder=7))
for s in (-1, 1):
    rect(s * HL, -20.16, s * (HL - 16.5), 20.16, "none", ec="white", lw=1.2, z=7)

# section grid (current stands = early: West main stand 13-15 with tunnel, East shed 3-5)
D = 8.0
for k in range(9):
    x0 = (k - 4.5) * SW
    for side, yy, sec in ((1, HW + FRONT, k), (-1, -HW - FRONT, 9 + k)):
        built = (side == -1 and 3 <= k <= 5) or (side == 1 and 3 <= k <= 5)
        rect(x0, yy, x0 + SW, yy + side * D, C["stand"] if built else "white", ec="#7d858d", lw=0.6, z=8, alpha=0.95)
        ax.text(x0 + SW / 2, yy + side * D / 2, str(sec), ha="center", va="center", fontsize=6.5, color="#333", zorder=9)
for k in range(5):
    y0 = (1.5 - k) * SW          # k = 0 is the East-most section (Godot z-, plan up)
    for side, xx, sec in ((-1, -HL - FRONT, 18 + k), (1, HL + FRONT, 23 + k)):
        away = side == 1 and k <= 1
        rect(xx, y0, xx + side * D, y0 + SW, "#F4C7C5" if away else "white", ec=C["away"] if away else "#7d858d",
             lw=1.4 if away else 0.6, z=8)
        ax.text(xx + side * D / 2, y0 + SW / 2, str(sec), ha="center", va="center", fontsize=6.5, color="#333", zorder=9)
# the South-East corner (away option)
ax.add_patch(Polygon([(HL + FRONT, HW + FRONT), (HL + FRONT + D, HW + FRONT), (HL + FRONT + D, 2.5 * SW + 0.0),
                      (HL + FRONT, 2.5 * SW)], closed=True, fc="none", ec=C["away"], lw=1.2, ls="--", zorder=8))
ax.add_patch(Polygon([(HL + FRONT, HW + FRONT), (HL + FRONT + 12, HW + FRONT), (HL + FRONT + 12, HW + FRONT + 12),
                      (HL + FRONT, HW + FRONT + 12)], closed=True, fc="#F4C7C5", ec=C["away"], lw=1.2, ls="--", zorder=8, alpha=0.7))
ax.text(HL + FRONT + 6, HW + FRONT + 6, "SE\ncorner", ha="center", va="center", fontsize=7.5, color=C["away"], zorder=9)

# ---------------------------------------------------------------- facilities (Claude's proposal)
FW = -MAX_Y - 8           # the West fence line (street side)
# 13 car park + 14 access road (North-West, off the High Road)
rect(-118, -108, -72, -76, C["park"], ec="#777", lw=1, z=10)
for i in range(16):
    ax.plot([-116 + i * 2.8] * 2, [-107, -101], color="white", lw=0.6, zorder=11)
    ax.plot([-116 + i * 2.8] * 2, [-83, -77], color="white", lw=0.6, zorder=11)
rect(-100, FW, -92, -108, C["road"], z=10)
label(13, -85, -92)
label(14, -96, -118)
# gate drive from the High Road to the main stand (bus) + 1 gatehouse + 2 ticket booth + 17 sign + 18 flags + 16 bikes
rect(-5, FW, 5, -52, C["park"], ec="#999", lw=0.6, z=9)
rect(-9, FW - 1, 9, FW + 6, C["fac"], ec="#8a5a12", lw=1, z=11)
label(1, 0, FW + 3)
rect(-18, FW + 2, -13, FW + 7, C["fac"], ec="#8a5a12", lw=1, z=11)
label(2, -15.5, FW + 12)
label(17, 14, FW - 5)
for fx in (-6, -2, 2, 6):
    ax.add_patch(Circle((fx, FW + 12), 0.8, fc="#2F5B3F", zorder=11))
label(18, 0, FW + 18)
rect(-30, FW + 2, -22, FW + 5, "#777", z=11)
label(16, -26, FW + 10)
# 15 team bus at the tunnel (behind the West main stand), 11 changing rooms, 12 boardroom
rect(-7, -62, 7, -59, "#3B6FB6", z=11)
label(15, 0, -67)
rect(-30, -66, -12, -56, C["fac"], ec="#8a5a12", lw=1, z=11)
label(11, -21, -61)
rect(12, -64, 26, -58, C["fac"], ec="#8a5a12", lw=1, z=11)
label(12, 19, -61)
# 6 clubhouse with bar (by the car park, near the gate), 7 merch tents + 8 programme seller (on the walk in)
rect(-66, -96, -36, -82, C["fac"], ec="#8a5a12", lw=1, z=11)
label(6, -51, -89)
for i in range(3):
    rect(16 + i * 9, -96, 22 + i * 9, -90, "#F2D6A2", ec="#8a5a12", lw=0.8, z=11)
label(7, 29, -85)
label(8, 9, -100)
# 4 chip van + 5 tea hut + 9 toilet block (home end, North)
rect(-74, -6, -66, 6, C["fac"], ec="#8a5a12", lw=1, z=11)
label(4, -70, 12)
rect(-74, -26, -66, -18, C["fac"], ec="#8a5a12", lw=1, z=11)
label(5, -70, -32)
rect(-76, 22, -66, 32, C["fac"], ec="#8a5a12", lw=1, z=11)
label(9, -71, 38)
# 10 groundsman's shed (South-West, gate to the pitch)
rect(92, -82, 104, -72, C["fac"], ec="#8a5a12", lw=1, z=11)
label(10, 98, -66)
# 19 advertising boards on the street-side fence (West)
for x0 in range(-120, 120, 12):
    if not (-34 < x0 < 12) and not (-104 < x0 < -86):
        rect(x0, FW - 0.6, x0 + 9, FW + 0.6, "#C0392B", z=12)
label(19, 60, FW - 5)
# 20 floodlight masts, 15 m diagonally out from each corner flag
import math
dd = MAST_D / math.sqrt(2)
for sx in (-1, 1):
    for sy in (-1, 1):
        mx, my = sx * (HL + dd), sy * (HW + dd)
        ax.plot([sx * HL, mx], [sy * HW, my], color="#555", lw=0.8, ls=":", zorder=12)
        rect(mx - 1.5, my - 1.5, mx + 1.5, my + 1.5, "#222", z=13)
label(20, -HL - dd - 6, HW + dd + 4)
# 3 away entrance (South-East) + segregated walk + 21 away coach bay on the South street
ax_x, ax_y = MAX_X + 8, MAX_Y - 10
rect(ax_x - 3, ax_y - 6, ax_x + 1, ax_y + 6, C["away"], z=13)
label(3, ax_x - 9, ax_y + 8)
path = [(ax_x - 3, ax_y), (95, 92), (75, 68), (HL + FRONT + 14, HW + FRONT + 8), (HL + FRONT + D + 2, 14)]
xs, ys = zip(*path)
ax.plot(xs, ys, color=C["away"], lw=2.2, ls="--", zorder=12)
ax.text(96, 78, "segregated\naway walk", color=C["away"], fontsize=7.5, zorder=12)
rect(ring_x - ST / 2 - PV - 3.2, 40, ring_x - ST / 2 - PV, 100, "#F4C7C5", ec=C["away"], lw=1, z=6)
label(21, ring_x - 12, 70)

# ---------------------------------------------------------------- open questions on the plan
rect(30, -84, 112, -50, "none", ec="#888", lw=0.8, ls=":", z=9, hatch="..")
ax.text(71, -90, "free (South-West): training pitch? trees?", ha="center", fontsize=7.5, color="#555", zorder=12)
rect(-118, 40, -64, 100, "none", ec="#888", lw=0.8, ls=":", z=9, hatch="..")
ax.text(-91, 36, "free (North-East): park / trees?", ha="center", fontsize=7.5, color="#555", zorder=12)
rect(-118, -60, -84, 16, "none", ec="#888", lw=0.8, ls=":", z=9, hatch="..")
ax.text(-101, -64, "free: trees?", ha="center", fontsize=7.5, color="#555", zorder=12)

# ---------------------------------------------------------------- frame, compass, scale, legend
ax.text(0, -ring_y + 0.2, "HIGH ROAD", ha="center", va="center", fontsize=7, color="white", zorder=6, weight="bold")
ax.set_xlim(-200, 345)
ax.set_ylim(-205, 190)
ax.set_xticks([]); ax.set_yticks([])
for t, (x, y) in {"EAST (far side)": (0, 178), "WEST (camera / main stand)": (0, -196),
                  "NORTH": (-192, 0), "SOUTH": (175, 0)}.items():
    ax.text(x, y, t, ha="center", va="center", fontsize=10, weight="bold", color="#333",
            rotation=90 if t in ("NORTH", "SOUTH") else 0, zorder=30,
            bbox=dict(fc="white", ec="none", alpha=0.8))
ax.plot([-190, -140], [-185, -185], color="#222", lw=3, zorder=30)
ax.text(-165, -181, "50 m", ha="center", fontsize=9, zorder=30)

legend = ["1  gatehouse + turnstiles (home)", "2  ticket booth", "3  away entrance (South-East)", "4  chip van / burger van",
          "5  tea hut", "6  clubhouse with bar", "7  merchandise tents (3)", "8  programme seller", "9  toilet block",
          "10 groundsman's shed", "11 changing rooms (until the main stand has them)", "12 boardroom / portakabin",
          "13 car park (~45 spaces)", "14 access road to the car park", "15 team bus (by the tunnel)", "16 bike racks",
          "17 club sign", "18 flagpoles", "19 advertising boards (street-side fence)", "20 floodlight masts (15 m out)",
          "21 away coach bay"]
ax.text(212, 150, "PLAN v1 — Claude's proposal\n\n" + "\n".join(legend) +
        "\n\nred = away end (23, 24, SE corner)\nvillage = placeholder, next round\nblue dashes = max stadium footprint\ngrey = stands now (early)",
        fontsize=8.3, va="top", ha="left", family="monospace", zorder=30,
        bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.6"))
plt.tight_layout()
plt.savefig(OUT, dpi=130)
print("saved", OUT)
