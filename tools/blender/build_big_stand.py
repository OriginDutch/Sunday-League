"""The Big Stand — two-tier cantilever stand POC for Sunday League (GDD §10i).

Run:  python3 build_big_stand.py [--render] [--render-dir DIR]
Blender 5 (bpy). Units: metres. Blender axes: X along the touchline, -Y towards the pitch, Z up.
Origin: front face of the stand, centre of the long side, ground level.

Outputs (repo-relative, next to this script):
  assets/models/big_stand.glb          structure only (concrete, steel, roof, glass, lights, facade)
  assets/models/big_stand_layout.json  every seat + every fan, in Godot coordinates (x, y-up, z towards pitch)
Seats and fans are drawn in the game with MultiMesh (scripts/big_stand.gd) so they are cheap and
club colours can change at runtime. For the preview renders they are also built here as meshes.
All numbers are Claude's picks (tunable) unless GDD §10i says Marcel chose them.
"""
import bpy, bmesh, math, sys, os, json, random
from mathutils import Vector, Matrix

random.seed(7)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
RENDER_DIR = sys.argv[sys.argv.index("--render-dir") + 1] if "--render-dir" in sys.argv else "/tmp"

# ------------------------------------------------------------------ dimensions
SECTIONS, SEC_W = 9, 11.5                 # Marcel: full long side, 11.5 m sections
W = SECTIONS * SEC_W                      # 103.5
HW = W / 2
AISLE_W = 1.2
SEATS_PER_BLOCK, SEAT_PITCH = 20, 0.5
BOUND = [-HW + i * SEC_W for i in range(SECTIONS + 1)]

# lower tier (Marcel: 20 rows)
L_ROWS, L_TREAD, L_RISE = 20, 0.80, 0.36
L_Y0, L_Z0 = 1.6, 1.2                     # front walkway depth / height
# cross-aisle (Marcel: tunnels on the stairs, a cross-aisle, the stair splits around the tunnel and merges again)
CROSS_ROW, CROSS_G, CROSS_JUMP = 10, 1.6, 0.54   # flat walkway behind row 9; rows behind it start 0.54 m higher
def lz(k): return L_Z0 + (k + 1) * L_RISE + (CROSS_JUMP if k >= CROSS_ROW else 0.0)
def ly(k): return L_Y0 + k * L_TREAD + (CROSS_G if k >= CROSS_ROW else 0.0)
L_BACK = ly(L_ROWS)                        # 17.6
L_TOP = lz(L_ROWS - 1)                     # 8.4

# skybox level
BAL_Y0, BAL_Y1, BAL_Z = L_BACK, L_BACK + 2.6, L_TOP + 0.5   # balcony in front of the glass
BOX_Y1, BOX_Z1 = BAL_Y1 + 4.8, BAL_Z + 3.2                  # box interior depth / ceiling
BOXES_PER_SEC = 3

# upper tier (Marcel: 15 rows)
U_ROWS, U_TREAD, U_RISE = 15, 0.85, 0.55
U_FRONT_Y = L_BACK - 0.6                  # upper tier overhangs the balcony
U_SOFFIT = BOX_Z1 + 0.4
U_Y0, U_Z0 = U_FRONT_Y + 1.2, U_SOFFIT + 0.6
def uz(k): return U_Z0 + (k + 1) * U_RISE
def uy(k): return U_Y0 + k * U_TREAD
U_BACK = uy(U_ROWS)
U_TOP = uz(U_ROWS - 1)
FACADE_Y = U_BACK + 1.6                   # rear walkway, then the back wall

# roof (Marcel: cantilever)
ROOF_FRONT_Y = -2.0
COL_Y = FACADE_Y + 0.9
TOP_BACK_Z, TOP_TIP_Z = U_TOP + 9.5, U_TOP + 5.0
BOT_BACK_Z, BOT_TIP_Z = U_TOP + 2.6, U_TOP + 4.3

# vomitories (lower tier only; upper tier is reached from the rear walkway): on 4 stairs, opening onto the cross-aisle
VOM_AISLES, VOM_ROWS, VOM_W = (1, 3, 6, 8), range(10, 14), 3.0   # Marcel: x = ±17.25 and ±40.25
VOM_WALL, SIDE_AISLE = 0.2, 0.9
VOM_CLEAR = VOM_W / 2 + VOM_WALL + SIDE_AISLE    # 2.6 m each side of the stair centre
LANDING_ROW = VOM_ROWS[-1] + 1                    # above the tunnel the two side stairs merge
MAST_DIST = math.hypot(52.5 + 8.0, 34.0 + 8.0)    # corner mast (8 m diagonally out from the corner flag) to centre spot

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------------ materials
def srgb_to_lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]

MATS = {}
def mat(key, name, hex_, rough=0.8, metal=0.0, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    lin = srgb_to_lin(hex_)
    m.diffuse_color = (*lin, alpha)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    MATS[key] = m
    return m

PRIMARY, SECONDARY = "#2F6DB5", "#ECE8DD"
mat("concrete", "Concrete", "#A3A29B")
mat("concrete_dark", "Concrete_Dark", "#85847D")
mat("step_edge", "Step_Edge_Yellow", "#D9B43A", 0.6)
mat("steel", "Steel_Frame", "#3B4A44", 0.5, 0.3)
mat("truss", "Roof_Truss_White", "#E9ECEA", 0.45, 0.2)
mat("sheet", "Roof_Sheet", "#9BA6AA", 0.55, 0.4)
mat("sheet_under", "Roof_Underside", "#C9CED0", 0.7, 0.1)
mat("sheet_clear", "Roof_Translucent", "#E4EEF2", 0.3, 0.0)
mat("glass", "Glass_Skybox", "#6F8FA3", 0.05, 0.1, alpha=0.38)
mat("box_inside", "Skybox_Interior", "#3A332C", 0.9)
mat("box_light", "Skybox_Light", "#FFE2B0", 0.5, emit=4.0)
mat("fascia", "Club_Secondary_Fascia", SECONDARY, 0.5)
mat("trim", "Club_Primary_Trim", PRIMARY, 0.5)
mat("rail", "Railing_White", "#E6E6E1", 0.4, 0.2)
mat("led", "LED_Band", "#14181B", 0.4)
mat("ad1", "Advert_1", "#C8553D", 0.6, emit=0.4)
mat("ad2", "Advert_2", "#2E8B6E", 0.6, emit=0.4)
mat("ad3", "Advert_3", "#E0B44C", 0.6, emit=0.4)
mat("clad_a", "Cladding_A", "#6E7B80", 0.6, 0.2)
mat("clad_b", "Cladding_B", "#56646A", 0.6, 0.2)
mat("door", "Door_Dark", "#1E2322", 0.9)
mat("lamp", "Floodlight_Lamp", "#FFF6E0", 0.3, emit=12.0)
mat("lamp_house", "Floodlight_Housing", "#2A2F31", 0.5, 0.4)
mat("perspex", "Dugout_Perspex", "#BFD6E0", 0.1, alpha=0.45)
# seats + fans (render only; the game rebuilds these from the layout json)
mat("seat_p", "Club_Primary_Seats", PRIMARY, 0.45)
mat("seat_s", "Club_Secondary_Seats", SECONDARY, 0.45)
mat("seat_x", "Seat_Premium", "#3A3F44", 0.6)
mat("seat_metal", "Seat_Bracket", "#4A4F52", 0.5, 0.5)
mat("shirt_p", "Fan_Shirt_Primary", PRIMARY, 0.8)
mat("shirt_s", "Fan_Shirt_Secondary", SECONDARY, 0.8)
RANDOM_SHIRTS = ["#2B2F3A", "#6B6F75", "#1E1E1E", "#A8322D", "#3E6B48", "#8A7F5C"]
for i, h in enumerate(RANDOM_SHIRTS):
    mat(f"shirt_r{i}", f"Fan_Shirt_{i}", h, 0.8)
TROUSERS = ["#3B5B85", "#2E3440", "#1E1E1E", "#6E7378", "#B9A27A", "#6F8DB5"]   # jeans, dark, black, grey, beige, light jeans
for i, h in enumerate(TROUSERS):
    mat(f"trousers{i}", f"Fan_Trousers_{i}", h, 0.8)
SKINS = ["#F1C9A5", "#C99A6E", "#7A5134"]
for i, h in enumerate(SKINS):
    mat(f"skin{i}", f"Fan_Skin_{i}", h, 0.7)

# ------------------------------------------------------------------ mesh accumulator (fast: one bmesh per group+material)
PARTS = {}
CUR = ["structure"]
def _bm(group, mk):
    group = group or CUR[0]
    if (group, mk) not in PARTS:
        PARTS[(group, mk)] = bmesh.new()
    return PARTS[(group, mk)]

_FACES = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
def box(mk, size, center, rot=None, group=None):
    bm = _bm(group, mk)
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    c = Vector(center)
    corners = [Vector((x, y, z)) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
    if rot is not None:
        corners = [rot @ v for v in corners]
    vs = [bm.verts.new(c + v) for v in corners]
    for f in _FACES:
        bm.faces.new([vs[i] for i in f])

def span_box(mk, x0, x1, y0, y1, z0, z1, group=None):
    box(mk, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), group=group)

def beam(mk, a, b, w, h=None, group=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = d.to_track_quat('X', 'Z').to_matrix()
    box(mk, (d.length, w, h if h else w), (a + b) / 2, rot, group)

def prism_x(mk, pts_yz, x0, x1, group=None):
    """Convex Y/Z polygon extruded along X."""
    bm = _bm(group, mk)
    v0 = [bm.verts.new((x0, y, z)) for y, z in pts_yz]
    v1 = [bm.verts.new((x1, y, z)) for y, z in pts_yz]
    bm.faces.new(v0[::-1]); bm.faces.new(v1)
    n = len(pts_yz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((v0[i], v0[j], v1[j], v1[i]))

_ico = bmesh.new()
bmesh.ops.create_icosphere(_ico, subdivisions=1, radius=1.0)
ICO_V = [v.co.copy() for v in _ico.verts]
ICO_F = [[v.index for v in f.verts] for f in _ico.faces]
_ico.free()
def ico(mk, r, center, group):
    bm = _bm(group, mk)
    c = Vector(center)
    vs = [bm.verts.new(c + v * r) for v in ICO_V]
    for f in ICO_F:
        bm.faces.new([vs[i] for i in f])

# ------------------------------------------------------------------ seat blocks / rows
def block_span(i):
    x0 = BOUND[i] + (AISLE_W / 2 if i > 0 else 0.3)
    x1 = BOUND[i + 1] - (AISLE_W / 2 if i < SECTIONS - 1 else 0.3)
    return x0, x1

VOM_X = [BOUND[a] for a in VOM_AISLES]

def subtract(segs, cuts):
    out = list(segs)
    for c0, c1 in cuts:
        nxt = []
        for a, b in out:
            if c1 <= a or c0 >= b:
                nxt.append((a, b))
                continue
            if a < c0:
                nxt.append((a, c0))
            if c1 < b:
                nxt.append((c1, b))
        out = nxt
    return [(a, b) for a, b in out if b - a > 0.01]

def vom_cuts(k):
    return [(x - VOM_CLEAR, x + VOM_CLEAR) for x in VOM_X] if (k in VOM_ROWS or k == LANDING_ROW) else []

def seat_xs(i):
    x0, x1 = block_span(i)
    c = (x0 + x1) / 2
    return [c + (j - (SEATS_PER_BLOCK - 1) / 2) * SEAT_PITCH for j in range(SEATS_PER_BLOCK)]

# ================================================================== STRUCTURE
# --- pitch-side front wall, advert band, raised front walkway
span_box("concrete", -HW, HW, -0.2, 0.0, 0.0, L_Z0 + 1.0)
span_box("concrete", -HW - 0.05, HW + 0.05, -0.28, 0.02, L_Z0 + 1.0, L_Z0 + 1.08)
span_box("trim", -HW, HW, -0.24, -0.2, L_Z0 + 0.45, L_Z0 + 0.8)
span_box("concrete", -HW, HW, 0.0, L_Y0, 0.0, L_Z0)
for x in [-HW + 0.3 + k * (W - 0.6) / 40 for k in range(41)]:
    beam("rail", (x, -0.1, L_Z0 + 1.08), (x, -0.1, L_Z0 + 1.5), 0.04)
beam("rail", (-HW + 0.3, -0.1, L_Z0 + 1.5), (HW - 0.3, -0.1, L_Z0 + 1.5), 0.05)

# --- stairs: steps of max ~0.3 m with yellow nosings, and handrails
def stair(xc, width, k0, k1, yf, zf, tread, z_first_low, z_floor):
    a, b = xc - width / 2, xc + width / 2
    for k in range(k0, k1 + 1):
        y0, ztop = yf(k), zf(k)
        zlow = zf(k - 1) if k > 0 else z_first_low
        n = max(2, math.ceil((ztop - zlow) / 0.3 - 1e-6))
        for j in range(n):
            zs = zlow + (j + 1) * (ztop - zlow) / n
            ys = y0 + j * tread / n
            span_box("concrete_dark", a, b, ys, ys + tread / n, z_floor, zs)
            span_box("step_edge", a, b, ys, ys + 0.05, zs, zs + 0.01)

def stair_rail(xc, k0, k1, yf, zf, tread, rail_h=0.95):
    p0 = Vector((xc, yf(k0) + 0.1, zf(k0) + rail_h - 0.2))
    p1 = Vector((xc, yf(k1) + tread - 0.1, zf(k1) + rail_h))
    beam("rail", p0, p1, 0.05)
    for t in (0.0, 0.33, 0.66, 1.0):
        p = p0.lerp(p1, t)
        beam("rail", (xc, p.y, p.z - rail_h + 0.1), (xc, p.y, p.z), 0.045)

# --- lower tier rows (cut out around the tunnels and their side stairs)
for i in range(SECTIONS):
    bx0, bx1 = block_span(i)
    for k in range(L_ROWS):
        y0, z = ly(k), lz(k)
        for a, b in subtract([(bx0, bx1)], vom_cuts(k)):
            span_box("concrete", a, b, y0, y0 + L_TREAD, 0.0, z)
            span_box("step_edge", a, b, y0, y0 + 0.05, z, z + 0.01)

# --- cross-aisle behind row 9, with a rail on the front edge of row 10 (open at every stair)
GY0, GY1, GZ = ly(CROSS_ROW - 1) + L_TREAD, ly(CROSS_ROW), lz(CROSS_ROW - 1)
span_box("concrete_dark", -HW, HW, GY0, GY1, 0.0, GZ)
span_box("step_edge", -HW, HW, GY0, GY0 + 0.05, GZ, GZ + 0.01)
gaps = [(BOUND[i] - AISLE_W / 2, BOUND[i] + AISLE_W / 2) for i in range(1, SECTIONS) if BOUND[i] not in VOM_X]
gaps += [(x - VOM_CLEAR, x + VOM_CLEAR) for x in VOM_X]
yr, zr = ly(CROSS_ROW) + 0.08, lz(CROSS_ROW) + 0.9
for a, b in subtract([(-HW + 0.2, HW - 0.2)], gaps):
    beam("rail", (a, yr, zr), (b, yr, zr), 0.05)
    n = max(1, int((b - a) / 2.5))
    for j in range(n + 1):
        x = a + (b - a) * j / n
        beam("rail", (x, yr, lz(CROSS_ROW)), (x, yr, zr), 0.04)

# --- lower tier stairs; on 4 of them a tunnel opens onto the cross-aisle and the stair splits around it
for i in range(1, SECTIONS):
    xc = BOUND[i]
    if xc not in VOM_X:
        stair(xc, AISLE_W, 0, L_ROWS - 1, ly, lz, L_TREAD, L_Z0, 0.0)
        stair_rail(xc, 0, CROSS_ROW - 1, ly, lz, L_TREAD)
        stair_rail(xc, CROSS_ROW, L_ROWS - 1, ly, lz, L_TREAD)
        continue
    stair(xc, AISLE_W, 0, CROSS_ROW - 1, ly, lz, L_TREAD, L_Z0, 0.0)          # front stair: cross-aisle down to the walkway
    stair_rail(xc, 0, CROSS_ROW - 1, ly, lz, L_TREAD)
    for sgn in (-1, 1):                                                         # two side stairs around the tunnel
        sx = xc + sgn * (VOM_W / 2 + VOM_WALL + SIDE_AISLE / 2)
        stair(sx, SIDE_AISLE, CROSS_ROW, VOM_ROWS[-1], ly, lz, L_TREAD, L_Z0, 0.0)
    stair(xc, 2 * VOM_CLEAR, LANDING_ROW, LANDING_ROW, ly, lz, L_TREAD, L_Z0, 0.0)   # landing: they merge again
    stair(xc, AISLE_W, LANDING_ROW + 1, L_ROWS - 1, ly, lz, L_TREAD, L_Z0, 0.0)
    stair_rail(xc, LANDING_ROW + 1, L_ROWS - 1, ly, lz, L_TREAD)
    # the tunnel: floor level with the cross-aisle, dark mouth under the landing, side walls with rails
    x0, x1 = xc - VOM_W / 2, xc + VOM_W / 2
    span_box("concrete_dark", x0, x1, ly(CROSS_ROW), ly(LANDING_ROW), 0.0, GZ)
    span_box("door", x0, x1, ly(LANDING_ROW) - 0.04, ly(LANDING_ROW) - 0.01, GZ, lz(VOM_ROWS[-1]))
    for sgn in (-1, 1):
        w0, w1 = sorted((xc + sgn * VOM_W / 2, xc + sgn * (VOM_W / 2 + VOM_WALL)))
        for k in VOM_ROWS:
            span_box("concrete", w0, w1, ly(k), ly(k) + L_TREAD, 0.0, lz(k) + 0.9)
        xr = (w0 + w1) / 2
        beam("rail", (xr, ly(CROSS_ROW), lz(CROSS_ROW) + 0.95), (xr, ly(LANDING_ROW), lz(VOM_ROWS[-1]) + 0.95), 0.05)
    beam("rail", (x0, ly(LANDING_ROW) + 0.05, lz(LANDING_ROW) + 0.9), (x1, ly(LANDING_ROW) + 0.05, lz(LANDING_ROW) + 0.9), 0.05)

# --- block behind the lower tier (concourse inside), balcony + skyboxes
span_box("concrete_dark", -HW, HW, L_BACK, FACADE_Y, 0.0, BAL_Z)
span_box("concrete", -HW, HW, BAL_Y0, BAL_Y1, BAL_Z - 0.1, BAL_Z)
span_box("concrete", -HW, HW, BAL_Y0, BAL_Y0 + 0.2, BAL_Z, BAL_Z + 0.25)          # balcony upstand
span_box("glass", -HW, HW, BAL_Y0 + 0.06, BAL_Y0 + 0.1, BAL_Z + 0.25, BAL_Z + 1.05)
beam("rail", (-HW, BAL_Y0 + 0.08, BAL_Z + 1.08), (HW, BAL_Y0 + 0.08, BAL_Z + 1.08), 0.06)
box_w = SEC_W / BOXES_PER_SEC
span_box("glass", -HW, HW, BAL_Y1, BAL_Y1 + 0.04, BAL_Z, BOX_Z1)                  # glass front
span_box("box_inside", -HW, HW, BAL_Y1, BOX_Y1, BAL_Z - 0.05, BAL_Z)               # box floors
span_box("box_inside", -HW, HW, BOX_Y1, BOX_Y1 + 0.1, BAL_Z, BOX_Z1)               # box back wall
span_box("concrete_dark", -HW, HW, BOX_Y1 + 0.1, FACADE_Y, BAL_Z, U_SOFFIT)        # corridor behind boxes
span_box("concrete", -HW, HW, BAL_Y1 - 0.2, BOX_Y1, BOX_Z1, U_SOFFIT)              # slab above boxes
for j in range(SECTIONS * BOXES_PER_SEC + 1):
    x = -HW + j * box_w
    span_box("steel", x - 0.06, x + 0.06, BAL_Y1 - 0.05, BAL_Y1 + 0.08, BAL_Z, BOX_Z1)   # mullion
    if j < SECTIONS * BOXES_PER_SEC:
        span_box("box_inside", x - 0.05, x + 0.05, BAL_Y1, BOX_Y1, BAL_Z, BOX_Z1)        # partition
        span_box("box_light", x + 0.6, x + box_w - 0.6, BAL_Y1 + 1.5, BOX_Y1 - 1.0, BOX_Z1 - 0.06, BOX_Z1 - 0.02)
        span_box("box_inside", x + 0.8, x + box_w - 0.8, BAL_Y1 + 1.8, BAL_Y1 + 3.0, BAL_Z, BAL_Z + 0.75)  # table/bar
        # balcony dividers between boxes
        span_box("glass", x - 0.03, x + 0.03, BAL_Y0 + 0.2, BAL_Y1, BAL_Z, BAL_Z + 1.0)
span_box("steel", -HW, HW, BAL_Y1 - 0.05, BAL_Y1 + 0.08, BOX_Z1 - 0.12, BOX_Z1)      # transom

# --- upper tier: front parapet with LED band, walkway, rows on a soffit
span_box("concrete", -HW, HW, U_FRONT_Y - 0.25, U_FRONT_Y, U_SOFFIT - 0.4, U_Z0 + 1.05)
span_box("led", -HW, HW, U_FRONT_Y - 0.3, U_FRONT_Y - 0.25, U_SOFFIT - 0.25, U_Z0 + 0.8)
for i in range(SECTIONS * 3):
    x0 = -HW + i * SEC_W / 3
    if i % 2 == 0:
        span_box(("ad1", "ad2", "ad3")[(i // 2) % 3], x0 + 0.4, x0 + SEC_W / 3 - 0.4, U_FRONT_Y - 0.32, U_FRONT_Y - 0.3, U_SOFFIT - 0.1, U_Z0 + 0.65)
span_box("trim", -HW, HW, U_FRONT_Y - 0.31, U_FRONT_Y + 0.02, U_Z0 + 1.0, U_Z0 + 1.1)
span_box("concrete", -HW, HW, U_FRONT_Y, U_Y0, U_SOFFIT, U_Z0)
span_box("concrete", -HW, HW, U_FRONT_Y - 0.25, BOX_Y1, U_SOFFIT - 0.4, U_SOFFIT)   # soffit
for x in [-HW + 0.3 + k * (W - 0.6) / 40 for k in range(41)]:
    beam("rail", (x, U_FRONT_Y - 0.12, U_Z0 + 1.1), (x, U_FRONT_Y - 0.12, U_Z0 + 1.45), 0.04)
beam("rail", (-HW + 0.3, U_FRONT_Y - 0.12, U_Z0 + 1.45), (HW - 0.3, U_FRONT_Y - 0.12, U_Z0 + 1.45), 0.05)
for i in range(SECTIONS):
    bx0, bx1 = block_span(i)
    for k in range(U_ROWS):
        y0, z = uy(k), uz(k)
        span_box("concrete", bx0, bx1, y0, y0 + U_TREAD, U_SOFFIT, z)
        span_box("step_edge", bx0, bx1, y0, y0 + 0.05, z, z + 0.01)
for i in range(1, SECTIONS):
    stair(BOUND[i], AISLE_W, 0, U_ROWS - 1, uy, uz, U_TREAD, U_Z0, U_SOFFIT)
    stair_rail(BOUND[i], 0, U_ROWS - 1, uy, uz, U_TREAD, rail_h=1.0)
# rear walkway + back wall
span_box("concrete", -HW, HW, U_BACK, FACADE_Y, U_SOFFIT, U_TOP)
span_box("concrete_dark", -HW, HW, FACADE_Y - 0.4, FACADE_Y, U_TOP, U_TOP + 1.6)

# --- end walls (clad), following the stand profile
profile = [(-0.2, 0.0), (-0.2, L_Z0 + 1.0), (L_BACK, L_TOP + 1.1), (L_BACK, U_Z0 + 1.1),
           (U_BACK, U_TOP + 1.1), (FACADE_Y, U_TOP + 1.6), (FACADE_Y, 0.0)]
for s in (-1, 1):
    x = s * HW
    prism_x("clad_a", profile, min(x, x + s * 0.35), max(x, x + s * 0.35))

# --- back facade: cladding panels, concourse window band, stair cores, sign
pw = W / 36
for j in range(36):
    x0 = -HW + j * pw
    span_box("clad_a" if j % 2 == 0 else "clad_b", x0, x0 + pw, FACADE_Y, FACADE_Y + 0.12, 0.0, U_TOP + 1.6)
span_box("glass", -HW, HW, FACADE_Y + 0.12, FACADE_Y + 0.16, BAL_Z + 0.4, BAL_Z + 2.4)
span_box("steel", -HW, HW, FACADE_Y + 0.12, FACADE_Y + 0.25, BAL_Z + 2.4, BAL_Z + 2.6)
for cx in (-34.5, 0.0, 34.5):
    span_box("clad_b", cx - 3.5, cx + 3.5, FACADE_Y + 0.12, FACADE_Y + 4.5, 0.0, U_TOP + 3.0)
    for gx in (cx - 1.6, cx + 1.6):
        span_box("glass", gx - 0.45, gx + 0.45, FACADE_Y + 4.5, FACADE_Y + 4.55, 3.5, U_TOP + 2.0)
    span_box("door", cx - 1.6, cx + 1.6, FACADE_Y + 4.5, FACADE_Y + 4.56, 0.0, 2.7)
    span_box("trim", cx - 2.2, cx + 2.2, FACADE_Y + 4.5, FACADE_Y + 6.0, 2.9, 3.1)   # entrance canopy

# ------------------------------------------------------------------ pixel font (5x7) for the seat text and the facade sign
FONT = {
    "S": [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}
TEXT = "SUNDAY LEAGUE"                        # Marcel: fine for the POC (later: the player's club name)
def text_bitmap(text):
    rows = ["" for _ in range(7)]
    for n, ch in enumerate(text):
        for r in range(7):
            rows[r] += FONT[ch][r] + ("." if n < len(text) - 1 else "")
    return rows
BITMAP = text_bitmap(TEXT)
TEXT_COLS = len(BITMAP[0])                   # 77

# facade sign (white pixel blocks above the centre core; read from behind, so mirrored in x)
px = 0.14   # fits between the rear columns at x = ±5.75
for r in range(7):
    for c in range(TEXT_COLS):
        if BITMAP[r][c] == "#":
            x = -(c - TEXT_COLS / 2 + 0.5) * px
            z = U_TOP + 6.0 - r * px
            span_box("fascia", x - px / 2 + 0.01, x + px / 2 - 0.01, FACADE_Y + 0.12, FACADE_Y + 0.22, z - px / 2 + 0.01, z + px / 2 - 0.01)

# ------------------------------------------------------------------ cantilever roof
for x in BOUND:
    tb, tt = Vector((x, COL_Y, TOP_BACK_Z)), Vector((x, ROOF_FRONT_Y, TOP_TIP_Z))
    bb, bt = Vector((x, COL_Y, BOT_BACK_Z)), Vector((x, ROOF_FRONT_Y + 0.4, BOT_TIP_Z))
    beam("truss", tb, tt, 0.35, 0.45)
    beam("truss", bb, bt, 0.35, 0.4)
    n = 12
    for k in range(n + 1):                                   # warren-truss webs
        t0 = k / n
        a = tb.lerp(tt, t0)
        b = bb.lerp(bt, t0)
        beam("truss", a, b, 0.18)
        if k < n:
            beam("truss", b, tb.lerp(tt, (k + 1) / n), 0.16)
    beam("steel", (x, COL_Y, 0.0), (x, COL_Y, TOP_BACK_Z + 0.2), 0.8, 0.8)                  # rear column
    beam("steel", (x, COL_Y + 0.3, TOP_BACK_Z), (x, COL_Y + 7.5, 0.0), 0.35, 0.35)         # back-stay tie
    span_box("concrete_dark", x - 0.8, x + 0.8, COL_Y + 6.7, COL_Y + 8.3, 0.0, 0.6)        # tie foundation

def roof_z(y):
    t = (y - COL_Y) / (ROOF_FRONT_Y - COL_Y)
    return TOP_BACK_Z + (TOP_TIP_Z - TOP_BACK_Z) * t
slope = math.atan2(TOP_BACK_Z - TOP_TIP_Z, COL_Y - ROOF_FRONT_Y)
R = Matrix.Rotation(slope, 3, 'X')
RX0, RX1 = -HW - 1.0, HW + 1.0
def roof_strip(mk, y0, y1, dz, thick):
    L = math.hypot(y1 - y0, roof_z(y0) - roof_z(y1))
    ym = (y0 + y1) / 2
    box(mk, (RX1 - RX0, L, thick), (0, ym, roof_z(ym) + dz), R)
CLEAR = 4.0
roof_strip("sheet_clear", ROOF_FRONT_Y, ROOF_FRONT_Y + CLEAR, 0.25, 0.03)
roof_strip("sheet", ROOF_FRONT_Y + CLEAR, COL_Y + 0.6, 0.25, 0.03)
roof_strip("sheet_under", ROOF_FRONT_Y + CLEAR, COL_Y + 0.6, 0.2, 0.01)
L_roof = math.hypot(COL_Y + 0.6 - ROOF_FRONT_Y - CLEAR, roof_z(ROOF_FRONT_Y + CLEAR) - roof_z(COL_Y + 0.6))
ym = (ROOF_FRONT_Y + CLEAR + COL_Y + 0.6) / 2
for k in range(int((RX1 - RX0) / 0.3)):
    xr = RX0 + 0.15 + k * 0.3
    box("sheet", (0.06, L_roof, 0.05), (xr, ym, roof_z(ym) + 0.29), R)
for k in range(10):                                          # purlins
    y = ROOF_FRONT_Y + 0.6 + k * (COL_Y - ROOF_FRONT_Y - 1.0) / 9
    span_box("steel", RX0, RX1, y - 0.08, y + 0.08, roof_z(y) - 0.02, roof_z(y) + 0.2)
# front fascia (club colour band) + gutter at the back
fz = TOP_TIP_Z
span_box("fascia", RX0 - 0.05, RX1 + 0.05, ROOF_FRONT_Y - 0.12, ROOF_FRONT_Y, fz - 1.1, fz + 0.4)
span_box("trim", RX0 - 0.05, RX1 + 0.05, ROOF_FRONT_Y - 0.14, ROOF_FRONT_Y - 0.1, fz + 0.32, fz + 0.45)
span_box("trim", RX0 - 0.05, RX1 + 0.05, ROOF_FRONT_Y - 0.14, ROOF_FRONT_Y - 0.1, fz - 1.15, fz - 1.02)
span_box("steel", RX0, RX1, COL_Y + 0.4, COL_Y + 0.8, TOP_BACK_Z - 0.1, TOP_BACK_Z + 0.25)

def chord_z(y):
    t = (y - COL_Y) / (ROOF_FRONT_Y + 0.4 - COL_Y)
    return BOT_BACK_Z + (BOT_TIP_Z - BOT_BACK_Z) * t
for j in range(36):                                          # cladding from the back wall up to the roof
    x0 = -HW + j * pw
    span_box("clad_a" if j % 2 == 0 else "clad_b", x0, x0 + pw, FACADE_Y, FACADE_Y + 0.12, U_TOP + 1.6, roof_z(FACADE_Y) + 0.2)
for s in (-1, 1):                                            # glazed wind screens at the ends
    x = s * HW
    prism_x("glass", [(U_FRONT_Y, U_Z0 + 1.1), (U_BACK, U_TOP + 1.1), (FACADE_Y, U_TOP + 1.6),
                      (FACADE_Y, chord_z(FACADE_Y)), (U_FRONT_Y, chord_z(U_FRONT_Y))],
            min(x, x + s * 0.06), max(x, x + s * 0.06))
    for y in (U_FRONT_Y, (U_FRONT_Y + FACADE_Y) / 2, FACADE_Y):   # mullions
        z0 = U_Z0 + 1.1 if y == U_FRONT_Y else (U_TOP + 1.1 if y != FACADE_Y else U_TOP + 1.6)
        beam("steel", (x + s * 0.08, y, z0 if y != (U_FRONT_Y + FACADE_Y) / 2 else (U_Z0 + U_TOP) / 2 + 1.1), (x + s * 0.08, y, chord_z(y)), 0.12)

# ------------------------------------------------------------------ floodlights (Marcel: both roof bar and masts)
PITCH_CENTRE = Vector((0.0, -40.0, 0.0))
def lamp_panel(center, target, cols, rows, du=0.8, dv=0.7):
    d = (Vector(target) - Vector(center)).normalized()
    rot = d.to_track_quat('-Y', 'Z').to_matrix()
    c = Vector(center)
    box("lamp_house", (cols * du + 0.3, 0.12, rows * dv + 0.3), c + rot @ Vector((0, 0.35, 0)), rot)
    for i in range(cols):
        for j in range(rows):
            off = Vector(((i - (cols - 1) / 2) * du, 0.0, (j - (rows - 1) / 2) * dv))
            box("lamp_house", (du * 0.85, 0.5, dv * 0.85), c + rot @ off, rot)
            box("lamp", (du * 0.7, 0.03, dv * 0.7), c + rot @ (off + Vector((0, -0.26, 0))), rot)

# roof-edge gantry: catwalk + a lamp every ~3.2 m
gy, gz = ROOF_FRONT_Y + 1.2, BOT_TIP_Z - 0.6
span_box("steel", RX0 + 1, RX1 - 1, gy - 0.4, gy + 0.4, gz - 0.05, gz + 0.03)
beam("rail", (RX0 + 1, gy + 0.4, gz + 1.0), (RX1 - 1, gy + 0.4, gz + 1.0), 0.04)
nl = int((W - 2) / 3.2)
for k in range(nl + 1):
    x = -HW + 1 + k * (W - 2) / nl
    lamp_panel((x, gy - 0.8, gz - 0.5), (x * 0.5, -40.0, 0.0), 1, 1, 0.9, 0.8)

# masts at both front corners
def mast(x0, y0, h=40.0):
    base, top = 1.5, 0.6
    segs = 10
    def corner(sx, sy, z):
        w = base + (top - base) * (z / h)
        return Vector((x0 + sx * w, y0 + sy * w, z))
    cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for sx, sy in cs:
        beam("steel", corner(sx, sy, 0), corner(sx, sy, h), 0.2)
    for s in range(segs + 1):
        z = h * s / segs
        for a in range(4):
            p, q = cs[a], cs[(a + 1) % 4]
            beam("steel", corner(*p, z), corner(*q, z), 0.1)
            if s < segs:
                z2 = h * (s + 1) / segs
                beam("steel", corner(*p, z), corner(*q, z2), 0.07)
                beam("steel", corner(*q, z), corner(*p, z2), 0.07)
    span_box("concrete_dark", x0 - 2.0, x0 + 2.0, y0 - 2.0, y0 + 2.0, 0.0, 0.5)
    span_box("steel", x0 - 1.3, x0 + 1.3, y0 - 1.3, y0 + 1.3, h - 0.1, h + 0.05)     # platform
    head = Vector((x0, y0, h + 2.4))
    lamp_panel(head, (x0, y0 - MAST_DIST, 0.0), 6, 4)
# Marcel: masts in all 4 corners -> one separate model (floodlight_mast.glb), placed 4x by the game
CUR[0] = "mast"
mast(0.0, 0.0)
CUR[0] = "structure"

# ------------------------------------------------------------------ pitch-side: advert boards + dugouts
for k in range(int(W / 6)):
    x0 = -HW + 1.5 + k * 6.0
    if abs(x0 + 3.0) < 14:          # gap behind the dugouts
        continue
    span_box(("ad1", "ad2", "ad3")[k % 3], x0, x0 + 5.9, -2.6, -2.5, 0.05, 0.95)
    span_box("lamp_house", x0, x0 + 5.9, -2.5, -2.3, 0.05, 0.95)
for s in (-1, 1):
    cx = s * 7.5
    span_box("perspex", cx - 3.5, cx + 3.5, -2.2, -2.15, 0.0, 2.0)            # back
    span_box("perspex", cx - 3.5, cx + 3.5, -4.0, -2.15, 1.95, 2.0)           # roof
    for e in (cx - 3.5, cx + 3.45):
        span_box("perspex", e, e + 0.05, -4.0, -2.15, 0.0, 2.0)
    span_box("concrete_dark", cx - 3.4, cx + 3.4, -2.8, -2.25, 0.0, 0.45)       # bench base

# ================================================================== SEATS + FANS
# Godot coordinates: gx = x, gy = z, gz = -y   (glTF Y-up conversion)
layout = {"text": TEXT, "primary": PRIMARY, "secondary": SECONDARY, "trousers": TROUSERS, "seats": [], "fans": []}

def text_mask(x, k):
    """1 if this upper-tier seat is part of a letter."""
    if k > 13:
        return 0
    prow = (13 - k) // 2
    col = math.floor((x + TEXT_COLS / 2 * 1.0) / 1.0)
    if 0 <= col < TEXT_COLS and BITMAP[prow][col] == "#":
        return 1
    return 0

def add_seat(x, y, z, kind):
    layout["seats"].append([round(x, 3), round(z, 3), round(-y, 3), kind])
    g = "seats"
    box("seat_metal", (0.06, 0.06, 0.3), (x, y, z + 0.15), group=g)
    mk = ("seat_p", "seat_s", "seat_x")[kind]
    box(mk, (0.44, 0.38, 0.05), (x, y - 0.04, z + 0.42), Matrix.Rotation(math.radians(-4), 3, 'X'), g)
    box(mk, (0.44, 0.05, 0.36), (x, y + 0.17, z + 0.62), Matrix.Rotation(math.radians(-12), 3, 'X'), g)

def add_fan(x, y, z, busy):
    if random.random() > busy:
        return
    r = random.random()
    if r < 0.65:
        kind, shirt, col = 0, "shirt_p", PRIMARY
    elif r < 0.8:
        kind, shirt, col = 1, "shirt_s", SECONDARY
    else:
        n = random.randrange(len(RANDOM_SHIRTS))
        kind, shirt, col = 2, f"shirt_r{n}", RANDOM_SHIRTS[n]
    skin = random.choices(range(3), weights=(5, 3, 2))[0]
    tr = random.choices(range(len(TROUSERS)), weights=(4, 3, 2, 2, 1, 2))[0]
    layout["fans"].append([round(x, 3), round(z, 3), round(-y, 3), kind, col, skin, tr])
    g = "fans"
    box(f"trousers{tr}", (0.32, 0.44, 0.15), (x, y - 0.16, z + 0.52), group=g)
    box(f"trousers{tr}", (0.26, 0.13, 0.45), (x, y - 0.36, z + 0.24), group=g)
    box(shirt, (0.32, 0.22, 0.5), (x, y + 0.06, z + 0.82), group=g)
    for s in (-1, 1):
        box(shirt, (0.08, 0.12, 0.44), (x + s * 0.2, y, z + 0.81), group=g)
    ico(f"skin{skin}", 0.11, (x, y + 0.04, z + 1.21), g)

BUSY = 0.30                                   # Marcel: ~30% full
def busy_at(x):
    return BUSY * (1.3 - 0.6 * abs(x) / HW)  # fuller in the middle, avg ≈ 30%

for i in range(SECTIONS):
    for k in range(L_ROWS):
        y = ly(k) + L_TREAD * 0.55
        for x in seat_xs(i):
            if vom_cuts(k) and any(abs(x - vx) < VOM_CLEAR + 0.22 for vx in VOM_X):
                continue
            add_seat(x, y, lz(k), 0)
            add_fan(x, y, lz(k), busy_at(x))
    for k in range(U_ROWS):
        y = uy(k) + U_TREAD * 0.55
        for x in seat_xs(i):
            add_seat(x, y, uz(k), text_mask(x, k))
            add_fan(x, y, uz(k), busy_at(x) * 0.85)
# skybox balconies: 2 rows of premium seats per box
for j in range(SECTIONS * BOXES_PER_SEC):
    x0 = -HW + j * box_w
    for r in range(2):
        y = BAL_Y0 + 0.75 + r * 0.9
        z = BAL_Z + r * 0.3
        if r == 1:
            span_box("concrete", x0 + 0.1, x0 + box_w - 0.1, y - 0.45, y + 0.45, BAL_Z, z)
        for n in range(6):
            x = x0 + box_w / 2 + (n - 2.5) * 0.55
            add_seat(x, y, z, 2)
            add_fan(x, y, z, 0.25)

# ------------------------------------------------------------------ build objects
groups = {}
for (group, mk), bm in PARTS.items():
    me = bpy.data.meshes.new(f"{group}_{MATS[mk].name}")
    bm.to_mesh(me); bm.free()
    me.materials.append(MATS[mk])
    prefix = {"structure": "BigStand", "mast": "Mast"}.get(group, group)
    ob = bpy.data.objects.new(f"{prefix}_{MATS[mk].name}", me)
    scene.collection.objects.link(ob)
    groups.setdefault(group, []).append(ob)
root = bpy.data.objects.new("BigStand", None)
scene.collection.objects.link(root)
for ob in groups["structure"]:
    ob.parent = root
mast_root = bpy.data.objects.new("FloodlightMast", None)
scene.collection.objects.link(mast_root)
for ob in groups["mast"]:
    ob.parent = mast_root

def faces(obs): return sum(len(o.data.polygons) for o in obs)
print(f"BIG STAND: structure {faces(groups['structure'])} faces, seats {len(layout['seats'])} "
      f"({faces(groups['seats'])} faces), fans {len(layout['fans'])} ({faces(groups['fans'])} faces)")

os.makedirs(os.path.join(REPO, "assets", "models"), exist_ok=True)
with open(os.path.join(REPO, "assets", "models", "big_stand_layout.json"), "w") as f:
    json.dump(layout, f, separators=(",", ":"))
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
for ob in groups["structure"]:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(REPO, "assets", "models", "big_stand.glb"),
                          export_format='GLB', use_selection=True)
bpy.ops.object.select_all(action='DESELECT')
mast_root.select_set(True)
for ob in groups["mast"]:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(REPO, "assets", "models", "floodlight_mast.glb"),
                          export_format='GLB', use_selection=True)
print("EXPORTED", f"mast {faces(groups['mast'])} faces")

# ------------------------------------------------------------------ preview renders
if "--render" in sys.argv:
    world = bpy.data.worlds.new("World"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.86, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    grass = mat("grass", "Grass", "#4E8F3A", 0.9)
    line = mat("line", "Line", "#F2F2F2", 0.8)
    span_box("grass", -160, 160, -160, 120, -0.02, -0.01, group="ground")
    span_box("line", -70, 70, -6.06, -5.94, -0.01, 0.0, group="ground")          # touchline
    span_box("line", -0.06, 0.06, -74.0, -6.0, -0.01, 0.0, group="ground")       # halfway line
    for (group, mk), bm in list(PARTS.items()):
        if group == "ground":
            me = bpy.data.meshes.new(mk); bm.to_mesh(me); bm.free(); me.materials.append(MATS[mk])
            scene.collection.objects.link(bpy.data.objects.new(mk, me))
    centre = Vector((0.0, -40.0))
    corners = [(sx * 60.5, y) for sx in (-1, 1) for y in (2.0, -82.0)]
    for n, (mx, my) in enumerate(corners):
        holder = mast_root if n == 0 else bpy.data.objects.new(f"MastHolder{n}", None)
        if n > 0:
            scene.collection.objects.link(holder)
            for ob in groups["mast"]:
                cp = ob.copy()
                scene.collection.objects.link(cp)
                cp.parent = holder
        d = centre - Vector((mx, my))
        holder.location = (mx, my, 0.0)
        holder.rotation_euler = (0.0, 0.0, math.atan2(d.x, -d.y))
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.2; sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
    scene.collection.objects.link(sun)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    scene.view_settings.view_transform = 'AgX'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam); scene.camera = cam
    views = {
        "pitch_wide": ((-62.0, -78.0, 16.0), (2.0, 12.0, 11.0), 28),
        "head_on": ((0.0, -95.0, 22.0), (0.0, 14.0, 12.0), 30),
        "lower_tier": ((14.0, -9.0, 2.5), (-4.0, 14.0, 12.0), 22),
        "outside_back": ((70.0, 95.0, 26.0), (0.0, 25.0, 12.0), 30),
        "tunnel": ((-17.25, -7.0, 7.5), (-17.25, 12.0, 5.0), 30),
    }
    only = sys.argv[sys.argv.index("--views") + 1].split(",") if "--views" in sys.argv else list(views)
    for name in only:
        pos, target, lens = views[name]
        cam.location = pos
        cam.data.lens = lens
        cam.data.clip_end = 1000
        cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(RENDER_DIR, f"bigstand_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", name)
