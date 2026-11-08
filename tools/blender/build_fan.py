"""Sunday League — crowd fans v2: low-poly man / woman / child + accessories, animations baked to bone matrices.

Run:  python3 tools/blender/build_fan.py   -> assets/crowd/fans.json

Fans are drawn as MultiMeshes (thousands of them), so there is no skeleton per fan. Instead every animation
frame stores one 3x4 skinning matrix per bone; the crowd shader looks them up (rigid skinning, like the
players). The meshes are exported as plain triangle lists with a bone index and a part id per corner:
  part ids: see PARTS below. Accessories (coat, scarf, cap, beanie, glasses, beards, flag) are in every mesh
  and switched on per fan by the shader, so they cost no extra variants.
Reuses the player's skeleton, head, hair and beard builders (tools/blender/build_player.py).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector, Matrix, Euler
import build_player as bp

OUT = os.path.join(bp.ROOT, "assets", "crowd", "fans.json")
FPS = 24

PARTS = ["Skin", "Shirt", "Trousers", "Shoes", "Hair", "Eyes", "Forearm", "Coat", "Scarf", "Cap", "Beanie",
         "Glasses", "Sunglasses", "BeardStubble", "BeardFull", "Goatee", "Moustache", "HeldScarf", "TwirlScarf",
         "FlagPole", "FlagCloth", "Brows"]
BONE_ORDER = list(bp.BONES.keys())

# hairstyles per body type (the "normal" ones — Marcel: no spikes everywhere); weights are applied in Godot
HAIR = {
    "man": ["crop", "buzz", "crop_high", "sidepart_l", "sidepart_r", "quiff", "receding", "horseshoe", "bald",
            "curly_short", "fade_crop", "slick_back", "afro_small", "crop_thick"],
    "woman": ["long", "long_straight", "bob", "ponytail", "medium", "man_bun", "curly_mop"],
    "child": ["crop", "buzz", "curly_short", "crop_fringe", "ponytail", "long", "bob"],
}

# Godot axes from Blender axes: (x, y, z) -> (x, z, -y)
C = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
CI = C.inverted()


def g(v):
    return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]


# ------------------------------------------------------------------ bodies

def body_parts(kind):
    """Low-poly body (6-8 sided tubes, rounded, not boxy). kind: man / woman / child (child = man shape,
    the head is enlarged and the whole fan scaled down in Godot)."""
    B = bp.BONES
    parts = []
    sh = 0.9 if kind == "woman" else 1.0          # shoulder / chest width
    hp_ = 1.08 if kind == "woman" else 1.0        # hip width
    p = bp.Part("Torso", "chest")
    p.tube_rings([((0, 0.005, 1.27), 0.155 * sh), ((0, 0.003, 1.39), 0.19 * sh), ((0, 0.003, 1.48), 0.15 * sh),
                  ((0, 0.005, 1.525), 0.08)], "Shirt", 8, squash=(1.0, 0.74))
    # coat shell (hidden unless worn)
    p.tube_rings([((0, 0.005, 1.25), 0.175 * sh), ((0, 0.003, 1.39), 0.21 * sh), ((0, 0.003, 1.49), 0.165 * sh),
                  ((0, 0.005, 1.54), 0.095)], "Coat", 8, squash=(1.0, 0.78))
    # neck scarf
    p.ring_tube((0, 0.0, 1.49), (0, 0.0, 1.56), 0.092, 0.085, "Scarf", 8, squash=(1.0, 0.9))
    p.box((0.05, -0.1, 1.43), (0.05, 0.02, 0.16), "Scarf", rot=(math.radians(-8), 0, 0))   # loose end
    parts.append(p)
    p = bp.Part("Belly", "spine")
    p.ring_tube((0, 0.01, 1.04), (0, 0.005, 1.28), 0.148 * hp_, 0.155 * sh, "Shirt", 8, squash=(1.0, 0.72))
    p.ring_tube((0, 0.01, 0.98), (0, 0.005, 1.28), 0.168 * hp_, 0.176 * sh, "Coat", 8, squash=(1.0, 0.76))
    parts.append(p)
    p = bp.Part("Pelvis", "hips")
    p.ring_tube((0, 0.01, 0.86), (0, 0.01, 1.07), 0.158 * hp_, 0.15 * hp_, "Trousers", 8, squash=(1.0, 0.74))
    parts.append(p)
    p = bp.Part("Neck", "neck")
    p.ring_tube((0, 0.0, 1.47), (0, -0.005, 1.58), 0.064, 0.058, "Skin", 6)
    parts.append(p)
    p = bp.Part("Head", "head")
    HC, HS = bp.HC, bp.HS
    p.blob(tuple(HC), tuple(HS), "Skin", 2, sym=True, segs=(10, 8))
    p.box(bp.on_head(0, -0.012, 0.01), (0.03, 0.04, 0.055), "Skin", rot=(math.radians(-10), 0, 0))      # nose
    for sx in (1, -1):
        p.box(bp.on_head(sx * 0.046, 0.024, 0.002), (0.024, 0.01, 0.02), "Eyes")                        # eyes
        p.box(bp.on_head(sx * 0.047, 0.058, 0.004), (0.044, 0.012, 0.011), "Brows")
        p.box(bp.on_head(sx * 0.046, 0.024, 0.012), (0.042, 0.008, 0.034), "Glasses")                 # lens rims
        p.box((sx * 0.085, HC.y - HS.y * 0.55, HC.z + 0.026), (0.012, 0.12, 0.008), "Glasses")         # arms
    p.box(bp.on_head(0, 0.03, 0.012), (0.03, 0.008, 0.008), "Glasses")                                  # bridge
    p.box(bp.on_head(0, 0.024, 0.018), (0.15, 0.012, 0.04), "Sunglasses")
    for sx in (1, -1):
        p.box((sx * 0.085, HC.y - HS.y * 0.55, HC.z + 0.026), (0.012, 0.12, 0.01), "Sunglasses")
    # cap: crown + brim; beanie: rolled-edge shell
    bp.shell(p, 1.07, lambda n: n.z > 0.35, mat="Cap", taper=0.0)
    p.box(bp.hp(0, -0.9, 0.42, 1.07) + Vector((0, -0.05, -0.006)), (0.17, 0.1, 0.012), "Cap", rot=(math.radians(-8), 0, 0))
    bp.shell(p, 1.13, lambda n: n.z > 0.25, mat="Beanie", taper=0.0)
    p.ring_tube(bp.HC + Vector((0, 0, HS.z * 0.25 * 1.13 - 0.02)), bp.HC + Vector((0, 0, HS.z * 0.25 * 1.13 + 0.025)),
                HS.x * 1.16, HS.x * 1.16, "Beanie", 10, cap=False, squash=(1.0, HS.y / HS.x))
    if kind == "man":
        beards(p)
    parts.append(p)

    for side, sx in (("L", 1), ("R", -1)):
        h, t, _ = B[f"upperarm.{side}"]
        p = bp.Part(f"UpperArm.{side}", f"upperarm.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.01), Vector(h).lerp(Vector(t), 0.55), 0.066 * sh, 0.058, "Shirt", 6)
        p.ring_tube(Vector(h).lerp(Vector(t), 0.5), t, 0.05, 0.045, "Forearm", 6)
        p.ring_tube((h[0], h[1], h[2] + 0.02), t, 0.08 * sh, 0.066, "Coat", 6)
        parts.append(p)
        h, t, _ = B[f"forearm.{side}"]
        p = bp.Part(f"ForeArm.{side}", f"forearm.{side}")
        p.ring_tube(h, t, 0.046, 0.035, "Forearm", 6)
        p.ring_tube(h, Vector(h).lerp(Vector(t), 0.9), 0.062, 0.052, "Coat", 6)
        parts.append(p)
        h, t, _ = B[f"hand.{side}"]
        p = bp.Part(f"Hand.{side}", f"hand.{side}")
        p.blob(tuple(Vector(h).lerp(Vector(t), 0.5)), (0.03, 0.045, 0.055), "Skin", 1)
        parts.append(p)
        h, t, _ = B[f"thigh.{side}"]
        p = bp.Part(f"Thigh.{side}", f"thigh.{side}")
        p.ring_tube((h[0], h[1], h[2] + 0.05), t, 0.1 * hp_, 0.072, "Trousers", 6)
        parts.append(p)
        h, t, _ = B[f"shin.{side}"]
        p = bp.Part(f"Shin.{side}", f"shin.{side}")
        p.ring_tube(h, t, 0.07, 0.052, "Trousers", 6)
        parts.append(p)
        p = bp.Part(f"Foot.{side}", f"foot.{side}")
        p.box((sx * 0.10, -0.035, 0.045), (0.09, 0.24, 0.08), "Shoes")
        parts.append(p)
    return parts


def beards(p):
    def base(n):
        return n.y < 0.35 and n.z < 0.02

    def mouth(n):
        return abs(n.x) < 0.4 and -0.62 < n.z < -0.25 and n.y < -0.55

    def full(n):
        return base(n) and not mouth(n) and (n.z < -0.12 or abs(n.x) > 0.8)

    def chin(n):
        return n.y < -0.4 and abs(n.x) < 0.42 and n.z < -0.6
    bp.shell(p, 1.014, full, mat="BeardStubble", taper=0.12, edge=1.012)
    bp.shell(p, 1.075, full, mat="BeardFull", taper=0.12, edge=1.012)
    p.box(bp.on_head(0, -0.04, 0.007), (0.075, 0.018, 0.018), "BeardFull")
    bp.shell(p, 1.04, chin, mat="Goatee", taper=0.1, edge=1.012)
    p.box(bp.on_head(0, -0.04, 0.005), (0.07, 0.014, 0.018), "Goatee")
    p.box(bp.on_head(0, -0.04, 0.005), (0.075, 0.014, 0.018), "Moustache")


# ------------------------------------------------------------------ animation clips

STAND_FWD = 0.32     # standing up you step forward off the seat (into the leg room), not through it


def P(rots, up=0.0, fwd=STAND_FWD, side=0.0):
    return (rots, up, fwd, side)


def both(r, bone, x=0.0, y=0.0, z=0.0):
    return bp.both(r, bone, x, y, z)


def sit(lean=4.0, hands="thighs"):
    r = {"spine": (lean, 0, 0)}
    both(r, "thigh", -86, 0, -5)
    both(r, "shin", 84)
    both(r, "foot", 2)
    if hands == "thighs":
        both(r, "upperarm", -22, 0, 6)
        both(r, "forearm", -62)
    return r


SIT_UP, SIT_FWD = -0.40, -0.03


def stand(arms=True):
    r = {"spine": (2, 0, 0)}
    both(r, "thigh", -2, 0, -3)
    both(r, "shin", 4)
    if arms:
        both(r, "upperarm", 2, 0, 8)
        both(r, "forearm", -14)
    return r


def loop(n, fn, step=1):
    """Looping clip from fn(phase 0..2pi) -> pose; keys every `step` frames, last key = first."""
    tl = []
    for f in range(0, n + 1, step):
        tl.append((f, fn(2 * math.pi * (f % n) / n)))
    return tl


def sit_idle(ph):
    r = sit()
    r["head"] = (math.sin(ph) * 3, math.sin(ph * 2) * 9, 0)
    r["spine"] = (4 + math.sin(ph) * 1.5, 0, math.sin(ph) * 1.5)
    return P(r, SIT_UP, SIT_FWD)


def sit_clap(ph):
    r = sit(6, hands=None)
    c = (1 + math.cos(ph)) * 0.5                 # 1 = hands apart, 0 = together
    both(r, "upperarm", -48, 0, -10 + 16 * c)
    both(r, "forearm", -78)
    both(r, "hand", 0, 0, 0)
    r["head"] = (-4, 0, 0)
    return P(r, SIT_UP, SIT_FWD)


def stand_idle(ph):
    r = stand()
    r["hips"] = (0, 0, math.sin(ph) * 2.5)
    r["spine"] = (2, 0, -math.sin(ph) * 2.0)
    r["head"] = (0, math.sin(ph * 2) * 10, 0)
    return P(r, -0.005 + math.sin(ph * 2) * 0.004)


def cheer_jump(ph):
    s = math.sin(ph)
    jump = max(0.0, s)
    land = max(0.0, -s)
    r = {"spine": (-4, 0, 0), "chest": (-6, 0, 0), "head": (-12, 0, 0)}
    both(r, "upperarm", -158 - 12 * s, 0, 22)
    both(r, "forearm", -25 - 25 * s)
    both(r, "thigh", -6 * jump - 25 * land, 0, -4)
    both(r, "shin", 10 * jump + 45 * land)
    both(r, "foot", 15 * jump - 15 * land)
    return P(r, jump * 0.2 - land * 0.07)


def cheer_arms(ph):
    s = math.sin(ph)
    r = stand(arms=False)
    r["spine"] = (-3, 0, s * 4)
    r["head"] = (-10, 0, -s * 4)
    both(r, "upperarm", -150, 0, 30)
    r["upperarm.L"] = (-150, 0, 30 + 18 * s)
    r["upperarm.R"] = (-150, 0, -(30 - 18 * s))
    both(r, "forearm", -30 + 15 * s)
    return P(r)


def clap_stand(ph):
    r = stand(arms=False)
    c = (1 + math.cos(ph)) * 0.5
    both(r, "upperarm", -70, 0, -8 + 18 * c)
    both(r, "forearm", -70)
    r["head"] = (-5, 0, 0)
    return P(r)


def fist_pump(ph):
    s = (1 + math.sin(ph)) * 0.5
    r = stand()
    r["upperarm.R"] = (-110 - 55 * s, 0, -15)
    r["forearm.R"] = (-95 + 75 * s, 0, 0)
    r["spine"] = (-2 - 3 * s, 0, 0)
    r["head"] = (-8 * s, 0, 0)
    return P(r)


def scarf_up(ph):
    s = math.sin(ph)
    r = stand(arms=False)
    r["spine"] = (-2, 0, s * 3)
    r["head"] = (-8, 0, 0)
    both(r, "upperarm", -165, 0, 32)
    both(r, "forearm", -12)
    both(r, "hand", 0, 0, -10)
    return P(r)


def scarf_twirl(ph):
    r = stand()
    r["upperarm.R"] = (-150 + 12 * math.cos(ph), 0, -(18 + 14 * math.sin(ph)))
    r["forearm.R"] = (-30 - 20 * math.sin(ph), 0, 0)
    r["hand.R"] = (0, math.degrees(ph), 0)              # twist round: the scarf swings in a circle
    r["head"] = (-8, 0, 0)
    return P(r)


def flag_wave(ph):
    """Figure-8 over the head: side to side once, up and down twice per loop; the body twists along."""
    s = math.sin(ph)
    s2 = math.sin(2 * ph)
    r = stand()
    r["spine"] = (-4, s * 12, s * 6)
    r["chest"] = (-4, s * 10, s * 4)
    r["head"] = (-12, -s * 10, 0)
    r["upperarm.R"] = (-148 + 22 * s2, 0, -(38 + 48 * s))
    r["forearm.R"] = (-28 - 22 * s2, 0, 0)
    r["hand.R"] = (0, 0, -s * 22)
    r["upperarm.L"] = (-110 + 15 * s, 0, -12)
    r["forearm.L"] = (-60, 0, 0)
    return P(r)


def despair_sit(ph):
    r = sit(34, hands=None)                          # elbows on the knees, face in the hands
    r["chest"] = (8, 0, 0)
    r["head"] = (22 + math.sin(ph) * 3, 0, 0)
    both(r, "upperarm", -58, 0, -14)
    both(r, "forearm", -150, 0, 0)
    both(r, "hand", 0, 0, -15)
    return P(r, SIT_UP, SIT_FWD)


def despair_stand(ph):
    r = stand(arms=False)
    r["spine"] = (-4, 0, 0)
    r["head"] = (-12 + math.sin(ph) * 3, 0, 0)
    both(r, "upperarm", -150, 0, 42)
    both(r, "forearm", -135)
    return P(r)


def stand_up_tl():
    a = sit()
    b = sit(28)
    both(b, "thigh", -60, 0, -5)
    both(b, "shin", 70)
    both(b, "upperarm", -30, 0, 8)
    both(b, "forearm", -40)
    return [(0, P(a, SIT_UP, SIT_FWD)), (8, P(b, -0.22, 0.14)), (16, P(stand()))]


def sit_down_tl():
    return [(f, pose) for f, (_, pose) in zip([0, 8, 16], reversed(stand_up_tl()))]


CLIPS = [  # name, timeline, loop
    ("sit_idle", loop(96, sit_idle, 8), True),
    ("sit_clap", loop(12, sit_clap, 2), True),
    ("stand_up", stand_up_tl(), False),
    ("sit_down", sit_down_tl(), False),
    ("stand_idle", loop(96, stand_idle, 8), True),
    ("cheer_jump", loop(16, cheer_jump, 2), True),
    ("cheer_arms", loop(24, cheer_arms, 3), True),
    ("clap_stand", loop(12, clap_stand, 2), True),
    ("fist_pump", loop(14, fist_pump, 2), True),
    ("scarf_up", loop(48, scarf_up, 6), True),
    ("scarf_twirl", loop(16, scarf_twirl, 1), True),
    ("flag_wave", loop(40, flag_wave, 2), True),
    ("despair_sit", loop(48, despair_sit, 6), True),
    ("despair_stand", loop(48, despair_stand, 6), True),
]
SITTING = {"sit_idle", "sit_clap", "despair_sit"}


def key_clip(arm, timeline):
    act = bpy.data.actions.new("clip")
    arm.animation_data_create()
    arm.animation_data.action = act
    for f, pose in timeline:
        bp.pose_key(arm, f, *pose)
    return act


def skin_matrices(arm):
    """Godot-space 3x4 skinning matrix per bone (pose @ rest^-1), current frame."""
    out = []
    for name in BONE_ORDER:
        pb = arm.pose.bones[name]
        m = arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
        gm = C @ m @ CI
        for row in range(3):
            out += [round(gm[row][c], 5) for c in range(4)]
    return out


def bake(arm):
    scene = bpy.context.scene
    clips, mats, sit_amount = {}, [], []
    row = 0
    for name, tl, is_loop in CLIPS:
        key_clip(arm, tl)
        last = tl[-1][0]
        n = last if is_loop else last + 1        # loops: the last key equals the first, skip it
        for f in range(n):
            scene.frame_set(f)
            mats += skin_matrices(arm)
            if name in SITTING:
                s = 1.0
            elif name == "stand_up":
                s = 1.0 - f / last
            elif name == "sit_down":
                s = f / last
            else:
                s = 0.0
            sit_amount.append(round(s, 3))
        clips[name] = {"row": row, "frames": n, "loop": is_loop}
        row += n
    return clips, mats, sit_amount


def posed_to_rest(arm, bone, clip_tl, verts_fn):
    """Accessories held in a pose (scarf above the head, flag): build them in that pose's world space,
    then move them back into rest space through the bone's inverse skinning matrix."""
    key_clip(arm, clip_tl)
    bpy.context.scene.frame_set(0)
    pb = arm.pose.bones[bone]
    m = arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
    return m.inverted(), pb


# ------------------------------------------------------------------ export

def export_part(p, arm=None):
    """Triangles of a Part -> dict of flat lists (godot space)."""
    bm = p.bm
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.normal_update()
    uv_over = getattr(p, "uv_over", {})
    n_over = getattr(p, "n_over", {})
    names = {v: k for k, v in p.mat_index.items()}
    bone = BONE_ORDER.index(p.bone)
    pos, part, uv, nrm = [], [], [], []
    # per-part bounding boxes for uv (scarves/flags)
    groups = {}
    for f in bm.faces:
        groups.setdefault(names[f.material_index], []).extend([l.vert.co.copy() for l in f.loops])
    boxes = {}
    for k, pts in groups.items():
        lo = Vector((min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)))
        hi = Vector((max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts)))
        boxes[k] = (lo, hi)
    for f in bm.faces:
        mname = names[f.material_index]
        lo, hi = boxes[mname]
        size = hi - lo
        ax = sorted(range(3), key=lambda i: -size[i])
        n = f.normal
        for l in f.loops:
            co = l.vert.co
            pos += g(co)
            part.append(PARTS.index(mname))
            if l.vert in uv_over:
                uv += list(uv_over[l.vert])
            else:
                uv += [round((co[ax[0]] - lo[ax[0]]) / max(1e-6, size[ax[0]]), 3),
                       round((co[ax[1]] - lo[ax[1]]) / max(1e-6, size[ax[1]]), 3)]
            nrm += g(n_over.get(mname, n))
    tris = len(part) // 3
    return {"pos": pos, "part": part, "uv": uv, "nrm": nrm, "bone": bone, "tris": tris}


def merge(chunks):
    out = {"pos": [], "part": [], "uv": [], "nrm": [], "bone": []}
    for c in chunks:
        out["pos"] += c["pos"]
        out["part"] += c["part"]
        out["uv"] += c["uv"]
        out["nrm"] += c["nrm"]
        out["bone"] += [c["bone"]] * len(c["part"])
    return out


def held_items(arm):
    """Scarf held above the head (chest bone), twirled scarf (right hand), flag (right hand)."""
    chunks = []
    # held scarf: between the hands in the scarf_up pose
    inv, _ = posed_to_rest(arm, "chest", [(0, scarf_up(0.0))], None)
    hl = arm.pose.bones["hand.L"].tail.copy()
    hr = arm.pose.bones["hand.R"].tail.copy()
    p = bp.Part("HeldScarf", "chest")
    a, b = hl + Vector((0, 0, 0.02)), hr + Vector((0, 0, 0.02))
    mid = (a + b) / 2
    p.box(mid + Vector((0, 0, -0.02)), ((a - b).length + 0.1, 0.012, 0.16), "HeldScarf")
    for v in p.bm.verts:
        v.co = inv @ v.co
    chunks.append(export_part(p))
    # twirl scarf: hangs out of the right hand, perpendicular to the forearm
    inv, pb = posed_to_rest(arm, "hand.R", [(0, scarf_twirl(0.0))], None)
    p = bp.Part("TwirlScarf", "hand.R")
    hand = pb.tail.copy()
    axis = (pb.tail - pb.head).normalized()
    side = axis.cross(Vector((0, 1, 0))).normalized()
    p.box(hand + side * 0.4, (0.8, 0.012, 0.15), "TwirlScarf",
          rot=(0, 0, math.atan2(side.y, side.x)))
    for v in p.bm.verts:
        v.co = inv @ v.co
    chunks.append(export_part(p))
    # flag: pole up out of the right hand, cloth to the side
    inv, pb = posed_to_rest(arm, "hand.R", [(0, flag_wave(0.0))], None)   # frame 0 of flag_wave
    hand = (pb.head + pb.tail) / 2
    up = (pb.tail - pb.head).normalized()            # the raised hand points up (wrist -> fingers)
    p = bp.Part("Flag", "hand.R")
    p.ring_tube(hand - up * 0.3, hand + up * 2.05, 0.017, 0.014, "FlagPole", 5)
    out = up.cross(Vector((0, 1, 0))).normalized()
    if out.x < 0:
        out = -out
    W, H, nx, ny = 1.55, 1.0, 12, 7
    p.uv_over = {}
    idx = p.mi("FlagCloth")
    for back in (False, True):                      # two sheets so both sides show
        grid = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                q = hand + up * (2.02 - H * j / ny) + out * (W * i / nx)
                v = p.bm.verts.new(q)
                p.uv_over[v] = (round(i / nx, 3), round(j / ny, 3))
                row.append(v)
            grid.append(row)
        for j in range(ny):
            for i in range(nx):
                quad = (grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1])
                f = p.bm.faces.new(tuple(reversed(quad)) if back else quad)
                f.material_index = idx
    # the cloth waves along one fixed direction (both sides share it)
    p.n_over = {"FlagCloth": (inv.to_3x3() @ up.cross(out)).normalized()}
    for v in p.bm.verts:
        v.co = inv @ v.co
    flag = export_part(p)
    # cloth uv: u from the pole outwards, v top to bottom — recompute from the grid order
    chunks.append(flag)
    arm.animation_data.action = None
    return chunks


def main():
    bp.reset()
    bp.mats()
    for name in PARTS:
        if name not in bp.MATS:
            bp.MATS[name] = bp.material(name, (0.5, 0.5, 0.5))
    bp.HAIR_SEGS = (14, 10)
    orig_curls = bp.curls
    bp.curls = lambda p, keep, k, size, count=150: orig_curls(p, keep, k, size * 1.4, int(count * 0.4))   # fewer, bigger curls
    arm = bp.armature()
    hair_parts = {p.name[5:]: p for p in bp.hair_styles()}
    wanted = set(HAIR["man"] + HAIR["woman"] + HAIR["child"])
    hairs, hair_tris = {}, {}
    for name, p in hair_parts.items():
        if name in wanted:
            e = export_part(p)
            hair_tris[name] = e["tris"]
            hairs[name] = merge([e])
        else:
            p.bm.free()
    bodies = {}
    held = held_items(arm)
    for kind in ("man", "woman", "child"):
        chunks = [export_part(p) for p in body_parts(kind)]
        bodies[kind] = merge(chunks + held)
        print(kind, "tris", len(bodies[kind]["part"]) // 3)
    clips, mats, sit_amount = bake(arm)
    data = {
        "parts": PARTS, "bones": BONE_ORDER, "fps": FPS, "clips": clips, "matrices": mats, "sit": sit_amount,
        "bodies": bodies, "hairs": hairs, "hair_sets": HAIR,
        "head_center": g(bp.HC), "seat_height": 0.455,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("hair tris", hair_tris)
    print("WROTE", OUT, os.path.getsize(OUT) // 1024, "KB, frames", len(sit_amount))


if __name__ == "__main__":
    main()
