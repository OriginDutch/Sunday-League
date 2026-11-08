"""The Shed — first stand section for Sunday League.

Blender 5 (bpy) build script. Run:  python3 build_shed.py [--rows N] [--render] [--render-set]
--rows N: export assets/models/the_shed_N.glb (3 also writes the_shed.glb).
--render-set: 3, 5 and 8 rows side by side for previews (design/3d/the_shed/rows_*.png).
Units: metres. Blender axes: X = along the touchline, -Y = towards the pitch, Z = up.
One section: 11.5 m wide, 3, 5 or 8 rows of tip-up seats (--rows N), steel frame, corrugated roof/back/sides.
Materials are named so the game can recolour them (Club_Primary = seats, Club_Secondary = fascia).
"""
import bpy, bmesh, math, sys
from mathutils import Vector, Matrix

W = 11.5                 # section width
HW = W / 2
ROWS = 3
for _i, _a in enumerate(sys.argv):
    if _a == "--rows":
        ROWS = int(sys.argv[_i + 1])
TREAD = 0.85             # row depth
RISE = 0.42              # row height step
WALK_D = 1.05            # front walkway depth
WALK_Z = 0.45            # front walkway height (raised so the front row sees over the wall)
ROW0_Z = 0.9             # first row tread height
AISLE_W = 1.2            # central gangway
SEAT_PITCH = 0.5
BACK_Y = WALK_D + ROWS * TREAD          # back edge of the top row
ROOF_FRONT_Y = -0.25                     # roof overhang over the walkway
ROOF_BACK_Y = BACK_Y + 0.35
ROOF_BACK_Z = ROW0_Z + (ROWS - 1) * RISE + 2.31    # head room over the top row (3 rows: 4.05 as before)
ROOF_FRONT_Z = ROOF_BACK_Z + 0.5
COLS_X = [-HW + 0.25, -1.95, 1.95, HW - 0.25]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------------ materials
def mat(name, hex_, rough=0.8, metal=0.0):
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
    return m

M = {
    "concrete": mat("Concrete", "#A3A29B"),
    "concrete_dark": mat("Concrete_Dark", "#85847D"),
    "step_edge": mat("Step_Edge_Yellow", "#D9B43A", 0.6),
    "steel": mat("Steel_Frame", "#3B4A44", 0.5, 0.3),
    "sheet": mat("Corrugated_Sheet", "#9BA6AA", 0.55, 0.4),
    "sheet_under": mat("Corrugated_Underside", "#7D888C", 0.6, 0.3),
    "seat": mat("Club_Primary_Seats", "#2F6DB5", 0.45),
    "fascia": mat("Club_Secondary_Fascia", "#ECE8DD", 0.5),
    "trim": mat("Club_Primary_Trim", "#2F6DB5", 0.5),
    "rail": mat("Railing_White", "#E6E6E1", 0.4, 0.2),
    "gutter": mat("Gutter", "#2C3330", 0.5, 0.2),
    "brick": mat("Front_Wall", "#7B4A3A", 0.9),
    "ad1": mat("Advert_1", "#C8553D", 0.6),
    "ad2": mat("Advert_2", "#2E8B6E", 0.6),
    "ad3": mat("Advert_3", "#E0B44C", 0.6),
    "seat_metal": mat("Seat_Bracket", "#4A4F52", 0.5, 0.5),
    "dark": mat("Shadow_Gap", "#1E2322", 0.9),
}

parts = []   # (object) collected for joining per material

def box(name, sx, sy, sz, loc, m, rot=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    me.materials.append(m)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def cyl(name, r, depth, loc, m, axis='Z', seg=10):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    me.materials.append(m)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def beam(name, a, b, w, h, m):
    """Rectangular beam from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    rot = d.to_track_quat('X', 'Z').to_matrix()
    return box(name, L, w, h, (a + b) / 2, m, rot)

def poly_prism(name, pts2d, x0, x1, m):
    """Extrude a Y/Z polygon along X (for side screens, end caps)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    v0 = [bm.verts.new((x0, y, z)) for y, z in pts2d]
    v1 = [bm.verts.new((x1, y, z)) for y, z in pts2d]
    bm.faces.new(v0[::-1]); bm.faces.new(v1)
    n = len(pts2d)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((v0[i], v0[j], v1[j], v1[i]))
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(m)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob

def roof_z(y):
    t = (y - ROOF_FRONT_Y) / (ROOF_BACK_Y - ROOF_FRONT_Y)
    return ROOF_FRONT_Z + (ROOF_BACK_Z - ROOF_FRONT_Z) * t

def set_rows(rows):
    """Recompute everything that depends on the row count (a section is built at x = 0, then moved)."""
    global ROWS, BACK_Y, ROOF_BACK_Y, ROOF_BACK_Z, ROOF_FRONT_Z
    ROWS = rows
    BACK_Y = WALK_D + ROWS * TREAD
    ROOF_BACK_Y = BACK_Y + 0.35
    ROOF_BACK_Z = ROW0_Z + (ROWS - 1) * RISE + 2.31
    ROOF_FRONT_Z = ROOF_BACK_Z + 0.5


def build_section(rows, x0=0.0):
    set_rows(rows)
    first = len(parts)
    n_seats = 0
    # ------------------------------------------------------------------ concrete base + terrace
    box("Plinth", W, BACK_Y + 0.6, 0.12, (0, (BACK_Y + 0.6) / 2 - 0.1, 0.06), M["concrete_dark"])
    box("Walkway", W, WALK_D, WALK_Z, (0, WALK_D / 2, WALK_Z / 2), M["concrete"])
    for r in range(ROWS):
        y0 = WALK_D + r * TREAD
        top = ROW0_Z + r * RISE
        # each row is a solid step block, full height to the ground
        box(f"Row{r}", W, TREAD, top, (0, y0 + TREAD / 2, top / 2), M["concrete"])
        # yellow safety nosing on the front edge of each step, both sides of the gangway
        for s in (-1, 1):
            box(f"Nosing{r}{s}", HW - AISLE_W / 2, 0.06, 0.03, (s * (AISLE_W / 2 + (HW - AISLE_W / 2) / 2), y0 + 0.03, top + 0.005), M["step_edge"])
    # gangway half-steps in the centre (two per row)
    for r in range(ROWS):
        y0 = WALK_D + r * TREAD
        base = ROW0_Z + (r - 1) * RISE if r > 0 else WALK_Z
        top = ROW0_Z + r * RISE
        mid = (base + top) / 2
        box(f"AisleStep{r}", AISLE_W, TREAD / 2, mid, (0, y0 + TREAD / 4, mid / 2), M["concrete_dark"])
        box(f"AisleEdge{r}", AISLE_W, 0.06, 0.03, (0, y0 + 0.03, mid + 0.005), M["step_edge"])
        box(f"AisleEdgeB{r}", AISLE_W, 0.06, 0.03, (0, y0 + TREAD / 2 + 0.03, top + 0.005), M["step_edge"])
    # rear upstand behind the top row
    box("RearUpstand", W, 0.25, ROW0_Z + ROWS * RISE + 0.25, (0, BACK_Y + 0.125, (ROW0_Z + ROWS * RISE + 0.25) / 2), M["concrete_dark"])

    # ------------------------------------------------------------------ front wall with advert boards + railing
    box("FrontWall", W, 0.22, 1.05, (0, -0.11, 0.525), M["brick"])
    box("FrontWallCap", W + 0.04, 0.28, 0.06, (0, -0.11, 1.08), M["concrete"])
    ads = [M["ad1"], M["ad2"], M["ad3"], M["ad2"]]
    panel_w = (W - 0.5) / 4
    for i in range(4):
        x = -HW + 0.25 + panel_w * (i + 0.5)
        box(f"Advert{i}", panel_w - 0.12, 0.03, 0.6, (x, -0.235, 0.55), ads[i])
    # crush rail on top of the wall
    for x in [-HW + 0.3 + i * (W - 0.6) / 7 for i in range(8)]:
        cyl(f"RailPost{x:.2f}", 0.025, 0.5, (x, -0.11, 1.36), M["rail"], seg=8)
    cyl("FrontRail", 0.03, W - 0.4, (0, -0.11, 1.62), M["rail"], axis='X', seg=10)
    # gangway handrail, following the steps up the middle
    p0 = Vector((0, WALK_D - 0.1, WALK_Z + 0.95))
    p1 = Vector((0, BACK_Y - 0.2, ROW0_Z + (ROWS - 1) * RISE + 0.95))
    beam("AisleRail", p0, p1, 0.05, 0.05, M["rail"])
    for t in (0.0, 0.5, 1.0):
        p = p0.lerp(p1, t)
        floor = WALK_Z if t == 0 else ROW0_Z + int(t * (ROWS - 1)) * RISE
        beam(f"AisleRailPost{t}", (0, p.y, floor), (0, p.y, p.z), 0.045, 0.045, M["rail"])

    # ------------------------------------------------------------------ seats (tip-up, 0.5 m pitch, gap for the gangway)
    seat_xs = []
    x = -HW + 0.4
    while x < HW - 0.3:
        if abs(x) > AISLE_W / 2 + 0.2:
            seat_xs.append(x)
        x += SEAT_PITCH
    for r in range(ROWS):
        y0 = WALK_D + r * TREAD
        top = ROW0_Z + r * RISE
        sy = y0 + TREAD * 0.55
        for sx in seat_xs:
            # pedestal + bracket
            box(f"SeatLeg{r}_{sx:.2f}", 0.06, 0.06, 0.32, (sx, sy, top + 0.16), M["seat_metal"])
            # seat pan, slightly tipped back
            box(f"SeatPan{r}_{sx:.2f}", 0.42, 0.38, 0.05, (sx, sy - 0.04, top + 0.42), M["seat"], Matrix.Rotation(math.radians(-4), 3, 'X'))
            # back rest, leaning back
            box(f"SeatBack{r}_{sx:.2f}", 0.42, 0.05, 0.36, (sx, sy + 0.17, top + 0.64), M["seat"], Matrix.Rotation(math.radians(-12), 3, 'X'))
            n_seats += 1

    # ------------------------------------------------------------------ steel frame
    col_front_y = 0.25
    col_back_y = BACK_Y + 0.2
    for i, cx in enumerate(COLS_X):
        # front columns stand on the walkway (yes, they block the view a bit — that's the charm)
        box(f"ColF{i}", 0.16, 0.16, roof_z(col_front_y), (cx, col_front_y, roof_z(col_front_y) / 2), M["steel"])
        box(f"ColFBase{i}", 0.3, 0.3, 0.08, (cx, col_front_y, WALK_Z + 0.04), M["concrete_dark"])
        box(f"ColB{i}", 0.16, 0.16, roof_z(col_back_y), (cx, col_back_y, roof_z(col_back_y) / 2), M["steel"])
        # rafter from front overhang to back
        beam(f"Rafter{i}", (cx, ROOF_FRONT_Y + 0.05, roof_z(ROOF_FRONT_Y + 0.05) - 0.16), (cx, ROOF_BACK_Y - 0.05, roof_z(ROOF_BACK_Y - 0.05) - 0.16), 0.12, 0.26, M["steel"])
        # knee braces
        beam(f"KneeF{i}", (cx, col_front_y, roof_z(col_front_y) - 1.0), (cx, col_front_y + 0.9, roof_z(col_front_y + 0.9) - 0.25), 0.07, 0.07, M["steel"])
        beam(f"KneeB{i}", (cx, col_back_y, roof_z(col_back_y) - 1.0), (cx, col_back_y - 0.9, roof_z(col_back_y - 0.9) - 0.25), 0.07, 0.07, M["steel"])
    # purlins across the width
    n_purl = max(6, ROWS + 3)
    for k in range(n_purl):
        y = ROOF_FRONT_Y + 0.2 + k * (ROOF_BACK_Y - ROOF_FRONT_Y - 0.4) / (n_purl - 1)
        box(f"Purlin{k}", W, 0.08, 0.14, (0, y, roof_z(y) - 0.08), M["steel"])
    # front eaves beam
    box("EavesBeam", W, 0.14, 0.3, (0, col_front_y, roof_z(col_front_y) - 0.28), M["steel"])

    # ------------------------------------------------------------------ corrugated roof
    roof_len = math.hypot(ROOF_BACK_Y - ROOF_FRONT_Y, ROOF_FRONT_Z - ROOF_BACK_Z)
    slope = math.atan2(ROOF_FRONT_Z - ROOF_BACK_Z, ROOF_BACK_Y - ROOF_FRONT_Y)
    rot_roof = Matrix.Rotation(-slope, 3, 'X')
    mid_y = (ROOF_FRONT_Y + ROOF_BACK_Y) / 2
    box("RoofSheet", W + 0.3, roof_len, 0.03, (0, mid_y, roof_z(mid_y) + 0.01), M["sheet"], rot_roof)
    box("RoofUnderside", W + 0.3, roof_len, 0.01, (0, mid_y, roof_z(mid_y) - 0.012), M["sheet_under"], rot_roof)
    n_ribs = int((W + 0.3) / 0.22)
    for k in range(n_ribs):
        x = -(W + 0.3) / 2 + 0.11 + k * 0.22
        box(f"RoofRib{k}", 0.05, roof_len, 0.035, (x, mid_y, roof_z(mid_y) + 0.04), M["sheet"], rot_roof)

    # fascia (club colour band, room for the club name later) + gutter + downpipes
    fz = roof_z(ROOF_FRONT_Y)
    box("Fascia", W + 0.36, 0.06, 0.42, (0, ROOF_FRONT_Y - 0.02, fz - 0.12), M["fascia"])
    box("FasciaTrimTop", W + 0.38, 0.07, 0.05, (0, ROOF_FRONT_Y - 0.02, fz + 0.1), M["trim"])
    box("FasciaTrimBot", W + 0.38, 0.07, 0.05, (0, ROOF_FRONT_Y - 0.02, fz - 0.34), M["trim"])
    cyl("Gutter", 0.07, W + 0.3, (0, ROOF_BACK_Y + 0.05, roof_z(ROOF_BACK_Y) - 0.06), M["gutter"], axis='X', seg=8)
    for s in (-1, 1):
        cyl(f"Downpipe{s}", 0.045, roof_z(ROOF_BACK_Y) - 0.1, (s * (HW + 0.05), ROOF_BACK_Y + 0.05, (roof_z(ROOF_BACK_Y) - 0.1) / 2), M["gutter"], seg=8)

    # ------------------------------------------------------------------ back wall (corrugated, vertical ribs)
    bw_y = BACK_Y + 0.33
    bw_h = roof_z(bw_y)
    box("BackWall", W + 0.3, 0.03, bw_h, (0, bw_y, bw_h / 2), M["sheet"])
    for k in range(n_ribs):
        x = -(W + 0.3) / 2 + 0.11 + k * 0.22
        box(f"BackRib{k}", 0.05, 0.035, bw_h, (x, bw_y + 0.03, bw_h / 2), M["sheet"])
    box("BackWallInner", W + 0.3, 0.01, bw_h, (0, bw_y - 0.02, bw_h / 2), M["sheet_under"])
    # a small exit door in the back wall, behind the gangway
    box("BackDoor", 1.0, 0.05, 2.05, (0, bw_y + 0.05, 1.03 + 0.08), M["dark"])
    box("BackDoorFrame", 1.15, 0.06, 0.08, (0, bw_y + 0.06, 2.18), M["steel"])

    # ------------------------------------------------------------------ side screens (corrugated, back half of each end)
    side_front_y = WALK_D + TREAD * 0.6
    for s in (-1, 1):
        x = s * (HW + 0.15)
        pts = [(side_front_y, 0.0), (bw_y, 0.0), (bw_y, roof_z(bw_y)), (side_front_y, roof_z(side_front_y))]
        poly_prism(f"SideScreen{s}", pts, x - 0.015, x + 0.015, M["sheet"])
        for k in range(int((bw_y - side_front_y) / 0.22)):
            y = side_front_y + 0.11 + k * 0.22
            h = roof_z(y)
            box(f"SideRib{s}_{k}", 0.035, 0.05, h, (x + s * 0.03, y, h / 2), M["sheet"])
        # frame post where the screen ends
        box(f"SidePost{s}", 0.12, 0.12, roof_z(side_front_y), (x, side_front_y, roof_z(side_front_y) / 2), M["steel"])

    for ob in parts[first:]:
        ob.location.x += x0
    return n_seats


if "--render-set" in sys.argv:
    n_seats = 0
    for rows, x0 in ((3, -W - 0.6), (5, 0.0), (8, W + 0.6)):
        n_seats += build_section(rows, x0)
else:
    n_seats = build_section(ROWS)

# ------------------------------------------------------------------ join per material (few draw calls in the game)
by_mat = {}
for ob in parts:
    by_mat.setdefault(ob.data.materials[0].name, []).append(ob)
for name, obs in by_mat.items():
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    obs[0].name = "Shed_" + name
root = bpy.data.objects.new("TheShed", None)
scene.collection.objects.link(root)
for ob in list(scene.collection.objects):
    if ob is not root and ob.type == 'MESH':
        ob.parent = root

tris = sum(len(p.data.polygons) for p in scene.objects if p.type == 'MESH')
print(f"THE SHED ({ROWS} rows): {n_seats} seats, {len([o for o in scene.objects if o.type=='MESH'])} meshes, {tris} faces")

import os
_models = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/models")
if "--render-set" not in sys.argv:
    for _name in (["the_shed_%d.glb" % ROWS] + (["the_shed.glb"] if ROWS == 3 else [])):
        bpy.ops.export_scene.gltf(filepath=os.path.join(_models, _name), export_format='GLB', use_selection=False, export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/the_shed.blend")

# ------------------------------------------------------------------ preview renders
if "--render" in sys.argv:
    world = bpy.data.worlds.new("World"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.86, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    # grass + a bit of pitch line in front
    grass = mat("Grass", "#4E8F3A", 0.9)
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, -0.01)); bpy.context.object.data.materials.append(grass)
    line = mat("Line", "#F2F2F2", 0.8)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -3.2, 0.0)); bpy.context.object.scale = (30, 0.06, 1); bpy.context.object.data.materials.append(line)
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.2; sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-35))
    scene.collection.objects.link(sun)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.view_settings.view_transform = 'AgX'
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 35
    scene.collection.objects.link(cam)
    scene.camera = cam
    views = {
        "front_34": ((-9.5, -11.5, 5.2), (0, 1.6, 1.6)),
        "pitch_level": ((3.5, -9.0, 1.7), (0, 1.8, 2.0)),
        "back_34": ((10.0, 12.0, 7.5), (0, 2.0, 1.5)),
    }
    prefix = "render_"
    if "--render-set" in sys.argv:
        prefix = "shed_set_"
        views = {
            "front": ((-6.0, -26.0, 8.0), (0, 3.0, 2.2)),
            "side_34": ((-24.0, -14.0, 9.0), (0, 3.0, 2.5)),
            "back_34": ((20.0, 24.0, 12.0), (0, 4.0, 2.5)),
            "inside": ((10.5, -1.0, 2.6), (14.0, 5.0, 3.0)),
        }
    for name, (pos, target) in views.items():
        cam.location = pos
        d = Vector(target) - Vector(pos)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f"/tmp/{prefix}{name}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERS DONE")
