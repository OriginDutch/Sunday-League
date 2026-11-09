"""The neighbourhood around the ground (mockup) — an English residential area out to ~400 m.

Blender 5 (bpy). Run:  python3 build_town.py [--render top,aerial,street,canal] [--quick]
Marcel (2026-11-09): a real English neighbourhood up to the fog (~400 m), static for now (but with
room for movement later: streets and the towpath are routes), the water is Claude's pick, home ground only.
Claude's proposals in this mockup: a canal along the East side (towpath, lock, stone arch bridge,
narrowboats), a ~70 m club-ground reserve around the pitch so the biggest stadium still fits.

Axes: Blender X = along the pitch (= Godot x), Blender -Y = West / camera side (= Godot +z), Z up.
Everything is built per material into a few big meshes, trees as linked duplicates.
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix

R = random.Random(20261109)
HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "../../assets/models")
QUICK = "--quick" in sys.argv

HALF_L, HALF_W = 52.5, 34.0
RES_X, RES_Y = 125.0, 105.0          # club ground reserve (half sizes)
EDGE = 400.0                         # the world out to the fog

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, hex_, rough=0.8, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    h = hex_.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    m.diffuse_color = (*lin, 1)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


M = {
    "grass": mat("Grass", "#5E9443", 0.95),
    "grass_club": mat("Grass_Club", "#679C4A", 0.95),
    "garden": mat("Garden_Lawn", "#6FA14F", 0.95),
    "asphalt": mat("Asphalt", "#4A4C50", 0.9),
    "pavement": mat("Pavement", "#A7A49C", 0.9),
    "kerb": mat("Kerb", "#C9C6BD", 0.8),
    "line": mat("Road_Line", "#E9E6DA", 0.7),
    "brick_a": mat("Brick_Red", "#8E4A36", 0.9),
    "brick_b": mat("Brick_Brown", "#7A4A3A", 0.9),
    "brick_c": mat("Brick_Orange", "#9C5B3F", 0.9),
    "brick_d": mat("Brick_Dark", "#6B3E33", 0.9),
    "render": mat("Render_Cream", "#DCD3BD", 0.85),
    "slate": mat("Roof_Slate", "#4B5057", 0.7),
    "slate_b": mat("Roof_Slate_Warm", "#5A5450", 0.7),
    "tile": mat("Roof_Tile", "#8A4B3A", 0.8),
    "chimney": mat("Chimney", "#7B4636", 0.9),
    "pot": mat("Chimney_Pot", "#A65A3D", 0.8),
    "window": mat("Window", "#3E5A66", 0.15, 0.2),
    "frame": mat("Window_Frame", "#EDEBE4", 0.6),
    "door_red": mat("Door_Red", "#8E2B2B", 0.5),
    "door_blue": mat("Door_Blue", "#2C4C7A", 0.5),
    "door_green": mat("Door_Green", "#2F5B3F", 0.5),
    "door_black": mat("Door_Black", "#22252A", 0.5),
    "door_yellow": mat("Door_Yellow", "#C9A13A", 0.5),
    "fence": mat("Fence_Wood", "#7A5A3C", 0.9),
    "hedge": mat("Hedge", "#3F6E33", 0.95),
    "wall_low": mat("Garden_Wall", "#8A5040", 0.9),
    "water": mat("Canal_Water", "#3D5F55", 0.08, 0.0),
    "stone": mat("Stone", "#9C968A", 0.85),
    "towpath": mat("Towpath", "#A38E6A", 0.95),
    "lock_wood": mat("Lock_Gate", "#2E2A26", 0.8),
    "boat_green": mat("Boat_Green", "#2E5B43", 0.5),
    "boat_red": mat("Boat_Red", "#8C2F2B", 0.5),
    "boat_blue": mat("Boat_Blue", "#2D4F7C", 0.5),
    "boat_cream": mat("Boat_Cream", "#E2D6B5", 0.6),
    "boat_black": mat("Boat_Hull", "#1E1E20", 0.6),
    "trunk": mat("Trunk", "#5A4632", 0.9),
    "leaf_a": mat("Leaves_A", "#3E6F32", 0.9),
    "leaf_b": mat("Leaves_B", "#557F37", 0.9),
    "leaf_c": mat("Leaves_C", "#2F5A2E", 0.9),
    "soil": mat("Allotment_Soil", "#6A4E36", 0.95),
    "crop": mat("Allotment_Crop", "#6E9A3E", 0.9),
    "shed": mat("Shed_Wood", "#6B7F5A", 0.8),
    "gravel": mat("Car_Park", "#8F8A80", 0.95),
    "lamp": mat("Lamp_Post", "#2B3033", 0.5, 0.3),
    "church": mat("Church_Stone", "#B3AA96", 0.85),
    "pub_sign": mat("Pub_Sign", "#7A1F1F", 0.5),
    "palisade": mat("Club_Fence", "#2F5B3F", 0.6, 0.3),
    "pitch": mat("Pitch", "#4F8F3A", 0.95),
    "pitch_line": mat("Pitch_Line", "#F2F2F2", 0.7),
}
DOORS = ["door_red", "door_blue", "door_green", "door_black", "door_yellow"]
BRICKS = ["brick_a", "brick_b", "brick_c", "brick_d"]

# ------------------------------------------------------------------ geometry accumulators (one bmesh per material)
BMS = {}


def bm_for(key):
    if key not in BMS:
        BMS[key] = bmesh.new()
    return BMS[key]


def box(key, cx, cy, cz, sx, sy, sz, rot=0.0):
    """Axis box (rotated around Z by rot), centre (cx, cy, cz)."""
    bm = bm_for(key)
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    c, s = math.cos(rot), math.sin(rot)
    vs = []
    for dz in (-hz, hz):
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            vs.append(bm.verts.new((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for q in f:
        bm.faces.new([vs[i] for i in q])


def quad(key, pts):
    bm = bm_for(key)
    bm.faces.new([bm.verts.new(p) for p in pts])


def flat(key, x0, y0, x1, y1, z=0.0):
    quad(key, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])


def roof(key, cx, cy, z0, length, depth, rise, rot=0.0, overhang=0.25):
    """Gable roof: ridge along the local x axis (length), sloping to both long sides."""
    bm = bm_for(key)
    c, s = math.cos(rot), math.sin(rot)
    L, D = length / 2, depth / 2 + overhang

    def P(x, y, z):
        return bm.verts.new((cx + x * c - y * s, cy + x * s + y * c, z))
    a = [P(-L, -D, z0), P(L, -D, z0), P(L, 0, z0 + rise), P(-L, 0, z0 + rise)]
    b = [P(L, D, z0), P(-L, D, z0), P(-L, 0, z0 + rise), P(L, 0, z0 + rise)]
    bm.faces.new(a)
    bm.faces.new(b)
    # gable triangles (closed ends)
    bm.faces.new([P(-L, -D + overhang, z0), P(-L, 0, z0 + rise), P(-L, D - overhang, z0)])
    bm.faces.new([P(L, D - overhang, z0), P(L, 0, z0 + rise), P(L, -D + overhang, z0)])


def cyl(key, cx, cy, z0, r, h, seg=8):
    bm = bm_for(key)
    bot = [bm.verts.new((cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    top = [bm.verts.new((v.co.x, v.co.y, z0 + h)) for v in bot]
    bm.faces.new(top)
    bm.faces.new(bot[::-1])
    for k in range(seg):
        j = (k + 1) % seg
        bm.faces.new((bot[k], bot[j], top[j], top[k]))


def cone(key, cx, cy, z0, r, h, seg=8):
    bm = bm_for(key)
    bot = [bm.verts.new((cx + r * math.cos(2 * math.pi * k / seg), cy + r * math.sin(2 * math.pi * k / seg), z0)) for k in range(seg)]
    tip = bm.verts.new((cx, cy, z0 + h))
    bm.faces.new(bot[::-1])
    for k in range(seg):
        bm.faces.new((bot[k], bot[(k + 1) % seg], tip))


def local(cx, cy, rot, x, y):
    c, s = math.cos(rot), math.sin(rot)
    return cx + x * c - y * s, cy + x * s + y * c


# ------------------------------------------------------------------ houses
HOUSE_W, HOUSE_D, WALL_H = 5.0, 8.0, 5.6
SEMI_W, SEMI_D = 13.0, 9.0
TREES = []      # (x, y, scale, kind 0..1)
LAMPS = []      # (x, y, rot)
CARS = []       # (x, y, rot, colour index)
CAR_COLS = ["#B8BDC2", "#2B2F36", "#8C1F24", "#2E4E86", "#E8E6E1", "#3D5E46", "#6B6F74"]


def terrace_house(cx, cy, rot, brick, door, roofk, end_right):
    """One Victorian terrace house. Local: x along the street, -y = the street side (front)."""
    box(brick, cx, cy, WALL_H / 2, HOUSE_W, HOUSE_D, WALL_H, rot)
    roof(roofk, cx, cy, WALL_H, HOUSE_W, HOUSE_D, 2.3, rot)
    for side, has in ((-1, True), (1, end_right)):
        if not has:
            continue
        x, y = local(cx, cy, rot, side * HOUSE_W / 2, 0.6)
        box("chimney", x, y, WALL_H + 2.6, 0.7, 1.1, 1.6, rot)
        for k in (-0.2, 0.2):
            px, py = local(x, y, rot, 0, k)
            cyl("pot", px, py, WALL_H + 3.4, 0.11, 0.35, 6)
    fy = -HOUSE_D / 2 - 0.02
    dx, dy = local(cx, cy, rot, -1.5, fy)
    box(door, dx, dy, 1.05, 0.95, 0.06, 2.1, rot)
    for wx, wz, ww, wh in ((0.9, 1.5, 1.6, 1.4), (-1.35, 4.1, 1.1, 1.2), (1.1, 4.1, 1.1, 1.2)):
        x, y = local(cx, cy, rot, wx, fy)
        box("frame", x, y, wz, ww + 0.16, 0.05, wh + 0.16, rot)
        x, y = local(cx, cy, rot, wx, fy - 0.03)
        box("window", x, y, wz, ww, 0.05, wh, rot)
    by = HOUSE_D / 2 + 0.02
    for wx, wz in ((1.0, 1.5), (-1.0, 4.1)):
        x, y = local(cx, cy, rot, wx, by)
        box("window", x, y, wz, 1.0, 0.05, 1.1, rot)


def hip_roof(key, cx, cy, z0, length, depth, rise, rot, overhang=0.3):
    bm = bm_for(key)
    c, s = math.cos(rot), math.sin(rot)
    L, D = length / 2 + overhang, depth / 2 + overhang
    rh = max(L - D, 0.5)

    def P(x, y, z):
        return bm.verts.new((cx + x * c - y * s, cy + x * s + y * c, z))
    a, b, cc, d = P(-L, -D, z0), P(L, -D, z0), P(L, D, z0), P(-L, D, z0)
    e, f = P(-rh, 0, z0 + rise), P(rh, 0, z0 + rise)
    bm.faces.new((a, b, f, e))
    bm.faces.new((cc, d, e, f))
    bm.faces.new((b, cc, f))
    bm.faces.new((d, a, e))


def semi_pair(cx, cy, rot, rr):
    """1930s semi-detached pair: brick ground floor, rendered or brick upstairs, hipped roof, two bays."""
    brick = rr.choice(BRICKS)
    upper = "render" if rr.random() < 0.55 else brick
    box(brick, cx, cy, 1.4, SEMI_W, SEMI_D, 2.8, rot)
    box(upper, cx, cy, 4.2, SEMI_W, SEMI_D, 2.8, rot)
    hip_roof(rr.choice(["tile", "tile", "slate_b"]), cx, cy, 5.6, SEMI_W, SEMI_D, 2.7, rot)
    x, y = local(cx, cy, rot, 0, 0.8)
    box("chimney", x, y, 8.4, 1.0, 1.0, 1.8, rot)
    fy = -SEMI_D / 2
    for sd in (-1, 1):
        bx, by = local(cx, cy, rot, sd * 3.6, fy - 0.45)
        box(brick, bx, by, 1.4, 2.8, 0.9, 2.8, rot)
        box(upper, bx, by, 4.1, 2.8, 0.9, 2.6, rot)
        wx, wy = local(cx, cy, rot, sd * 3.6, fy - 0.92)
        box("window", wx, wy, 1.5, 2.2, 0.05, 1.4, rot)
        box("window", wx, wy, 4.2, 2.0, 0.05, 1.2, rot)
        dx, dy = local(cx, cy, rot, sd * 0.9, fy - 0.03)
        box(rr.choice(DOORS), dx, dy, 1.05, 0.95, 0.06, 2.1, rot)


# ------------------------------------------------------------------ occupancy grid (keeps houses off roads, water and each other)
GC = 1.5
GO = EDGE + 120
GN = int(2 * GO / GC)
OCC = bytearray(GN * GN)
WORLD_R = 430.0


def _cell(x, y):
    i, j = int((x + GO) / GC), int((y + GO) / GC)
    if 0 <= i < GN and 0 <= j < GN:
        return j * GN + i
    return -1


def stamp_disc(x, y, r):
    n = int(r / GC) + 1
    for dj in range(-n, n + 1):
        for di in range(-n, n + 1):
            px, py = x + di * GC, y + dj * GC
            if (px - x) ** 2 + (py - y) ** 2 <= r * r:
                c = _cell(px, py)
                if c >= 0:
                    OCC[c] = 1


def _rect_pts(cx, cy, rot, sx, sy, step=1.2):
    nu, nv = max(1, int(sx / step)), max(1, int(sy / step))
    for a in range(nu + 1):
        for b in range(nv + 1):
            yield local(cx, cy, rot, -sx / 2 + sx * a / nu, -sy / 2 + sy * b / nv)


def free_rect(cx, cy, rot, sx, sy):
    for x, y in _rect_pts(cx, cy, rot, sx, sy):
        if x * x + y * y > WORLD_R ** 2:
            return False
        c = _cell(x, y)
        if c < 0 or OCC[c]:
            return False
    return True


def stamp_rect(cx, cy, rot, sx, sy):
    for x, y in _rect_pts(cx, cy, rot, sx, sy, 0.9):
        c = _cell(x, y)
        if c >= 0:
            OCC[c] = 1


def stamp_box(x0, y0, x1, y1):
    stamp_rect((x0 + x1) / 2, (y0 + y1) / 2, 0.0, x1 - x0, y1 - y0)


def is_free(x, y):
    c = _cell(x, y)
    return c >= 0 and not OCC[c]


# ------------------------------------------------------------------ curves
def resample(pts, step=2.0):
    out = [pts[0]]
    carry = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        d = step - carry
        while d <= seg:
            t = d / seg
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
            d += step
        carry = seg - (d - step)
    if math.dist(out[-1], pts[-1]) > 0.3:
        out.append(pts[-1])
    return out


def smooth(ctrl, closed=False, step=2.0):
    """Catmull-Rom through the control points, resampled evenly."""
    P = ([ctrl[-1]] + list(ctrl) + [ctrl[0], ctrl[1]]) if closed else ([ctrl[0]] + list(ctrl) + [ctrl[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int(math.dist(p1, p2) / 1.0))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[q] + (-p0[q] + p2[q]) * t + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * t2
                                    + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * t3) for q in (0, 1)))
    out.append(tuple(ctrl[0]) if closed else tuple(ctrl[-1]))
    res = resample(out, step)
    clean = [res[0]]
    for p in res[1:]:
        if math.dist(p, clean[-1]) > 0.8:
            clean.append(p)
    return clean


def cumlen(poly):
    c = [0.0]
    for a, b in zip(poly, poly[1:]):
        c.append(c[-1] + math.dist(a, b))
    return c


def at(poly, cum, s):
    """Point + unit tangent at arc length s."""
    s = max(0.0, min(s, cum[-1] - 1e-6))
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if cum[m] <= s:
            lo = m
        else:
            hi = m
    (x0, y0), (x1, y1) = poly[lo], poly[hi]
    seg = max(cum[hi] - cum[lo], 1e-6)
    t = (s - cum[lo]) / seg
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, (x1 - x0) / seg, (y1 - y0) / seg


def normals(poly):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[max(i - 1, 0)], poly[min(i + 1, n - 1)]
        d = math.dist(a, b) or 1.0
        tx, ty = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        out.append((-ty, tx))          # left normal
    return out


def ribbon(key, poly, o0, o1, z):
    """Flat strip between left offsets o0 and o1 along the polyline."""
    bm = bm_for(key)
    ns = normals(poly)
    prev = None
    for (x, y), (nx, ny) in zip(poly, ns):
        cur = (bm.verts.new((x + nx * o0, y + ny * o0, z)), bm.verts.new((x + nx * o1, y + ny * o1, z)))
        if prev:
            f = (prev[0], cur[0], cur[1], prev[1]) if o1 > o0 else (prev[1], cur[1], cur[0], prev[0])
            bm.faces.new(f)
        prev = cur


def wall_ribbon(key, poly, off, z0, z1):
    bm = bm_for(key)
    ns = normals(poly)
    prev = None
    for (x, y), (nx, ny) in zip(poly, ns):
        cur = (bm.verts.new((x + nx * off, y + ny * off, z0)), bm.verts.new((x + nx * off, y + ny * off, z1)))
        if prev:
            bm.faces.new((prev[0], cur[0], cur[1], prev[1]))
        prev = cur


def ngon(key, pts, z):
    bm = bm_for(key)
    bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts])


# ------------------------------------------------------------------ streets
ROAD_W, PAVE_W = 7.0, 2.2
ROADS = []      # (poly, style, avenue)


def road(ctrl, style="terrace", avenue=False, closed=False, parked=True, width=ROAD_W):
    poly = smooth(ctrl, closed, 2.0)
    if not closed:
        poly = [p for p in poly if math.hypot(*p) < 470] or poly
    if closed:
        poly.append(poly[0])
    ribbon("asphalt", poly, -width / 2, width / 2, 0.05)
    ribbon("pavement", poly, width / 2, width / 2 + PAVE_W, 0.035)
    ribbon("pavement", poly, -width / 2 - PAVE_W, -width / 2, 0.035)
    for x, y in poly:
        stamp_disc(x, y, width / 2 + PAVE_W - 1.0)
    ROADS.append((poly, style, avenue, parked, width))
    return poly


def road_dressing(seed):
    rr = random.Random(seed)
    for poly, style, avenue, parked, width in ROADS:
        cum = cumlen(poly)
        s, k = rr.uniform(6, 16), 0
        while s < cum[-1] - 4:
            x, y, tx, ty = at(poly, cum, s)
            sd = 1 if k % 2 else -1
            LAMPS.append((x - ty * sd * (width / 2 + 0.6), y + tx * sd * (width / 2 + 0.6), math.atan2(ty, tx)))
            s += 30.0
            k += 1
        if avenue:
            s = rr.uniform(4, 10)
            while s < cum[-1] - 4:
                x, y, tx, ty = at(poly, cum, s)
                for sd in (-1, 1):
                    o = width / 2 + PAVE_W - 0.7
                    TREES.append((x - ty * sd * o, y + tx * sd * o, rr.uniform(0.7, 0.95), 0.3))
                s += 15.0
        if parked and style != "semi":
            s = rr.uniform(3, 8)
            while s < cum[-1] - 6:
                x, y, tx, ty = at(poly, cum, s)
                for sd in (-1, 1):
                    if rr.random() < 0.38:
                        o = width / 2 - 1.1
                        CARS.append((x - ty * sd * o, y + tx * sd * o, math.atan2(ty, tx) + (math.pi if rr.random() < 0.5 else 0), rr.randrange(len(CAR_COLS))))
                s += 6.0


def disc_flat(key, cx, cy, r, z, seg=20):
    ngon(key, [(cx + r * math.cos(math.tau * k / seg), cy + r * math.sin(math.tau * k / seg)) for k in range(seg)], z)


# ------------------------------------------------------------------ houses along a road
def houses_along(poly, side, style, seed, skip_start=10.0):
    """Walk along the road and line one side with houses (side +1 = left of the travel direction)."""
    rr = random.Random(seed)
    cum = cumlen(poly)
    total = cum[-1]
    edge = ROAD_W / 2 + PAVE_W
    s = skip_start + rr.uniform(0, 5)
    run = []

    def flush():
        for i, (cx, cy, rot, b, door, rk) in enumerate(run):
            terrace_house(cx, cy, rot, b, door, rk, i == len(run) - 1)
        run.clear()

    run_len = rr.randint(6, 16)
    brick, roofk = rr.choice(BRICKS), rr.choice(["slate", "slate", "slate_b", "tile"])
    kind = style if style != "mix" else rr.choice(["terrace", "semi"])
    while s < total - 8:
        unit, depth, front = (HOUSE_W, HOUSE_D, 2.0) if kind == "terrace" else (SEMI_W, SEMI_D, 5.5)
        x, y, tx, ty = at(poly, cum, s + unit / 2)
        nx, ny = -ty * side, tx * side
        rot = math.atan2(ny, nx) - math.pi / 2
        placed = False
        for garden in (rr.uniform(9, 14), 6.0):
            hx, hy = x + nx * (edge + front + depth / 2), y + ny * (edge + front + depth / 2)
            fx, fy = x + nx * (edge + 0.8 + (front + depth - 0.8) / 2), y + ny * (edge + 0.8 + (front + depth - 0.8) / 2)
            gx, gy = x + nx * (edge + front + depth + garden / 2), y + ny * (edge + front + depth + garden / 2)
            if free_rect(fx, fy, rot, unit - 0.3, front + depth - 0.8) and free_rect(gx, gy, rot, unit * 0.5, garden - 0.4):
                stamp_rect(fx, fy, rot, unit - 0.3, front + depth - 0.8)
                stamp_rect(gx, gy, rot, unit * 0.7, garden)
                placed = True
                break
        if not placed:
            flush()
            s += 3.0
            run_len = rr.randint(6, 16)
            if style == "mix":
                kind = rr.choice(["terrace", "semi"])
            continue
        # garden: lawn, fences, sometimes a shed and a tree
        box("garden", gx, gy, 0.03, unit, garden, 0.06, rot)
        for sx in (-unit / 2, unit / 2):
            px, py = local(gx, gy, rot, sx, 0)
            box("fence", px, py, 0.9, 0.06, garden, 1.8, rot)
        px, py = local(gx, gy, rot, 0, garden / 2)
        box("fence", px, py, 0.9, unit, 0.06, 1.8, rot)
        if rr.random() < 0.45:
            px, py = local(gx, gy, rot, rr.uniform(-unit / 4, unit / 4), rr.uniform(-garden / 4, garden / 3))
            TREES.append((px, py, rr.uniform(0.5, 0.85), rr.random()))
        if rr.random() < 0.3:
            px, py = local(gx, gy, rot, unit / 2 - 1.3, garden / 2 - 1.2)
            box("shed", px, py, 1.0, 2.0, 1.6, 2.0, rot)
        wx, wy = x + nx * (edge + 0.15), y + ny * (edge + 0.15)
        if kind == "terrace":
            b = brick if rr.random() > 0.12 else rr.choice(BRICKS + ["render"])
            run.append((hx, hy, rot, b, rr.choice(DOORS), roofk))
            box("wall_low", wx, wy, 0.4, unit - 1.2, 0.25, 0.8, rot)
            s += unit
            if len(run) >= run_len:
                flush()
                s += rr.uniform(2.5, 4.0)          # a ginnel between two terraces
                run_len = rr.randint(6, 16)
                brick, roofk = rr.choice(BRICKS), rr.choice(["slate", "slate", "slate_b", "tile"])
                if style == "mix" and rr.random() < 0.35:
                    kind = "semi"
        else:
            semi_pair(hx, hy, rot, rr)
            box("hedge", wx, wy, 0.5, unit - 3.0, 0.7, 1.0, rot)
            # driveway at the side
            dx, dy = local(x + nx * (edge + front / 2), y + ny * (edge + front / 2), rot, unit / 2 + 1.2, 0)
            box("pavement", dx, dy, 0.03, 2.6, front + 1.0, 0.04, rot)
            if rr.random() < 0.6:
                CARS.append((dx, dy, rot + math.pi / 2, rr.randrange(len(CAR_COLS))))
            s += unit + 3.5
            if style == "mix" and rr.random() < 0.2:
                kind = "terrace"
    flush()


# ------------------------------------------------------------------ the club ground (reserve)
RA, RB = 150.0, 128.0          # reserve (fence) half sizes, superellipse n=4
RING_A, RING_B = RA + 9.5, RB + 9.5


def sup(a, b, th, n=4.0):
    c, s = math.cos(th), math.sin(th)
    return (a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s))


def in_reserve(x, y, pad=0.0):
    return (abs(x) / (RA + pad)) ** 4 + (abs(y) / (RB + pad)) ** 4 <= 1.0


def reserve_outline(a=RA, b=RB, n=160):
    return resample([sup(a, b, math.tau * k / n) for k in range(n)] + [sup(a, b, 0)], 2.0)


def club_ground(variant):
    outline = reserve_outline()
    ngon("grass_club" if variant == "early" else "pavement", outline[:-1], 0.012)
    # palisade fence round the reserve, gap for the gate (West, -y)
    cum = cumlen(outline)
    s = 0.0
    while s < cum[-1]:
        x, y, tx, ty = at(outline, cum, s)
        if not (abs(x) < 14 and y < 0):
            box("palisade", x, y, 1.1, 0.12, 0.12, 2.2)
            box("palisade", x, y, 1.9, 2.5, 0.08, 0.08, math.atan2(ty, tx))
            box("palisade", x, y, 0.5, 2.5, 0.08, 0.08, math.atan2(ty, tx))
        s += 2.5
    # gate posts
    for gx in (-14, 14):
        y = -RB * (1 - (abs(gx) / RA) ** 4) ** 0.25
        box("brick_a", gx, y, 1.4, 1.0, 1.0, 2.8)
    # pitch (placeholder for the game's own pitch)
    flat("pitch", -HALF_L - 3, -HALF_W - 3, HALF_L + 3, HALF_W + 3, 0.02)
    for x0, y0, x1, y1 in ((-HALF_L, -HALF_W, HALF_L, -HALF_W), (-HALF_L, HALF_W, HALF_L, HALF_W),
                           (-HALF_L, -HALF_W, -HALF_L, HALF_W), (HALF_L, -HALF_W, HALF_L, HALF_W), (0, -HALF_W, 0, HALF_W)):
        box("pitch_line", (x0 + x1) / 2, (y0 + y1) / 2, 0.025, max(abs(x1 - x0), 0.12), max(abs(y1 - y0), 0.12), 0.01)
    rr = random.Random(77)
    if variant == "early":
        # car parks either side of the gate drive
        flat("gravel", -9, -RB + 0.5, 9, -84, 0.02)
        for x0, x1 in ((-112.0, -12.0), (12.0, 112.0)):
            flat("gravel", x0, -110, x1, -82, 0.022)
            k = x0 + 3
            while k < x1 - 3:
                for yy in (-104.5, -87.5):
                    box("line", k, yy, 0.03, 0.12, 5.0, 0.01)
                    if rr.random() < 0.55:
                        CARS.append((k + 1.4, yy, math.pi / 2, rr.randrange(len(CAR_COLS))))
                k += 2.8
        # training pitch at the South end (+x)
        flat("grass_club", 74, -36, 122, 36, 0.015)
        flat("pitch", 78, -32, 118, 32, 0.022)
        for x0, y0, x1, y1 in ((78, -32, 118, -32), (78, 32, 118, 32), (78, -32, 78, 32), (118, -32, 118, 32), (78, 0, 118, 0)):
            box("pitch_line", (x0 + x1) / 2, (y0 + y1) / 2, 0.027, max(abs(x1 - x0), 0.1), max(abs(y1 - y0), 0.1), 0.01)
        for gy in (-32, 32):
            box("pitch_line", 98, gy, 1.0, 5.0, 0.12, 0.12)
            for gx in (95.5, 100.5):
                box("pitch_line", gx, gy, 0.5, 0.12, 0.12, 1.0)
        for x0, y0, x1, y1 in ((74, -36, 122, -36), (74, 36, 122, 36), (74, -36, 74, 36), (122, -36, 122, 36)):
            for z in (0.5, 1.1):          # a low rail fence, not a wall
                box("palisade", (x0 + x1) / 2, (y0 + y1) / 2, z, max(abs(x1 - x0), 0.06), max(abs(y1 - y0), 0.06), 0.06)
            L = math.hypot(x1 - x0, y1 - y0)
            for k in range(int(L / 3) + 1):
                t = k / max(int(L / 3), 1)
                box("palisade", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.6, 0.08, 0.08, 1.2)
        # park at the North end (-x): winding path, pond, benches, lots of trees
        path = smooth([(-62, -70), (-90, -45), (-118, -30), (-128, 5), (-105, 40), (-80, 55), (-62, 75)], step=2.0)
        ribbon("towpath", path, -1.3, 1.3, 0.03)
        ngon("water", [(-100 + 16 * math.cos(math.tau * k / 28), 4 + 10 * math.sin(math.tau * k / 28)) for k in range(28)], 0.05)
        for bx, by in ((-118, -10), (-96, -14), (-84, 22)):
            box("fence", bx, by, 0.45, 1.8, 0.5, 0.15)
        n = 0
        while n < 70:
            x, y = rr.uniform(-146, -60), rr.uniform(-115, 115)
            if not in_reserve(x, y, -6) or ((x + 100) / 19) ** 2 + ((y - 4) / 13) ** 2 < 1:
                continue
            TREES.append((x, y, rr.uniform(0.9, 1.5), rr.random() * 0.95))
            n += 1
        # tree belt inside the fence
        ocum = cumlen(outline)
        s = 0.0
        while s < ocum[-1]:
            x, y, tx, ty = at(outline, ocum, s)
            ix, iy = x * 0.95, y * 0.95
            if not (abs(x) < 120 and y < -70) and not (x > 70 and abs(y) < 40):
                TREES.append((ix + rr.uniform(-2, 2), iy + rr.uniform(-2, 2), rr.uniform(0.9, 1.35), rr.random()))
            s += rr.uniform(7, 11)
        # a few by the corners of the pitch and along the car parks
        for x in range(-108, 110, 12):
            if abs(x) > 14:
                TREES.append((x, -79, 0.7, 0.3))
    else:
        # max stadium: a plaza round it, grass islands with trees in the corners, a tree row along the fence
        for sx in (-1, 1):
            for sy in (-1, 1):
                disc_flat("grass_club", sx * 120, sy * 99, 13, 0.02)
                for k in range(5):
                    TREES.append((sx * 120 + rr.uniform(-8, 8), sy * 99 + rr.uniform(-8, 8), rr.uniform(0.9, 1.3), rr.random()))
        ocum = cumlen(outline)
        s = 0.0
        while s < ocum[-1]:
            x, y, tx, ty = at(outline, ocum, s)
            if not (abs(x) < 20 and y < 0):
                TREES.append((x * 0.965, y * 0.965, 0.8, 0.3))
                disc_flat("hedge", x * 0.965, y * 0.965, 1.4, 0.05, 8)
            s += 12.0
        flat("gravel", -9, -RB + 0.5, 9, -112, 0.02)


# ------------------------------------------------------------------ canal (East side, winding)
CANAL_W = 12.0


def canal():
    poly = smooth([(-500, 190), (-300, 190), (-150, 178), (0, 172), (150, 182), (240, 194), (340, 205), (500, 195)], step=2.0)
    h = CANAL_W / 2
    ribbon("water", poly, -h, h, 0.07)
    for sd in (-1, 1):
        ribbon("stone", poly, sd * h, sd * (h + 0.7), 0.32)
        wall_ribbon("stone", poly, sd * h, 0.07, 0.32)
    ribbon("towpath", poly, -h - 0.7, -h - 4.0, 0.04)            # towpath on the stadium side (right of travel = -y)
    ribbon("grass_club", poly, h + 0.7, h + 6.0, 0.02)
    for x, y in poly:
        stamp_disc(x, y, h + 6.5)
    cum = cumlen(poly)
    rr = random.Random(5)
    # hedge behind the towpath, trees on the far bank
    s = 0.0
    while s < cum[-1]:
        x, y, tx, ty = at(poly, cum, s)
        if rr.random() < 0.7:
            o = h + 3.5
            TREES.append((x - ty * o, y + tx * o, rr.uniform(0.9, 1.3), 0.95 if rr.random() < 0.4 else rr.random() * 0.6))
        s += rr.uniform(10, 18)
    # the lock (South-East): chamber walls, two pairs of gates with balance beams
    s_lock = min(range(len(poly)), key=lambda i: abs(poly[i][0] - 290)) * 2.0
    x, y, tx, ty = at(poly, cum, s_lock)
    rot = math.atan2(ty, tx)
    for sd in (-1, 1):
        px, py = local(x, y, rot, 0, sd * (h - 2.6))
        box("stone", px, py, 0.15, 32, 1.4, 1.0, rot)
    for gxl in (-16, 16):
        for sd in (-1, 1):
            px, py = local(x, y, rot, gxl, sd * 1.7)
            box("lock_wood", px, py, 0.2, 0.4, 3.4, 2.2, rot + sd * 0.18)
            px, py = local(x, y, rot, gxl + (2.8 if gxl > 0 else -2.8), sd * (h + 1.4))
            box("lock_wood", px, py, 1.1, 5.0, 0.25, 0.25, rot)
    px, py = local(x, y, rot, 25, -h - 9)
    box("brick_b", px, py, 2.6, 7, 6, 5.2, rot)                    # lock keeper's cottage
    roof("slate", px, py, 5.2, 7, 6, 2.0, rot)
    stamp_disc(px, py, 7)
    # narrowboats moored along the towpath
    for k, sb in enumerate((120, 150, 185, 330, 365, 420, 560, 700, 735)):
        x, y, tx, ty = at(poly, cum, sb)
        rot = math.atan2(ty, tx)
        L = rr.uniform(17, 21)
        col = ["boat_green", "boat_red", "boat_blue"][k % 3]
        bx, by = local(x, y, rot, 0, -h + 1.5)
        box("boat_black", bx, by, 0.0, L, 2.1, 0.7, rot)
        box(col, bx, by, 0.7, L - 3.2, 2.0, 1.1, rot)
        box("boat_cream", bx, by, 1.3, L - 3.2, 2.1, 0.12, rot)
        for w in range(int((L - 4) / 2.2)):
            wx, wy = local(bx, by, rot, -(L - 4) / 2 + 1.0 + w * 2.2, -1.02)
            box("window", wx, wy, 0.75, 0.6, 0.05, 0.4, rot)
    return poly


def bridge(p0, p1, water_a, water_b):
    """Humpback stone bridge from p0 to p1 (ground level both ends); water between fractions water_a..water_b."""
    bm = bm_for("stone")
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    span = math.hypot(dx, dy)
    rot = math.atan2(dy, dx)

    def W(u, v, z):
        x, y = local(p0[0], p0[1], rot, u, v)
        return bm.verts.new((x, y, z))

    def deck(t):
        return 0.06 + math.sin(math.pi * t) * 2.6
    n = 24
    prof = [(-3.8, 0.0), (3.8, 0.0), (3.8, 1.0), (3.4, 1.0), (3.4, 0.25), (-3.4, 0.25), (-3.4, 1.0), (-3.8, 1.0)]
    rings = [[W(span * k / n, pv, deck(k / n) + pz) for pv, pz in prof] for k in range(n + 1)]
    for a, b in zip(rings, rings[1:]):
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for sd in (-3.8, 3.8):
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n

            def soff(t):
                if water_a < t < water_b:
                    return 0.07 + math.sin(math.pi * (t - water_a) / (water_b - water_a)) * 2.0
                return 0.0
            vs = [W(span * t0, sd, soff(t0)), W(span * t1, sd, soff(t1)), W(span * t1, sd, deck(t1)), W(span * t0, sd, deck(t0))]
            bm.faces.new(vs if sd < 0 else vs[::-1])


# ------------------------------------------------------------------ landmarks
def church(cx, cy):
    box("church", cx, cy, 5.5, 30, 12, 11)
    roof("slate", cx, cy, 11, 30, 12, 5.5, 0.0, 0.3)
    box("church", cx - 18, cy, 10, 7, 7, 20)
    cone("slate", cx - 18, cy, 20, 4.2, 15, 8)
    for k in range(5):
        box("window", cx - 10 + k * 5, cy - 6.05, 6, 1.2, 0.05, 3.5)


def pub(cx, cy, rot):
    box("render", cx, cy, 3.6, 14, 11, 7.2, rot)
    roof("tile", cx, cy, 7.2, 14, 11, 3.2, rot)
    for wx in (-4.5, 0, 4.5):
        x, y = local(cx, cy, rot, wx, -5.53)
        box("window", x, y, 1.8, 2.4, 0.05, 1.6, rot)
        box("window", x, y, 5.0, 1.6, 0.05, 1.4, rot)
    x, y = local(cx, cy, rot, -7.2, -5.6)
    box("lamp", x, y, 3.0, 0.1, 0.1, 6.0, rot)
    x, y = local(cx, cy, rot, -7.2, -6.6)
    box("pub_sign", x, y, 4.6, 0.08, 1.4, 1.6, rot)
    # beer garden
    for k in range(4):
        x, y = local(cx, cy, rot, 10 + (k % 2) * 3, -2 + (k // 2) * 3.5)
        box("fence", x, y, 0.75, 1.8, 0.8, 0.08, rot)


def allotments(x0, y0, x1, y1):
    flat("grass_club", x0, y0, x1, y1, 0.02)
    rr = random.Random(9)
    x = x0 + 2
    while x < x1 - 8:
        y = y0 + 2
        while y < y1 - 12:
            flat("soil", x, y, x + 8, y + 12, 0.04)
            for r in range(5):
                box("crop", x + 1 + r * 1.5, y + 6, 0.2, 0.6, 10, 0.4)
            if rr.random() < 0.5:
                box("shed", x + 6.8, y + 10.5, 1.0, 2.0, 1.8, 2.0)
            y += 14
        x += 10
    for yy in (y0, y1):
        box("hedge", (x0 + x1) / 2, yy, 0.8, x1 - x0, 1.0, 1.6)
    for xx in (x0, x1):
        box("hedge", xx, (y0 + y1) / 2, 0.8, 1.0, y1 - y0, 1.6)
    stamp_box(x0 - 1, y0 - 1, x1 + 1, y1 + 1)


def rec(x0, y0, x1, y1):
    """The rec: open grass with a footpath, trees round the edge, the church at one end."""
    rr = random.Random(11)
    flat("grass_club", x0, y0, x1, y1, 0.015)
    path = smooth([(x0, (y0 + y1) / 2 + 10), ((x0 + x1) / 2, (y0 + y1) / 2 - 8), (x1, (y0 + y1) / 2 + 4)], step=2.0)
    ribbon("towpath", path, -1.2, 1.2, 0.03)
    for _ in range(60):
        x, y = rr.uniform(x0 + 3, x1 - 3), rr.uniform(y0 + 3, y1 - 3)
        if min(x - x0, x1 - x, y - y0, y1 - y) < 14 or rr.random() < 0.15:
            TREES.append((x, y, rr.uniform(1.0, 1.6), rr.random() * 0.8))
    stamp_box(x0, y0, x1, y1)


# ------------------------------------------------------------------ the layout
def rp(th):
    return sup(RING_A, RING_B, th)


def build(variant):
    flat("grass", -EDGE - 200, -EDGE - 200, EDGE + 200, EDGE + 200, 0.0)
    # the reserve is off limits for the neighbourhood
    for x in range(-int(RA) - 2, int(RA) + 3, 1):
        for y in range(-int(RB) - 2, int(RB) + 3, 1):
            if in_reserve(x, y, 1.0):
                c = _cell(x, y)
                if c >= 0:
                    OCC[c] = 1
    club_ground(variant)
    canal()

    # --- roads (all stamped before any house goes in)
    ring = [rp(math.tau * k / 120) for k in range(120)]
    R_ring = road(ring, "terrace", avenue=True, closed=True)
    W1 = road([rp(-1.9), (-75, -185), (-95, -245), (-105, -310), (-95, -440)], "terrace", avenue=True)
    W2 = road([rp(-1.2), (95, -190), (120, -255), (160, -330), (185, -440)], "terrace")
    W3 = road([(-84, -212), (-45, -238), (5, -246), (55, -236), (104, -215)], "terrace")          # crescent
    W4 = road([(-440, -300), (-300, -285), (-180, -300), (-104, -300), (0, -335), (155, -325), (300, -295), (440, -320)], "semi")
    W5 = road([(0, -335), (10, -368), (6, -392)], "semi", parked=False)                       # close
    disc_flat("asphalt", 6, -394, 9, 0.052)
    stamp_disc(6, -394, 11)
    W7 = road([(-95, -245), (-150, -252), (-220, -232), (-300, -216), (-440, -226)], "semi")
    W8 = road([(120, -255), (190, -250), (262, -240), (340, -252), (440, -240)], "mix")
    N1 = road([rp(math.pi), (-205, 5), (-255, -15), (-320, -35), (-440, -25)], "terrace", avenue=True)
    N2 = road([rp(-2.5), (-215, -150), (-262, -190), (-300, -216)], "mix")
    N3 = road([rp(2.45), (-205, 140), (-265, 150), (-340, 145), (-440, 150)], "terrace")
    S1 = road([rp(0), (210, -5), (270, 15), (340, 5), (440, 15)], "terrace", avenue=True)
    S2 = road([rp(-0.7), (200, -150), (240, -200), (262, -240)], "terrace")
    S3 = road([rp(0.7), (205, 135), (270, 150), (330, 158)], "terrace")
    S4 = road([(340, 5), (330, -60), (372, -110), (440, -125)], "semi")                         # crescent
    S5 = road([(200, 72), (175, 84)], "terrace", parked=False)                                   # allotments lane stub
    # across the canal: two humpback bridges
    B2a = road([rp(math.pi / 2), (0, 152), (0, 159)], "terrace", parked=False)
    B2b = road([(0, 185), (-6, 210), (-16, 236)], "terrace")
    B1a = road([(-265, 150), (-264.5, 167), (-264, 173)], "terrace", parked=False)
    B1b = road([(-263, 199), (-262, 230), (-260, 262), (-250, 335)], "terrace")
    E1 = road([(-440, 265), (-260, 262), (-130, 242), (-16, 236), (130, 250), (230, 262), (330, 272), (440, 262)], "mix", avenue=True)
    E2 = road([(-440, 345), (-250, 335), (-100, 320), (50, 320), (200, 345), (440, 345)], "semi")
    E3 = road([(-440, 420), (-200, 410), (0, 400), (200, 420), (440, 410)], "semi")
    C1 = road([(-130, 242), (-120, 285), (-100, 320)], "terrace")
    C2 = road([(230, 262), (215, 300), (200, 345)], "mix")
    C4 = road([(50, 320), (40, 360), (0, 400)], "semi")
    C5 = road([(-250, 335), (-235, 375), (-200, 410)], "semi")
    bridge((0, 159), (0, 185), 0.2, 0.8)
    bridge((-264, 173), (-263, 199), 0.2, 0.8)

    # --- landmarks (claim their ground before the houses)
    pub(0.0, -RING_B - ROAD_W / 2 - PAVE_W - 6.5, math.pi)       # opposite the gate
    stamp_disc(0.0, -RING_B - 12, 13)
    rec(-330, -150, -195, -45)
    church(-232, -72)
    allotments(212, 34, 318, 126)

    # --- houses: main roads first, then the rest
    order = [(R_ring, -1, "terrace"), (W1, 1, "terrace"), (W1, -1, "terrace"), (W2, 1, "terrace"), (W2, -1, "terrace"),
             (N1, 1, "terrace"), (N1, -1, "terrace"), (S1, 1, "terrace"), (S1, -1, "terrace"),
             (W3, 1, "terrace"), (W3, -1, "terrace"), (N3, 1, "terrace"), (N3, -1, "terrace"),
             (S2, 1, "terrace"), (S2, -1, "terrace"), (S3, 1, "terrace"), (S3, -1, "terrace"),
             (B1b, 1, "terrace"), (B1b, -1, "terrace"), (B2b, 1, "terrace"), (B2b, -1, "terrace"), (C1, 1, "terrace"), (C1, -1, "terrace"),
             (E1, 1, "mix"), (E1, -1, "mix"), (W8, 1, "mix"), (W8, -1, "mix"), (N2, 1, "mix"), (N2, -1, "mix"), (C2, 1, "mix"), (C2, -1, "mix"),
             (W4, 1, "semi"), (W4, -1, "semi"), (W5, 1, "semi"), (W5, -1, "semi"), (W7, 1, "semi"), (W7, -1, "semi"),
             (S4, 1, "semi"), (S4, -1, "semi"), (E2, 1, "semi"), (E2, -1, "semi"), (E3, 1, "semi"), (E3, -1, "semi"),
             (C4, 1, "semi"), (C4, -1, "semi"), (C5, 1, "semi"), (C5, -1, "semi")]
    for k, (poly, side, style) in enumerate(order):
        houses_along(poly, side, style, 1000 + k * 17)
    road_dressing(3)

    # --- whatever is left: green, with trees in clumps (denser towards the edge of the world)
    rr = random.Random(21)
    y = -EDGE - 60
    while y < EDGE + 60:
        x = -EDGE - 60
        while x < EDGE + 60:
            px, py = x + rr.uniform(-3, 3), y + rr.uniform(-3, 3)
            d = math.hypot(px, py)
            if not in_reserve(px, py, 4) and is_free(px, py) and d < EDGE + 80:
                clump = 0.5 + 0.5 * math.sin(px * 0.031 + 1.3) * math.cos(py * 0.027 - 0.4)
                p = 0.06 + 0.32 * clump + (0.45 if d > 390 else 0.0)
                if rr.random() < p:
                    TREES.append((px, py, rr.uniform(0.9, 1.5), rr.random()))
            x += 8.0
        y += 8.0


# ------------------------------------------------------------------ trees + lamps as linked duplicates
def make_tree_meshes():
    out = []
    for kind, (leaf, tall) in enumerate((("leaf_a", False), ("leaf_b", False), ("leaf_c", True))):
        bm = bmesh.new()
        me = bpy.data.meshes.new(f"Tree{kind}")
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.35, radius2=0.25, depth=4.0,
                              matrix=Matrix.Translation((0, 0, 2.0)))
        tr = bm.verts[:]
        if tall:
            r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.2, matrix=Matrix.Translation((0, 0, 7.5)) @ Matrix.Diagonal((0.9, 0.9, 2.6, 1)))
        else:
            r = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=3.4, matrix=Matrix.Translation((0, 0, 6.0)))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.4, matrix=Matrix.Translation((1.8, 0.8, 7.2)))
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M["trunk"])
        me.materials.append(M[leaf])
        for p in me.polygons:
            p.material_index = 0 if p.center.z < 4.0 and abs(p.center.x) < 0.5 and abs(p.center.y) < 0.5 else 1
        out.append(me)
    return out



def place_instances():
    meshes = make_tree_meshes()
    col = bpy.data.collections.new("Instances")
    scene.collection.children.link(col)
    for i, (x, y, s, k) in enumerate(TREES):
        me = meshes[0 if k < 0.45 else (1 if k < 0.8 else 2)]
        ob = bpy.data.objects.new(f"Tree{i}", me)
        ob.location = (x, y, 0)
        ob.scale = (s, s, s)
        ob.rotation_euler = (0, 0, R.uniform(0, math.tau))
        col.objects.link(ob)
    # lamp posts
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.06, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0.35, 5.5)) @ Matrix.Diagonal((0.25, 0.9, 0.18, 1)))
    lm = bpy.data.meshes.new("Lamp")
    bm.to_mesh(lm)
    bm.free()
    lm.materials.append(M["lamp"])
    for i, (x, y, rot) in enumerate(LAMPS):
        ob = bpy.data.objects.new(f"Lamp{i}", lm)
        ob.location = (x, y, 0)
        col.objects.link(ob)
    # cars: one mesh per colour (body + cabin + dark windows)
    glass = M["window"]
    car_meshes = []
    for ci, hexc in enumerate(CAR_COLS):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.6)) @ Matrix.Diagonal((4.2, 1.75, 0.75, 1)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((-0.2, 0, 1.22)) @ Matrix.Diagonal((2.3, 1.6, 0.55, 1)))
        me = bpy.data.meshes.new(f"Car{ci}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat(f"Car_{ci}", hexc, 0.35, 0.4))
        me.materials.append(glass)
        for p in me.polygons:
            p.material_index = 1 if p.center.z > 0.98 and abs(p.normal.z) < 0.5 else 0
        car_meshes.append(me)
    for i, (x, y, rot, c) in enumerate(CARS):
        ob = bpy.data.objects.new(f"Car{i}", car_meshes[c])
        ob.location = (x, y, 0)
        ob.rotation_euler = (0, 0, rot)
        col.objects.link(ob)


def stadium(variant):
    """The real stand models. Early: a short main stand with the tunnel (West) and a Shed (East).
    Max: the two-tier POC stand on all four sides (the reserve leaves room for a third tier)."""
    def imp(name, loc, rot, sx=1.0):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name))
        for r in [o for o in bpy.data.objects if o not in before and o.parent is None]:
            r.rotation_mode = 'XYZ'          # the glTF importer uses quaternions: euler would be ignored
            r.rotation_euler = (0, 0, rot)
            r.location = loc
            r.scale = (sx, 1, 1)
    W = 11.5
    if variant == "early":
        for k in (3, 4, 5):
            imp("main_stand_10_tunnel.glb" if k == 4 else "main_stand_10.glb", ((k - 4) * W, -HALF_W - 2.9, 0), math.pi)
        for k in (3, 4, 5):
            imp("the_shed_5.glb", ((k - 4) * W, HALF_W + 2.9, 0), 0.0)
    else:
        imp("big_stand.glb", (0, -HALF_W - 2.9, 0), math.pi)
        imp("big_stand.glb", (0, HALF_W + 2.9, 0), 0.0)
        imp("big_stand.glb", (-HALF_L - 2.9, 0, 0), math.pi / 2, 0.66)
        imp("big_stand.glb", (HALF_L + 2.9, 0, 0), -math.pi / 2, 0.66)


def finish():
    objs = []
    for key, bm in BMS.items():
        me = bpy.data.meshes.new(key)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        for f in bm.faces:                 # ground-level flats must face up (loose quads can come out flipped)
            if f.normal.z < -0.9 and f.calc_center_median().z < 0.1:
                f.normal_flip()
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M[key])
        ob = bpy.data.objects.new("Town_" + key, me)
        scene.collection.objects.link(ob)
        objs.append(ob)
    faces = sum(len(o.data.polygons) for o in objs)
    print(f"TOWN: {len(objs)} material meshes, {faces} faces, {len(TREES)} trees, {len(LAMPS)} lamps, {len(CARS)} cars")


VARIANT = "max" if "--max" in sys.argv else "early"
build(VARIANT)
finish()
place_instances()
stadium(VARIANT)
bpy.ops.wm.save_as_mainfile(filepath=f"/tmp/town_{VARIANT}.blend")


def mist_material():
    m = bpy.data.materials.new("MistPass")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 120.0       # FOG_BEGIN
    mr.inputs["From Max"].default_value = 400.0       # FOG_END
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cam.outputs["View Distance"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], em.inputs["Strength"])
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def render(views):
    world = bpy.data.worlds.new("World"); scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.74, 0.86, 1)
    bg.inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.4
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(48), math.radians(10), math.radians(-35))
    scene.collection.objects.link(sun)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    rb = -RING_B - ROAD_W / 2 - PAVE_W + 0.8
    shots = {
        "top": {"ortho": 900, "pos": (0, 0, 700), "target": (0, 0.001, 0), "res": (1500, 1500)},
        "aerial": {"lens": 30, "pos": (-240, -430, 230), "target": (0, -20, 0), "res": (1440, 810)},
        "hub": {"lens": 35, "pos": (8, 120, 75), "target": (8, -20, 0), "res": (1440, 810)},
        "pitch_north": {"lens": 22, "pos": (-15, 14, 1.7), "target": (-200, -30, 14), "res": (1440, 810)},
        "pitch_east": {"lens": 22, "pos": (0, -24, 1.7), "target": (0, 200, 16), "res": (1440, 810)},
        "pitch_south": {"lens": 22, "pos": (20, -18, 1.7), "target": (220, 90, 12), "res": (1440, 810)},
        "street": {"lens": 26, "pos": (75, -135.5, 1.7), "target": (-10, -143, 3.5), "res": (1440, 810)},
        "canal": {"lens": 26, "pos": (-48, 166.0, 1.7), "target": (0, 171, 2.5), "res": (1440, 810)},
    }
    mist = mist_material()
    for name in views:
        sh = shots[name]
        if "ortho" in sh:
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = sh["ortho"]
        else:
            cam.data.type = 'PERSP'
            cam.data.lens = sh["lens"]
        cam.data.clip_end = 3000
        cam.location = sh["pos"]
        d = Vector(sh["target"]) - Vector(sh["pos"])
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scene.render.resolution_x, scene.render.resolution_y = sh["res"]
        # beauty
        scene.view_layers[0].material_override = None
        bg.inputs[0].default_value = (0.62, 0.74, 0.86, 1)
        bg.inputs[1].default_value = 0.9
        sun.hide_render = False
        scene.cycles.samples = 12 if QUICK else 24
        scene.cycles.use_denoising = True
        scene.view_settings.view_transform = 'AgX'
        scene.render.filepath = f"/tmp/town_{VARIANT}_{name}.png"
        bpy.ops.render.render(write_still=True)
        if "ortho" in sh:
            continue
        # distance pass for the fog (the game: nothing up to 120 m, building up to 400 m)
        scene.view_layers[0].material_override = mist
        bg.inputs[0].default_value = (1, 1, 1, 1)
        bg.inputs[1].default_value = 1.0
        sun.hide_render = True
        scene.cycles.samples = 2
        scene.cycles.use_denoising = False
        scene.view_settings.view_transform = 'Standard'
        scene.render.filepath = f"/tmp/town_{VARIANT}_{name}_mist.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERS DONE")


for i, a in enumerate(sys.argv):
    if a == "--render":
        render(sys.argv[i + 1].split(","))
