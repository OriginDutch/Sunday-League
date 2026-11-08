"""Sunday League — base player: low-poly, realistic-ish proportions, rigid-skinned to an armature.

Run:  python3 tools/blender/build_player.py            -> assets/models/player.glb
      python3 tools/blender/build_player.py --preview  -> also renders design/3d/player/*.png + preview gif

Blender axes: Z up, the player faces -Y (Godot: +Z after export). Left = +X.
Materials (recoloured in Godot per team/player): Shirt, Shorts, Socks, Boots, Skin, Hair, Eyes.
Hair variants are separate objects (Hair_Short, Hair_Buzz, Hair_Quiff, Hair_Long) + Beard, toggled in Godot.
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

    def blob(self, center, scale, mat, subdiv=2, keep=None, sym=False):
        """Icosphere (or a left/right-symmetric UV sphere when sym), scaled; keep(v_local) -> bool drops
        vertices to cut shells (hair caps, beards)."""
        m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1.0))
        if sym:
            # rotate so the seam/poles are top-bottom and the vertex columns mirror across x = 0
            geo = bmesh.ops.create_uvsphere(self.bm, u_segments=14, v_segments=10, radius=1.0,
                                            matrix=m @ Euler((0, 0, math.pi / 14)).to_matrix().to_4x4())
        else:
            geo = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=1.0, matrix=m)
        verts = geo["verts"]
        if keep:
            drop = [v for v in verts if not keep((v.co - Vector(center)) / 1.0)]
            bmesh.ops.delete(self.bm, geom=drop, context="VERTS")
            verts = [v for v in verts if v.is_valid]
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

    # hair variants + beard: shells of the same head shape, slightly bigger, so they always fit
    def hair_keep(back_low, side_low, front_low):
        def keep(v):
            n = Vector((v.x / HS.x, v.y / HS.y, v.z / HS.z))
            if n.y > 0.25:             # back of the head: down to the nape
                return n.z > back_low
            if n.y < -0.55:            # front: hairline above the forehead
                return n.z > front_low
            return n.z > side_low      # sides: down to the top of the ears
        return keep
    variants = {
        "Hair_Short": (1.06, hair_keep(-0.55, -0.12, 0.42)),
        "Hair_Buzz": (1.035, hair_keep(-0.5, -0.1, 0.45)),
        "Hair_Quiff": (1.06, hair_keep(-0.5, -0.1, 0.4)),
        "Hair_Long": (1.08, hair_keep(-0.95, -0.55, 0.38)),
    }
    for name, (k, keep) in variants.items():
        p = Part(name, "head")
        p.blob(tuple(HC), tuple(HS * k), "Hair", 2, keep=lambda v, k=k, keep=keep: keep(v / k), sym=True)
        if name == "Hair_Quiff":
            p.blob((0, HC.y - 0.07, HC.z + 0.13), (0.07, 0.06, 0.04), "Hair", 1)
        parts.append(p)

    def beard_keep(v):
        n = Vector((v.x / HS.x, v.y / HS.y, v.z / HS.z))
        if n.y > 0.35 or n.z > 0.05:
            return False
        if abs(n.x) < 0.38 and -0.5 < n.z < -0.25 and n.y < -0.6:     # keep the mouth free
            return False
        return n.z < -0.15 or abs(n.x) > 0.8                           # jaw, chin + sideburns
    p = Part("Beard", "head")
    p.blob(tuple(HC), tuple(HS * 1.045), "Hair", 2, keep=lambda v: beard_keep(v / 1.045), sym=True)
    parts.append(p)

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

def pose_key(arm, frame, rots, hips_z=0.0, hips_y=0.0):
    for name, pb in arm.pose.bones.items():
        pb.rotation_mode = "XYZ"
        r = rots.get(name, (0, 0, 0))
        pb.rotation_euler = Euler([math.radians(a) for a in r])
        pb.keyframe_insert("rotation_euler", frame=frame)
    hb = arm.pose.bones["hips"]
    hb.location = (0, hips_y, hips_z)
    hb.keyframe_insert("location", frame=frame)


def make_action(arm, name, frames, keyfn, cyclic=True):
    act = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = act
    for f in frames:
        rots, hz, hy = keyfn(f)
        pose_key(arm, f, rots, hz, hy)
    if cyclic:
        for fc in getattr(act, "fcurves", []):
            fc.modifiers.new("CYCLES")
    # keep the action for export
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
        return rots, abs(math.cos(ph)) * bob - bob * 0.5, 0.0
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
        return rots, b * 0.006, 0.0
    return key


def animations(arm):
    make_action(arm, "idle", list(range(0, 49, 6)), idle_cycle(48))
    make_action(arm, "jog", list(range(0, 17, 2)), run_cycle(16, 28, 55, 24, 75, 6, 0.035))
    make_action(arm, "sprint", list(range(0, 13, 1)), run_cycle(12, 48, 95, 50, 85, 14, 0.06))


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
            if o.name == "Beard":
                o.hide_render = not beard

    def shoot(path, pos, look=(0, 0, 1.0)):
        cam.location = pos
        d = Vector(look) - Vector(pos)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)

    # stills: front / side / back / face close-ups with hair + beard variants
    arm.animation_data.action = bpy.data.actions["idle"]
    scene.frame_set(0)
    show_hair("Hair_Short", False)
    shoot(os.path.join(PREVIEW_DIR, "front.png"), (0.9, -3.2, 1.25))
    shoot(os.path.join(PREVIEW_DIR, "side.png"), (3.3, 0.0, 1.2))
    shoot(os.path.join(PREVIEW_DIR, "back.png"), (-0.8, 3.2, 1.25))
    scene.render.resolution_x, scene.render.resolution_y = 360, 360
    for i, (hair, beard) in enumerate([("Hair_Short", False), ("Hair_Buzz", True), ("Hair_Quiff", False), ("Hair_Long", True)]):
        show_hair(hair, beard)
        shoot(os.path.join(PREVIEW_DIR, f"face_{i}.png"), (0.42, -1.15, 1.73), (0, 0, 1.67))
    show_hair("Hair_Short", False)
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
            o.hide_render = o.name != "Hair_Short"
        if o.name == "Beard":
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
    if "--game-view" in sys.argv:
        game_view(arm, objs)


main()
