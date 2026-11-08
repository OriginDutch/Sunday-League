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
    "neck":        ((0, 0, 1.47), (0, 0, 1.57), "chest"),
    "head":        ((0, 0, 1.57), (0, 0, 1.80), "neck"),
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

    def box(self, center, size, mat, rot=None):
        m = Matrix.Translation(Vector(center))
        if rot:
            m = m @ Euler(rot).to_matrix().to_4x4()
        geo = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m @ Matrix.Diagonal((*size, 1.0)))
        for f in {f for v in geo["verts"] for f in v.link_faces}:
            f.material_index = self.mi(mat)

    def blob(self, center, scale, mat, subdiv=2, keep=None):
        """Icosphere, scaled; keep(v_local) -> bool drops vertices to cut shells (hair caps, beards)."""
        geo = bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=1.0,
                                         matrix=Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1.0)))
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


def body(arm):
    B = BONES
    parts = []
    # torso
    p = Part("Torso", "chest")
    p.ring_tube((0, 0.005, 1.27), (0, 0.0, 1.47), 0.15, 0.185, "Shirt", 10, squash=(1.0, 0.62))
    p.ring_tube((0, 0.0, 1.47), (0, 0.0, 1.50), 0.185, 0.09, "Shirt", 10, squash=(1.0, 0.62))   # shoulders slope
    parts.append(p)
    p = Part("Belly", "spine")
    p.ring_tube((0, 0.01, 1.05), (0, 0.005, 1.28), 0.145, 0.15, "Shirt", 10, squash=(1.0, 0.62))
    parts.append(p)
    p = Part("Pelvis", "hips")
    p.ring_tube((0, 0.01, 0.88), (0, 0.01, 1.07), 0.15, 0.148, "Shorts", 10, squash=(1.0, 0.66))
    parts.append(p)
    p = Part("Neck", "neck")
    p.ring_tube((0, 0.0, 1.46), (0, -0.005, 1.60), 0.064, 0.058, "Skin", 8)
    parts.append(p)
    # head + face
    p = Part("Head", "head")
    hc = (0, -0.005, 1.685)
    p.blob(hc, (0.088, 0.102, 0.118), "Skin", 2)
    p.box((0, -0.105, 1.675), (0.024, 0.03, 0.05), "Skin", rot=(math.radians(-8), 0, 0))           # nose
    for sx in (1, -1):
        p.blob((sx * 0.035, -0.088, 1.705), (0.011, 0.006, 0.009), "Eyes", 1)                     # eyes
        p.box((sx * 0.036, -0.094, 1.728), (0.032, 0.008, 0.008), "Hair", rot=(0, 0, math.radians(-sx * 6)))  # brows
        p.blob((sx * 0.09, -0.0, 1.69), (0.012, 0.024, 0.032), "Skin", 1)                          # ears
    p.box((0, -0.097, 1.637), (0.036, 0.006, 0.006), "Eyes")                                         # mouth line
    parts.append(p)

    # hair variants (separate objects, same bone) + beard
    def cap(v, low=0.0, front_cut=-0.6):
        # keep the top/back of the skull; front: stop above the forehead
        return v.z > low and not (v.y < front_cut * 0.102 and v.z < 0.55 * 0.118)
    variants = {
        "Hair_Short": dict(scale=(0.094, 0.108, 0.124), low=-0.03),
        "Hair_Buzz": dict(scale=(0.0935, 0.1075, 0.1235), low=-0.045),
        "Hair_Quiff": dict(scale=(0.095, 0.11, 0.128), low=-0.01),
        "Hair_Long": dict(scale=(0.097, 0.112, 0.126), low=-0.07),
    }
    for name, cfg in variants.items():
        p = Part(name, "head")
        sc = Vector(cfg["scale"])
        low = cfg["low"]
        p.blob(hc, cfg["scale"], "Hair", 2, keep=lambda v, low=low: (v.z > low and not (v.y < -0.05 and v.z < 0.055)))
        if name == "Hair_Quiff":
            p.blob((0, -0.06, 1.79), (0.06, 0.05, 0.035), "Hair", 1)
        if name == "Hair_Long":
            p.blob((0, 0.05, 1.62), (0.085, 0.05, 0.07), "Hair", 1)
        parts.append(p)
    p = Part("Beard", "head")
    p.blob((0, -0.015, 1.655), (0.09, 0.098, 0.088), "Hair", 2,
           keep=lambda v: v.z < -0.012 and v.y < 0.03 and not (abs(v.x) < 0.03 and v.z > -0.035 and v.y < -0.06))
    parts.append(p)

    for side, sx in (("L", 1), ("R", -1)):
        h, t, _ = B[f"upperarm.{side}"]
        p = Part(f"UpperArm.{side}", f"upperarm.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.02), Vector(h).lerp(Vector(t), 0.55), 0.06, 0.052, "Shirt", 8)   # sleeve
        p.ring_tube(Vector(h).lerp(Vector(t), 0.5), t, 0.043, 0.038, "Skin", 8)
        p.blob((sx * 0.175, 0, 1.425), (0.062, 0.058, 0.05), "Shirt", 2)                                   # shoulder cap
        parts.append(p)
        h, t, _ = B[f"forearm.{side}"]
        p = Part(f"ForeArm.{side}", f"forearm.{side}")
        p.ring_tube(h, t, 0.038, 0.03, "Skin", 8)
        parts.append(p)
        h, t, _ = B[f"hand.{side}"]
        p = Part(f"Hand.{side}", f"hand.{side}")
        p.box(Vector(h).lerp(Vector(t), 0.5), (0.035, 0.055, 0.09), "Skin")
        parts.append(p)
        h, t, _ = B[f"thigh.{side}"]
        p = Part(f"Thigh.{side}", f"thigh.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.05), Vector(h).lerp(Vector(t), 0.45), 0.09, 0.08, "Shorts", 8)   # shorts leg
        p.ring_tube(Vector(h).lerp(Vector(t), 0.42), t, 0.068, 0.054, "Skin", 8)
        parts.append(p)
        h, t, _ = B[f"shin.{side}"]
        p = Part(f"Shin.{side}", f"shin.{side}")
        p.ring_tube(h, Vector(h).lerp(Vector(t), 0.14), 0.05, 0.05, "Skin", 8)
        p.ring_tube(Vector(h).lerp(Vector(t), 0.12), t, 0.052, 0.036, "Socks", 8, ring_mid=(0.35, 0.056))
        parts.append(p)
        p = Part(f"Foot.{side}", f"foot.{side}")
        p.box((sx * 0.10, -0.035, 0.045), (0.085, 0.25, 0.08), "Boots")
        p.box((sx * 0.10, 0.06, 0.012), (0.08, 0.06, 0.024), "Boots")
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
        shoot(os.path.join(PREVIEW_DIR, f"face_{i}.png"), (0.35, -1.0, 1.72), (0, 0, 1.68))
    show_hair("Hair_Short", False)
    # run cycles side view, frame by frame
    scene.render.resolution_x, scene.render.resolution_y = 360, 420
    scene.cycles.samples = 12
    for act, n in (("jog", 16), ("sprint", 12)):
        arm.animation_data.action = bpy.data.actions[act]
        for f in range(n):
            scene.frame_set(f)
            shoot(os.path.join(PREVIEW_DIR, f"_{act}_{f:02d}.png"), (3.0, -0.4, 1.1), (0, -0.1, 0.95))


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


main()
