"""Village land v1 — step 1 of the rebuilt village: the land. Height, water, railway, the viewpoint + sight lines.
No roads, no houses yet. python3 tools/plan/village_land_v1.py -> design/world/village_land_v1.png

Marcel, 2026-11-09:
  option B (town ~v5 size, countryside ring, map 2.2 x 2.2 km); start the foundation again, one step at a time;
  a hill to the north-west, turned a little towards the main stand (not exactly diagonal), top 850 m from the ground;
  higher (option A: ~120-150 m), so you really look down on the town and the ground;
  a viewpoint you can reach from the town (lane + footpath), houses creeping up the lower slope;
  the railway may move; no second mill: Mill Brook runs from the hill to the mill on the canal.
Plan orientation as always: right = South (+x), up = East (+y), left = North, down = West.
Bearings in game terms: North = 0 deg, East = 90, South = 180, West = 270 (clockwise).
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
import world_plan_v5 as W
import village_plan_v1 as V

NO_WATER = os.environ.get("NO_WATER") == "1"          # Marcel: "Ik bedoelde geheel zonder water :D" — just to look at the land
NO_RIVER = os.environ.get("NO_RIVER") == "1" or NO_WATER          # Marcel (2026-11-09): "Kan je me een versie geven zonder rivier?"
OUT = os.path.join(HERE, "../../design/world/" + ("village_land_v1_no_water.png" if NO_WATER else "village_land_v1_no_river.png" if NO_RIVER
                                                     else "village_land_v1_holme_below_weir.png" if os.environ.get("HOLME_BELOW") == "1"
                                                     else "village_land_v1.png"))
R = 1100

# ---------------------------------------------------------------- the hill: a real one, not a bump
# Marcel: "Een heuvel is nooit een bijna perfect ovaal." Built from: a winding crest that rises and dips, spurs pushing
# out towards the town with combes (little valleys) between them, a separate knoll, and noise at three scales.
def _smooth(pts, n=4):
    for _ in range(n):
        out = [pts[0]]
        for a_, b_ in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a_[0] + 0.25 * b_[0], 0.75 * a_[1] + 0.25 * b_[1]), (0.25 * a_[0] + 0.75 * b_[0], 0.25 * a_[1] + 0.75 * b_[1])]
        out.append(pts[-1])
        pts = out
    return pts


# the canal follows the land in long gentle bends (Marcel: no hard kinks); same route as before
_cp = _smooth([(-R, 150 - (R - 750) * 0.14)] + list(V.CANAL.coords) + [(R, 292 + (R - 750) * 0.17)], 5)
# Marcel (2026-11-09): "Wat als ons kanaal eigenlijk een rivier met kades is?" -> a river, 20 m wide, quays mainly in the
# centre. Through the town it keeps the old course (held between quays); outside the town it meanders freely.
def _meander(pts):
    out = []
    for x, y in pts:
        d = max(0.0, -600 - x, x - 760)                 # distance beyond the town on either side
        a = min(1.0, d / 250.0) * 55.0
        out.append((x, y + a * math.sin(x / 105.0) + 0.4 * a * math.sin(x / 41.0)))
    return out


def _town_bend(pts):
    """Panel: a river keeps its big curve even between quays. One broad bend through the centre, bulging away from the ground."""
    out = []
    for x, y in pts:
        f = min(1.0, max(0.0, (x + 650) / 1400.0))
        out.append((x, y + 32.0 * math.sin(math.pi * f) ** 1.5))
    return out


# Marcel's own drawing (2026-11-09): the river enters in the west, comes down the valley to a confluence with the brook
# from the hill, runs along the ground (a strong quay with trees, benches, paths), out past the rail bridge and the dock.
# Along the ground it sits ~18 m further out than drawn so the quay fits (the ground's plot ends at y = 119).
import json as _json
# Marcel's drawing, traced pixel-for-pixel (tools/plan/marcel_water_2026-11-09.json): "We doen de rivier zo"
_MW = _json.load(open(os.path.join(HERE, "marcel_water_2026-11-09.json")))
def _away_from_ground(x):
    """Marcel: shift the river 18 m away from the ground along its stretch, for room for the ground and the green round it.
    Full 18 m from x = -260 to 330, fading out smoothly over 180 m either side (confluence and dock stay put)."""
    if -260 <= x <= 330:
        return 18.0
    d = (-260 - x) if x < -260 else (x - 330)
    f = max(0.0, 1.0 - d / 180.0)
    return 18.0 * f * f * (3 - 2 * f)


_RIVER_DRAWN = [(x, y + _away_from_ground(x)) for x, y in _MW["river"]]
CANAL_PTS = _smooth(_RIVER_DRAWN, 2)      # light smoothing only: his line stays his line                       # name kept for the code; it is the RIVER
CANAL_BASE = _smooth(CANAL_PTS[::12] + [CANAL_PTS[-1]], 3)  # the valley's line (for the insides of the bends)
RIVER_W = 20.0
BEARING = 300.0                     # deg, game compass: between West (270) and North-West (315), nearer the main stand
TOP_DIST = 850.0
TOP_H = 130.0


def bearing_vec(b):
    """Game bearing -> plan vector (plan x = South = -North, plan y = East)."""
    n, e = math.cos(math.radians(b)), math.sin(math.radians(b))
    return (-n, e)


BV = bearing_vec(BEARING)                        # from the ground towards the hill
AX = (-BV[1], BV[0])                             # roughly along the ridge
TOP = (BV[0] * TOP_DIST, BV[1] * TOP_DIST)


def P(along, out):
    """Point `along` the ridge direction and `out` beyond the 850 m line (negative = towards the town)."""
    return (TOP[0] + AX[0] * along + BV[0] * out, TOP[1] + AX[1] * along + BV[1] * out)


# crest: (along, out, height) — winds, rises to the summit by the viewpoint, dips to a saddle, rises again, fades out
CREST = [(-1500, 330, 35), (-1150, 120, 66), (-860, 180, 92), (-560, -20, 110), (-330, 90, 101), (-120, -10, 118), (60, 0, 133),
         (230, 95, 120), (430, 30, 101), (640, 170, 97), (900, 90, 86), (1200, 300, 55), (1700, 420, 20)]
# spurs pushing out towards the town: (along at the crest, along at the foot, out at the foot, foot height, width)
SPURS = [(60, 20, -330, 22, 70),          # the viewpoint spur: the lane climbs it
         (-560, -650, -300, 15, 90),
         (620, 760, -260, 18, 135)]          # broad shoulder
# combes between them, cut into the slope: (along at the head, along at the mouth, out at the mouth, depth, width)
COMBES = [(-230, -300, -380, 22, 55),      # Mill Brook rises here
          (330, 420, -330, 18, 50),
          (-900, -980, -260, 14, 60)]
KNOLL = None                                # removed (Marcel: the knoll felt odd); the spur beside it got a broad shoulder


def _noise(x, y, scale, seed):
    rng = np.random.default_rng(seed)
    g = rng.uniform(-1, 1, (64, 64))
    g[63, :] = g[0, :]                     # periodic: no seam where the grid wraps (that drew straight lines)
    g[:, 63] = g[:, 0]
    u = (x + 2 * R) / scale
    v = (y + 2 * R) / scale
    i, j = np.floor(u).astype(int) % 63, np.floor(v).astype(int) % 63
    fu, fv = u - np.floor(u), v - np.floor(v)
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a, b, c, d = g[i, j], g[i + 1, j], g[i, j + 1], g[i + 1, j + 1]
    return a * (1 - fu) * (1 - fv) + b * fu * (1 - fv) + c * (1 - fu) * fv + d * fu * fv


def _seg_param(px, py, ax_, ay_, bx_, by_):
    dx, dy = bx_ - ax_, by_ - ay_
    L2 = dx * dx + dy * dy
    t = np.clip(((px - ax_) * dx + (py - ay_) * dy) / L2, 0, 1)
    qx, qy = ax_ + t * dx, ay_ + t * dy
    return t, np.hypot(px - qx, py - qy), (px - qx) * (-dy) + (py - qy) * dx      # t, distance, signed side


def height_raw(x, y):
    x0_ = np.asarray(x, dtype=float)
    y0_ = np.asarray(y, dtype=float)
    # warp the ground plan a little so no line in the land is straight
    x = x0_ + 75 * _noise(x0_, y0_, 520, 21) + 25 * _noise(x0_, y0_, 170, 23)
    y = y0_ + 75 * _noise(x0_, y0_, 520, 22) + 25 * _noise(x0_, y0_, 170, 24)
    # main ridge: distance to the crest polyline, height interpolated along it, steep on the town side
    # nearest crest, blended softly between neighbouring stretches (a hard switch draws straight creases in the land)
    pts = [P(a_, o_) + (h_, a_) for a_, o_, h_ in CREST]
    segs = [(_seg_param(x, y, ax_, ay_, bx_, by_), ah, bh, aa, ba) for (ax_, ay_, ah, aa), (bx_, by_, bh, ba) in zip(pts[:-1], pts[1:])]
    dmin = np.min(np.stack([sg[0][1] for sg in segs]), axis=0)
    wsum = np.zeros(x.shape); hsum = np.zeros(x.shape); ssum = np.zeros(x.shape); asum = np.zeros(x.shape)
    for (t, d, side), ah, bh, aa, ba in segs:
        w = np.exp(-(d - dmin) / 45.0)
        wsum += w
        hsum += w * (ah + (bh - ah) * t)
        ssum += w * np.clip(side / np.maximum(d, 1e-6), -1, 1) * np.minimum(d, 60.0) / 60.0
        asum += w * (aa + (ba - aa) * t)
    best_d, best_h, best_al = dmin, hsum / wsum, asum / wsum
    side_soft = ssum / wsum
    # town side steep, back side long; blended smoothly across the crest (no step)
    side_n = side_soft                                                                      # -1 .. 1
    town_w = 1.0 / (1.0 + np.exp(np.clip(-4.0 * side_n, -50, 50)))
    k = np.clip(np.abs(best_al - 60.0) / 380.0, 0, 1)
    k = k * k * (3 - 2 * k)                                     # 0 at the viewpoint stretch, 1 from ~380 m along
    s_town = 200.0 + 170.0 * k + 70.0 * _noise(x, y, 300, 4)   # 200 m: the wooded scarp; ~370 m: broad slopes
    s_back = 560.0 * (1.0 + 0.35 * _noise(x, y, 330, 5))       # the back is not one even slope either
    s = s_back + (s_town - s_back) * town_w
    h = best_h * np.exp(-(best_d / s) ** 1.7)
    # spurs: raise the slope along a line from the crest down to the foot
    for ca, fa, fo, fh, w in SPURS:
        A, B = P(ca, 0), P(fa, fo)
        t, d, _ = _seg_param(x, y, A[0], A[1], B[0], B[1])
        root_h = float(np.interp(ca, [c_[0] for c_ in CREST], [c_[2] for c_ in CREST])) - 6.0   # a spur starts just below the crest
        ridge_h = root_h + (fh - root_h) * t
        sp = ridge_h * np.exp(-(d / w) ** 2)
        k_ = 6.0 * np.clip(sp / 15.0, 0.01, 1.0)              # soft max only where the spur is really there
        hh_ = np.clip(0.5 + 0.5 * (sp - h) / k_, 0, 1)
        h = h + (sp - h) * hh_ + k_ * hh_ * (1 - hh_) * 0.5    # no crease where spur meets slope, no lift elsewhere
    # combes: cut little valleys in
    for ha, ma, mo, dep, w in COMBES:
        A, B = P(ha, -60), P(ma, mo)
        t, d, _ = _seg_param(x, y, A[0], A[1], B[0], B[1])
        cut = dep * np.exp(-(d / (w * (0.6 + 0.8 * t))) ** 2) * np.sin(np.pi * np.clip(t * 0.9 + 0.1, 0, 1)) * (1 - t) ** 0.7
        h = h - np.minimum(cut, h * 0.35)
    # the ground and its surroundings stay level (the stadium plan needs flat land): the hill fades out before it
    rr_ = np.hypot(x0_, y0_)
    f_ = np.clip((rr_ - 300.0) / 220.0, 0, 1)
    f_ = f_ * f_ * (3 - 2 * f_)
    h = h * f_
    # valley: the land falls ~8 m to the canal from the hill side and rises ~18 m beyond it to the map edge
    cy_ = np.interp(x0_, [c_[0] for c_ in CANAL_PTS], [c_[1] for c_ in CANAL_PTS])
    dy_ = y0_ - cy_
    tilt = np.where(dy_ < 0, 8.0 * np.clip(-dy_ / 900.0, 0, 1), 18.0 * np.clip(dy_ / 850.0, 0, 1) ** 1.3)
    # the old core on a low dry rise beside the brook (churches sit on the driest spot)
    core = 4.5 * np.exp(-((x0_ + 385.0) ** 2 + (y0_ + 60.0) ** 2) / (2 * 120.0 ** 2))
    valley = tilt + core
    h = h + valley * f_ + 4.0 * (1 - f_)                     # round the ground: one level platform at ~4 m
    # noise at three scales, stronger on the hill than in the valley
    h = _quarry(x0_, y0_, h)
    hill_ = np.clip(h / TOP_H, 0, 1)
    h = h + (0.25 + hill_) * 7 * _noise(x0_, y0_, 420, 11) + hill_ * (4 * _noise(x0_, y0_, 160, 12) + 1.5 * _noise(x0_, y0_, 55, 13)) \
        + 0.6 * _noise(x0_, y0_, 160, 12)                     # the valley stays calm: long swells, no pockmarks
    # a little swell on top so nothing is a table (Marcel: natural, gentle height differences)
    h = h + 1.6 * np.sin(x0_ / 260.0 + 0.7) * np.cos(y0_ / 310.0 - 0.3) * f_
    return np.maximum(h, 0.0)


# ---------------------------------------------------------------- old quarry (Marcel: yes) — where the town's stone came from
# an irregular bite into the slope (worked faces, a spoil tip spilling out at the front), not a shape
QUARRY = Polygon([P(-690, -150), P(-668, -168), P(-640, -160), P(-612, -178), P(-590, -150), P(-575, -118), P(-588, -92),
                  P(-570, -60), P(-602, -48), P(-630, -70), P(-655, -52), P(-684, -78), P(-702, -112)])
QUARRY_FLOOR = 45.0


def _quarry(x, y, h):
    from shapely import contains_xy, distance
    inside = contains_xy(QUARRY, x, y)
    if not inside.any():
        return h
    edge = np.zeros(x.shape)
    edge[inside] = distance(QUARRY.exterior, [Point(a, b) for a, b in zip(x[inside], y[inside])])
    floor = QUARRY_FLOOR + np.clip(8.0 - edge, 0, 8) * 2.2          # the face rises steeply in the last 8 m
    return np.where(inside & (h > floor), floor, h)


# ---------------------------------------------------------------- viewpoint
VP_DIST = 830.0                                  # just below the crest on the town side, on the viewpoint spur
def _clears(q):
    """The sight line from q to the ground stays >= 2 m above the land for its first 350 m (free view of the foreground)."""
    h0 = float(height_raw(np.array(q[0]), np.array(q[1]))) + 1.7
    d0 = math.hypot(*q)
    for f in np.linspace(0.02, 350 / d0, 30):
        x_, y_ = q[0] * (1 - f), q[1] * (1 - f)
        if float(height_raw(np.array(x_), np.array(y_))) > h0 - (h0 - 7) * f - 2:
            return False
    return True


_c = [P(a_, o_) for a_ in np.linspace(0, 120, 9) for o_ in np.linspace(-130, -10, 13)]
_c = [q for q in _c if _clears(q)] or _c
VP = max(_c, key=lambda q: float(height_raw(np.array(q[0]), np.array(q[1]))))
VP_H = float(height_raw(np.array(VP[0]), np.array(VP[1])))
EYE = VP_H + 1.7
GROUND_H = float(height_raw(np.array(0.0), np.array(0.0)))

# ---------------------------------------------------------------- canal first, then the railway follows it (option B)
# ---------------------------------------------------------------- canal: stays in the valley, carried on to the map edge
CANAL = LineString(CANAL_PTS)
# the two locks in town + a flight climbing the hill's north flank at the west end (land rises ~1 -> 18 m there)
# a river runs downhill (west -> east); it is made navigable up to the town: a lock beside a weir at x = 60 is the head of
# navigation; another weir + lock at x = 520; upstream (west) just weirs where the river comes down off the high ground
# Marcel (option A): at the ground a WEIR ONLY, no lock — boats stop there (the last wharf is just below it);
# upstream the quays are quay walls with the riverside walk. One lock + weir further downstream (x = 520).
TOWN_WEIR = CANAL.interpolate(CANAL.project(Point(60, 200)))
LOCK_X = (520,)
LOCKS = [CANAL.interpolate(CANAL.project(Point(x, 200))) for x in LOCK_X]
WEIRS = [CANAL.interpolate(CANAL.project(Point(x, 200))) for x in (-980, -660)]          # was 3 weirs within ~450 m; one removed (review, Marcel)
# water meadows: for each meander lobe outside the town, the land between the bend and the valley's line = inside of the bend
def _meadows():
    base_y = lambda x: float(np.interp(x, [c[0] for c in CANAL_BASE], [c[1] for c in CANAL_BASE]))
    pts = [(x, y) for x, y in CANAL_PTS if x < -640 or x > 800]
    out, cur, sgn = [], [], 0
    for x, y in pts + [(None, None)]:
        dv = None if x is None else y - base_y(x)
        s_ = 0 if dv is None else (1 if dv > 0 else -1)
        if cur and (s_ != sgn or x is None or abs(x - cur[-1][0]) > 30):
            if len(cur) > 3 and max(abs(c[1] - base_y(c[0])) for c in cur) > 18:
                # from the bend across the valley line and ~60 m on: the low flat land the bend has built up
                poly = Polygon(cur + [(c[0], base_y(c[0]) - sgn * 60.0) for c in cur[::-1]]).buffer(0)
                g_ = poly.buffer(8).buffer(-8).difference(LineString(CANAL_PTS).buffer(RIVER_W / 2 + 3))
                if not g_.is_empty and g_.area > 1500:
                    out += [q for q in getattr(g_, "geoms", [g_]) if q.area > 1500]
            cur = []
        if x is None:
            break
        sgn = s_
        cur.append((x, y))
    return out


MEADOWS = _meadows()

# quays: mainly the centre, plus the mill reach and the industrial wharf (Marcel: "voornamelijk centrum, kleine stukjes daarbuiten")
QUAY_X = [(-330, 330), (-560, -470), (700, 1060)]
CONFLUENCE = tuple(_MW["mill"][-1])
MILL = None                  # set below, once the river exists (Marcel: across the water from the ground)

# railway: Marcel drew his own line (see below)
def _chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a_, b_ in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a_[0] + 0.25 * b_[0], 0.75 * a_[1] + 0.25 * b_[1]), (0.25 * a_[0] + 0.75 * b_[0], 0.25 * a_[1] + 0.75 * b_[1])]
        out.append(pts[-1])
        pts = out
    return pts


# Marcel's line (2026-11-09 sketch): along the top of the town, a long gentle curve, over the canal, out to the south
_rail_pts = [(-1100, 499), (-519, 519), (-96, 543), (95, 540), (314, 513), (505, 437), (642, 328), (778, 178), (915, 28),
             (1120, -184)]
RAIL = LineString(_chaikin(_rail_pts, 4)).intersection(box(-R, -R, R, R))
# Marcel: the station moves north along the line, nearer the edge of the town (size still not fixed)
# Marcel (2026-11-09, later): the station to the other side of the water, towards the industry — just past the rail bridge,
# between the river and the goods yard. Away fans come in from the south-east, straight to the away end.
_xb = RAIL.intersection(LineString(CANAL_PTS))
_xb = _xb if _xb.geom_type == "Point" else list(_xb.geoms)[0]
_d0 = RAIL.project(_xb)
from shapely.ops import substring as _sub
STATION = None     # placed once the industry zone exists (below)
RAIL_X_CANAL = RAIL.intersection(CANAL)
# industry moves to where railway and canal cross: a wharf on the canal + sidings off the line (zone only; layout later)
# a long strip along the south bank (quays + warehouses facing the water), from just past the lock to the map edge,
# plus a wedge of sidings along the railway south of the canal (Marcel: "iets langer langs het water")
# Marcel's outline (2026-11-09 sketch): from the rail bridge along the canal to near the map edge, down along the railway
IND_ZONE = Polygon([(703, 263), (1051, 324), (1068, 256), (1021, 164), (1058, 39), (931, -72), (792, 11), (728, 119)]).difference(
    CANAL.buffer(RIVER_W / 2 + 4))
# basin: a short arm cut into the zone, warehouses round it (the heart of the wharf)
BASIN = Polygon([(868, 318), (896, 322), (906, 205), (898, 186), (874, 184), (866, 200)])
IND_ZONE = IND_ZONE.difference(BASIN.buffer(4))
_ri = RAIL.intersection(IND_ZONE)
_ri = max(getattr(_ri, "geoms", [_ri]), key=lambda g_: g_.length)
_dm = RAIL.project(_ri.interpolate(0.5, normalized=True))
STATION = _sub(RAIL, _dm - 70, _dm + 70).buffer(15, cap_style=2)      # Marcel: middle of the industry, on the straight
FARMLAND_NOTCH = (1060, 160)      # Marcel: farmland round the bite out of the zone
# the strip beyond the railway: a small "over the tracks" neighbourhood (Marcel), up to the town edge
OVER_TRACKS_LABEL = (-150, 680)

# ---------------------------------------------------------------- Mill Brook: a spring in a fold of the hill, down to the mill
# Mill Brook (Marcel's drawing): from the wooded scarp down to the confluence; the mill sits where it meets the river
def _meanders(pts, zones, seed, step=2.0):
    """Round meanders, no kinks (Marcel: "waarom rechthoekige stukken in plaats van ronde meanders?").
    The base line is smoothed hard; the offset is a smooth wave. zones: list of (from, to, wavelength m, amplitude m) as
    fractions of the length; between zones the wave fades in/out so it joins the rest of the line softly."""
    base = LineString(_chaikin(list(pts), 3))
    L_ = base.length
    n = int(L_ / step)
    rng_ = np.random.default_rng(seed)
    phase, out = rng_.uniform(0, 6.28), []
    for i in range(n + 1):
        d = L_ * i / n
        f = d / L_
        lam, amp = 1e9, 0.0
        for a0, a1, lw, aw in zones:
            if a0 <= f <= a1:
                edge = min(f - a0, a1 - f) / max(a1 - a0, 1e-6)
                k = min(1.0, edge / 0.15)
                k = k * k * (3 - 2 * k)
                lam, amp = lw, aw * k
        # wavelength and amplitude wander a little, so no two bends are alike
        lam_i = lam * (1 + 0.45 * float(_noise(np.array(d), np.array(seed * 13.0), 140, seed)))
        amp_i = amp * (1 + 0.6 * float(_noise(np.array(d + 50), np.array(seed * 7.0), 110, seed + 1)))
        phase += 2 * math.pi * (L_ / n) / lam_i
        p = base.interpolate(d)
        q = base.interpolate(min(d + 3, L_)); r = base.interpolate(max(d - 3, 0))
        tx, ty = q.x - r.x, q.y - r.y
        T = math.hypot(tx, ty) or 1
        o = amp_i * math.sin(phase)
        out.append((p.x - ty / T * o, p.y + tx / T * o))
    return out


def _dance(pts, amp, upto, seed):
    """Small irregular twists, strongest where the brook starts in the wood, fading out by `upto` (0..1 of its length)."""
    ln = LineString(pts)
    out = []
    n = int(ln.length / 7)
    for i in range(n + 1):
        d = ln.length * i / n
        p = ln.interpolate(d)
        q = ln.interpolate(min(d + 2, ln.length))
        r = ln.interpolate(max(d - 2, 0))
        tx, ty = q.x - r.x, q.y - r.y
        L_ = math.hypot(tx, ty) or 1
        f = max(0.0, 1.0 - (d / ln.length) / upto)
        o = amp * f * (float(_noise(np.array(d * 3.1), np.array(d * 1.7 + seed), 60, seed)) +
                       0.5 * float(_noise(np.array(d * 2.3 + 7), np.array(seed * 1.0), 23, seed + 1)))
        out.append((p.x - ty / L_ * o, p.y + tx / L_ * o))
    return out


# Mill Brook (Marcel's drawing): from the wooded scarp down to the confluence; the mill sits where it meets the river.
# Marcel: the start may dance more — in a wood, on a hill, it twists round roots, rocks and bumps.
_MB = [(-738, -334), (-724, -245), (-711, -164), (-745, -95), (-724, -68), (-629, -27), (-588, 14), (-615, 48), (-601, 82),
       (-547, 103), CONFLUENCE]
SPRING = _MB[0]
# small, tight bends high up in the wood (round bumps and roots), larger and calmer ones lower down; none at the mouth
_MB = [tuple(c) for c in _MW["mill"]]          # Marcel's drawing, traced
SPRING = _MB[0]
_mbl = LineString(_MB)
_flat = _mbl.length - 110.0
_upper = _sub(_mbl, 0, _flat).simplify(45.0)               # the clough: nearly straight
_lower = _sub(_mbl, _flat, _mbl.length)
BROOK = LineString(_chaikin(list(_upper.coords) + list(_lower.coords)[1:], 2))
FALLS = [BROOK.interpolate(f, normalized=True) for f in (0.12, 0.27, 0.41, 0.55)]      # small waterfalls in the ravine
# Holme Beck: exactly Marcel's bends (incl. the S-bends on the slope) + a little dance at the top; his loop at full size
_HB = [(-615, 991), (-369, 984), (-349, 916), (-342, 820), (-308, 738), (-233, 670), (-178, 547), (-123, 437),
       (-82, 350),
       (-118, 300), (-180, 262), (-192, 218), (-140, 192), (-80, 188), (-38, 168)]   # the loop, clear of the river
# small bends at the top, round meanders between the railway and the park (Marcel: more winding), the loop itself untouched
_HB = [tuple(c) for c in _MW["holme"]]         # Marcel's drawing, traced (his bends and his loop)
# its last stretch moves up with the river so the mouth stays on it (fades out over 120 m up the beck)
_HBL = LineString(_HB)
_HB = [(x, y + _away_from_ground(x) * max(0.0, 1.0 - (_HBL.length - _HBL.project(Point(x, y))) / 120.0)) for x, y in _HB]
BROOK2 = LineString(_chaikin(_HB, 2))

# the mill: across the water from the ground, at the town weir, on a mill race (goit) that leaves the river above the weir
# and returns below it. The lane to it: "Miller's Lane" (Marcel)
_RV = LineString(CANAL_PTS)
_north = lambda x, off: (x, float(np.interp(x, [c[0] for c in CANAL_PTS], [c[1] for c in CANAL_PTS])) + off)
GOIT = LineString(_chaikin([_north(-15, RIVER_W / 2), _north(10, 24), _north(60, 26), _north(110, 26), _north(140, 22),
                            _north(160, RIVER_W / 2)], 3))
MILL = (_north(95, 40)[0], _north(95, 40)[1])
MILL_BOX = box(MILL[0] - 18, MILL[1] - 9, MILL[0] + 18, MILL[1] + 9)
# Holme Beck variant (review point 6): its mouth carried past the weir so it joins below it (not into the lock)
HOLME_BELOW = os.environ.get("HOLME_BELOW") == "1"
if HOLME_BELOW:
    _hb = list(BROOK2.coords)
    _hx0 = _hb[-1][0]
    _ext = [_north(x, 72 + 6 * math.sin(x / 40.0)) for x in np.linspace(_hx0 + 25, 185, 9)] + [_north(215, 40), _north(232, RIVER_W / 2)]
    BROOK2 = LineString(_chaikin(_hb[:-3] + [_north(_hx0 + 5, 66)] + _ext, 2))
_loop_pts = [c for c in _HB if c[1] < 330]
LOOP_PARK = Polygon(_loop_pts).buffer(0).buffer(28).difference(BROOK2.buffer(4)).difference(
    LineString(CANAL_PTS).buffer(RIVER_W / 2 + 2))
# the quay along the ground: a strong quay wall with a broad tree-lined walk, benches, paths (counts as green, Marcel)
_south = Polygon(CANAL_PTS + [(R, -R), (-R, -R)])
QUAY_WALK = LineString(CANAL_PTS).buffer(RIVER_W / 2 + 18).intersection(_south).difference(
    LineString(CANAL_PTS).buffer(RIVER_W / 2 + 1)).intersection(box(-230, -R, 200, R))

BROOKS = []
for _b in (CANAL, BROOK, BROOK2):
    _bd = np.linspace(0, _b.length, 400)
    _bp = [_b.interpolate(d_) for d_ in _bd]
    _bh = np.minimum.accumulate(np.array([float(height_raw(np.array(q.x), np.array(q.y))) for q in _bp]) - 1.5)
    BROOKS.append((np.array([(q.x, q.y) for q in _bp]), np.maximum(_bh, -0.5)))


def height(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    h = height_raw(x, y)
    flat_x, flat_y = x.ravel(), y.ravel()
    out = h.ravel().copy()
    for k_, (pts, bh_) in enumerate([] if NO_WATER else BROOKS):
        out = _carve(flat_x, flat_y, out, pts, bh_, ((45.0 if NO_RIVER else 90.0), 45.0, 55.0)[k_])
    return out.reshape(h.shape)


def _carve(flat_x, flat_y, out, pts, bh_, width=45.0):
    # nearest bed sample (chunked, so the big grid fits in memory)
    for k in range(0, flat_x.size, 20000):
        dx = flat_x[k:k + 20000, None] - pts[None, :, 0]
        dy = flat_y[k:k + 20000, None] - pts[None, :, 1]
        d2 = dx * dx + dy * dy
        i = np.argmin(d2, axis=1)
        d = np.sqrt(d2[np.arange(i.size), i])
        bed = bh_[i]
        w = np.clip(d / width, 0, 1)
        w = w * w * (3 - 2 * w)                       # 0 in the bed, 1 from 45 m out: a shallow little valley
        hh = out[k:k + 20000]
        out[k:k + 20000] = np.where(hh > bed, bed + (hh - bed) * w, hh)
    return out


# ---------------------------------------------------------------- bridges (Marcel's drawing, step 2 start; positions traced)
_BR = _json.load(open(os.path.join(HERE, "marcel_bridges_2026-11-09.json")))
_bkind = {(-502.7, 112.2): ("old stone bridge (the old crossing)", "stone"), (-236.1, 145.6): ("modern bridge (to the ground)", "modern"),
          (206.1, 147.6): ("road bridge", "road"), (672.8, 259.8): ("station bridge", "road"),
          (-107.5, 350.3): ("road bridge over Holme Beck", "road"), (-280.4, 531.9): ("rail bridge over Holme Beck", "rail")}
BRIDGES = [(_bkind[tuple(c)][0], _bkind[tuple(c)][1], tuple(c)) for c in _BR["car"]]
BRIDGES += [("footbridge", "foot", tuple(c)) for c in _BR["foot"]]
BRIDGES.append(("footpath over the weir", "foot", (TOWN_WEIR.x - 14, TOWN_WEIR.y)))

# ---------------------------------------------------------------- step 2: main roads (Marcel's sketch, traced)
_RD = _json.load(open(os.path.join(HERE, "marcel_roads_2026-11-09.json")))
MAIN_ROADS = [LineString(_chaikin([tuple(c) for c in ln], 2)) for ln in _RD["lines"]]
ROUNDABOUT = tuple(_RD["roundabout"])
# the old straight road via the station bridge is gone (Marcel): its bridge goes; the new road crosses rail and river
# by two separate bridges from different periods (Marcel)
BRIDGES = [b_ for b_ in BRIDGES if b_[0] != "station bridge"]
_mr = unary_union(MAIN_ROADS)
for _x in getattr(_mr.intersection(LineString(CANAL_PTS)), "geoms", [_mr.intersection(LineString(CANAL_PTS))]):
    if _x.geom_type == "Point" and min(Point(b_[2]).distance(_x) for b_ in BRIDGES) > 25:
        BRIDGES.append(("new road bridge (later period)", "modern", (_x.x, _x.y)))
RAIL_CROSSINGS = [q for q in getattr(_mr.intersection(RAIL), "geoms", [_mr.intersection(RAIL)]) if q.geom_type == "Point"]
# west main road becomes an ordinary road towards the old stone bridge (Marcel)
OLD_BRIDGE_LINK = LineString(_chaikin([(-312, -73), (-360, -20), (-410, 30), (-460, 75), (-500, 102)], 2))


# ---------------------------------------------------------------- the way up (proposal): a lane with two hairpins + a footpath
LANE = [P(20, -420), P(25, -330), P(45, -270), P(5, -235), P(55, -190), P(10, -150), P(50, -110), P(35, -70), VP]
FOOTPATH = [P(-10, -420), P(5, -250), P(15, -120), VP]

# ---------------------------------------------------------------- the ground: stands + compass sides
HL, HW = W.HL, W.HW
STADIUM = box(-HL - 30, -HW - 30, HL + 30, HW + 30)          # rough outline incl. stands (max)
SIDES = {"North (home end)": (-HL - 30, 0), "South": (HL + 30, 0), "East": (0, HW + 30), "West (main stand)": (0, -HW - 30)}


def visible_sides():
    """A side's outside faces you when you stand on its side of the ground; the far sides you see into, over the roofs."""
    out = []
    vx, vy = VP
    for name, (sx, sy) in SIDES.items():
        nx, ny = (np.sign(sx), 0) if sx else (0, np.sign(sy))
        facing = (vx - sx) * nx + (vy - sy) * ny > 0
        out.append((name, "outside / facade" if facing else "inside, over the roof"))
    return out


# ---------------------------------------------------------------- drawing
def main():
    n = 620
    xs = np.linspace(-R, R, n)
    ys = np.linspace(-R, R, n)
    X, Y = np.meshgrid(xs, ys)
    H = height(X, Y)
    fig = plt.figure(figsize=(16, 21), dpi=110)
    ax = fig.add_axes([0.03, 0.27, 0.94, 0.70])
    ax2 = fig.add_axes([0.07, 0.04, 0.88, 0.18])
    ax.set_aspect("equal")
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_xticks([]); ax.set_yticks([])
    cmap = LinearSegmentedColormap.from_list("land", ["#dfe8c8", "#cfdcab", "#bccb92", "#a9b97f", "#9aa874", "#8d966c"])
    ls = LightSource(azdeg=315, altdeg=40)
    rgb = ls.shade(H, cmap=cmap, vert_exag=6, blend_mode="soft", vmin=0, vmax=TOP_H)
    ax.imshow(rgb, extent=(-R, R, -R, R), origin="lower", zorder=0)
    cs = ax.contour(X, Y, H, levels=np.arange(10, 160, 10), colors="#6b5a45", linewidths=0.6, alpha=0.7, zorder=1)
    ax.contour(X, Y, H, levels=[2.5, 5, 7.5, 12.5, 15, 17.5], colors="#6b5a45", linewidths=0.35, alpha=0.45, linestyles="dotted", zorder=1)
    ax.clabel(cs, levels=np.arange(20, TOP_H + 1, 20), fmt="%d m", fontsize=7, inline=True)
    # wooded scarp (proposal): the steep top of the town side
    Hs = H.copy()
    for _ in range(4):                      # light blur so the wooded-scarp outline follows the land, not the grid
        Hs = (Hs + np.roll(Hs, 1, 0) + np.roll(Hs, -1, 0) + np.roll(Hs, 1, 1) + np.roll(Hs, -1, 1)) / 5.0
    gyy, gxx = np.gradient(Hs, ys, xs)
    slope_f = np.hypot(gxx, gyy) * np.clip((Hs - 20) / 10, 0, 1)        # continuous: the outline is a smooth line
    ax.contourf(X, Y, slope_f, levels=[0.22, 10], colors=["#5f8a4a"], alpha=0.35, zorder=1.5)
    ax.text(*P(-420, -150), "wooded scarp\n(steep)", fontsize=9,
            color="#1d3b14", style="italic", ha="center", zorder=20)
    # town edge of option B, faded, for reference
    import village_skeleton_v1 as SK      # same town edge as village_edge_v1 option B (rebuilt here: that file runs the whole v5 plan)
    pts_ = []
    for i in range(160):
        a_ = 2 * math.pi * i / 160
        r_ = 740 + 35 * math.sin(2 * a_ + 0.6) + 30 * math.sin(3 * a_ + 2.0) + 18 * math.sin(5 * a_ + 1.1)
        pts_.append((r_ * math.cos(a_), r_ * math.sin(a_)))
    tb = Polygon(pts_).union(SK.IND_POLY.buffer(15)).buffer(25).buffer(-25)
    xs_, ys_ = tb.exterior.xy
    ax.plot(xs_, ys_, color="#6b5a45", lw=1.4, ls=(0, (6, 4)), alpha=0.8, zorder=3)
    ax.text(230, -790, "town edge (option B, still to be redrawn)", fontsize=8, color="#6b5a45", rotation=0, zorder=3)
    # houses creeping up the lower slope (proposal zone: 10-40 m, inside reach of the town)
    creep = (H > 10) & (H < 40) & ((X - TOP[0]) * BV[0] + (Y - TOP[1]) * BV[1] < 60) & (np.hypot(X, Y) < 800)
    ax.contourf(X, Y, creep.astype(float), levels=[0.5, 1.5], colors=["#c98a6a"], alpha=0.30, zorder=2)
    cx, cy = P(330, -470)
    ax.text(cx, cy, "houses creep up\nthe lower slope\n(villas with a view)", fontsize=9, color="#7a3e22",
            ha="center", zorder=20, style="italic")
    # water
    from shapely.geometry import mapping
    def fill(g, fc, ec, z, lw=0.8):
        for p in getattr(g, "geoms", [g]):
            xx, yy = p.exterior.xy
            ax.fill(xx, yy, fc=fc, ec=ec, lw=lw, zorder=z)
    if NO_WATER:
        pass
    elif NO_RIVER:
        fill(CANAL.buffer(2.5), "#9cc7dc", "#3f7fa8", 5, lw=0.5)
        ax.text(-150, 225, "a small beck along the valley floor (the brooks' water has to go somewhere)", fontsize=8.5,
                color="#245", weight="bold", zorder=20, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    else:
        fill(CANAL.buffer(RIVER_W / 2), "#9cc7dc", "#3f7fa8", 5)
    for x0q, x1q in ([] if NO_RIVER else QUAY_X):
        seg = CANAL.intersection(box(x0q, -R, x1q, R))
        for g_ in getattr(seg, "geoms", [seg]):
            if g_.geom_type != "LineString":
                continue
            for side in ("left", "right"):
                o_ = g_.parallel_offset(RIVER_W / 2 + 1, side, join_style=2)
                for q_ in getattr(o_, "geoms", [o_]):
                    if q_.geom_type == "LineString":
                        qx, qy = q_.xy
                        ax.plot(qx, qy, color="#4a4a4a", lw=2.2, zorder=6)
    for W_ in ([] if NO_RIVER else WEIRS + [TOWN_WEIR]):
        ax.plot([W_.x - 8, W_.x + 8], [W_.y - 12, W_.y + 12], color="white", lw=2.5, zorder=6)
        ax.plot([W_.x - 8, W_.x + 8], [W_.y - 12, W_.y + 12], color="#3f7fa8", lw=1.0, zorder=6, ls=(0, (1, 1)))
    # main roads (Marcel's sketch) + roundabout + where they cross the railway (bridges)
    for rd in MAIN_ROADS:
        xx_, yy_ = rd.xy
        ax.plot(xx_, yy_, color="#222", lw=5.2, zorder=10.5, solid_capstyle="round")
        ax.plot(xx_, yy_, color="#f2d27a", lw=3.2, zorder=10.6, solid_capstyle="round")
    xx_, yy_ = OLD_BRIDGE_LINK.xy
    ax.plot(xx_, yy_, color="#222", lw=3.0, zorder=10.5, solid_capstyle="round")
    ax.plot(xx_, yy_, color="white", lw=1.6, zorder=10.6, solid_capstyle="round")
    ax.text(-440, -10, "ordinary road on to\nthe old stone bridge", fontsize=7.5, zorder=21, ha="center",
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    ax.add_patch(plt.Circle(ROUNDABOUT, 16, fc="#f2d27a", ec="#222", lw=1.6, zorder=10.7))
    ax.add_patch(plt.Circle(ROUNDABOUT, 7, fc="#8DBF73", ec="#222", lw=0.8, zorder=10.8))
    ax.text(ROUNDABOUT[0] - 70, ROUNDABOUT[1] + 30, "roundabout", fontsize=7.5, zorder=21, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    for q in RAIL_CROSSINGS:
        ax.add_patch(plt.Rectangle((q.x - 9, q.y - 9), 18, 18, fc="none", ec="#222", lw=1.6, zorder=10.9))
        ax.text(q.x + 14, q.y + 12, "road over rail", fontsize=7, zorder=21, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    # bridges: a deck across the nearest water, square to it
    waters = [(CANAL, RIVER_W), (BROOK, 7.0), (BROOK2, 6.0)]
    style = {"stone": ("#b49a74", "#5a4630", 9.0), "modern": ("#d9d9d9", "#333", 10.0), "road": ("#c8c3b8", "#444", 9.0),
             "rail": ("#555", "#111", 8.0), "foot": ("#8a5a2b", "#3d2a14", 3.5)}
    for name_, kind_, (bx0, by0) in BRIDGES:
        ln_, ww_ = min(waters, key=lambda w_: w_[0].distance(Point(bx0, by0)))
        dd_ = ln_.project(Point(bx0, by0))
        c_ = ln_.interpolate(dd_)
        a_ = ln_.interpolate(max(dd_ - 3, 0)); b_ = ln_.interpolate(min(dd_ + 3, ln_.length))
        tx_, ty_ = b_.x - a_.x, b_.y - a_.y
        T_ = math.hypot(tx_, ty_) or 1
        tx_, ty_ = tx_ / T_, ty_ / T_
        fc_, ec_, wd_ = style[kind_]
        half_l, half_w = ww_ / 2 + 6, wd_ / 2
        deck = Polygon([(c_.x - ty_ * half_l - tx_ * half_w, c_.y + tx_ * half_l - ty_ * half_w),
                        (c_.x - ty_ * half_l + tx_ * half_w, c_.y + tx_ * half_l + ty_ * half_w),
                        (c_.x + ty_ * half_l + tx_ * half_w, c_.y - tx_ * half_l + ty_ * half_w),
                        (c_.x + ty_ * half_l - tx_ * half_w, c_.y - tx_ * half_l - ty_ * half_w)])
        dx_, dy_ = deck.exterior.xy
        ax.fill(dx_, dy_, fc=fc_, ec=ec_, lw=1.0, zorder=11)
        if kind_ != "foot" or "weir" in name_:
            oy_ = 18 if kind_ == "rail" else (-48 if "weir" in name_ else -22)
            ax.text(c_.x + (-60 if "weir" in name_ else 18), c_.y + oy_, name_, fontsize=7.5, zorder=21,
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    # water meadows: the insides of the meander bends outside the town (where a river leaves its silt)
    for mg in ([] if NO_RIVER else MEADOWS):
        mx_, my_ = mg.exterior.xy
        ax.fill(mx_, my_, fc="#b7d8a8", ec="#6c9a55", lw=0.6, ls="--", alpha=0.75, zorder=4)
    for L in ([] if NO_RIVER else LOCKS):
        ax.plot([L.x, L.x], [L.y - 8, L.y + 8], color="#3b2f22", lw=2.5, zorder=6)
    if not NO_WATER:
        fill(BROOK.buffer(3.5), "#9cc7dc", "#3f7fa8", 5, lw=0.5)
        fill(BROOK2.buffer(3.0), "#9cc7dc", "#3f7fa8", 5, lw=0.5)
        for g_ in getattr(LOOP_PARK, "geoms", [LOOP_PARK]):
            xx_, yy_ = g_.exterior.xy
            ax.fill(xx_, yy_, fc="#8DBF73", ec="#4f7a3a", lw=0.8, alpha=0.85, zorder=4)
        ax.text(-120, 300, "park in the loop", fontsize=8, style="italic", color="#1d3b14", zorder=20, ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.2))
        for g_ in getattr(QUAY_WALK, "geoms", [QUAY_WALK]):
            xx_, yy_ = g_.exterior.xy
            ax.fill(xx_, yy_, fc="#8DBF73", ec="#4f7a3a", lw=0.6, alpha=0.85, zorder=6)
        ax.text(-10, 112, "quay walk: trees, benches, paths", fontsize=7.5, style="italic", color="#1d3b14", zorder=20, ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
        ax.text(CONFLUENCE[0] - 10, CONFLUENCE[1] + 45, "confluence\n(old crossing?)", fontsize=8, color="#245", zorder=20, ha="center",
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.2))
    qx_, qy_ = QUARRY.exterior.xy
    ax.fill(qx_, qy_, fc="#d9d2c3", ec="#6b5a45", lw=1.0, hatch="..", zorder=3)
    ax.text(QUARRY.centroid.x, QUARRY.centroid.y, "old quarry", fontsize=8, style="italic", ha="center", zorder=20, color="#3a2a1e")
    if not NO_WATER:
      ax.text(-310, 860, "Holme Beck (name: proposal)", color="#245", fontsize=8, rotation=75, weight="bold", ha="center", va="center",
            zorder=20, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    if not NO_WATER:
        fill(GOIT.buffer(3.0), "#9cc7dc", "#3f7fa8", 6, lw=0.5)
        mx_, my_ = MILL_BOX.exterior.xy
        ax.fill(mx_, my_, fc="#7A6A5A", ec="#222", lw=0.8, zorder=12)
        for f_ in FALLS:
            ax.plot([f_.x - 6, f_.x + 6], [f_.y, f_.y], color="white", lw=2.2, zorder=7)
            ax.plot([f_.x - 6, f_.x + 6], [f_.y, f_.y], color="#3f7fa8", lw=0.8, zorder=7, ls=(0, (1, 1)))
    # railway
    rx, ry = RAIL.xy
    ax.plot(rx, ry, color="#444", lw=3.2, zorder=8)
    ax.plot(rx, ry, color="white", lw=1.3, zorder=8, ls=(0, (3, 3)))
    ox, oy = V.RAIL.xy
    ax.plot(ox, oy, color="#999", lw=1.4, ls=(0, (2, 3)), zorder=4)
    sx0, sy0 = STATION.exterior.xy
    ax.fill(sx0, sy0, fc="#5c8fc9", ec="#1d4f91", lw=1.2, zorder=9)
    ax.text(STATION.centroid.x, STATION.centroid.y + 30, "STATION (size not fixed)", ha="center", fontsize=9, weight="bold",
            zorder=20, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.3))
    for g_ in getattr(IND_ZONE, "geoms", [IND_ZONE]):
        ix_, iy_ = g_.exterior.xy
        ax.fill(ix_, iy_, fc="#8E8A84", ec="#444", lw=1.0, alpha=0.35, hatch="//", zorder=4)
    ax.text(880, 80, ("INDUSTRY\nsidings off the railway\n(zone; layout later)" if NO_RIVER else "INDUSTRY\nquays on the river +\nsidings off the railway\n(zone; layout later)"),
            ha="center", fontsize=8.5, weight="bold", zorder=20, bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.3))
    ax.text(*OVER_TRACKS_LABEL, "\"over the tracks\"\nneighbourhood", ha="center", fontsize=9, style="italic", color="#7a3e22", zorder=20)
    if not NO_RIVER:
        bx_, by_ = BASIN.exterior.xy
        ax.fill(bx_, by_, fc="#BFD9E6", ec="#5f95b3", lw=0.8, zorder=6)
        ax.text(940, 230, "dock (basin)", fontsize=8, style="italic", color="#245", zorder=20)
    ax.text(*FARMLAND_NOTCH, "farmland", fontsize=8, style="italic", color="#4a3b22", zorder=20, ha="center")
    for g_ in getattr(RAIL_X_CANAL, "geoms", [RAIL_X_CANAL]):
        if g_.geom_type == "Point":
            ax.plot([g_.x], [g_.y], marker="s", ms=8, mfc="none", mec="#222", mew=1.5, zorder=12)
            ax.text(g_.x + 25, g_.y + 25, "rail bridge", fontsize=8, zorder=20)
    # the ground
    gx, gy = W.PLOT.exterior.xy
    ax.fill(gx, gy, fc="#E3EFD9", ec="#2F5B3F", lw=1.2, zorder=9)
    sx_, sy_ = STADIUM.exterior.xy
    ax.fill(sx_, sy_, fc="#b9b4aa", ec="#333", lw=0.8, zorder=10)
    ax.fill([-HL, HL, HL, -HL], [-HW, -HW, HW, HW], fc="#7DB36A", ec="white", lw=0.8, zorder=11)
    for nm, (x, y) in SIDES.items():
        ax.text(x * 1.9 if x else 0, y * 1.9 if y else 0, nm.split(" (")[0][0], ha="center", va="center", fontsize=10,
                weight="bold", color="#1d4f91", zorder=12)
    # sight lines: centre + the four corners of the ground, the view cone
    for (x, y) in [(0, 0)] + [(sx * (HL + 30), sy * (HW + 30)) for sx in (-1, 1) for sy in (-1, 1)]:
        ax.plot([VP[0], x], [VP[1], y], color="#c0392b", lw=1.6 if (x, y) == (0, 0) else 0.8,
                ls="-" if (x, y) == (0, 0) else (0, (4, 3)), zorder=13)
    d = math.hypot(*VP)
    ang = math.degrees(math.atan2(EYE - GROUND_H, d))
    look = math.atan2(-VP[1], -VP[0])
    for half in (-25, 25):
        a = look + math.radians(half)
        ax.plot([VP[0], VP[0] + math.cos(a) * 1500], [VP[1], VP[1] + math.sin(a) * 1500], color="#c0392b", lw=0.6, alpha=0.5, zorder=13)
    ax.plot([VP[0]], [VP[1]], marker="*", ms=20, color="#e8a33d", mec="#222", zorder=15)
    ax.text(VP[0] - 260, VP[1] - 170, f"VIEWPOINT\n{VP_H:.0f} m up, {d:.0f} m from the ground\nlooking down {ang:.1f} deg\n50 deg view cone",
            fontsize=9.5, weight="bold", zorder=20, bbox=dict(fc="white", ec="#c0392b", alpha=0.9, pad=0.4))
    iy, ix = np.unravel_index(np.argmax(H), H.shape)
    ax.plot([xs[ix]], [ys[iy]], marker="^", ms=12, color="#6b5a45", zorder=15)
    ax.text(xs[ix], ys[iy] - 45, f"summit {H.max():.0f} m", fontsize=9, zorder=20, ha="center")
    ax.text(-385, -60, "old core on a\nlow dry rise", fontsize=8.5, zorder=20, ha="center", style="italic", color="#3a2a1e")
    ax.text(560, 860, "the land rises gently" if NO_RIVER else "the land rises gently\nbeyond the river", fontsize=8.5, zorder=20, ha="center", style="italic", color="#3a2a1e")
    # the way up
    lx, ly = LineString(LANE).xy
    ax.plot(lx, ly, color="#8a6a3a", lw=2.4, zorder=14, solid_capstyle="round")
    fx, fy = LineString(FOOTPATH).xy
    ax.plot(fx, fy, color="#8a6a3a", lw=1.2, ls=(0, (2, 1.5)), zorder=14)
    ax.text(-120, -560, "lane up (2 hairpins)\n- - footpath (steep, direct)", fontsize=8.5, color="#5a3e1a", zorder=20,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.3))
    # labels
    def lab(x, y, t, col="#222", fs=9, rot=0):
        ax.text(x, y, t, fontsize=fs, color=col, weight="bold", ha="center", va="center", rotation=rot, zorder=20,
                bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.3))
    if not NO_WATER:
        lab(MILL[0] + 150, MILL[1] + 30, "mill + mill race\n(Miller's Lane)", col="#4a3b22", fs=8)
        lab(-760, -60, "Mill Brook: wooded clough\nwith small falls", col="#245", fs=7.5)
        lab(*SPRING, "spring", col="#245", fs=8)
    if not NO_RIVER:
        lab(520, 300, "river, 20 m · quays in the centre (dark lines)", col="#245", fs=8.5)
        lab(60, 90, "weir: head of navigation (last wharf just below)", col="#245", fs=8)
        lab(-900, 60, "weirs: the river comes down\noff the high ground", col="#245", fs=8)
    if MEADOWS and not NO_RIVER:
        m0 = max(MEADOWS, key=lambda g_: g_.area).representative_point()
        lab(m0.x, m0.y, "water meadows\n(insides of the bends)", col="#2f5f23", fs=8)
    p = RAIL.interpolate(0.18, normalized=True)
    lab(p.x, p.y + 30, "railway (Marcel's line)", fs=8.5)
    lab(150, -420, "old railway line (v5), dotted", col="#777", fs=8)
    # compass (game directions)
    cxp, cyp = 930, -930
    for t_, (dx, dy) in (("N", (-1, 0)), ("S", (1, 0)), ("E", (0, 1)), ("W", (0, -1))):
        ax.annotate("", xy=(cxp + dx * 70, cyp + dy * 70), xytext=(cxp, cyp), arrowprops=dict(arrowstyle="->", color="#222"), zorder=30)
        ax.text(cxp + dx * 95, cyp + dy * 95, t_, ha="center", va="center", fontsize=11, weight="bold", zorder=30)
    ax.plot([-R + 40, -R + 240], [-R + 40, -R + 40], color="#222", lw=3, zorder=30)
    ax.text(-R + 140, -R + 60, "200 m", ha="center", fontsize=10, zorder=30)
    vis = visible_sides()
    ax.text(-R + 15, R - 15,
            ("VILLAGE LAND v1 — VARIANT WITHOUT ANY WATER (sketch, just the land)\n" if NO_WATER else "VILLAGE LAND v1 — VARIANT WITHOUT THE RIVER (sketch)\n" if NO_RIVER else "VILLAGE LAND v1 — step 1: height, water, railway, viewpoint (no roads, no houses yet)\n") +
            f"hill: bearing {BEARING:.0f} deg (between West and North-West, turned to the main stand), winding crest with spurs and combes"
            f" · summit {H.max():.0f} m · contours every 10 m (dotted: every 2.5 m in the valley)\n"
            "from the viewpoint you see: " + " · ".join(f"{n.split(' (')[0]}: {v}" for n, v in vis),
            ha="left", va="top", fontsize=10.5, zorder=40, bbox=dict(fc="white", ec="#999", boxstyle="round,pad=0.5"))
    # ---------------- cross-section along the centre sight line
    dd = np.linspace(0, d + 400, 900)
    ux, uy = -VP[0] / d, -VP[1] / d
    px, py = VP[0] + ux * dd, VP[1] + uy * dd
    hh = height(px, py)
    ax2.fill_between(dd, 0, hh, color="#bccb92", zorder=1)
    ax2.plot(dd, hh, color="#6b5a45", lw=1.2, zorder=2)
    slope = np.abs(np.gradient(hh, dd))
    town = (np.hypot(px, py) < 760) & (np.hypot(px, py) > 290) & (hh < 45) & (slope < 0.18)   # no houses on the steep scarp
    ax2.fill_between(dd, hh, hh + 9, where=town, color="#c98a6a", alpha=0.6, zorder=3, label="houses (~9 m)")
    st = np.abs(dd - d) < 150
    ax2.fill_between(dd, hh, hh + 22, where=st, color="#7d7d7d", alpha=0.85, zorder=3, label="the ground (stands ~22 m, max)")
    ax2.plot([0, d], [EYE, GROUND_H], color="#c0392b", lw=1.5, zorder=4, label=f"sight line, {ang:.1f} deg down")
    ax2.plot([0, d + 150], [EYE, GROUND_H - math.tan(math.radians(ang)) * 150], color="#c0392b", lw=0.8, ls=(0, (4, 3)), zorder=4)
    ax2.set_xlim(0, d + 400)
    ax2.set_ylim(0, TOP_H + 25)
    ax2.set_xlabel("metres from the viewpoint, towards the ground")
    ax2.set_ylabel("height (m)")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.set_title("cross-section along the centre sight line (vertical scale stretched ~5x so you can see it)", fontsize=10)
    fig.savefig(OUT, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("saved", os.path.relpath(OUT))
    print(f"viewpoint at ({VP[0]:.0f}, {VP[1]:.0f}), {VP_H:.0f} m, {d:.0f} m out, looking down {ang:.1f} deg; ground at {GROUND_H:.1f} m")
    for nm, v in vis:
        print("  ", nm, "->", v)
    hr = [float(height(np.array(x), np.array(y))) for x, y in RAIL.coords]
    print(f"railway height range: {min(hr):.0f}-{max(hr):.0f} m")
    rb = BROOKS[0][1]
    print("river bed (west -> east):", [round(float(v), 1) for v in rb[::50]])
    hb = [float(height(np.array(x), np.array(y))) for x, y in BROOK.coords]
    print("brook heights from spring to mill:", [round(v) for v in hb])


if __name__ == "__main__":
    main()
