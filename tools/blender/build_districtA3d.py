"""3D proof of district A (round the ground) — built straight from tools/plan/village_district_A_v1.py (streets, houses one
by one, corner houses, club square, green, match-day layout) on the land model village_land_v1.py; inside the plot the club
ground of world plan v5 (stands, paths, facilities). Marcel 2026-11-10: Blender mockup first, min stadium.

Blender 5 (bpy). Run:  python3 build_districtA3d.py [--render top,aerial,...] [--quick]
min = 13th division ground, max = 1st division. Renders go to /tmp/w3d_<stage>_<shot>.png (+ _mist for the fog).
Axes: Blender X = along the pitch (= Godot x), Blender -Y = West / camera side (= Godot +z), Z up.
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

# ================================================================== 3D proof of district A (built straight from the town plan)
import numpy as np
import shapely
from shapely.geometry import Point, LineString, Polygon, box as sbox
from shapely.ops import unary_union

sys.path.insert(0, os.path.join(HERE, "../plan"))
import world_plan_v5 as W                     # the club ground inside the plot (stands, paths, facilities) is still v5's
import village_land_v1 as L
import village_district_A_v1 as A
import district_A_matchday_proposal as MD

STAGE = "max" if "--max" in sys.argv else "min"
G = W.ground(STAGE)
M["path"] = mat("Path", "#B9AE96", 0.95)
M["concrete"] = mat("Concrete", "#A9A9A4", 0.9)
M["tent"] = mat("Tent", "#F2F0EA", 0.8)
M["club"] = mat("Club_Colour", "#1D4F91", 0.6)
M["away"] = mat("Away_Red", "#B03A35", 0.6)
M["portakabin"] = mat("Portakabin", "#D9DCD6", 0.7)
M["steel"] = mat("Steel", "#6E757C", 0.5, 0.4)
M["bowl"] = mat("Stadium_Shell", "#8C949C", 0.8)
M["roofsteel"] = mat("Stadium_Roof", "#C9CDD1", 0.5, 0.2)
M["yard"] = mat("Yard_Paving", "#9C978C", 0.95)
M["wall_yard"] = mat("Yard_Wall", "#7E4A3A", 0.9)
M["bus"] = mat("Bus", "#E8E4D8", 0.5)
M["square"] = mat("Square_Setts", "#A39A8A", 0.9)
M["shopfront"] = mat("Shop_Front", "#2F4F6F", 0.5)
M["shop_sign"] = mat("Shop_Sign", "#C9A13A", 0.5)

# the land model sits ~5 m up round the ground; the 3D world has the pitch at 0, so everything is shifted down by Z_OFF
Z_OFF = 5.0
WATER_Z = 1.2 - Z_OFF                           # river surface ~1 m above its bed by the ground (the town weir holds it)
RIVER = LineString(L.CANAL_PTS)
WATER = RIVER.buffer(L.RIVER_W / 2)
EXT = (-420, -400, 420, 360)                    # terrain out to the fog
VIEWB = sbox(*EXT)
BRIDGE_ROAD = (206.1, 147.6)


# ------------------------------------------------------------------ heights
def traw(x, y):
    return L.height(np.asarray(x, float), np.asarray(y, float)) - Z_OFF


PB = W.PLOT.exterior


def ground_z(x, y):
    """Final ground: the land, the club ground levelled at 0 with a 7 m bank inside the fence."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    z = traw(x, y)
    pts = shapely.points(x.ravel(), y.ravel())
    inside = shapely.contains_xy(W.PLOT, x.ravel(), y.ravel()).reshape(x.shape)
    d = shapely.distance(pts, PB).reshape(x.shape)
    w = np.clip(d / 7.0, 0, 1)
    w = w * w * (3 - 2 * w)
    return np.where(inside, z * (1 - w), z)


def gz(x, y):
    return float(ground_z(np.array([x]), np.array([y]))[0])


def road_z(x, y, bridge=False):
    z = float(traw(np.array(x), np.array(y)))
    if bridge:
        dc = RIVER.distance(Point(x, y))
        if dc < 18:
            top = WATER_Z + 3.5
            z = max(z, z + (top - z) * math.cos(math.pi / 2 * dc / 18) ** 0.6)
    return z


# ------------------------------------------------------------------ meshes from plan polygons
def drape(key, geom, zf, off=0.0, seg=3.0):
    """Triangulate a (multi)polygon (holes ok) and drape it: z = zf(x, y) + off."""
    if geom.is_empty:
        return
    x0, y0, x1, y1 = geom.bounds
    cell = 4.0
    xs = np.arange(math.floor(x0 / cell) * cell, x1 + cell, cell)
    ys = np.arange(math.floor(y0 / cell) * cell, y1 + cell, cell)
    cells = shapely.box(*[a.ravel() for a in np.meshgrid(xs, ys)], *[a.ravel() + cell for a in np.meshgrid(xs, ys)])
    pieces = shapely.intersection(cells, geom)
    pieces = [q for q in pieces if not q.is_empty]
    flat_parts = []
    for q in pieces:
        flat_parts += [g for g in getattr(q, "geoms", [q]) if g.geom_type == "Polygon"]
    parts = []
    for part in flat_parts:
        if part.area < 0.05:
            continue
        g = None
        for fix in (lambda q: q, lambda q: q.buffer(0).simplify(0.02), lambda q: q.buffer(-0.02).buffer(0.02)):
            try:
                g = shapely.constrained_delaunay_triangles(fix(part))
                break
            except Exception:
                g = None
        if g is None:
            DRAPE_FAIL.append((key, round(part.area, 1)))
            continue
        parts.append(g)
    bm = bm_for(key)
    cache = {}
    for t in [t for g in parts for t in getattr(g, "geoms", [g])]:
        cs = list(t.exterior.coords)[:3]
        if (cs[1][0] - cs[0][0]) * (cs[2][1] - cs[0][1]) - (cs[1][1] - cs[0][1]) * (cs[2][0] - cs[0][0]) < 0:
            cs = cs[::-1]
        vs = []
        for (x, y) in cs:
            k = (round(x, 3), round(y, 3))
            if k not in cache:
                cache[k] = bm.verts.new((x, y, zf(x, y) + off))
            vs.append(cache[k])
        try:
            if len({id(v) for v in vs}) == 3:
                bm.faces.new(vs)
        except ValueError:
            pass


def terrain_mesh():
    xs = np.arange(EXT[0], EXT[2] + 1, 3.0)
    ys = np.arange(EXT[1], EXT[3] + 1, 3.0)
    X, Y = np.meshgrid(xs, ys)
    Z = ground_z(X, Y)
    inw = shapely.contains_xy(WATER.buffer(0.5), X.ravel(), Y.ravel()).reshape(X.shape)
    Z = np.where(inw, np.minimum(Z, WATER_Z - 1.2), Z)
    bm = bm_for("grass")
    V = [[bm.verts.new((float(X[j, i]), float(Y[j, i]), float(Z[j, i]))) for i in range(len(xs))] for j in range(len(ys))]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((V[j][i], V[j][i + 1], V[j + 1][i + 1], V[j + 1][i]))


def ribbon_wall(key, line, z0f, z1f, step=2.0):
    bm = bm_for(key)
    Ln = line.length
    prev = None
    d = 0.0
    while True:
        p = line.interpolate(min(d, Ln))
        cur = (bm.verts.new((p.x, p.y, z0f(p.x, p.y))), bm.verts.new((p.x, p.y, z1f(p.x, p.y))))
        if prev:
            bm.faces.new((prev[0], cur[0], cur[1], prev[1]))
        prev = cur
        if d >= Ln:
            break
        d += step


# ------------------------------------------------------------------ streets (district A + the main roads)
def _roads():
    out = []
    for nm, ln, w, k in A.STREETS:
        pv = 2.0 if k == "ring" else 1.5
        out.append((nm, ln, w - 2 * pv, pv, k))
    for i, r in enumerate(L.MAIN_ROADS):
        g = r.intersection(VIEWB)
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "LineString" and q.length > 5:
                out.append((f"main{i}", q, 7.0, 1.5, "main"))
    for i, s in enumerate(A.STUBS):
        out.append((f"stub{i}", s, 5.5, 1.5, "stub"))
    return out


ROADS = _roads()
CARR = unary_union([ln.buffer(cw / 2, cap_style=2, join_style=1) for nm, ln, cw, pv, k in ROADS])
CARR = CARR.buffer(4, join_style=1).buffer(-4, join_style=1).union(CARR)          # kerb radii at junctions
PAVE = unary_union([ln.buffer(cw / 2 + pv, cap_style=2, join_style=1) for nm, ln, cw, pv, k in ROADS])
PAVE = PAVE.buffer(5, join_style=1).buffer(-5, join_style=1).union(PAVE).difference(CARR)


def on_bridge(x, y):
    return Point(x, y).distance(Point(BRIDGE_ROAD)) < 30 and WATER.buffer(18).contains(Point(x, y))


def streets():
    drape("asphalt", CARR.intersection(VIEWB).difference(WATER.buffer(-0.5)), lambda x, y: road_z(x, y, on_bridge(x, y)), 0.10)
    drape("pavement", PAVE.intersection(VIEWB).difference(WATER.buffer(-0.5)), lambda x, y: road_z(x, y, on_bridge(x, y)), 0.22)
    # the road bridge at the end of Shelley Street: a deck over the river with parapets
    deck = LineString([(206.0, 120.0), (206.8, 185.0)])
    seg = deck.intersection(WATER.buffer(14))
    for s in getattr(seg, "geoms", [seg]):
        for sd in (-5.0, 5.0):
            e = s.parallel_offset(abs(sd), "left" if sd > 0 else "right")
            for q in getattr(e, "geoms", [e]):
                ribbon_wall("stone", q, lambda x, y: WATER_Z - 0.3, lambda x, y: road_z(x, y, True) + 1.1)
        drape("asphalt", s.buffer(4.0, cap_style=2), lambda x, y: road_z(x, y, True), 0.10)
    for nm, ln, cw, pv, k in ROADS:
        s, i = 8.0, 0
        while s < ln.length - 4:
            p = ln.interpolate(s)
            q = ln.interpolate(min(s + 1, ln.length))
            tx, ty = q.x - p.x, q.y - p.y
            Lq = math.hypot(tx, ty) or 1
            sd = 1 if i % 2 else -1
            x, y = p.x - ty / Lq * sd * (cw / 2 + 0.4), p.y + tx / Lq * sd * (cw / 2 + 0.4)
            if VIEWB.contains(Point(x, y)) and not WATER.contains(Point(x, y)):
                LAMPS.append((x, y, road_z(x, y) + 0.2))
            s += 30.0
            i += 1
        if k == "street":              # parked cars on the terrace streets
            rr = random.Random(sum(map(ord, nm)))
            s = 6.0
            while s < ln.length - 6:
                p = ln.interpolate(s)
                q = ln.interpolate(min(s + 1, ln.length))
                tx, ty = q.x - p.x, q.y - p.y
                Lq = math.hypot(tx, ty) or 1
                for sd in (-1, 1):
                    if rr.random() < 0.35:
                        o = cw / 2 - 1.0
                        x, y = p.x - ty / Lq * sd * o, p.y + tx / Lq * sd * o
                        CARS.append((x, y, road_z(x, y) + 0.1, math.atan2(ty, tx), rr.randrange(len(CAR_COLS))))
                s += 5.8


# ------------------------------------------------------------------ houses (one per plan house cell)
PUB_GEOMS = [g for g, t in MD.PUBS] + ([A.PUB] if A.PUB is not None else [])
SHOP_GEOMS = [g for g, t in MD.SHOPS]


def _prism(key, poly, z0, h):
    bm = bm_for(key)
    cs = list(poly.exterior.coords)[:-1]
    if poly.exterior.is_ccw is False:
        cs = cs[::-1]
    bot = [bm.verts.new((x, y, z0)) for x, y in cs]
    top = [bm.verts.new((x, y, z0 + h)) for x, y in cs]
    n = len(cs)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    try:
        bm.faces.new(top)
    except ValueError:
        pass
    return cs


def _hip_roof(key, poly, z0, rise):
    bm = bm_for(key)
    cs = list(poly.exterior.coords)[:-1]
    c = poly.representative_point()
    apex = bm.verts.new((c.x, c.y, z0 + rise))
    ring = [bm.verts.new((x, y, z0)) for x, y in cs]
    for i in range(len(ring)):
        try:
            bm.faces.new((ring[i], ring[(i + 1) % len(ring)], apex))
        except ValueError:
            pass


def houses():
    corner_ids = {id(c) for c in A.CORNERS}
    for idx, h in enumerate(A.HOUSES):
        if h.geom_type != "Polygon":
            continue
        rr = random.Random(idx * 7919)
        is_pub = any(h.intersection(g).area > 0.5 * h.area for g in PUB_GEOMS)
        is_shop = any(h.intersection(g).area > 0.5 * h.area for g in SHOP_GEOMS)
        c = h.centroid
        z0 = float(traw(np.array(c.x), np.array(c.y))) + 0.25
        Hh = 7.0 if is_pub else rr.uniform(5.4, 6.0)
        # a row keeps one brick per ~6 houses (built in runs)
        brick = "render" if is_pub else BRICKS[(idx // 6 + int(c.x // 40)) % len(BRICKS)]
        roofk = "tile" if is_pub else ("slate" if (idx // 6) % 3 else "slate_b")
        cs = list(h.exterior.coords)[:-1]
        if id(h) in corner_ids or len(cs) != 4:
            _prism(brick, h, z0 - 0.3, Hh + 0.3)
            _hip_roof(roofk, h, z0 + Hh, 2.2)
            front = None
        else:
            f0, f1, b1, b0 = cs
            _prism(brick, h, z0 - 0.3, Hh + 0.3)
            bm = bm_for(roofk)
            m0 = ((f0[0] + b0[0]) / 2, (f0[1] + b0[1]) / 2)
            m1 = ((f1[0] + b1[0]) / 2, (f1[1] + b1[1]) / 2)
            rise = 2.3
            # small eaves overhang front and back
            def out(p, m, k=0.25):
                dx, dy = p[0] - m[0], p[1] - m[1]
                Lq = math.hypot(dx, dy) or 1
                return (p[0] + dx / Lq * k, p[1] + dy / Lq * k)
            F0, F1, B0, B1 = out(f0, m0), out(f1, m1), out(b0, m0), out(b1, m1)
            V = lambda p, z: bm.verts.new((p[0], p[1], z))
            for quad_ in ((V(F0, z0 + Hh), V(F1, z0 + Hh), V(m1, z0 + Hh + rise), V(m0, z0 + Hh + rise)),
                          (V(B1, z0 + Hh), V(B0, z0 + Hh), V(m0, z0 + Hh + rise), V(m1, z0 + Hh + rise))):
                bm.faces.new(quad_)
            for tri in ((V(f0, z0 + Hh), V(m0, z0 + Hh + rise), V(b0, z0 + Hh)), (V(f1, z0 + Hh), V(b1, z0 + Hh), V(m1, z0 + Hh + rise))):
                bm.faces.new(tri)
            # chimney on the party wall
            chx, chy = m0[0] * 0.55 + f0[0] * 0.45, m0[1] * 0.55 + f0[1] * 0.45
            box("chimney", chx, chy, z0 + Hh + rise * 0.6 + 0.6, 0.6, 1.0, 1.6, math.atan2(f1[1] - f0[1], f1[0] - f0[0]))
            front = (f0, f1, b0)
        if front is None:
            continue
        f0, f1, b0 = front
        tx, ty = f1[0] - f0[0], f1[1] - f0[1]
        wdt = math.hypot(tx, ty) or 1
        tx, ty = tx / wdt, ty / wdt
        nx, ny = f0[0] - b0[0], f0[1] - b0[1]
        nl = math.hypot(nx, ny) or 1
        nx, ny = nx / nl, ny / nl                         # out of the front wall, towards the street
        rot = math.atan2(ty, tx)

        def P(u, off=0.04):
            return (f0[0] + tx * u + nx * off, f0[1] + ty * u + ny * off)
        if is_shop or is_pub:
            px, py = P(wdt * 0.5)
            box("shopfront" if is_shop else "window", px, py, z0 + 1.5, wdt * 0.8, 0.1, 2.0, rot)
            px, py = P(wdt * 0.5, 0.15)
            box("shop_sign" if is_shop else "pub_sign", px, py, z0 + 3.0, wdt * 0.85, 0.12, 0.6, rot)
        else:
            rr2 = random.Random(idx)
            for (u, zc, ww, wh, k) in ((wdt * 0.28, 1.05, 0.9, 2.1, "door"), (wdt * 0.68, 1.5, 1.5, 1.4, "win"),
                                       (wdt * 0.3, 4.1, 1.1, 1.2, "win"), (wdt * 0.7, 4.1, 1.1, 1.2, "win")):
                px, py = P(u)
                box(rr2.choice(DOORS) if k == "door" else "window", px, py, z0 + zc, ww, 0.08, wh, rot)
        # front wall at the back of the pavement (1.5 m front garden / step); a tunnel-back house leaves a gap for the passage
        if any(h is t_[0] for t_ in A.TUNNELS):
            continue
        px, py = P(wdt / 2, 1.35)
        box("wall_low", px, py, z0 + 0.1, wdt, 0.25, 0.7, rot)


def backs():
    """Walled yards (paved), rear extensions with a lean-to roof, cobbled back alleys (ginnels)."""
    hu = unary_union(A.HOUSES).buffer(0.3)
    for y in A.YARDS:
        drape("yard", y, lambda x, y_: gz(x, y_), 0.08)
        wall = y.exterior.difference(hu)
        for seg in getattr(wall, "geoms", [wall]):
            if seg.geom_type == "LineString" and seg.length > 0.5:
                ribbon_wall("wall_yard", seg, lambda x, y_: gz(x, y_) - 0.1, lambda x, y_: gz(x, y_) + 1.8, 1.5)
    for k, o in enumerate(A.OUTRIGGERS):
        c = o.centroid
        z0 = float(traw(np.array(c.x), np.array(c.y))) + 0.25
        brick = BRICKS[(k // 6 + int(c.x // 40)) % len(BRICKS)]
        _prism(brick, o, z0 - 0.3, 3.6)
        _hip_roof("slate_b", o, z0 + 3.3, 0.8)
    drape("gravel", A.GINNEL_U.intersection(VIEWB), lambda x, y_: gz(x, y_), 0.06)
    # tunnel backs: a dark arched opening in the front wall and the back wall of the house it passes through
    for h, ln in A.TUNNELS:
        (sx_, sy_), (px_, py_) = ln.coords[0], ln.coords[-1]
        a = math.atan2(py_ - sy_, px_ - sx_)
        cut = ln.intersection(h.exterior)
        pts = [cut] if cut.geom_type == "Point" else list(getattr(cut, "geoms", []))
        for q in pts:
            zq = float(traw(np.array(q.x), np.array(q.y))) + 0.25
            box("door_black", q.x, q.y, zq + 1.3, 0.3, 1.6, 2.6, a)


# ------------------------------------------------------------------ the river, the green spaces and the district's buildings
def river_and_green():
    drape("water", WATER.intersection(VIEWB), lambda x, y: WATER_Z, 0.0)
    for sd in (1, -1):                                            # stone quay walls along the town reach
        e = RIVER.parallel_offset(L.RIVER_W / 2, "left" if sd > 0 else "right")
        for s in getattr(e, "geoms", [e]):
            s = s.intersection(VIEWB)
            for q in getattr(s, "geoms", [s]):
                if q.geom_type == "LineString" and q.length > 2:
                    ribbon_wall("stone", q, lambda x, y: WATER_Z - 1.0, lambda x, y: gz(x, y) + 0.3)
    for g in (L.QUAY_WALK, A.RIVER_STRIP, A.NE_GREEN):
        drape("garden", g.intersection(VIEWB).difference(PAVE.union(CARR)).difference(WATER), lambda x, y: gz(x, y), 0.06)
    drape("square", A.CLUB_SQUARE.difference(PAVE.union(CARR)), lambda x, y: gz(x, y), 0.12)
    # clubhouse (two storeys, the club's colours over the door), church hall, war memorial
    for g, key, H, rk in ((A.CLUBHOUSE, "brick_b", 6.8, "tile"), (A.CHURCH_HALL, "church", 5.5, "slate")):
        if g is None:
            continue
        x0, y0, x1, y1 = g.bounds
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        z = gz(cx, cy)
        long_x = (x1 - x0) >= (y1 - y0)
        box(key, cx, cy, z + H / 2, x1 - x0, y1 - y0, H)
        roof(rk, cx, cy, z + H, max(x1 - x0, y1 - y0), min(x1 - x0, y1 - y0), 2.8, 0.0 if long_x else math.pi / 2, 0.4)
    if A.PUB is not None:                                          # the hard-core pub on the corner of North Street
        for q in getattr(A.PUB, "geoms", [A.PUB]):
            c = q.centroid
            zp = float(traw(np.array(c.x), np.array(c.y))) + 0.25
            _prism("render", q, zp - 0.3, 7.3)
            _hip_roof("tile", q, zp + 7.0, 2.4)
            box("pub_sign", c.x, c.y - 5.6, zp + 3.4, 3.0, 0.12, 0.8)
    x0, y0, x1, y1 = A.CLUBHOUSE.bounds
    box("club", x1 + 0.06, (y0 + y1) / 2, gz(x1, y0) + 5.4, 0.1, 10.0, 1.2)
    # club square: a statue in front of the club square gate, benches under the trees, a kiosk
    sx_, sy_ = A.SQUARE_STATUE
    z = gz(sx_, sy_)
    box("stone", sx_, sy_, z + 0.7, 3.2, 3.2, 1.4)
    box("steel", sx_, sy_, z + 2.6, 0.9, 0.7, 2.4)
    box("steel", sx_, sy_, z + 4.05, 0.5, 0.5, 0.5)
    for bx_, by_ in A.SQUARE_BENCHES:
        zb = gz(bx_, by_)
        box("fence", bx_, by_, zb + 0.45, 1.8, 0.5, 0.08)
        box("fence", bx_, by_ + 0.25, zb + 0.75, 1.8, 0.08, 0.5)
    if A.SQUARE_KIOSK is not None:
        kx0, ky0, kx1, ky1 = A.SQUARE_KIOSK.bounds
        kc = ((kx0 + kx1) / 2, (ky0 + ky1) / 2)
        box("club", kc[0], kc[1], gz(*kc) + 1.3, kx1 - kx0, ky1 - ky0, 2.6)
        roof("tile", kc[0], kc[1], gz(*kc) + 2.6, kx1 - kx0, ky1 - ky0, 0.8)
    mx, my = A.MEMORIAL
    z = gz(mx, my)
    box("stone", mx, my, z + 0.4, 3.0, 3.0, 0.8)
    box("stone", mx, my, z + 2.6, 0.9, 0.9, 3.6)
    box("stone", mx, my, z + 3.6, 0.3, 2.0, 0.3)
    # away coach bay + coaches
    drape("asphalt", MD.COACH_BAY, lambda x, y: road_z(x, y), 0.2)
    for cx_, cy_ in MD.COACH_SLOTS_NOW:
        box("away", cx_, cy_, road_z(cx_, cy_) + 1.9, 2.55, 12.0, 3.5)
    drape("garden", MD.COACH_BAY_RESERVE, lambda x, y: road_z(x, y), 0.18)     # kept free for the bay to grow: a grass verge now
    # the away walk across the green (gravel path)
    drape("path", MD.AWAY_ROUTE.buffer(1.4).difference(CARR.union(PAVE)).difference(WATER), lambda x, y: gz(x, y), 0.1)


# ------------------------------------------------------------------ the club ground
def fence_along(line, key, h=2.2, step=2.5, zf=None):
    L = line.length
    d = 0.0
    while d <= L:
        p = line.interpolate(d)
        q = line.interpolate(min(d + 0.5, L))
        a = math.atan2(q.y - p.y, q.x - p.x)
        z = (zf or gz)(p.x, p.y)
        box(key, p.x, p.y, z + h / 2, 0.1, 0.1, h)
        for zz in (0.4, h - 0.3):
            px, py = local(p.x, p.y, a, step / 2, 0)
            box(key, px, py, z + zz, step, 0.06, 0.06, a)
        d += step


def facility(b):
    name = b["name"]
    g = b["g"]
    x0, y0, x1, y1 = g.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sx, sy = x1 - x0, y1 - y0
    z = gz(cx, cy)
    if name.startswith("merch"):
        box("tent", cx, cy, z + 1.1, sx, sy, 2.2)
        cone("tent", cx, cy, z + 2.2, max(sx, sy) * 0.72, 1.2, 4)
    elif name in ("chip van",):
        box("frame", cx, cy, z + 1.6, sx, sy, 2.6)
        box("pub_sign", cx + sx / 2 + 0.02, cy, z + 2.0, 0.05, sy * 0.7, 0.9)
    elif name.startswith("CLUBHOUSE"):
        box("brick_b", cx, cy, z + 2.2, sx, sy, 4.4)
        roof("tile", cx, cy, z + 4.4, sx, sy, 2.4, 0.0, 0.4)
        for k in range(4):
            box("window", x0 + 3 + k * (sx - 6) / 3, y0 - 0.04, z + 1.6, 1.8, 0.08, 1.4)
    elif name.startswith("gate arch"):
        for gx in (x0 + 1, x1 - 1):
            box("brick_a", gx, cy, z + 2.2, 1.6, 1.6, 4.4)
        box("brick_a", cx, cy, z + 4.8, sx, 1.2, 0.9)
        box("club", cx, cy - 0.65, z + 4.8, sx * 0.7, 0.05, 0.6)
        for k in range(4):             # flagpoles just inside the gate
            fx, fy = cx - 4.5 + k * 3.0, cy + 7.0
            fz = gz(fx, fy)
            cyl("steel", fx, fy, fz, 0.06, 7.0, 6)
            box("club" if k % 2 == 0 else "frame", fx + 0.62, fy, fz + 6.4, 1.2, 0.04, 0.8)
    elif name.startswith("offices"):
        box("portakabin", cx, cy, z + 1.4, sx, sy, 2.8)
    elif name in ("club building",):
        box("bowl", cx, cy, z + 15, sx, sy, 30)
        for k in range(8):
            box("window", x0 + 6 + k * (sx - 12) / 7, y0 - 0.05, z + 8, 4, 0.1, 10)
        box("club", cx, y0 - 0.06, z + 26, sx * 0.6, 0.1, 2.5)
    elif name.startswith("stair"):
        box("bowl", cx, cy, z + 17, sx, sy, 34)
    elif name in ("bikes",):
        for k in range(int(sx / 0.9)):
            box("steel", x0 + 0.45 + k * 0.9, cy, z + 0.45, 0.05, sy * 0.6, 0.9)
    elif name in ("programmes",):
        box("club", cx, cy, z + 0.6, sx, sy, 1.2)
    elif name in ("away kiosk", "away wc", "away gate"):
        box("away", cx, cy, z + 1.3, sx, sy, 2.6)
    elif name in ("tea hut",):
        box("shed", cx, cy, z + 1.4, sx, sy, 2.8)
        roof("tile", cx, cy, z + 2.8, sx, sy, 1.0)
    elif name in ("groundsman", "groundsman yard"):
        box("steel", cx, cy, z + 2.4, sx, sy, 4.8)
    else:        # changing rooms, toilets, tickets ...
        box("brick_c", cx, cy, z + 1.6, sx, sy, 3.2)
        box("concrete", cx, cy, z + 3.3, sx + 0.4, sy + 0.4, 0.2)


def imp(name, loc, rot, sx=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name))
    for r in [o for o in bpy.data.objects if o not in before and o.parent is None]:
        r.rotation_mode = 'XYZ'
        r.rotation_euler = (0, 0, rot)
        r.location = loc
        r.scale = (sx, 1, 1)


def club_ground():
    # ground surfaces
    drape("grass_club", W.PLOT, lambda x, y: gz(x, y), 0.03)
    for hd in G["hard"]:
        drape("gravel", hd, lambda x, y: gz(x, y), 0.08)
    for p in G["paths"]:
        drape("path", p["g"], lambda x, y: gz(x, y), 0.1)
    for dv in G["drives"]:
        drape("pavement", dv, lambda x, y: road_z(x, y), 0.24)
    for b in G["bays"]:
        drape("asphalt", b, lambda x, y: gz(x, y), 0.12)
    # pitch + lines
    box("pitch", 0, 0, 0.02, 2 * W.HL + 6, 2 * W.HW + 6, 0.06)
    for (a, b2, c, d) in ((-W.HL, -W.HW, W.HL, -W.HW), (-W.HL, W.HW, W.HL, W.HW), (-W.HL, -W.HW, -W.HL, W.HW), (W.HL, -W.HW, W.HL, W.HW), (0, -W.HW, 0, W.HW)):
        box("pitch_line", (a + c) / 2, (b2 + d) / 2, 0.06, max(abs(c - a), 0.12), max(abs(d - b2), 0.12), 0.01)
    for name, g in G["green"]:
        x0, y0, x1, y1 = g.bounds
        box("pitch", (x0 + x1) / 2, (y0 + y1) / 2, gz((x0 + x1) / 2, (y0 + y1) / 2) + 0.06, x1 - x0, y1 - y0, 0.06)
        if "training" in name:
            for gy in (y0, y1):
                box("pitch_line", (x0 + x1) / 2, gy, gz(x0, gy) + 2.1, 5.0, 0.12, 0.12)
                for gx in ((x0 + x1) / 2 - 2.5, (x0 + x1) / 2 + 2.5):
                    box("pitch_line", gx, gy, gz(gx, gy) + 1.05, 0.12, 0.12, 2.1)
    # fences
    fence_along(W.PLOT.exterior, "palisade", 2.2)
    if G["fence_pay"] is not None:
        fence_along(G["fence_pay"].exterior, "club", 1.8, 3.0)
    for pts, col in G["lines"]:
        fence_along(LineString(pts), "away", 2.0, 2.0)
    for k, g in G["turnstiles"]:
        c = g.centroid
        x0, y0, x1, y1 = g.bounds
        box("club", c.x, c.y, gz(c.x, c.y) + 1.4, x1 - x0, y1 - y0, 2.8)
    for b in G["buildings"]:
        facility(b)
    # team bus
    for b in G["bays"]:
        c = b.centroid
        x0, y0, x1, y1 = b.bounds
        box("bus", c.x, c.y, gz(c.x, c.y) + 1.8, min(x1 - x0, 11.5), 2.55, 3.4)
    # cars in the car park
    rr = random.Random(12)
    for hd in G["hard"]:
        x0, y0, x1, y1 = hd.bounds
        if x0 >= 39 and y1 <= -132:
            for row in (y0 + 3.5, y1 - 3.5):
                x = x0 + 2
                while x < x1 - 2:
                    if rr.random() < (0.5 if STAGE == "min" else 0.75):
                        CARS.append((x, row, gz(x, row) + 0.1, math.pi / 2, rr.randrange(len(CAR_COLS))))
                    x += 2.7
    # stands
    E_FRONT, S_FRONT = W.END_FRONT, W.SIDE_FRONT
    if STAGE == "min":
        for k in (-1, 0, 1):
            imp("main_stand_10_tunnel.glb" if k == 0 else "main_stand_10.glb", (k * W.SW, -S_FRONT, 0), math.pi)
            imp("the_shed_3.glb", (k * W.SW, S_FRONT, 0), 0.0)
        for k in range(W.N_END):
            y = (k - (W.N_END - 1) / 2) * W.SW
            imp("the_shed_3.glb", (-E_FRONT, y, 0), math.pi / 2)
        # away end: three concrete standing steps + a rail
        for s in range(3):
            box("concrete", E_FRONT + 0.5 + s, 0, 0.15 + s * 0.3, 1.0, W.END_HALF * 2, 0.3 + s * 0.6)
        box("steel", E_FRONT + 0.1, 0, 1.0, 0.06, W.END_HALF * 2, 0.06)
        for m in G["masts"]:
            c = m.centroid
            imp("floodlight_mast.glb", (c.x, c.y, 0), math.atan2(-c.y, -c.x) - math.pi / 2)
    else:
        imp("big_stand.glb", (0, -S_FRONT, 0), math.pi)
        imp("big_stand.glb", (0, S_FRONT, 0), 0.0)
        imp("big_stand.glb", (-E_FRONT, 0, 0), math.pi / 2, W.END_HALF * 2 / 103.5)
        imp("big_stand.glb", (E_FRONT, 0, 0), -math.pi / 2, W.END_HALF * 2 / 103.5)
        # shell: corners + the rear of the stands out to the max line, closed bowl from outside
        inner = unary_union([sbox(-51.75, -S_FRONT - 35, 51.75, S_FRONT + 35), sbox(-E_FRONT - 35, -W.END_HALF, E_FRONT + 35, W.END_HALF),
                             sbox(-E_FRONT, -S_FRONT, E_FRONT, S_FRONT)])
        shell = sbox(-W.STAND_MAX_X, -W.STAND_MAX_Y, W.STAND_MAX_X, W.STAND_MAX_Y).difference(inner)
        for part in getattr(shell, "geoms", [shell]):
            drape("bowl", part, lambda x, y: 0.0, 32.0)
            ribbon_wall("bowl", part.exterior, lambda x, y: 0.0, lambda x, y: 32.0, 3.0)
        # roof ring over the corners
        ring = sbox(-W.STAND_MAX_X, -W.STAND_MAX_Y, W.STAND_MAX_X, W.STAND_MAX_Y).difference(sbox(-E_FRONT - 4, -S_FRONT - 4, E_FRONT + 4, S_FRONT + 4))
        drape("roofsteel", ring.difference(inner), lambda x, y: 0.0, 34.0)


# ------------------------------------------------------------------ trees

# ------------------------------------------------------------------ trees
def plan_trees():
    avoid = unary_union([p["g"] for p in G["paths"]] + [b["g"] for b in G["buildings"]] + G["stands"] + G["hard"] +
                        [g for _, g in G["green"]] + G["masts"] + [g for _, g in G["plots"]])
    r = random.Random(3)
    for z in G["trees"]:
        x0, y0, x1, y1 = z.bounds
        y = y0 + 3
        while y < y1 - 2:
            x = x0 + 3 + r.random() * 3
            while x < x1 - 2:
                px, py = x + r.uniform(-1.5, 1.5), y + r.uniform(-1.5, 1.5)
                if z.contains(Point(px, py)) and not Point(px, py).buffer(3.0).intersects(avoid):
                    TREES.append((px, py, gz(px, py), r.uniform(0.85, 1.3), r.random()))
                x += 8.0
            y += 7.0
    # the square, the green and the quay walk get trees; a line of trees along the quay
    blocked = unary_union([A.CLUBHOUSE, A.CHURCH_HALL or Point(0, 0), Point(*A.MEMORIAL).buffer(4), MD.AWAY_ROUTE.buffer(3),
                           CARR, PAVE, WATER.buffer(2), MD.COACH_BAY.buffer(2)] + A.HOUSES)
    for x_, y_ in A.SQUARE_TREES:
        TREES.append((x_, y_, gz(x_, y_), r.uniform(0.75, 0.95), r.random() * 0.8))
    for zone, step in ((A.NE_GREEN.buffer(-2), 8.0), (L.QUAY_WALK.intersection(VIEWB).buffer(-2), 11.0)):
        x0, y0, x1, y1 = zone.bounds
        y = y0 + 2
        while y < y1:
            x = x0 + 2 + r.random() * 3
            while x < x1:
                p = Point(x + r.uniform(-2, 2), y + r.uniform(-2, 2))
                if zone.contains(p) and not p.buffer(2.5).intersects(blocked):
                    TREES.append((p.x, p.y, gz(p.x, p.y), r.uniform(0.8, 1.2), r.random()))
                x += step
            y += step
    # a few trees in the back yards
    for h in A.HOUSES:
        if r.random() < 0.05:
            c = h.centroid
            TREES.append((c.x + r.uniform(-1, 1), c.y + r.uniform(-1, 1) - 0, gz(c.x, c.y), r.uniform(0.5, 0.7), r.random()))


TREES, LAMPS, CARS = [], [], []
DRAPE_FAIL = []
CAR_COLS = ["#B8BDC2", "#2B2F36", "#8C1F24", "#2E4E86", "#E8E6E1", "#3D5E46", "#6B6F74"]


def instances():
    meshes = make_tree_meshes()
    col = bpy.data.collections.new("Instances")
    scene.collection.children.link(col)
    for i, (x, y, z, s, k) in enumerate(TREES):
        ob = bpy.data.objects.new(f"Tree{i}", meshes[0 if k < 0.45 else (1 if k < 0.8 else 2)])
        ob.location = (x, y, z)
        ob.scale = (s, s, s)
        ob.rotation_euler = (0, 0, (i * 2.399) % math.tau)
        col.objects.link(ob)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.06, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0.35, 5.5)) @ Matrix.Diagonal((0.25, 0.9, 0.18, 1)))
    lm = bpy.data.meshes.new("Lamp")
    bm.to_mesh(lm)
    bm.free()
    lm.materials.append(M["lamp"])
    for i, (x, y, z) in enumerate(LAMPS):
        ob = bpy.data.objects.new(f"Lamp{i}", lm)
        ob.location = (x, y, z)
        col.objects.link(ob)
    car_meshes = []
    for ci, hexc in enumerate(CAR_COLS):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.6)) @ Matrix.Diagonal((4.2, 1.75, 0.75, 1)))
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((-0.2, 0, 1.22)) @ Matrix.Diagonal((2.3, 1.6, 0.55, 1)))
        me = bpy.data.meshes.new(f"Car{ci}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat(f"Car_{ci}", hexc, 0.35, 0.4))
        me.materials.append(M["window"])
        for p in me.polygons:
            p.material_index = 1 if p.center.z > 0.98 and abs(p.normal.z) < 0.5 else 0
        car_meshes.append(me)
    for i, (x, y, z, rot, c) in enumerate(CARS):
        ob = bpy.data.objects.new(f"Car{i}", car_meshes[c])
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, rot)
        col.objects.link(ob)


def finish():
    n = 0
    for key, bm in BMS.items():
        me = bpy.data.meshes.new(key)
        bm.normal_update()
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M[key])
        ob = bpy.data.objects.new("World_" + key, me)
        scene.collection.objects.link(ob)
        n += len(me.polygons)
    print("DRAPE FAILURES:", DRAPE_FAIL)
    print(f"WORLD3D {STAGE}: {n} faces, {len(TREES)} trees, {len(LAMPS)} lamps, {len(CARS)} cars, {len(A.HOUSES)} houses")


terrain_mesh()
streets()
houses()
backs()
river_and_green()
club_ground()
plan_trees()
finish()
instances()
# glTF materials are single-sided-safe; make every face render from both sides (loose quads, terrain edges)
for m in bpy.data.materials:
    m.use_backface_culling = False


def mist_material():
    m = bpy.data.materials.new("MistPass")
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 120.0
    mr.inputs["From Max"].default_value = 400.0
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cam.outputs["View Distance"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def eye(x, y, h=1.7, road=False):
    return (x, y, (road_z(x, y) + 0.2 if road else gz(x, y)) + h)


SHOTS = {
    "top": {"ortho": 520, "pos": (-7, -55, 600), "target": (-7, -54.999, 0), "res": (1600, 1400)},
    "aerial": {"lens": 28, "pos": (-330, -340, 170), "target": (-20, -40, 0), "res": (1600, 900)},
    "aerial_ne": {"lens": 28, "pos": (330, 280, 150), "target": (0, -30, 0), "res": (1600, 900)},
    "club_square": {"lens": 24, "pos": ("eye", -135, -150), "target": (-195, -95, 4), "res": (1600, 900)},
    "turnstile_lane": {"lens": 24, "pos": ("eye", -205, 41), "target": (-139, 50, 3), "res": (1600, 900)},
    "main_gate": {"lens": 24, "pos": ("eye", -45, -138), "target": (-10, -122, 3), "res": (1600, 900)},
    "lower_road": {"lens": 26, "pos": ("eye", 125, -186), "target": (0, -186, 3), "res": (1600, 900)},
    "ginnel": {"lens": 24, "pos": ("eye", 175, -212.5), "target": (110, -213, 2), "res": (1600, 900)},
    "yards_low": {"lens": 30, "pos": (40, -260, 28), "target": (60, -205, 0), "res": (1600, 900)},
    "tunnel": {"lens": 28, "pos": ("eye", 210, 8), "target": (200, 22, 1.8), "res": (1600, 900)},
    "away_walk": {"lens": 24, "pos": ("eye", 192, 128), "target": (139, 100, 3), "res": (1600, 900)},
    "pitch_home": {"lens": 22, "pos": (-10, 6, 1.7), "target": (-200, 0, 10), "res": (1600, 900)},
    "pitch_west": {"lens": 22, "pos": (0, 18, 1.7), "target": (0, -200, 12), "res": (1600, 900)},
}


def resolve(pos):
    if isinstance(pos, tuple) and pos and pos[0] == "eye":
        return eye(pos[1], pos[2], 1.7, True)
    return pos


def render(views):
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.4
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(46), math.radians(8), math.radians(-35))
    scene.collection.objects.link(sun)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    mist = mist_material()
    for name in views:
        sh = SHOTS[name]
        if "ortho" in sh:
            cam.data.type = 'ORTHO'
            cam.data.ortho_scale = sh["ortho"]
        else:
            cam.data.type = 'PERSP'
            cam.data.lens = sh["lens"]
        cam.data.clip_end = 3000
        pos = resolve(sh["pos"])
        cam.location = pos
        cam.rotation_euler = (Vector(sh["target"]) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.resolution_x, scene.render.resolution_y = sh["res"]
        scene.view_layers[0].material_override = None
        bg.inputs[0].default_value = (0.62, 0.74, 0.86, 1)
        bg.inputs[1].default_value = 0.9
        sun.hide_render = False
        scene.cycles.samples = 12 if QUICK else 24
        scene.cycles.use_denoising = True
        scene.view_settings.view_transform = 'AgX'
        scene.render.filepath = f"/tmp/dA3d_{STAGE}_{name}.png"
        bpy.ops.render.render(write_still=True)
        print("RENDERED", name, flush=True)
        if "ortho" in sh or name.startswith("aerial"):
            continue
        scene.view_layers[0].material_override = mist
        bg.inputs[0].default_value = (1, 1, 1, 1)
        bg.inputs[1].default_value = 1.0
        sun.hide_render = True
        scene.cycles.samples = 2
        scene.cycles.use_denoising = False
        scene.view_settings.view_transform = 'Standard'
        scene.render.filepath = f"/tmp/dA3d_{STAGE}_{name}_mist.png"
        bpy.ops.render.render(write_still=True)


bpy.ops.wm.save_as_mainfile(filepath=f"/tmp/districtA3d_{STAGE}.blend")
for i, a in enumerate(sys.argv):
    if a == "--render":
        render(sys.argv[i + 1].split(","))
