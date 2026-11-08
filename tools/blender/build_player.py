"""Sunday League — base player: low-poly, realistic-ish proportions, rigid-skinned to an armature.

Run:  python3 tools/blender/build_player.py            -> assets/models/player.glb
      python3 tools/blender/build_player.py --preview  -> also renders design/3d/player/*.png + preview gif

Blender axes: Z up, the player faces -Y (Godot: +Z after export). Left = +X.
Materials (recoloured in Godot per team/player): Shirt, Shorts, Socks, Boots, Skin, Hair, Eyes.
Hairstyles (Hair_<style>) and beards (Beard_<style>_<stubble|short|full>) are separate objects; Godot keeps one of each.
Each mesh part is weighted 100% to one bone (rigid skinning): cheap, stable, stylised.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_GLB = os.path.join(ROOT, "assets", "models", "player.glb")
PREVIEW_DIR = os.path.join(ROOT, "design", "3d", "player")
FPS = 24

# ------------------------------------------------------------------ skeleton (head, tail) in metres
BONES = {
    "root":        ((0, 0, 0), (0, 0, 0.2), None),
    "hips":        ((0, 0, 0.95), (0, 0, 1.06), "root"),
    "spine":       ((0, 0, 1.06), (0, 0, 1.28), "hips"),
    "chest":       ((0, 0, 1.28), (0, 0, 1.47), "spine"),
    "neck":        ((0, 0, 1.47), (0, 0, 1.55), "chest"),
    "head":        ((0, 0, 1.55), (0, 0, 1.84), "neck"),
}
for side, sx in (("L", 1), ("R", -1)):
    BONES.update({
        f"shoulder.{side}": ((sx * 0.03, 0, 1.43), (sx * 0.18, 0, 1.43), "chest"),
        f"upperarm.{side}": ((sx * 0.19, 0, 1.43), (sx * 0.22, 0.01, 1.16), f"shoulder.{side}"),
        f"forearm.{side}":  ((sx * 0.22, 0.01, 1.16), (sx * 0.23, 0, 0.92), f"upperarm.{side}"),
        f"hand.{side}":     ((sx * 0.23, 0, 0.92), (sx * 0.23, 0, 0.83), f"forearm.{side}"),
        f"thigh.{side}":    ((sx * 0.095, 0, 0.95), (sx * 0.10, -0.01, 0.52), "hips"),
        f"shin.{side}":     ((sx * 0.10, -0.01, 0.52), (sx * 0.10, 0.02, 0.09), f"thigh.{side}"),
        f"foot.{side}":     ((sx * 0.10, 0.02, 0.09), (sx * 0.10, -0.13, 0.03), f"shin.{side}"),
    })


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


MATS = {}


def mats():
    MATS["Shirt"] = material("Shirt", (0.05, 0.40, 0.12), 0.75)
    MATS["Shorts"] = material("Shorts", (0.92, 0.92, 0.92), 0.75)
    MATS["Socks"] = material("Socks", (0.05, 0.40, 0.12), 0.8)
    MATS["Boots"] = material("Boots", (0.03, 0.03, 0.035), 0.45)
    MATS["Skin"] = material("Skin", (0.80, 0.55, 0.40), 0.65)
    MATS["Hair"] = material("Hair", (0.10, 0.06, 0.03), 0.85)
    MATS["Eyes"] = material("Eyes", (0.02, 0.02, 0.025), 0.3)


# ------------------------------------------------------------------ mesh builders (bmesh, per bone + material)

class Part:
    """Collects geometry for one object (one bone, several materials)."""
    def __init__(self, name, bone):
        self.name, self.bone = name, bone
        self.bm = bmesh.new()
        self.mat_index = {}

    def mi(self, mat):
        if mat not in self.mat_index:
            self.mat_index[mat] = len(self.mat_index)
        return self.mat_index[mat]

    def ring_tube(self, a, b, ra, rb, mat, sides=8, cap=True, squash=(1.0, 1.0), ring_mid=None):
        """Tapered tube from point a to b. squash scales the cross-section (x, y) — wider than deep."""
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        up = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((0, 1, 0))
        u = axis.cross(up).normalized()
        v = axis.cross(u).normalized()
        # keep "width" along world X where possible
        if abs(u.x) < abs(v.x):
            u, v = v, u
        rings = [(a, ra), (b, rb)]
        if ring_mid:
            t, r = ring_mid
            rings.insert(1, (a.lerp(b, t), r))
        verts = []
        for c, r in rings:
            ring = []
            for i in range(sides):
                ang = 2 * math.pi * (i + 0.5) / sides
                p = c + u * math.cos(ang) * r * squash[0] + v * math.sin(ang) * r * squash[1]
                ring.append(self.bm.verts.new(p))
            verts.append(ring)
        idx = self.mi(mat)
        for k in range(len(verts) - 1):
            r0, r1 = verts[k], verts[k + 1]
            for i in range(sides):
                f = self.bm.faces.new((r0[i], r0[(i + 1) % sides], r1[(i + 1) % sides], r1[i]))
                f.material_index = idx
        if cap:
            f = self.bm.faces.new(list(reversed(verts[0])))
            f.material_index = idx
            f = self.bm.faces.new(verts[-1])
            f.material_index = idx

    def tube_rings(self, rings, mat, sides=10, squash=(1.0, 1.0)):
        """Closed vertical tube through several (center, radius) rings — one watertight piece (no seams)."""
        verts = []
        for c, r in rings:
            c = Vector(c)
            ring = []
            for i in range(sides):
                ang = 2 * math.pi * (i + 0.5) / sides
                ring.append(self.bm.verts.new(c + Vector((math.cos(ang) * r * squash[0], math.sin(ang) * r * squash[1], 0))))
            verts.append(ring)
        idx = self.mi(mat)
        for k in range(len(verts) - 1):
            r0, r1 = verts[k], verts[k + 1]
            for i in range(sides):
                f = self.bm.faces.new((r0[i], r0[(i + 1) % sides], r1[(i + 1) % sides], r1[i]))
                f.material_index = idx
        for ring in (verts[0], verts[-1]):
            f = self.bm.faces.new(ring)
            f.material_index = idx

    def box(self, center, size, mat, rot=None):
        m = Matrix.Translation(Vector(center))
        if rot:
            m = m @ Euler(rot).to_matrix().to_4x4()
        geo = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m @ Matrix.Diagonal((*size, 1.0)))
        for f in {f for v in geo["verts"] for f in v.link_faces}:
            f.material_index = self.mi(mat)

    def blob(self, center, scale, mat, subdiv=2, keep=None, sym=False, segs=(14, 10), warp=None):
        """Icosphere (or a left/right-symmetric UV sphere when sym), scaled; keep(v_local) -> bool drops
        vertices to cut shells (hair caps, beards)."""
        m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1.0))
        if sym:
            # rotate so the seam/poles are top-bottom and the vertex columns mirror across x = 0
            geo = bmesh.ops.create_uvsphere(self.bm, u_segments=segs[0], v_segments=segs[1], radius=1.0,
                                            matrix=m @ Euler((0, 0, math.pi / segs[0])).to_matrix().to_4x4())
        else:
            geo = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=1.0, matrix=m)
        verts = geo["verts"]
        if keep:
            drop = [v for v in verts if not keep((v.co - Vector(center)) / 1.0)]
            bmesh.ops.delete(self.bm, geom=drop, context="VERTS")
            verts = [v for v in verts if v.is_valid]
        if warp:
            c = Vector(center)
            for v in verts:
                v.co = c + warp(v.co - c)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = self.mi(mat)

    def build(self, arm):
        me = bpy.data.meshes.new(self.name)
        self.bm.normal_update()
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        order = sorted(self.mat_index.items(), key=lambda kv: kv[1])
        for mat, _ in order:
            me.materials.append(MATS[mat])
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        vg = ob.vertex_groups.new(name=self.bone)
        vg.add(range(len(me.vertices)), 1.0, "REPLACE")
        ob.parent = arm
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        return ob


def armature():
    data = bpy.data.armatures.new("PlayerRig")
    arm = bpy.data.objects.new("PlayerRig", data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name, (h, t, parent) in BONES.items():
        b = data.edit_bones.new(name)
        b.head, b.tail = h, t
        b.roll = 0.0
        eb[name] = b
    for name, (h, t, parent) in BONES.items():
        if parent:
            eb[name].parent = eb[parent]
            eb[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


HC = Vector((0, -0.01, 1.705))       # head centre
HS = Vector((0.118, 0.136, 0.158))   # head half-sizes (Marcel: head was far too small)


def on_head(x, z, out=0.004):
    """Point on the head ellipsoid's front at (x, z) offset from the centre, pushed out a little."""
    k = 1.0 - (x / HS.x) ** 2 - (z / HS.z) ** 2
    y = -HS.y * math.sqrt(max(0.0, k)) - out
    return (HC.x + x, HC.y + y, HC.z + z)



# ------------------------------------------------------------------ hair + beard library
# Every style is its own object on the head bone ("Hair_<style>", "Beard_<style>_<stage>"); Godot keeps the
# one a player has and frees the rest. Shapes are shells of the head ellipsoid (so they always fit) plus
# a few extra pieces (quiffs, buns, dreads, moustaches...). n = normalised head coords: x left, y back, z up.

HAIR_SEGS = (24, 18)


def _lerp_thr(ny, front, side, back):
    """Hairline height along the head from the forehead (ny = -1) over the sides to the nape (ny = 1)."""
    if ny < -0.3:
        t = (ny + 1.0) / 0.7
        return front + (side - front) * t
    t = min(1.0, (ny + 0.3) / 0.7)
    return side + (back - side) * t


def cap(front, side, back):
    return lambda n: n.z > _lerp_thr(n.y, front, side, back)


def hp(nx, ny, nz, k=1.0):
    """Point on (k x) the head ellipsoid in the direction (nx, ny, nz) (normalised first)."""
    d = Vector((nx, ny, nz)).normalized()
    return Vector((HC.x + d.x * HS.x * k, HC.y + d.y * HS.y * k, HC.z + d.z * HS.z * k))


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _margin(n, keep, limit):
    """How far (in normalised head units) n is inside the kept area, probing down / sideways / front / back."""
    best = limit
    for d in ((0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, -1, 0), (0, 1, 0)):
        t = 0.0
        while t < best:
            t += 0.025
            q = Vector((n.x + d[0] * t, n.y + d[1] * t, n.z + d[2] * t))
            if not keep(q):
                best = t
                break
    return best


def shell(p, k, keep, mat="Hair", taper=0.2, flat=None, hang=0.0, hang_back_only=False, edge=1.012):
    """Shell of the head shape, cut by keep(n). The thickness tapers to ~0 at the cut (no helmet lip);
    flat clamps the top (flat-top cuts, metres above the head centre); hang pulls the lower part down (long hair)."""
    def warp(v):
        n = Vector((v.x / HS.x, v.y / HS.y, v.z / HS.z))
        kk = edge + (k - edge) * _smooth(_margin(n, keep, taper) / taper) if taper > 0 else k
        out = v * kk
        if flat is not None and out.z > flat:
            out.z = flat
        if hang > 0 and n.z < 0.15:
            w = _smooth((n.y + 0.2) / 0.6) if hang_back_only else 1.0
            out.z -= hang * (0.15 - n.z) / 1.15 * w
        return out
    p.blob(tuple(HC), tuple(HS), mat, keep=lambda v: keep(Vector((v.x / HS.x, v.y / HS.y, v.z / HS.z))),
           sym=True, segs=HAIR_SEGS, warp=warp)


def spike(p, base, direction, r, length, mat="Hair", sides=5):
    d = Vector(direction).normalized()
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    m = Matrix.Translation(Vector(base) + d * length * 0.5) @ rot
    geo = bmesh.ops.create_cone(p.bm, cap_ends=True, segments=sides, radius1=r, radius2=r * 0.15, depth=length, matrix=m)
    for f in {f for v in geo["verts"] for f in v.link_faces}:
        f.material_index = p.mi(mat)


def golden(n_pts):
    """Even directions over a sphere (Fibonacci), mirrored left/right so styles stay symmetric."""
    pts = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n_pts):
        z = 1 - 2 * (i + 0.5) / n_pts
        r = math.sqrt(1 - z * z)
        x, y = math.cos(ga * i) * r, math.sin(ga * i) * r
        if x >= 0:
            pts.append((x, y, z))
            if x > 0.05:
                pts.append((-x, y, z))
    return pts


def curls(p, keep, k, size, count=150):
    for d in golden(count):
        n = Vector(d)
        if keep(n):
            p.blob(tuple(hp(*d, k)), (size, size, size * 0.85), "Hair", 1)


def dreads(p, keep, length, count=110, r=0.016):
    for d in golden(count):
        n = Vector(d)
        if keep(n) and n.z < 0.55 and n.y > -0.45:     # nothing hanging in front of the face
            a = hp(*d, 1.05)
            out = Vector((n.x, n.y, 0)).normalized() * 0.25 if n.xy.length > 0.05 else Vector()
            b = a + Vector((out.x * length * 0.3, out.y * length * 0.3, -length))
            p.ring_tube(a, b, r, r * 0.8, "Hair", 5)


def cornrows(p, rows=7, width=0.1):
    for i in range(rows):
        x = -width + 2 * width * i / (rows - 1)
        pts = []
        for j in range(9):
            ny = -0.75 + 1.6 * j / 8
            nz = math.sqrt(max(0.02, 1 - (x / HS.x) ** 2 - ny * ny * 0.85))
            pts.append(hp(x / HS.x, ny, nz, 1.035))
        for a, b in zip(pts, pts[1:]):
            p.ring_tube(a, b, 0.011, 0.011, "Hair", 5)


def hair_styles():
    styles = {}

    def add(name, fn):
        styles[name] = fn

    def plain(k, front, side, back, extra=None):
        def fn(p):
            shell(p, k, cap(front, side, back))
            if extra:
                extra(p)
        return fn

    def quiff(size):
        return lambda p: p.blob(tuple(hp(0, -0.55, 0.8, 1.02)), (0.07 * size, 0.06 * size, 0.045 * size), "Hair", 1)

    def topbox(h, w=0.85, d=0.9):
        return lambda p: p.box((HC.x, HC.y - 0.005, HC.z + HS.z * 0.82 + h / 2), (HS.x * 2 * w, HS.y * 2 * d * 0.85, h), "Hair")

    def sidepart(sx):
        return lambda p: p.blob(tuple(hp(sx * 0.35, -0.35, 0.85, 1.03)), (0.07, 0.085, 0.035), "Hair", 1)

    def fringe(drop, swept=0.0):
        return lambda p: p.box(tuple(hp(swept * 0.3, -0.9, 0.42, 1.04)), (0.16, 0.03, 0.05 + drop),
                               "Hair", rot=(0, math.radians(swept * 18), 0))

    def bun(top):
        pos = hp(0, 0.2, 1.0, 1.12) if top else hp(0, 0.85, 0.35, 1.1)
        return lambda p: p.blob(tuple(pos), (0.052, 0.052, 0.048), "Hair", 1)

    def drape(length, sides=True):
        def fn(p):
            p.box((HC.x, HC.y + HS.y * 0.72, HC.z - 0.06 - length / 2), (HS.x * 1.7, 0.06, length + 0.12), "Hair")
            if sides:
                for sx in (1, -1):
                    p.box((sx * HS.x * 0.98, HC.y + 0.02, HC.z - 0.04 - length * 0.35), (0.04, HS.y * 1.3, length * 0.7 + 0.12), "Hair")
        return fn

    def ponytail(p):
        a = hp(0, 0.95, 0.15, 1.05)
        p.ring_tube(a, a + Vector((0, 0.06, -0.2)), 0.03, 0.018, "Hair", 6)

    def curtains(p):
        for sx in (1, -1):
            p.blob(tuple(hp(sx * 0.45, -0.75, 0.45, 1.05)), (0.06, 0.03, 0.065), "Hair", 1)

    def spikes(count, length):
        def fn(p):
            for d in golden(count):
                n = Vector(d)
                if n.z > 0.45 and n.y < 0.6:
                    spike(p, hp(*d, 1.02), (n.x * 0.6, n.y * 0.6 - 0.15, n.z), 0.024, length)
        return fn

    def combo(*fns):
        def fn(p):
            for f in fns:
                f(p)
        return fn

    std = (0.5, 0.05, -0.55)              # forehead / side / nape hairline of a normal cut
    fade = (0.5, 0.4, 0.05)

    def shaped(k, line, extra=None, **kw):
        def fn(p):
            shell(p, k, cap(*line), **kw)
            if extra:
                extra(p)
        return fn

    # crops and buzz cuts
    add("crop", shaped(1.06, std))
    add("crop_thick", shaped(1.09, std))
    add("crop_high", shaped(1.06, (0.66, 0.15, -0.45)))
    add("crop_fringe", shaped(1.06, std, fringe(0.0)))
    add("crop_swept", shaped(1.06, std, fringe(0.01, 1.0)))
    add("buzz", shaped(1.03, (0.52, 0.1, -0.5), taper=0.1))
    add("buzz_high", shaped(1.03, (0.6, 0.25, -0.3), taper=0.1))
    add("buzz_fade", shaped(1.03, (0.52, 0.42, -0.05), taper=0.1))
    add("skin_fade", shaped(1.05, (0.5, 0.52, 0.25)))
    # fades with something on top
    add("fade_crop", shaped(1.07, fade))
    add("fade_quiff", shaped(1.06, fade, quiff(1.0)))
    add("fade_flattop", shaped(1.17, fade, flat=HS.z * 1.07, taper=0.3))
    add("fade_hightop", shaped(1.42, fade, flat=HS.z * 1.3, taper=0.35))
    add("fade_curls", lambda p: (shell(p, 1.05, cap(*fade)), curls(p, lambda n: n.z > 0.55, 1.07, 0.03)))
    add("fade_twists", lambda p: (shell(p, 1.04, cap(*fade)), dreads(p, lambda n: n.z > 0.6, 0.05, 160, 0.013)))
    add("fade_spikes", shaped(1.05, fade, spikes(60, 0.06)))
    # quiffs and parts
    add("quiff", shaped(1.06, std, quiff(1.0)))
    add("quiff_big", shaped(1.07, std, quiff(1.5)))
    add("sidepart_l", shaped(1.06, std, sidepart(1)))
    add("sidepart_r", shaped(1.06, std, sidepart(-1)))
    add("slick_back", shaped(1.05, (0.45, 0.05, -0.6), lambda p: p.blob(tuple(hp(0, 0.6, 0.6, 1.03)), (0.09, 0.06, 0.05), "Hair", 1)))
    add("curtains", shaped(1.07, (0.45, -0.1, -0.6), curtains))
    add("spiky", shaped(1.05, std, spikes(70, 0.07)))
    add("spiky_short", shaped(1.05, std, spikes(90, 0.04)))
    # curls and afros
    add("curly_short", lambda p: (shell(p, 1.05, cap(*std)), curls(p, cap(0.52, 0.12, -0.45), 1.06, 0.028)))
    add("curly_top", lambda p: (shell(p, 1.05, cap(0.5, 0.25, -0.3)), curls(p, lambda n: n.z > 0.4, 1.08, 0.035)))
    add("curly_mop", lambda p: (shell(p, 1.1, cap(0.42, -0.25, -0.65)), curls(p, cap(0.45, -0.2, -0.6), 1.12, 0.04)))
    add("afro_small", lambda p: (shell(p, 1.14, cap(0.56, 0.2, -0.45), taper=0.3), curls(p, cap(0.62, 0.3, -0.4), 1.15, 0.034, 220)))
    add("afro", lambda p: (shell(p, 1.25, cap(0.56, 0.15, -0.5), taper=0.4), curls(p, cap(0.64, 0.25, -0.45), 1.26, 0.042, 220)))
    add("afro_big", lambda p: (shell(p, 1.37, cap(0.56, 0.1, -0.55), taper=0.45), curls(p, cap(0.66, 0.2, -0.5), 1.38, 0.05, 220)))
    add("afro_puff", lambda p: (shell(p, 1.04, cap(*fade)), p.blob(tuple(hp(0, 0.1, 1.0, 1.22)), (0.12, 0.12, 0.09), "Hair", 2)))
    # braids, twists, dreads
    add("cornrows", lambda p: (shell(p, 1.025, cap(*std), taper=0.08), cornrows(p)))
    add("cornrows_wide", lambda p: (shell(p, 1.025, cap(*std), taper=0.08), cornrows(p, 5, 0.09)))
    add("twists", lambda p: (shell(p, 1.05, cap(*std)), dreads(p, cap(0.52, 0.12, -0.45), 0.06, 150, 0.014)))
    add("dreads_short", lambda p: (shell(p, 1.05, cap(*std)), dreads(p, cap(0.52, 0.12, -0.45), 0.12)))
    add("dreads_long", lambda p: (shell(p, 1.05, cap(*std)), dreads(p, cap(0.52, 0.12, -0.45), 0.28)))
    add("dreads_tied", lambda p: (shell(p, 1.05, cap(*std)), bun(True)(p),
                                  dreads(p, lambda n: n.y > 0.5 and n.z > 0.2, 0.18, 120)))
    # longer hair
    add("medium", shaped(1.08, (0.48, -0.45, -0.8), hang=0.04))
    add("medium_part", shaped(1.08, (0.48, -0.45, -0.8), curtains, hang=0.04))
    add("bob", shaped(1.08, (0.45, -0.7, -0.85), hang=0.07))
    add("long", shaped(1.08, (0.48, -0.6, -0.95), hang=0.13))
    add("long_straight", shaped(1.07, (0.5, -0.65, -0.95), hang=0.22))
    add("mullet", shaped(1.06, (0.5, 0.05, -0.95), hang=0.12, hang_back_only=True))
    add("man_bun", shaped(1.05, (0.48, -0.05, -0.55), bun(False)))
    add("top_knot", shaped(1.04, fade, bun(True)))
    add("ponytail", shaped(1.06, (0.46, -0.25, -0.65), ponytail))
    # strips
    add("mohawk", lambda p: shell(p, 1.13, lambda n: abs(n.x) < 0.2 and n.z > 0.0 and (n.y > -0.5 or n.z > 0.55), taper=0.12))
    add("faux_hawk", lambda p: (shell(p, 1.03, cap(*fade)), shell(p, 1.12, lambda n: abs(n.x) < 0.32 and n.z > 0.45, taper=0.15)))
    # thinning
    add("receding", shaped(1.045, (0.78, 0.1, -0.5)))
    add("horseshoe", lambda p: shell(p, 1.035, lambda n: cap(*std)(n) and not (n.z > 0.6 and n.y < 0.45), taper=0.1))
    add("thin_crown", lambda p: shell(p, 1.035, lambda n: cap(0.66, 0.05, -0.55)(n) and not (n.z > 0.78 and abs(n.y - 0.1) < 0.35), taper=0.1))
    add("bald", None)

    parts = []
    for name, fn in styles.items():
        if fn is None:
            continue
        p = Part("Hair_" + name, "head")
        fn(p)
        parts.append(p)
    return parts


BEARD_STAGES = {"stubble": 1.014, "short": 1.045, "full": 1.085}


def beard_styles():
    def base(n):
        return n.y < 0.35 and n.z < 0.02

    def mouth(n):
        return abs(n.x) < 0.4 and -0.62 < n.z < -0.25 and n.y < -0.55

    def full(n):
        return base(n) and not mouth(n) and (n.z < -0.12 or abs(n.x) > 0.8)

    def boxed(n):
        return full(n) and n.z < -0.08 and n.y < 0.15

    def chinstrap(n):
        return full(n) and not (abs(n.x) < 0.78 and n.z > -0.62 and n.y < -0.3)

    def chops(n):
        return full(n) and abs(n.x) > 0.55 and n.z > -0.75

    def chin(n):
        return n.y < -0.4 and abs(n.x) < 0.42 and n.z < -0.6

    def moustache(p, th, wide=1.0):
        p.box(on_head(0, -0.04, th * 0.5), (0.07 * wide, th + 0.004, 0.018), "Hair")

    def droops(p, th):
        for sx in (1, -1):
            p.box(on_head(sx * 0.036, -0.068, th * 0.5), (0.012, th + 0.004, 0.05), "Hair")

    styles = {
        "full": (full, [moustache]),
        "boxed": (boxed, [moustache]),
        "chinstrap": (chinstrap, []),
        "chops": (chops, [moustache]),
        "goatee": (chin, [moustache]),
        "vandyke": (lambda n: chin(n) and abs(n.x) < 0.3, [lambda p, th: moustache(p, th, 1.15)]),
        "moustache": (None, [lambda p, th: moustache(p, th, 1.1)]),
        "horseshoe": (None, [moustache, droops]),
        "long": (full, [moustache, "long"]),
        "circle": (lambda n: chin(n) and abs(n.x) < 0.36, [moustache, droops]),
    }
    parts = []
    for name, (keep, extras) in styles.items():
        for stage, k in BEARD_STAGES.items():
            p = Part(f"Beard_{name}_{stage}", "head")
            th = {"stubble": 0.003, "short": 0.008, "full": 0.014}[stage]
            if keep:
                shell(p, k, keep, taper=0.12, edge=min(k, 1.012))
            for e in extras:
                if e == "long":
                    if stage == "full":
                        p.blob(tuple(hp(0, -0.55, -0.95, 1.06)), (0.075, 0.06, 0.06), "Hair", 1)
                else:
                    e(p, th)
            parts.append(p)
    return parts


def body(arm):
    B = BONES
    parts = []
    # torso: wider, deeper chest, squarer shoulders sloping into the neck (trapezius)
    p = Part("Torso", "chest")
    p.tube_rings([((0, 0.005, 1.27), 0.16), ((0, 0.003, 1.38), 0.195), ((0, 0.0, 1.45), 0.2),
                  ((0, 0.003, 1.495), 0.15), ((0, 0.005, 1.525), 0.085)], "Shirt", 10, squash=(1.0, 0.74))
    for sx in (1, -1):
        # deltoid/shoulder block: square-ish, not a ball
        p.box((sx * 0.178, 0.0, 1.43), (0.085, 0.11, 0.085), "Shirt", rot=(0, math.radians(sx * 18), 0))
    parts.append(p)
    p = Part("Belly", "spine")
    p.ring_tube((0, 0.01, 1.04), (0, 0.005, 1.28), 0.15, 0.16, "Shirt", 10, squash=(1.0, 0.72))
    parts.append(p)
    p = Part("Pelvis", "hips")
    p.ring_tube((0, 0.01, 0.87), (0, 0.01, 1.07), 0.16, 0.152, "Shorts", 10, squash=(1.0, 0.72))
    parts.append(p)
    p = Part("Neck", "neck")
    p.ring_tube((0, 0.0, 1.47), (0, -0.005, 1.58), 0.068, 0.062, "Skin", 8)
    parts.append(p)
    # head + face
    p = Part("Head", "head")
    p.blob(tuple(HC), tuple(HS), "Skin", 2, sym=True)
    p.box(on_head(0, -0.012, 0.01), (0.03, 0.04, 0.058), "Skin", rot=(math.radians(-10), 0, 0))     # nose
    for sx in (1, -1):
        p.blob(on_head(sx * 0.046, 0.024, 0.002), (0.014, 0.007, 0.012), "Eyes", 1)                 # eyes
        p.box(on_head(sx * 0.047, 0.058, 0.004), (0.044, 0.012, 0.011), "Hair", rot=(0, 0, math.radians(-sx * 6)))  # brows
        p.blob((sx * HS.x * 0.98, HC.y + 0.005, HC.z + 0.0), (0.014, 0.028, 0.038), "Skin", 1)      # ears
    p.box(on_head(0, -0.068, 0.001), (0.046, 0.007, 0.008), "Eyes")                                 # mouth line
    parts.append(p)

    parts += hair_styles() + beard_styles()

    for side, sx in (("L", 1), ("R", -1)):
        h, t, _ = B[f"upperarm.{side}"]
        p = Part(f"UpperArm.{side}", f"upperarm.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.01), Vector(h).lerp(Vector(t), 0.55), 0.072, 0.064, "Shirt", 8)   # sleeve
        p.ring_tube(Vector(h).lerp(Vector(t), 0.5), t, 0.055, 0.048, "Skin", 8)
        parts.append(p)
        h, t, _ = B[f"forearm.{side}"]
        p = Part(f"ForeArm.{side}", f"forearm.{side}")
        p.ring_tube(h, t, 0.049, 0.036, "Skin", 8, ring_mid=(0.3, 0.052))
        parts.append(p)
        h, t, _ = B[f"hand.{side}"]
        p = Part(f"Hand.{side}", f"hand.{side}")
        p.box(Vector(h).lerp(Vector(t), 0.5), (0.042, 0.07, 0.1), "Skin")
        parts.append(p)
        h, t, _ = B[f"thigh.{side}"]
        p = Part(f"Thigh.{side}", f"thigh.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.05), Vector(h).lerp(Vector(t), 0.45), 0.105, 0.095, "Shorts", 8)  # shorts leg
        p.ring_tube(Vector(h).lerp(Vector(t), 0.42), t, 0.085, 0.066, "Skin", 8)
        parts.append(p)
        h, t, _ = B[f"shin.{side}"]
        p = Part(f"Shin.{side}", f"shin.{side}")
        p.ring_tube(h, Vector(h).lerp(Vector(t), 0.14), 0.064, 0.064, "Skin", 8)
        p.ring_tube(Vector(h).lerp(Vector(t), 0.12), t, 0.066, 0.042, "Socks", 8, ring_mid=(0.35, 0.07))
        parts.append(p)
        p = Part(f"Foot.{side}", f"foot.{side}")
        p.box((sx * 0.10, -0.035, 0.045), (0.095, 0.26, 0.085), "Boots")
        p.box((sx * 0.10, 0.06, 0.012), (0.09, 0.06, 0.024), "Boots")
        parts.append(p)
    return [q.build(arm) for q in parts]


# ------------------------------------------------------------------ animations (rotation keys per bone, degrees)

def pose_key(arm, frame, rots, up=0.0, fwd=0.0, side=0.0):
    """rots: bone -> (x, y, z) degrees. up/fwd/side: hips offset in metres (side + = the player's left, Blender +X).
    The hips bone points up, so its local axes are X = +X, Y = up, Z = forward (-Y)."""
    for name, pb in arm.pose.bones.items():
        pb.rotation_mode = "XYZ"
        r = rots.get(name, (0, 0, 0))
        pb.rotation_euler = Euler([math.radians(a) for a in r])
        pb.keyframe_insert("rotation_euler", frame=frame)
    hb = arm.pose.bones["hips"]
    hb.location = (side, up, fwd)
    hb.keyframe_insert("location", frame=frame)


def make_action(arm, name, frames, keyfn, cyclic=True):
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for f in frames:
        k = keyfn(f)
        rots, offs = k[0], k[1:]
        pose_key(arm, f, rots, *offs)
    if cyclic:
        for fc in getattr(act, "fcurves", []):
            fc.modifiers.new("CYCLES")
    act.use_fake_user = True
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, frames[0], act)
    arm.animation_data.action = None
    return act


def run_cycle(n, thigh_amp, knee_amp, arm_amp, elbow, lean, bob):
    """Frames 0..n (n = one full stride). Bone rotation X: + swings the limb backwards for these bone orientations."""
    def key(f):
        ph = 2 * math.pi * f / n
        s = math.sin(ph)
        rots = {
            "spine": (lean, 0, 0),
            "chest": (lean * 0.4, 0, -s * 4),
            "head": (-lean * 0.9, 0, s * 2),
            "hips": (0, 0, s * 5),
        }
        for side, sg in (("L", 1), ("R", -1)):
            ls = s * sg
            lc = math.cos(ph) * sg
            # thigh: -X swings forward; a forward bias so the foot lands under/in front of the body
            rots[f"thigh.{side}"] = (-ls * thigh_amp - thigh_amp * 0.35, 0, 0)
            # knee: nearly straight at foot contact and in stance, most bent mid-swing (leg coming through)
            knee = knee_amp * max(0.0, lc) ** 1.3 + 8
            rots[f"shin.{side}"] = (knee, 0, 0)
            rots[f"foot.{side}"] = (-knee * 0.25, 0, 0)
            rots[f"upperarm.{side}"] = (ls * arm_amp, 0, sg * 6)
            rots[f"forearm.{side}"] = (-elbow, 0, 0)
        return rots, abs(math.cos(ph)) * bob - bob * 0.5
    return key


def idle_cycle(n):
    def key(f):
        ph = 2 * math.pi * f / n
        b = math.sin(ph)
        rots = {"chest": (b * 1.2, 0, 0), "head": (0, 0, math.sin(ph * 0.5) * 6), "spine": (2, 0, 0)}
        for side, sg in (("L", 1), ("R", -1)):
            rots[f"upperarm.{side}"] = (b * 2, 0, sg * 8)
            rots[f"forearm.{side}"] = (-14, 0, 0)
            rots[f"thigh.{side}"] = (-2, 0, sg * -3)
            rots[f"shin.{side}"] = (4, 0, 0)
        return rots, b * 0.006
    return key


# One-shot actions are keyed as poses on a timeline: [(frame, pose)], pose = (rots, up, fwd, side).
# Conventions (checked in renders): spine/chest/head/hips +X bends forward; limbs -X swing forward;
# arms: Z = +sg * a lifts the arm sideways (sg = +1 left, -1 right); hips +Z tilts towards the player's right.

def keyed(timeline):
    def key(f):
        for fr, pose in timeline:
            if fr == f:
                return pose
        raise KeyError(f)
    return key, [fr for fr, _ in timeline]


def P(rots, up=0.0, fwd=0.0, side=0.0):
    return (rots, up, fwd, side)


def both(rots, bone, x=0.0, y=0.0, z=0.0, mirror_z=True):
    """Same rotation on .L and .R (Z mirrored so 'outwards' stays outwards)."""
    rots[f"{bone}.L"] = (x, y, z)
    rots[f"{bone}.R"] = (x, -y if mirror_z else y, -z if mirror_z else z)
    return rots


def stand():
    r = {"spine": (2, 0, 0)}
    both(r, "upperarm", 2, 0, 8)
    both(r, "forearm", -14)
    both(r, "thigh", -2, 0, -3)
    both(r, "shin", 4)
    return r


def kick_timeline(power):
    """Right-foot strike. power 1 = shot, ~0.55 = pass (side-foot: the leg turns out)."""
    a = power
    turn = (1.0 - a) * 40.0            # side-foot: thigh turned outwards
    def pose(thR, shR, lean, armout, plant_th, plant_sh, twist):
        r = {"spine": (lean, twist, 0), "chest": (lean * 0.5, twist, 0), "head": (-lean * 0.6, -twist, 0)}
        r["thigh.R"] = (thR, -turn, 0)
        r["shin.R"] = (shR, 0, 0)
        r["foot.R"] = (-10, 0, 0)
        r["thigh.L"] = (plant_th, 0, -4)
        r["shin.L"] = (plant_sh, 0, 0)
        r["foot.L"] = (-plant_sh * 0.4, 0, 0)
        r["upperarm.L"] = (-25 * a, 0, armout)          # left arm out for balance
        r["upperarm.R"] = (30 * a, 0, -armout * 0.6)
        both(r, "forearm", -35)
        return r
    tl = [
        (0, P(pose(45 * a, 100 * a, 4, 35 * a, -18, 28, 12 * a), -0.04)),          # wound up (no slow back-swing: the ball goes now)
        (3, P(pose(-35 * a, 25, -4, 55 * a, -12, 22, -4 * a), -0.05)),             # contact
        (6, P(pose(-80 * a, 12, -10 * a, 60 * a, -6, 14, -14 * a), -0.03)),         # follow-through
        (10, P(pose(-30 * a, 30, -2, 30 * a, -4, 10, -5 * a), -0.01)),
        (14, P(stand())),
    ]
    return tl


def slide_timeline():
    def lying(depth):
        r = {"hips": (-50 * depth, 0, 8 * depth), "spine": (10 * depth, 0, 0), "chest": (12 * depth, 0, 0), "head": (20 * depth, 0, 0)}
        r["thigh.L"] = (-40 * depth, 0, -4)          # lead leg straight out at the ball
        r["shin.L"] = (4, 0, 0)
        r["foot.L"] = (-15 * depth, 0, 0)
        r["thigh.R"] = (10 * depth, 0, 0)            # trailing leg tucked under
        r["shin.R"] = (110 * depth, 0, 0)
        r["upperarm.R"] = (40 * depth, 0, -35 * depth)   # right hand down behind for support
        r["forearm.R"] = (-10, 0, 0)
        r["upperarm.L"] = (-40 * depth, 0, 45 * depth)
        r["forearm.L"] = (-40, 0, 0)
        return r
    return [
        (0, P(lying(0.35), -0.15)),
        (4, P(lying(1.0), -0.62)),
        (12, P(lying(1.0), -0.66)),
        (17, P(lying(0.55), -0.35)),
        (22, P(stand())),
    ]


def celebrate_cycle(n):
    def key(f):
        ph = 2 * math.pi * f / n
        s = math.sin(ph)
        jump = max(0.0, s)
        r = {"spine": (-6, 0, 0), "chest": (-8, 0, 0), "head": (-14, 0, 0)}
        both(r, "upperarm", -150 - 20 * s, 0, 25)     # both fists up, pumping
        both(r, "forearm", -40 - 30 * s)
        both(r, "thigh", -10 * jump, 0, -4)
        both(r, "shin", 22 * jump + 6)
        both(r, "foot", 20 * jump)
        return r, jump * 0.22
    return key


def dive_timeline(d):
    """Keeper dive; d = +1 to the keeper's left (+X), -1 to his right."""
    L, R = ("L", "R") if d > 0 else ("R", "L")      # L = the arm/leg on the diving side
    def pose(tilt, reach, crouch):
        r = {"hips": (0, 0, -d * tilt), "spine": (crouch * 10, 0, -d * tilt * 0.15), "head": (0, 0, d * tilt * 0.25)}
        r[f"upperarm.{L}"] = (-30 - 140 * reach, 0, (1 if L == "L" else -1) * 20 * reach)
        r[f"upperarm.{R}"] = (-30 - 130 * reach, 0, (1 if R == "L" else -1) * 10 * reach)
        both(r, "forearm", -40 + 30 * reach)
        r[f"thigh.{L}"] = (-30 * crouch, 0, 0)
        r[f"shin.{L}"] = (60 * crouch, 0, 0)
        r[f"thigh.{R}"] = (-20 * crouch, 0, -(1 if R == "L" else -1) * 25 * reach)   # trailing leg kicks out
        r[f"shin.{R}"] = (20 + 40 * crouch, 0, 0)
        return r
    return [
        # small sideways offsets only: in the game the keeper's node itself flies across the goal
        (0, P(pose(10, 0.0, 1.0), -0.22, 0, d * 0.05)),
        (4, P(pose(55, 0.9, 0.4), -0.25, 0, d * 0.3)),
        (9, P(pose(85, 1.0, 0.2), -0.7, 0, d * 0.45)),
        (18, P(pose(90, 0.7, 0.3), -0.78, 0, d * 0.5)),
        (26, P(pose(40, 0.2, 0.8), -0.45, 0, d * 0.4)),
        (32, P(stand(), 0, 0, d * 0.3)),
    ]


def catch_timeline():
    def pose(reach, crouch):
        r = {"spine": (10 + 8 * crouch, 0, 0), "chest": (6, 0, 0), "head": (-6, 0, 0)}
        both(r, "upperarm", -40 - 30 * reach, 0, 4)
        both(r, "forearm", -110 + 60 * reach)
        both(r, "thigh", -30 * crouch, 0, -6)
        both(r, "shin", 55 * crouch)
        both(r, "foot", -15 * crouch)
        return r
    return [
        (0, P(pose(1.0, 0.6), -0.12)),
        (4, P(pose(0.7, 0.8), -0.18)),
        (9, P(pose(0.0, 0.4), -0.08)),     # ball tucked into the chest
        (16, P(pose(0.0, 0.0))),
    ]


def animations(arm):
    make_action(arm, "idle", list(range(0, 49, 6)), idle_cycle(48))
    make_action(arm, "jog", list(range(0, 17, 2)), run_cycle(16, 28, 55, 24, 75, 6, 0.035))
    make_action(arm, "sprint", list(range(0, 13, 1)), run_cycle(12, 48, 95, 50, 85, 14, 0.06))
    make_action(arm, "celebrate", list(range(0, 21, 2)), celebrate_cycle(20))
    for name, tl in (("shoot", kick_timeline(1.0)), ("pass", kick_timeline(0.55)), ("slide", slide_timeline()),
                     ("dive_left", dive_timeline(1)), ("dive_right", dive_timeline(-1)), ("catch", catch_timeline())):
        key, frames = keyed(tl)
        make_action(arm, name, frames, key, cyclic=False)


def poses_sheet(arm, objs):
    """Quick check of every new action: a few frames each, front-left 3/4 view, contact sheet."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 8
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 260, 300
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.55, 1)
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(50), math.radians(10), math.radians(-30)))
    bpy.context.collection.objects.link(sun)
    me = bpy.data.meshes.new("G")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
    bm.to_mesh(me)
    g = bpy.data.objects.new("Ground", me)
    g.data.materials.append(material("Grass", (0.12, 0.35, 0.12), 0.9))
    bpy.context.collection.objects.link(g)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 35
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    for o in objs:
        if o.name.startswith("Hair_"):
            o.hide_render = o.name != "Hair_crop"
        if o.name.startswith("Beard_"):
            o.hide_render = True
    cam.location = (2.6, -3.6, 1.6)
    cam.rotation_euler = (Vector((0.2, 0, 0.7)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    for act, frames in (("shoot", [0, 3, 6, 10]), ("pass", [0, 3, 6, 10]), ("slide", [0, 4, 12, 17]),
                        ("celebrate", [0, 5, 10, 15]), ("dive_left", [0, 4, 9, 26]), ("dive_right", [0, 4, 9, 26]),
                        ("catch", [0, 4, 9, 16])):
        arm.animation_data.action = bpy.data.actions[act]
        for i, f in enumerate(frames):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(PREVIEW_DIR, f"_pose_{act}_{i}.png")
            bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ preview renders

def preview(arm, objs):
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 480, 600
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.55, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(50), math.radians(10), math.radians(-30)))
    bpy.context.collection.objects.link(sun)
    ground = bpy.data.meshes.new("G")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4)
    bm.to_mesh(ground)
    g = bpy.data.objects.new("Ground", ground)
    g.data.materials.append(material("Grass", (0.12, 0.35, 0.12), 0.9))
    bpy.context.collection.objects.link(g)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 60
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    def show_hair(which, beard):
        for o in objs:
            if o.name.startswith("Hair_"):
                o.hide_render = o.name != which
            if o.name.startswith("Beard_"):
                o.hide_render = not (beard and o.name == "Beard_full_full")

    def shoot(path, pos, look=(0, 0, 1.0)):
        cam.location = pos
        d = Vector(look) - Vector(pos)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

    # stills: front / side / back / face close-ups with hair + beard variants
    arm.animation_data.action = bpy.data.actions["idle"]
    scene.frame_set(0)
    show_hair("Hair_crop", False)
    shoot(os.path.join(PREVIEW_DIR, "front.png"), (0.9, -3.2, 1.25))
    shoot(os.path.join(PREVIEW_DIR, "side.png"), (3.3, 0.0, 1.2))
    shoot(os.path.join(PREVIEW_DIR, "back.png"), (-0.8, 3.2, 1.25))
    scene.render.resolution_x, scene.render.resolution_y = 360, 360
    for i, (hair, beard) in enumerate([("Hair_crop", False), ("Hair_buzz", True), ("Hair_quiff", False), ("Hair_long", True)]):
        show_hair(hair, beard)
        shoot(os.path.join(PREVIEW_DIR, f"face_{i}.png"), (0.42, -1.15, 1.73), (0, 0, 1.67))
    show_hair("Hair_crop", False)
    # run cycles side view, frame by frame
    scene.render.resolution_x, scene.render.resolution_y = 360, 420
    scene.cycles.samples = 12
    for act, n in (("jog", 16), ("sprint", 12)):
        arm.animation_data.action = bpy.data.actions[act]
        for f in range(n):
            scene.frame_set(f)
            shoot(os.path.join(PREVIEW_DIR, f"_{act}_{f:02d}.png"), (3.0, -0.4, 1.1), (0, -0.1, 0.95))


def game_view(arm, objs):
    """Render jog + sprint from the in-match camera (Godot: target + (0, 25, 21), looking at target - 1 z, fov 48°)."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.68, 0.75, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = Euler((math.radians(40), math.radians(15), math.radians(-35)))
    bpy.context.collection.objects.link(sun)
    # mown stripes every 5 m so you can see the speed
    for i in range(-10, 11):
        me = bpy.data.meshes.new("S")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5,
                              matrix=Matrix.Translation((i * 5.0, 0, 0)) @ Matrix.Diagonal((5.0, 80.0, 1.0, 1.0)))
        bm.to_mesh(me)
        g = bpy.data.objects.new("Stripe", me)
        g.data.materials.append(material("G%d" % (i % 2), (0.16, 0.42, 0.14) if i % 2 else (0.13, 0.36, 0.12), 0.9))
        bpy.context.collection.objects.link(g)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(48)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    for o in objs:
        if o.name.startswith("Hair_"):
            o.hide_render = o.name != "Hair_crop"
        if o.name.startswith("Beard_"):
            o.hide_render = True
    arm.rotation_euler = Euler((0, 0, math.radians(90)))     # run along +X (Godot: along the pitch)
    for act, n, speed in (("sprint", 12, 8.4), ("jog", 16, 6.0)):
        arm.animation_data.action = bpy.data.actions[act]
        frames = n * 2
        for f in range(frames):
            scene.frame_set(f % n)
            x = speed * f / FPS
            arm.location = (x, 0, 0)
            target = Vector((x, 0, 0))
            cam.location = target + Vector((0, -21.0, 25.0))
            cam.rotation_euler = (target + Vector((0, 1.0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(PREVIEW_DIR, f"_g{act}_{f:02d}.png")
            bpy.ops.render.render(write_still=True)


def hair_sheet(arm, objs):
    """Every hairstyle (3/4 front + back) and every beard at its three growth stages -> contact sheets."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 10
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = 200, 200
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.64, 0.6, 1)
    scene.world = world
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(50), math.radians(10), math.radians(-30)))
    bpy.context.collection.objects.link(sun)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 60
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    arm.animation_data.action = bpy.data.actions["idle"]
    scene.frame_set(0)
    hairs = sorted(o.name for o in objs if o.name.startswith("Hair_")) + ["Hair_bald"]
    beards = [o.name for o in objs if o.name.startswith("Beard_")]

    def show(h, b):
        for o in objs:
            if o.name.startswith("Hair_"):
                o.hide_render = o.name != h
            if o.name.startswith("Beard_"):
                o.hide_render = o.name != b

    def shoot(path, pos, look):
        cam.location = pos
        cam.rotation_euler = (Vector(look) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    out = []
    for h in hairs:
        show(h, None)
        shoot(os.path.join(PREVIEW_DIR, f"_h_{h}_a.png"), (0.55, -1.0, 1.82), (0, 0, 1.69))
        shoot(os.path.join(PREVIEW_DIR, f"_h_{h}_b.png"), (-0.5, 1.0, 1.85), (0, 0, 1.66))
        out.append(h)
    for b in beards:
        show("Hair_buzz", b)
        shoot(os.path.join(PREVIEW_DIR, f"_b_{b}.png"), (0.5, -1.05, 1.72), (0, 0, 1.64))
    with open(os.path.join(PREVIEW_DIR, "_sheet_index.txt"), "w") as f:
        f.write("\n".join(hairs) + "\n#\n" + "\n".join(beards))


def main():
    reset()
    bpy.context.scene.render.fps = FPS
    mats()
    arm = armature()
    objs = body(arm)
    animations(arm)
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(o.name == "PlayerRig" or o.parent == arm)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_animations=True,
                              export_animation_mode="ACTIONS", export_skins=True, export_yup=True)
    print("WROTE", OUT_GLB, "objects", len(objs))
    if "--preview" in sys.argv:
        preview(arm, objs)
    if "--hair-sheet" in sys.argv:
        hair_sheet(arm, objs)
    if "--poses" in sys.argv:
        poses_sheet(arm, objs)
    if "--game-view" in sys.argv:
        game_view(arm, objs)


main()
