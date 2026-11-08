"""Main stand — classic English stand section for Sunday League (stage after The Shed).

Blender 5 (bpy) build script. Run:
  python3 build_main_stand.py [--rows 10|12|15] [--tunnel] [--render-set full|rows]
--rows N [--tunnel]: export assets/models/main_stand_N[_tunnel].glb (one 11.5 m section).
--render-set full: three 15-row sections, players' tunnel in the middle one (previews in /tmp/main_*.png).
--render-set rows: 10, 12 and 15 rows side by side.

Units: metres. Blender axes: X = along the touchline, -Y = towards the pitch, Z = up.
Marcel (2026-11-08): classic English (roof on columns in front, columns in your view), concrete
terrace with steel trusses and a corrugated roof, plastic seats in club colour, simple rear facade
with entrances, players' tunnel in the middle section. Scoreboard and floodlights are paid upgrades
(not part of this model). Material names follow The Shed so the game can recolour them.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

W = 11.5
HW = W / 2
TREAD = 0.80
RISE = 0.40
WALK_D = 1.5             # paddock walkway in front of the first row
WALK_Z = 0.6
ROW0_Z = 1.25
AISLE_W = 1.0            # 20 seats per row fit (Marcel 2026-11-08)
SEAT_PITCH = 0.5
COL_X = [-HW / 2, HW / 2]       # 5.75 m apart, continuous across sections, clear of the gangway
TUNNEL_W = 2.8                  # tunnel mouth width
TUNNEL_H = 2.5
TUNNEL_ROWS = 4                 # tunnel section: the first rows go over the full width (Marcel)

ROWS = 15
TUNNEL = "--tunnel" in sys.argv
for _i, _a in enumerate(sys.argv):
    if _a == "--rows":
        ROWS = int(sys.argv[_i + 1])
RENDER_SET = ""
for _i, _a in enumerate(sys.argv):
    if _a == "--render-set":
        RENDER_SET = sys.argv[_i + 1]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


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
    "brick_rear": mat("Rear_Brick", "#8A5443", 0.9),
    "cladding": mat("Rear_Cladding", "#C9C6BC", 0.7, 0.1),
    "glass": mat("Window_Glass", "#5D7680", 0.15, 0.3),
    "ad1": mat("Advert_1", "#C8553D", 0.6),
    "ad2": mat("Advert_2", "#2E8B6E", 0.6),
    "ad3": mat("Advert_3", "#E0B44C", 0.6),
    "seat_metal": mat("Seat_Bracket", "#4A4F52", 0.5, 0.5),
    "dark": mat("Shadow_Gap", "#1E2322", 0.9),
    "tunnel": mat("Tunnel_Canopy", "#F1F0EA", 0.5),
}

parts = []
SEATS = []


def _ob(name, me, loc, m):
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    me.materials.append(m)
    scene.collection.objects.link(ob)
    parts.append(ob)
    return ob


def box(name, sx, sy, sz, loc, m, rot=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    bm.to_mesh(me); bm.free()
    return _ob(name, me, loc, m)


def cyl(name, r, depth, loc, m, axis='Z', seg=10):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bm.to_mesh(me); bm.free()
    return _ob(name, me, loc, m)


def beam(name, a, b, w, h, m):
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = d.to_track_quat('X', 'Z').to_matrix()
    return box(name, d.length, w, h, (a + b) / 2, m, rot)


def poly_prism(name, pts2d, x0, x1, m):
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
    return _ob(name, me, (0, 0, 0), m)


def half_tube(name, r, length, loc, m, seg=12, thick=0.05):
    """Arched canopy along Y (the extendable players' tunnel)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for y in (-length / 2, length / 2):
        ring = []
        for k in range(seg + 1):
            a = math.pi * k / seg
            for rr in (r, r - thick):
                pass
            ring.append((bm.verts.new((math.cos(a) * r, y, math.sin(a) * r)), bm.verts.new((math.cos(a) * (r - thick), y, math.sin(a) * (r - thick)))))
        rings.append(ring)
    a0, a1 = rings
    for k in range(seg):
        bm.faces.new((a0[k][0], a0[k + 1][0], a1[k + 1][0], a1[k][0]))      # outside
        bm.faces.new((a0[k][1], a1[k][1], a1[k + 1][1], a0[k + 1][1]))      # inside
    for ring, flip in ((a0, True), (a1, False)):
        for k in range(seg):
            f = (ring[k][0], ring[k][1], ring[k + 1][1], ring[k + 1][0])
            bm.faces.new(f[::-1] if flip else f)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    return _ob(name, me, loc, m)


def profile(rows):
    """(roof front y, front z, back y, back z, facade y) of a main stand with `rows` rows."""
    back_y = WALK_D + rows * TREAD
    top_z = ROW0_Z + (rows - 1) * RISE
    rby = back_y + 1.2 + 0.4
    return -0.4, top_z + 2.6 + 0.9, rby, top_z + 2.6, rby + 0.02


def line_z(p, y):
    fy, fz, by, bz, _ = p
    return fz + (bz - fz) * (y - fy) / (by - fy)


def build_section(rows, tunnel=False, x0=0.0, left=None, right=None):
    """left/right: the neighbour's row count, or None for an open end (full side screen)."""
    first = len(parts)
    back_y = WALK_D + rows * TREAD
    top_z = ROW0_Z + (rows - 1) * RISE
    rear_walk_y = back_y + 1.2                  # walkway behind the top row
    roof_back_y = rear_walk_y + 0.4
    roof_front_y = -0.4
    roof_back_z = top_z + 2.6
    roof_front_z = roof_back_z + 0.9            # mono-pitch, drains to the back

    def roof_z(y):
        t = (y - roof_front_y) / (roof_back_y - roof_front_y)
        return roof_front_z + (roof_back_z - roof_front_z) * t

    tx = TUNNEL_W / 2 + 0.3                     # half width of the tunnel block
    in_tunnel = lambda x: tunnel and abs(x) < tx

    # ---- terrace: one solid step block per row, left and right of the gangway
    box("Plinth", W, rear_walk_y + 0.4, 0.12, (0, rear_walk_y / 2, 0.06), M["concrete_dark"])
    t_depth = WALK_D + TUNNEL_ROWS * TREAD
    t_top = ROW0_Z + (TUNNEL_ROWS - 1) * RISE + 0.2
    r_start = TUNNEL_ROWS if tunnel else 0
    if tunnel:
        # the tunnel section starts above the tunnel over its full width: a podium (dressing rooms) with the tunnel in it
        for s in (-1, 1):
            w = HW - tx
            box(f"Podium{s}", w, t_depth, t_top, (s * (tx + w / 2), t_depth / 2, t_top / 2), M["concrete_dark"])
            box(f"PodiumBand{s}", w, 0.04, 0.25, (s * (tx + w / 2), -0.02, t_top - 0.2), M["trim"])
            for k in range(2):
                wx = s * (tx + 0.9 + k * 1.6)
                box(f"PodiumWindow{s}{k}", 1.0, 0.04, 0.5, (wx, -0.02, 1.75), M["glass"])
    else:
        box("Walkway", W, WALK_D, WALK_Z, (0, WALK_D / 2, WALK_Z / 2), M["concrete"])
    for r in range(r_start, rows):
        y0 = WALK_D + r * TREAD
        top = ROW0_Z + r * RISE
        for s in (-1, 1):
            w = HW - AISLE_W / 2
            box(f"Row{r}{s}", w, TREAD, top, (s * (AISLE_W / 2 + w / 2), y0 + TREAD / 2, top / 2), M["concrete"])
            box(f"Nosing{r}{s}", w, 0.06, 0.03, (s * (AISLE_W / 2 + w / 2), y0 + 0.03, top + 0.005), M["step_edge"])
    # gangway: two treads per row (front half at half height, back half at the row's height)
    for r in range(r_start, rows):
        y0 = WALK_D + r * TREAD
        if tunnel and r == r_start:
            base = t_top
        else:
            base = ROW0_Z + (r - 1) * RISE if r > 0 else WALK_Z
        top = ROW0_Z + r * RISE
        mid = (base + top) / 2
        box(f"AisleStep{r}", AISLE_W, TREAD / 2, mid, (0, y0 + TREAD / 4, mid / 2), M["concrete_dark"])
        box(f"AisleStepB{r}", AISLE_W, TREAD / 2, top, (0, y0 + TREAD * 0.75, top / 2), M["concrete_dark"])
        box(f"AisleEdge{r}", AISLE_W, 0.06, 0.03, (0, y0 + 0.03, mid + 0.005), M["step_edge"])
        box(f"AisleEdgeB{r}", AISLE_W, 0.06, 0.03, (0, y0 + TREAD / 2 + 0.03, top + 0.005), M["step_edge"])
    # rear walkway + upstand + rail
    box("RearWalk", W, rear_walk_y - back_y, top_z + 0.4, (0, (back_y + rear_walk_y) / 2, (top_z + 0.4) / 2), M["concrete_dark"])
    cyl("RearRail", 0.03, W - 0.2, (0, back_y + 0.1, top_z + 1.4), M["rail"], axis='X')
    for x in [-HW + 0.3 + i * (W - 0.6) / 5 for i in range(6)]:
        cyl(f"RearRailPost{x:.1f}", 0.025, 1.0, (x, back_y + 0.1, top_z + 0.9), M["rail"], seg=8)

    # ---- players' tunnel: concrete block under the first rows, dark mouth, extendable canopy
    if tunnel:
        for s in (-1, 1):
            box(f"TunnelWall{s}", 0.3, t_depth, t_top, (s * (TUNNEL_W / 2 + 0.15), t_depth / 2, t_top / 2), M["concrete_dark"])
        box("TunnelRoof", TUNNEL_W + 0.6, t_depth, t_top - TUNNEL_H, (0, t_depth / 2, TUNNEL_H + (t_top - TUNNEL_H) / 2), M["concrete_dark"])
        box("TunnelInside", TUNNEL_W, 0.1, TUNNEL_H, (0, t_depth - 0.05, TUNNEL_H / 2), M["dark"])
        box("TunnelFloor", TUNNEL_W, t_depth, 0.05, (0, t_depth / 2, 0.025), M["dark"])
        box("TunnelLintel", TUNNEL_W + 0.6, 0.12, 0.4, (0, -0.06, TUNNEL_H + 0.2), M["trim"])
        # rail along the front edge of the podium, full width
        cyl("PodiumRail", 0.03, W - 0.2, (0, 0.15, t_top + 0.95), M["rail"], axis='X')
        for k in range(6):
            x = -HW + 0.3 + k * (W - 0.6) / 5
            cyl(f"PodiumRailPost{k}", 0.025, 0.95, (x, 0.15, t_top + 0.475), M["rail"], seg=8)
        # extendable canopy out onto the pitch side: slim hoops of white fabric with club-colour bands
        r_c, skirt = 1.15, 1.25
        for k in range(3):
            rk = r_c - k * 0.03
            yk = -0.75 - k * 1.25
            half_tube(f"TunnelHoop{k}", rk, 1.3, (0, yk, skirt), M["tunnel"])
            for s in (-1, 1):
                box(f"TunnelSkirt{k}{s}", 0.05, 1.3, skirt, (s * (rk - 0.025), yk, skirt / 2), M["tunnel"])
                box(f"TunnelBand{k}{s}", 0.06, 1.3, 0.28, (s * (rk - 0.02), yk, skirt * 0.75), M["trim"])

    # ---- front wall with adverts + rail (gap for the tunnel)
    ads = [M["ad1"], M["ad2"], M["ad3"], M["ad2"]]
    panel_w = (W - 0.5) / 4
    for i in range(4):
        x = -HW + 0.25 + panel_w * (i + 0.5)
        if in_tunnel(x) or (tunnel and abs(x) < tx + panel_w / 2):
            continue
        box(f"FrontWall{i}", panel_w + 0.02, 0.22, 1.1, (x, -0.11, 0.55), M["brick"])
        box(f"FrontCap{i}", panel_w + 0.04, 0.28, 0.06, (x, -0.11, 1.13), M["concrete"])
        box(f"Advert{i}", panel_w - 0.12, 0.03, 0.62, (x, -0.235, 0.58), ads[i])
    if tunnel:
        for s in (-1, 1):
            w = HW - 0.25 - 2 * panel_w - tx
            if w > 0.05:
                x = s * (tx + w / 2)
                box(f"FrontWallT{s}", w, 0.22, 1.1, (x, -0.11, 0.55), M["brick"])
    for side in ((-HW + 0.2, HW - 0.2),) if not tunnel else ((-HW + 0.2, -tx - 0.1), (tx + 0.1, HW - 0.2)):
        a, b = side
        cyl(f"FrontRail{a:.1f}", 0.03, b - a, ((a + b) / 2, -0.11, 1.68), M["rail"], axis='X')
        n = max(2, int((b - a) / 1.6) + 1)
        for k in range(n):
            x = a + k * (b - a) / (n - 1)
            cyl(f"FrontRailPost{x:.2f}", 0.025, 0.5, (x, -0.11, 1.42), M["rail"], seg=8)

    # ---- seats
    seat_xs = [sgn * (AISLE_W / 2 + 0.25 + k * SEAT_PITCH) for sgn in (-1, 1) for k in range(10)]   # 20 per row
    n_seats = 0
    for r in range(rows):
        y0 = WALK_D + r * TREAD
        top = ROW0_Z + r * RISE
        sy = y0 + TREAD * 0.55
        for sx in seat_xs:
            if tunnel and r < TUNNEL_ROWS:
                continue
            box(f"SeatLeg{r}_{sx:.2f}", 0.06, 0.06, 0.32, (sx, sy, top + 0.16), M["seat_metal"])
            box(f"SeatPan{r}_{sx:.2f}", 0.42, 0.38, 0.05, (sx, sy - 0.04, top + 0.42), M["seat"], Matrix.Rotation(math.radians(-4), 3, 'X'))
            box(f"SeatBack{r}_{sx:.2f}", 0.42, 0.05, 0.36, (sx, sy + 0.17, top + 0.64), M["seat"], Matrix.Rotation(math.radians(-12), 3, 'X'))
            if x0 == 0.0:
                SEATS.append((round(sx, 3), round(top + 0.44, 3), round(-sy, 3), r))   # Godot axes (x, up, -y)
            n_seats += 1

    # ---- steel: front columns (in your view — that's the charm), rear columns, trussed rafters
    col_front_y = 0.35
    col_back_y = rear_walk_y + 0.15
    for i, cx in enumerate(COL_X):
        fz = roof_z(col_front_y)
        box(f"ColF{i}", 0.24, 0.24, fz - WALK_Z, (cx, col_front_y, WALK_Z + (fz - WALK_Z) / 2), M["steel"])
        box(f"ColFBase{i}", 0.42, 0.42, 0.1, (cx, col_front_y, WALK_Z + 0.05), M["concrete_dark"])
        bz = roof_z(col_back_y)
        box(f"ColB{i}", 0.26, 0.26, bz, (cx, col_back_y, bz / 2), M["steel"])
        # truss: top chord under the roof, bottom chord, verticals + diagonals
        y_a, y_b = roof_front_y + 0.1, roof_back_y - 0.1
        depth = 0.9
        top_a, top_b = roof_z(y_a) - 0.12, roof_z(y_b) - 0.12
        beam(f"TrussTop{i}", (cx, y_a, top_a), (cx, y_b, top_b), 0.12, 0.14, M["steel"])
        beam(f"TrussBot{i}", (cx, col_front_y, top_a - depth), (cx, y_b, top_b - depth * 0.6), 0.1, 0.12, M["steel"])
        n_bays = max(4, int((y_b - col_front_y) / 1.6))
        prev = None
        for k in range(n_bays + 1):
            y = col_front_y + k * (y_b - col_front_y) / n_bays
            t = (y - col_front_y) / (y_b - col_front_y)
            zt = roof_z(y) - 0.12
            zb = (top_a - depth) + ((top_b - depth * 0.6) - (top_a - depth)) * t
            beam(f"TrussV{i}_{k}", (cx, y, zb), (cx, y, zt), 0.06, 0.06, M["steel"])
            if prev is not None:
                beam(f"TrussD{i}_{k}", (cx, prev[0], prev[1]), (cx, y, zt), 0.05, 0.05, M["steel"])
            prev = (y, zb)
    # purlins + eaves beam
    n_purl = max(8, int((roof_back_y - roof_front_y) / 1.3))
    for k in range(n_purl):
        y = roof_front_y + 0.25 + k * (roof_back_y - roof_front_y - 0.5) / (n_purl - 1)
        box(f"Purlin{k}", W, 0.08, 0.16, (0, y, roof_z(y) - 0.1), M["steel"])
    box("EavesBeam", W, 0.16, 0.4, (0, col_front_y, roof_z(col_front_y) - 0.32), M["steel"])

    # ---- corrugated roof + deep fascia (room for the club name later) + gutter
    roof_len = math.hypot(roof_back_y - roof_front_y, roof_front_z - roof_back_z)
    slope = math.atan2(roof_front_z - roof_back_z, roof_back_y - roof_front_y)
    rot_roof = Matrix.Rotation(-slope, 3, 'X')
    mid_y = (roof_front_y + roof_back_y) / 2
    box("RoofSheet", W + 0.02, roof_len, 0.03, (0, mid_y, roof_z(mid_y) + 0.01), M["sheet"], rot_roof)
    box("RoofUnderside", W + 0.02, roof_len, 0.01, (0, mid_y, roof_z(mid_y) - 0.012), M["sheet_under"], rot_roof)
    n_ribs = int(W / 0.25)
    for k in range(n_ribs):
        x = -W / 2 + 0.125 + k * 0.25
        box(f"RoofRib{k}", 0.05, roof_len, 0.035, (x, mid_y, roof_z(mid_y) + 0.04), M["sheet"], rot_roof)
    fz = roof_z(roof_front_y)
    box("Fascia", W + 0.02, 0.08, 0.95, (0, roof_front_y - 0.03, fz - 0.3), M["fascia"])
    box("FasciaTrimTop", W + 0.02, 0.09, 0.07, (0, roof_front_y - 0.03, fz + 0.18), M["trim"])
    box("FasciaTrimBot", W + 0.02, 0.09, 0.07, (0, roof_front_y - 0.03, fz - 0.78), M["trim"])
    cyl("Gutter", 0.08, W, (0, roof_back_y + 0.05, roof_z(roof_back_y) - 0.06), M["gutter"], axis='X', seg=8)

    # ---- rear facade: brick ground floor with windows + doors, cladding above up to the roof
    fy = roof_back_y + 0.02
    fh = roof_z(fy)
    box("RearBrick", W, 0.3, 3.2, (0, fy, 1.6), M["brick_rear"])
    box("RearClad", W, 0.12, fh - 3.2, (0, fy - 0.08, 3.2 + (fh - 3.2) / 2), M["cladding"])
    box("RearCladInner", W, 0.02, fh, (0, fy - 0.2, fh / 2), M["sheet_under"])
    for k in range(int(W / 0.4)):
        x = -W / 2 + 0.2 + k * 0.4
        box(f"CladRib{k}", 0.05, 0.04, fh - 3.25, (x, fy - 0.0, 3.25 + (fh - 3.25) / 2), M["cladding"])
    box("RearBand", W, 0.34, 0.18, (0, fy, 3.25), M["trim"])
    # windows (offices / bar under the stand) and one entrance with a canopy per section
    for wx in (-4.3, -2.5):
        box(f"Window{wx}", 1.2, 0.05, 1.0, (wx, fy + 0.16, 1.9), M["glass"])
        box(f"WindowSill{wx}", 1.35, 0.12, 0.08, (wx, fy + 0.2, 1.36), M["concrete"])
    box("EntranceDoor", 1.6, 0.05, 2.3, (0, fy + 0.16, 1.15), M["dark"])
    box("EntranceCanopy", 2.4, 1.0, 0.1, (0, fy + 0.65, 2.65), M["trim"])
    box("EntranceSign", 1.2, 0.05, 0.3, (0, fy + 0.17, 2.85), M["fascia"])
    # stair core to the rear walkway (fans go up here and down the gangways to their row)
    sc_x0, sc_x1 = 1.6, 4.9
    sc_w = sc_x1 - sc_x0
    sc_cx = (sc_x0 + sc_x1) / 2
    sc_d = 3.2
    sc_h = top_z + 0.4 + 2.9
    box("StairBrick", sc_w, sc_d, 3.2, (sc_cx, fy + sc_d / 2, 1.6), M["brick_rear"])
    box("StairClad", sc_w - 0.1, sc_d - 0.1, sc_h - 3.2, (sc_cx, fy + sc_d / 2, 3.2 + (sc_h - 3.2) / 2), M["cladding"])
    box("StairBand", sc_w + 0.04, sc_d + 0.04, 0.18, (sc_cx, fy + sc_d / 2, 3.25), M["trim"])
    box("StairCap", sc_w + 0.12, sc_d + 0.12, 0.2, (sc_cx, fy + sc_d / 2, sc_h + 0.1), M["trim"])
    box("StairDoor", 1.4, 0.05, 2.3, (sc_cx, fy + sc_d + 0.01, 1.15), M["dark"])
    box("StairCanopy", 2.0, 0.8, 0.1, (sc_cx, fy + sc_d + 0.4, 2.6), M["trim"])
    n_slits = max(1, int((sc_h - 4.0) / 2.4))
    for k in range(n_slits):
        z = 4.2 + k * 2.4
        box(f"StairSlit{k}", 0.35, 0.04, 1.6, (sc_cx, fy + sc_d + 0.02, z + 0.8), M["glass"])
    for s in (-1, 1):
        cyl(f"Downpipe{s}", 0.06, roof_z(roof_back_y) - 0.2, (s * (HW - 0.15), fy + 0.2, (roof_z(roof_back_y) - 0.2) / 2), M["gutter"], seg=8)
    # upper window band in the cladding
    box("UpperWindows", 2.8, 0.04, 0.6, (-3.4, fy + 0.0, min(fh - 1.0, 5.5)), M["glass"])

    # ---- side screens: full at an open end; none between equal neighbours; between unequal ones only
    # the strip between the lower and the higher roof, drawn by the taller section (Marcel 2026-11-08)
    side_front_y = WALK_D + TREAD * 2
    for s, nb in ((-1, left), (1, right)):
        x = s * (HW + 0.06)
        if nb is not None:
            if nb >= rows:
                continue
            other = profile(nb)
            fy0, nbw = roof_front_y, other[4]
            pts = [(fy0, line_z(other, fy0)), (nbw, line_z(other, nbw)), (nbw, 0.0), (fy, 0.0), (fy, roof_z(fy)), (fy0, roof_z(fy0))]
            poly_prism(f"StepScreen{s}", pts, x - 0.05, x + 0.05, M["cladding"])
            continue
        pts = [(side_front_y, 0.0), (fy, 0.0), (fy, roof_z(fy)), (side_front_y, roof_z(side_front_y))]
        poly_prism(f"SideScreen{s}", pts, x - 0.05, x + 0.05, M["cladding"])
        box(f"SidePost{s}", 0.16, 0.16, roof_z(side_front_y), (x, side_front_y, roof_z(side_front_y) / 2), M["steel"])

    for ob in parts[first:]:
        ob.location.x += x0
    return n_seats


if RENDER_SET == "full":
    n_seats = sum(build_section(15, k == 1, (k - 1) * W, None if k == 0 else 15, None if k == 2 else 15) for k in range(3))
elif RENDER_SET == "rows":
    rs = (10, 12, 15)
    n_seats = sum(build_section(r, False, (k - 1) * W, rs[k - 1] if k > 0 else None, rs[k + 1] if k < 2 else None) for k, r in enumerate(rs))
else:
    n_seats = build_section(ROWS, TUNNEL)

# join per material (few draw calls in the game)
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
    obs[0].name = "Main_" + name
root = bpy.data.objects.new("MainStand", None)
scene.collection.objects.link(root)
for ob in list(scene.collection.objects):
    if ob is not root and ob.type == 'MESH':
        ob.parent = root
faces = sum(len(p.data.polygons) for p in scene.objects if p.type == 'MESH')
print(f"MAIN STAND ({RENDER_SET or ROWS}): {n_seats} seats, {faces} faces")

if not RENDER_SET:
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/models",
        "main_stand_%d%s.glb" % (ROWS, "_tunnel" if TUNNEL else ""))
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True)
    import json
    with open(out.replace(".glb", "_seats.json"), "w") as f:
        json.dump({"rows": ROWS, "tunnel": TUNNEL, "seats": SEATS, "note": "[x, y, z, row] in the section's local Godot space"}, f)

if RENDER_SET:
    world = bpy.data.worlds.new("World"); scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.86, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    grass = mat("Grass", "#4E8F3A", 0.9)
    bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, -0.01)); bpy.context.object.data.materials.append(grass)
    line = mat("Line", "#F2F2F2", 0.8)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -5.0, 0.0)); bpy.context.object.scale = (60, 0.06, 1); bpy.context.object.data.materials.append(line)
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
    cam.data.lens = 32
    scene.collection.objects.link(cam)
    scene.camera = cam
    views = {
        "front": ((-4.0, -34.0, 9.0), (0, 6.0, 4.5)),
        "side_34": ((-30.0, -20.0, 12.0), (0, 6.0, 4.5)),
        "back_34": ((26.0, 34.0, 15.0), (0, 8.0, 4.0)),
        "pitch_level": ((6.0, -11.0, 1.7), (0, 3.0, 3.0)),
    }
    if RENDER_SET == "rows":
        views = {k: v for k, v in views.items() if k != "pitch_level"}
    for name, (pos, target) in views.items():
        cam.location = pos
        d = Vector(target) - Vector(pos)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f"/tmp/main_{RENDER_SET}_{name}.png"
        bpy.ops.render.render(write_still=True)
    print("RENDERS DONE")
