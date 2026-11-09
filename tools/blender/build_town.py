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


def terrace_house(cx, cy, rot, brick, door, roofk, end_left, end_right):
    """One Victorian terrace house. Local: x along the street, -y = the street side (front)."""
    box(brick, cx, cy, WALL_H / 2, HOUSE_W, HOUSE_D, WALL_H, rot)
    roof(roofk, cx, cy, WALL_H, HOUSE_W, HOUSE_D, 2.3, rot)
    # chimney stack on the party wall (shared, so only on the left wall) + pots
    for side, has in ((-1, True), (1, end_right)):
        if not has:
            continue
        x, y = local(cx, cy, rot, side * HOUSE_W / 2, 0.6)
        box("chimney", x, y, WALL_H + 2.6, 0.7, 1.1, 1.6, rot)
        for k in (-0.2, 0.2):
            px, py = local(x, y, rot, 0, k)
            cyl("pot", px, py, WALL_H + 3.4, 0.11, 0.35, 6)
    # front: door, windows downstairs + upstairs, white frames
    fy = -HOUSE_D / 2 - 0.02
    dx, dy = local(cx, cy, rot, -1.5, fy)
    box(door, dx, dy, 1.05, 0.95, 0.06, 2.1, rot)
    for wx, wz, ww, wh in ((0.9, 1.5, 1.6, 1.4), (-1.35, 4.1, 1.1, 1.2), (1.1, 4.1, 1.1, 1.2)):
        x, y = local(cx, cy, rot, wx, fy)
        box("frame", x, y, wz, ww + 0.16, 0.05, wh + 0.16, rot)
        x, y = local(cx, cy, rot, wx, fy - 0.03)
        box("window", x, y, wz, ww, 0.05, wh, rot)
    # back: one window up, one down
    by = HOUSE_D / 2 + 0.02
    for wx, wz in ((1.0, 1.5), (-1.0, 4.1)):
        x, y = local(cx, cy, rot, wx, by)
        box("window", x, y, wz, 1.0, 0.05, 1.1, rot)


def terrace_row(x0, y0, length, rot, garden=10.0, front=2.0, seed_key=0):
    """A row of terraced houses along local x from (x0, y0); front (street) towards local -y.
    Back gardens behind with fences. Returns nothing."""
    rr = random.Random(seed_key)
    n = int(length // HOUSE_W)
    brick = rr.choice(BRICKS)
    roofk = rr.choice(["slate", "slate", "slate_b", "tile"])
    for i in range(n):
        lx = (i + 0.5) * HOUSE_W
        cx, cy = local(x0, y0, rot, lx, front + HOUSE_D / 2)
        b = brick if rr.random() > 0.12 else rr.choice(BRICKS + ["render"])
        terrace_house(cx, cy, rot, b, rr.choice(DOORS), roofk, i == 0, i == n - 1)
        # front: low wall + gate gap along the pavement
        wx, wy = local(x0, y0, rot, lx + 0.6, 0.15)
        box("wall_low", wx, wy, 0.4, HOUSE_W - 1.2, 0.25, 0.8, rot)
        # back garden lawn + fences
        gx, gy = local(x0, y0, rot, lx, front + HOUSE_D + garden / 2)
        box("garden", gx, gy, 0.03, HOUSE_W, garden, 0.06, rot)
        fx, fy = local(x0, y0, rot, i * HOUSE_W, front + HOUSE_D + garden / 2)
        box("fence", fx, fy, 0.9, 0.06, garden, 1.8, rot)
        if rr.random() < 0.45:
            tx, ty = local(x0, y0, rot, lx + rr.uniform(-1.2, 1.2), front + HOUSE_D + garden * rr.uniform(0.4, 0.85))
            TREES.append((tx, ty, rr.uniform(0.55, 0.85), rr.random()))
        if rr.random() < 0.3:
            sx, sy = local(x0, y0, rot, lx + 1.2, front + HOUSE_D + garden - 1.2)
            box("shed", sx, sy, 1.0, 2.0, 1.6, 2.0, rot)
    ex, ey = local(x0, y0, rot, n * HOUSE_W, front + HOUSE_D + garden / 2)
    box("fence", ex, ey, 0.9, 0.06, garden, 1.8, rot)
    bx, by = local(x0, y0, rot, n * HOUSE_W / 2, front + HOUSE_D + garden)
    box("fence", bx, by, 0.9, n * HOUSE_W, 0.06, 1.8, rot)


# ------------------------------------------------------------------ streets
ROAD_W, PAVE_W = 7.0, 2.2
LAMPS = []


def street(x0, y0, x1, y1, lamps=True, lines=True):
    """Axis-aligned street (asphalt + pavements both sides + kerbs), centreline from (x0,y0) to (x1,y1)."""
    horiz = abs(y1 - y0) < 0.01
    if horiz:
        a, b = min(x0, x1), max(x0, x1)
        flat("asphalt", a, y0 - ROAD_W / 2, b, y0 + ROAD_W / 2, 0.02)
        for s in (-1, 1):
            yc = y0 + s * (ROAD_W / 2 + PAVE_W / 2)
            box("pavement", (a + b) / 2, yc, 0.07, b - a, PAVE_W, 0.14)
            box("kerb", (a + b) / 2, y0 + s * (ROAD_W / 2 + 0.08), 0.08, b - a, 0.16, 0.16)
        if lines:
            x = a + 2
            while x < b - 3:
                box("line", x + 1.5, y0, 0.035, 3.0, 0.15, 0.01)
                x += 9.0
        if lamps:
            x = a + 12
            k = 0
            while x < b - 4:
                LAMPS.append((x, y0 + (1 if k % 2 else -1) * (ROAD_W / 2 + 0.6)))
                x += 26.0
                k += 1
    else:
        a, b = min(y0, y1), max(y0, y1)
        flat("asphalt", x0 - ROAD_W / 2, a, x0 + ROAD_W / 2, b, 0.028)
        for s in (-1, 1):
            xc = x0 + s * (ROAD_W / 2 + PAVE_W / 2)
            box("pavement", xc, (a + b) / 2, 0.07, PAVE_W, b - a, 0.14)
            box("kerb", x0 + s * (ROAD_W / 2 + 0.08), (a + b) / 2, 0.08, 0.16, b - a, 0.16)
        if lines:
            y = a + 2
            while y < b - 3:
                box("line", x0, y + 1.5, 0.035, 0.15, 3.0, 0.01)
                y += 9.0
        if lamps:
            y = a + 12
            k = 0
            while y < b - 4:
                LAMPS.append((x0 + (1 if k % 2 else -1) * (ROAD_W / 2 + 0.6), y))
                y += 26.0
                k += 1


TREES = []      # (x, y, scale, kind 0..1)


def block_rows(x0, x1, y_street, side, seed):
    """Terraces facing a horizontal street at y_street; side = -1 below it (front towards +y), +1 above."""
    edge = ROAD_W / 2 + PAVE_W
    if side > 0:
        terrace_row(x0, y_street + edge, x1 - x0, 0.0, seed_key=seed)
    else:
        # rotate 180: start at x1, local x runs to -x, front (local -y) faces +y
        terrace_row(x1, y_street - edge, x1 - x0, math.pi, seed_key=seed)


# ------------------------------------------------------------------ the club ground (reserve)
def club_ground():
    flat("grass_club", -RES_X, -RES_Y, RES_X, RES_Y, 0.01)
    # palisade fence round the reserve with a gap for the entrance on West
    for x0, y0, x1, y1 in ((-RES_X, -RES_Y, -12, -RES_Y), (12, -RES_Y, RES_X, -RES_Y), (-RES_X, RES_Y, RES_X, RES_Y),
                           (-RES_X, -RES_Y, -RES_X, RES_Y), (RES_X, -RES_Y, RES_X, RES_Y)):
        length = math.hypot(x1 - x0, y1 - y0)
        n = int(length / 2.5)
        for k in range(n + 1):
            t = k / max(n, 1)
            box("palisade", x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.1, 0.12, 0.12, 2.2)
        box("palisade", (x0 + x1) / 2, (y0 + y1) / 2, 1.9, max(abs(x1 - x0), 0.08), max(abs(y1 - y0), 0.08), 0.08)
        box("palisade", (x0 + x1) / 2, (y0 + y1) / 2, 0.5, max(abs(x1 - x0), 0.08), max(abs(y1 - y0), 0.08), 0.08)
    # car park inside the gate (South-West)
    flat("gravel", 30, -RES_Y + 2, 110, -RES_Y + 34, 0.02)
    for k in range(14):
        box("line", 34 + k * 5.5, -RES_Y + 10, 0.03, 0.12, 5.0, 0.01)
        box("line", 34 + k * 5.5, -RES_Y + 26, 0.03, 0.12, 5.0, 0.01)
    # pitch (placeholder for the game's own pitch)
    flat("pitch", -HALF_L - 3, -HALF_W - 3, HALF_L + 3, HALF_W + 3, 0.015)
    for x0, y0, x1, y1 in ((-HALF_L, -HALF_W, HALF_L, -HALF_W), (-HALF_L, HALF_W, HALF_L, HALF_W),
                           (-HALF_L, -HALF_W, -HALF_L, HALF_W), (HALF_L, -HALF_W, HALF_L, HALF_W), (0, -HALF_W, 0, HALF_W)):
        box("pitch_line", (x0 + x1) / 2, (y0 + y1) / 2, 0.02, max(abs(x1 - x0), 0.12), max(abs(y1 - y0), 0.12), 0.01)


# ------------------------------------------------------------------ canal (East, Blender +y)
CANAL_Y0, CANAL_Y1 = 122.0, 136.0     # water edges


def canal():
    flat("water", -EDGE, CANAL_Y0, EDGE, CANAL_Y1, -0.5)
    for y in (CANAL_Y0, CANAL_Y1):
        box("stone", 0, y, -0.2, 2 * EDGE, 0.6, 0.8)
    # banks down to the water
    box("stone", 0, CANAL_Y0 - 0.3, -0.25, 2 * EDGE, 0.1, 0.5)
    # towpath on the stadium side
    flat("towpath", -EDGE, RES_Y + 4, EDGE, CANAL_Y0 - 0.3, 0.03)
    box("hedge", 0, RES_Y + 3, 0.7, 2 * EDGE, 1.2, 1.4)
    # far bank: grass strip + trees
    flat("grass", -EDGE, CANAL_Y1 + 0.3, EDGE, CANAL_Y1 + 10, 0.02)
    x = -EDGE + 8
    while x < EDGE:
        TREES.append((x + R.uniform(-3, 3), CANAL_Y1 + 5 + R.uniform(-1.5, 1.5), R.uniform(0.9, 1.3), 0.95 if R.random() < 0.4 else R.random() * 0.6))
        x += R.uniform(14, 24)
    # lock (South-East): chamber walls, two pairs of gates with balance beams
    lx = 150.0
    for y in (CANAL_Y0 + 3.4, CANAL_Y1 - 3.4):
        box("stone", lx, y, 0.0, 34, 1.2, 1.6)
    flat("water", lx - 17, CANAL_Y0 + 4, lx + 17, CANAL_Y1 - 4, -0.9)
    for gx in (lx - 17, lx + 17):
        for s in (-1, 1):
            box("lock_wood", gx, (CANAL_Y0 + CANAL_Y1) / 2 + s * 1.6, 0.0, 0.4, 3.4, 2.2, s * 0.18)
            box("lock_wood", gx + (1 if gx > lx else -1) * 2.6, (CANAL_Y0 + CANAL_Y1) / 2 + s * 4.2, 1.1, 5.0, 0.25, 0.25)
    # stone arch bridge (North-East) carrying a lane over the canal
    bx = -150.0
    span = CANAL_Y1 - CANAL_Y0 + 8
    y0 = CANAL_Y0 - 4
    n = 20
    bm = bm_for("stone")
    # deck + parapets as one swept profile over a segmental arch, and a solid spandrel under it
    def arch_z(t):
        return 2.6 + math.sin(math.pi * t) * 2.0
    prof = [(-3.8, 0.0), (3.8, 0.0), (3.8, 1.1), (3.4, 1.1), (3.4, 0.3), (-3.4, 0.3), (-3.4, 1.1), (-3.8, 1.1)]
    rings = []
    for k in range(n + 1):
        t = k / n
        y = y0 + span * t
        z = arch_z(t)
        rings.append([bm.verts.new((bx + px, y, z + pz)) for px, pz in prof])
    for k in range(n):
        a, b = rings[k], rings[k + 1]
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    # spandrel walls (both faces) from the arch soffit down to the water / banks
    for side in (-3.8, 3.8):
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            ya, yb = y0 + span * t0, y0 + span * t1
            za, zb = arch_z(t0), arch_z(t1)
            # soffit follows a lower arch over the water, the banks are solid
            sa = 0.0 if not (CANAL_Y0 < ya < CANAL_Y1) else 0.4 + math.sin(math.pi * (ya - CANAL_Y0) / (CANAL_Y1 - CANAL_Y0)) * 2.6
            sb = 0.0 if not (CANAL_Y0 < yb < CANAL_Y1) else 0.4 + math.sin(math.pi * (yb - CANAL_Y0) / (CANAL_Y1 - CANAL_Y0)) * 2.6
            vs = [bm.verts.new((bx + side, ya, sa)), bm.verts.new((bx + side, yb, sb)), bm.verts.new((bx + side, yb, zb)), bm.verts.new((bx + side, ya, za))]
            bm.faces.new(vs if side > 0 else vs[::-1])
    # narrowboats moored along the towpath
    for k, x in enumerate((-90, -64, -30, 10, 46, 86)):
        col = ["boat_green", "boat_red", "boat_blue"][k % 3]
        y = CANAL_Y0 + 1.5
        L = R.uniform(17, 21)
        box("boat_black", x, y, -0.15, L, 2.1, 0.7)
        box(col, x, y, 0.55, L - 3.2, 2.0, 1.1)
        box("boat_cream", x, y, 1.15, L - 3.2, 2.1, 0.12)
        for w in range(int((L - 4) / 2.2)):
            box("window", x - (L - 4) / 2 + 1.0 + w * 2.2, y - 1.02, 0.6, 0.6, 0.05, 0.4)


# ------------------------------------------------------------------ landmarks
def church(cx, cy):
    box("church", cx, cy, 5.5, 30, 12, 11)
    roof("slate", cx, cy, 11, 30, 12, 5.5, 0.0, 0.3)
    box("church", cx - 18, cy, 10, 7, 7, 20)
    cone("slate", cx - 18, cy, 20, 4.2, 15, 8)
    for k in range(5):
        box("window", cx - 10 + k * 5, cy - 6.05, 6, 1.2, 0.05, 3.5)


def pub(cx, cy, rot):
    """Corner pub: bigger, rendered cream, with a hanging sign."""
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


def allotments(x0, y0, x1, y1):
    flat("grass", x0, y0, x1, y1, 0.02)
    x = x0 + 2
    while x < x1 - 8:
        y = y0 + 2
        while y < y1 - 12:
            flat("soil", x, y, x + 8, y + 12, 0.04)
            for r in range(5):
                box("crop", x + 1 + r * 1.5, y + 6, 0.2, 0.6, 10, 0.4)
            if R.random() < 0.5:
                box("shed", x + 6.8, y + 10.5, 1.0, 2.0, 1.8, 2.0)
            y += 14
        x += 10
    box("hedge", (x0 + x1) / 2, y0, 0.8, x1 - x0, 1.0, 1.6)
    box("hedge", (x0 + x1) / 2, y1, 0.8, x1 - x0, 1.0, 1.6)


def park(x0, y0, x1, y1):
    flat("grass", x0, y0, x1, y1, 0.02)
    for _ in range(int((x1 - x0) * (y1 - y0) / 500)):
        TREES.append((R.uniform(x0 + 4, x1 - 4), R.uniform(y0 + 4, y1 - 4), R.uniform(1.0, 1.6), R.random() * 0.7))
    flat("towpath", x0, (y0 + y1) / 2 - 1.5, x1, (y0 + y1) / 2 + 1.5, 0.04)


# ------------------------------------------------------------------ the layout
def build():
    # ground in two parts: the canal is a cut, not water under the grass
    flat("grass", -EDGE - 60, -EDGE - 60, EDGE + 60, CANAL_Y0 - 0.3, 0.0)
    flat("grass", -EDGE - 60, CANAL_Y1 + 0.3, EDGE + 60, EDGE + 60, 0.0)
    box("stone", 0, (CANAL_Y0 + CANAL_Y1) / 2, -1.6, 2 * EDGE + 120, CANAL_Y1 - CANAL_Y0 + 0.6, 0.2)   # canal bed
    club_ground()
    canal()

    # High Road along West (outside the reserve), the club gate faces it
    hy = -RES_Y - 9
    street(-EDGE, hy, EDGE, hy)
    # a parade of terraces on the far side of the High Road, the pub at the corner opposite the gate
    yy = hy - ROAD_W / 2 - PAVE_W
    for k, x in enumerate(range(-380, 380, 76)):
        if -40 < x < 30:
            continue
        block_rows(float(x), float(x) + 70, hy, -1, 100 + k)
    pub(8.0, yy - 7.5, math.pi)
    # side streets off the High Road going West (Blender -y), with terraces both sides
    for k, x in enumerate(range(-380, 380, 76)):
        sx = float(x) + 73.0          # in the gaps between the blocks
        street(sx, -EDGE, sx, hy - ROAD_W / 2 - PAVE_W)
    # parallel streets further West with back-to-back terraces between them
    y = hy - 48
    row = 0
    while y > -EDGE + 20:
        street(-EDGE, y, EDGE, y, lines=False)
        for k, x in enumerate(range(-380, 380, 76)):
            x0, x1 = float(x) + 6.5, float(x) + 69.5
            block_rows(x0, x1, y, -1, 1000 + row * 50 + k)
            block_rows(x0, x1, y, 1, 2000 + row * 50 + k)
        y -= 52
        row += 1

    # North (Blender -x) and South (+x) of the reserve, between the High Road and the canal
    for side in (-1, 1):
        xs = side * (RES_X + 10)
        street(xs, hy, xs, RES_Y + 2, lines=False)
        y = -RES_Y + 26
        k = 0
        while y < RES_Y - 10:
            # streets stop at the park (North) and the allotments (South)
            zone = (-310.0, -150.0, -100.0, -10.0) if side < 0 else (150.0, 260.0, -60.0, 60.0)
            a, b = sorted((xs, side * (EDGE - 10)))
            if zone[2] < y < zone[3]:
                if a < zone[0]:
                    street(a, y, zone[0], y, lines=False)
                if b > zone[1]:
                    street(zone[1], y, b, y, lines=False)
            else:
                street(xs, y, side * (EDGE - 10), y, lines=False)
            k += 1
            y += 52
    # North: church + park, then terraces; South: allotments, then terraces
    church(-200.0, -60.0)
    park(-310.0, -100.0, -150.0, -10.0)
    allotments(150.0, -60.0, 260.0, 60.0)
    for side in (-1, 1):
        y = -RES_Y + 26
        row = 0
        while y < RES_Y - 10:
            a = RES_X + 14
            b = EDGE - 16
            x0, x1 = (a, b) if side > 0 else (-b, -a)
            for k in range(int((x1 - x0) // 76) + 1):
                bx0 = x0 + k * 76 + 3
                bx1 = min(bx0 + 70, x1)
                if bx1 - bx0 < 20:
                    continue
                busy = (side < 0 and bx0 < -150 and bx1 > -310 and y < 0) or (side > 0 and bx0 < 260 and bx1 > 150 and -60 < y < 60)
                if busy:
                    continue
                if y + 52 < RES_Y + 20:
                    block_rows(bx0, bx1, y, 1, 5000 + side * 300 + row * 20 + k)
                if y > -RES_Y + 26:
                    block_rows(bx0, bx1, y, -1, 6000 + side * 300 + row * 20 + k)
            y += 52
            row += 1

    # East of the canal: streets parallel to it, terraces
    y = CANAL_Y1 + 22
    row = 0
    while y < EDGE - 10:
        street(-EDGE, y, EDGE, y, lines=False)
        for k, x in enumerate(range(-380, 380, 76)):
            x0, x1 = float(x) + 6.5, float(x) + 69.5
            if row > 0 or True:
                block_rows(x0, x1, y, 1, 7000 + row * 50 + k)
            if row > 0:
                block_rows(x0, x1, y, -1, 8000 + row * 50 + k)
        y += 52
        row += 1
    # street trees along the High Road
    x = -EDGE + 10
    while x < EDGE:
        if not (-20 < x < 20):
            TREES.append((x, hy + ROAD_W / 2 + PAVE_W - 0.6, R.uniform(0.8, 1.1), 0.3))
        x += 18


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
    col = bpy.data.collections.new("Trees")
    scene.collection.children.link(col)
    for i, (x, y, s, k) in enumerate(TREES):
        if abs(x) < RES_X - 2 and abs(y) < RES_Y - 2:
            continue
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
    for i, (x, y) in enumerate(LAMPS):
        ob = bpy.data.objects.new(f"Lamp{i}", lm)
        ob.location = (x, y, 0)
        col.objects.link(ob)


def stadium():
    """The real stand models for scale: West main stand (tunnel in the middle), East a Shed, ends bleachers-free."""
    def imp(name):
        path = os.path.join(MODELS, name)
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        roots = [o for o in new if o.parent is None]
        return roots
    W = 11.5
    for k in range(9):
        name = "main_stand_15_tunnel.glb" if k == 4 else "main_stand_15.glb"
        for r in imp(name):
            # model front faces -Y in Blender (towards the pitch at... ) place on West (Blender -y side), facing +y
            r.rotation_mode = 'XYZ'          # the glTF importer uses quaternions: euler would be ignored
            r.rotation_euler = (0, 0, math.pi)   # the model faces -y; on West it must face the pitch (+y)
            r.location = ((k - 4) * W, -HALF_W - 2.9, 0)
    for k in range(9):
        for r in imp("the_shed_8.glb"):
            r.location = ((k - 4) * W, HALF_W + 2.9, 0)   # faces -y = the pitch


def finish():
    objs = []
    for key, bm in BMS.items():
        me = bpy.data.meshes.new(key)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M[key])
        ob = bpy.data.objects.new("Town_" + key, me)
        scene.collection.objects.link(ob)
        objs.append(ob)
    faces = sum(len(o.data.polygons) for o in objs)
    print(f"TOWN: {len(objs)} material meshes, {faces} faces, {len(TREES)} trees, {len(LAMPS)} lamps")


build()
finish()
place_instances()
stadium()
bpy.ops.wm.save_as_mainfile(filepath="/tmp/town.blend")


def render(views):
    world = bpy.data.worlds.new("World"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.86, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.4
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(48), math.radians(10), math.radians(-35))
    scene.collection.objects.link(sun)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16 if QUICK else 32
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = 'AgX'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    shots = {
        "top": {"ortho": 840, "pos": (0, 0, 600), "target": (0, 0.001, 0), "res": (1600, 1600)},
        "aerial": {"lens": 30, "pos": (-170, -330, 190), "target": (0, -20, 0), "res": (1600, 900)},
        "street": {"lens": 28, "pos": (-120, -116.5, 1.7), "target": (-40, -121, 4.0), "res": (1600, 900)},
        "canal": {"lens": 26, "pos": (-188, 116.5, 2.2), "target": (-120, 128, 2.0), "res": (1600, 900)},
        "hub": {"lens": 35, "pos": (8, 120, 75), "target": (8, -20, 0), "res": (1600, 900)},
    }
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
        scene.render.filepath = f"/tmp/town_{name}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERS DONE")


for i, a in enumerate(sys.argv):
    if a == "--render":
        render(sys.argv[i + 1].split(","))
