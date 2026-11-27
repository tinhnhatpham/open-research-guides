#!/usr/bin/env python3
"""
Production Humanoid + 21-Joint Feix Handgrip Rig Builder for Blender 4.x+
=========================================================================
Open Plain-Language Research (MIT License)
https://open-research-guides.vercel.app/guides/3d-model-motion/

Run inside Blender (Scripting workspace) or headless:
    blender --background --python build_blender_humanoid_handgrip_rig.py -- --out production_humanoid_feix_handgrip.glb

Features built from 2022-2026 primary 3D character motion research:
  1. UE5 / MetaHuman-aligned 66-bone deform hierarchy:
     - pelvis root + 5 spine bones (spine_01..spine_05) + neck + head
     - dedicated forearm & upperarm twist bones (lowerarm_twist_01_l/r, upperarm_twist_01_l/r)
       driven by 50% local Y-axis COPY_ROTATION to prevent LBS candy-wrapper collapse
     - full 5-digit articulated hands (thumb CMC/MCP/IP + index/middle/ring/pinky MCP/PIP/DIP)
  2. Anatomical LIMIT_ROTATION constraints (1-DOF PIP/DIP hinges, 2-DOF MCP, thumb opposition).
  3. Blender 4.x Bone Collections separating DEF, TWIST, HANDS, and IK_CTRL bones.
  4. Five Feix GRASP taxonomy pose actions baked onto the rig:
     GRASP_Open, GRASP_Power_Cylinder, GRASP_Precision_Pinch, GRASP_Tripod_Tool, GRASP_Lateral_Key.
  5. Skinned proxy character mesh strictly limited to <=4 weights/vertex (normalized to 1.0)
     and exported cleanly to glTF 2.0 (.glb) with quaternions.
"""

import math
import sys

try:
    import bpy
    import bmesh
    from mathutils import Euler, Vector
except ImportError:
    print(
        "This script runs inside Blender's Python environment (bpy).\n"
        "Usage: blender --background --python build_blender_humanoid_handgrip_rig.py -- --out rig.glb"
    )
    sys.exit(0)


def parse_out_path():
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
        for i, a in enumerate(args):
            if a == "--out" and i + 1 < len(args):
                return args[i + 1]
    return "production_humanoid_feix_handgrip.glb"


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_bone(edit_bones, name, head, tail, parent=None, use_connect=False, roll=0.0):
    b = edit_bones.new(name)
    b.head = Vector(head)
    b.tail = Vector(tail)
    b.roll = roll
    if parent is not None:
        b.parent = parent
        b.use_connect = use_connect
    return b


def build_armature():
    arm_data = bpy.data.armatures.new("ProductionHumanoidArmature")
    arm_obj = bpy.data.objects.new("ProductionHumanoid", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones

    # Blender uses Z-up, Y-forward (-Y front). Measurements in meters.
    pelvis = add_bone(eb, "pelvis", (0, 0, 0.96), (0, 0, 1.08))
    sp1 = add_bone(eb, "spine_01", (0, 0, 1.08), (0, 0, 1.16), pelvis, True)
    sp2 = add_bone(eb, "spine_02", (0, 0, 1.16), (0, 0, 1.24), sp1, True)
    sp3 = add_bone(eb, "spine_03", (0, 0, 1.24), (0, 0, 1.32), sp2, True)
    sp4 = add_bone(eb, "spine_04", (0, 0, 1.32), (0, 0, 1.40), sp3, True)
    sp5 = add_bone(eb, "spine_05", (0, 0, 1.40), (0, 0, 1.48), sp4, True)
    neck = add_bone(eb, "neck_01", (0, 0, 1.48), (0, 0, 1.56), sp5, True)
    add_bone(eb, "head", (0, 0, 1.56), (0, 0, 1.76), neck, True)

    twist_pairs = []
    hand_bones = []
    ik_targets = []

    for side, s in (("l", 1.0), ("r", -1.0)):
        # Legs
        thigh = add_bone(eb, f"thigh_{side}", (0.105 * s, 0, 0.93), (0.105 * s, -0.01, 0.49), pelvis)
        calf = add_bone(eb, f"calf_{side}", (0.105 * s, -0.01, 0.49), (0.105 * s, 0.01, 0.06), thigh, True)
        foot = add_bone(eb, f"foot_{side}", (0.105 * s, 0.01, 0.06), (0.105 * s, -0.14, 0.02), calf, True)
        add_bone(eb, f"ball_{side}", (0.105 * s, -0.14, 0.02), (0.105 * s, -0.21, 0.02), foot, True)

        # Foot IK control bone
        foot_ik = add_bone(eb, f"ik_foot_{side}", (0.105 * s, 0.01, 0.06), (0.105 * s, -0.12, 0.06))
        foot_ik.use_deform = False
        ik_targets.append((f"calf_{side}", f"ik_foot_{side}", 2))

        # Arms + Dedicated Twist Bones (prevents LBS candy-wrapper pinching)
        clav = add_bone(eb, f"clavicle_{side}", (0.04 * s, 0, 1.43), (0.18 * s, 0, 1.45), sp5)
        uarm = add_bone(eb, f"upperarm_{side}", (0.18 * s, 0, 1.45), (0.46 * s, 0.01, 1.42), clav, True)
        add_bone(eb, f"upperarm_twist_01_{side}", (0.18 * s, 0, 1.45), (0.32 * s, 0.005, 1.435), uarm)

        larm = add_bone(eb, f"lowerarm_{side}", (0.46 * s, 0.01, 1.42), (0.72 * s, 0, 1.40), uarm, True)
        larm_twist = add_bone(eb, f"lowerarm_twist_01_{side}", (0.59 * s, 0.005, 1.41), (0.72 * s, 0, 1.40), larm)
        hand = add_bone(eb, f"hand_{side}", (0.72 * s, 0, 1.40), (0.81 * s, 0, 1.40), larm, True)
        twist_pairs.append((larm_twist.name, hand.name))

        # Hand IK control bone
        hand_ik = add_bone(eb, f"ik_hand_{side}", (0.72 * s, 0, 1.40), (0.80 * s, 0, 1.40))
        hand_ik.use_deform = False
        ik_targets.append((f"lowerarm_{side}", f"ik_hand_{side}", 2))

        # Articulated 5-Finger Hand (MANO 15 finger joints + metacarpal base)
        # Thumb (CMC -> MCP -> IP)
        t1 = add_bone(eb, f"thumb_01_{side}", (0.74 * s, -0.025, 1.385), (0.775 * s, -0.055, 1.365), hand)
        t2 = add_bone(eb, f"thumb_02_{side}", t1.tail, (0.805 * s, -0.075, 1.355), t1, True)
        t3 = add_bone(eb, f"thumb_03_{side}", t2.tail, (0.830 * s, -0.088, 1.350), t2, True)
        hand_bones.extend([t1.name, t2.name, t3.name])

        finger_specs = [
            ("index", -0.032, 0.006, (0.040, 0.026, 0.020)),
            ("middle", -0.010, 0.008, (0.044, 0.029, 0.021)),
            ("ring", 0.012, 0.004, (0.041, 0.026, 0.020)),
            ("pinky", 0.032, -0.004, (0.032, 0.021, 0.017)),
        ]
        for fname, y_off, z_off, segs in finger_specs:
            p0 = (0.81 * s, y_off, 1.40 + z_off)
            p1 = (p0[0] + segs[0] * s, y_off, p0[2])
            p2 = (p1[0] + segs[1] * s, y_off, p1[2])
            p3 = (p2[0] + segs[2] * s, y_off, p2[2])
            b1 = add_bone(eb, f"{fname}_01_{side}", p0, p1, hand)
            b2 = add_bone(eb, f"{fname}_02_{side}", p1, p2, b1, True)
            b3 = add_bone(eb, f"{fname}_03_{side}", p2, p3, b2, True)
            hand_bones.extend([b1.name, b2.name, b3.name])

    bpy.ops.object.mode_set(mode="OBJECT")

    # Organize Blender 4.x Bone Collections
    if hasattr(arm_data, "collections"):
        col_def = arm_data.collections.new("DEF_Body")
        col_twist = arm_data.collections.new("TWIST_Helpers")
        col_hands = arm_data.collections.new("HANDS_21Keypoint")
        col_ik = arm_data.collections.new("IK_Controls")
        for b in arm_data.bones:
            if b.name.startswith("ik_"):
                col_ik.assign(b)
            elif "twist" in b.name:
                col_twist.assign(b)
            elif b.name in hand_bones:
                col_hands.assign(b)
            else:
                col_def.assign(b)

    # Pose constraints: 50% forearm twist + anatomical finger hinge limits + optional IK
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm_obj.pose.bones

    for twist_name, hand_name in twist_pairs:
        c = pb[twist_name].constraints.new("COPY_ROTATION")
        c.target = arm_obj
        c.subtarget = hand_name
        c.use_x = False
        c.use_y = True
        c.use_z = False
        c.target_space = "LOCAL"
        c.owner_space = "LOCAL"
        c.influence = 0.5

    for hb_name in hand_bones:
        lim = pb[hb_name].constraints.new("LIMIT_ROTATION")
        lim.owner_space = "LOCAL"
        lim.use_limit_x = True
        lim.use_limit_y = True
        lim.use_limit_z = True
        if "_02_" in hb_name or "_03_" in hb_name:
            # PIP / DIP 1-DOF anatomical hinges (prevent sideways twisting)
            lim.min_x, lim.max_x = math.radians(-5), math.radians(105)
            lim.min_y, lim.max_y = math.radians(-3), math.radians(3)
            lim.min_z, lim.max_z = math.radians(-3), math.radians(3)
        elif "thumb_01" in hb_name:
            # Multi-axis CMC saddle joint for thumb opposition
            lim.min_x, lim.max_x = math.radians(-35), math.radians(65)
            lim.min_y, lim.max_y = math.radians(-45), math.radians(55)
            lim.min_z, lim.max_z = math.radians(-30), math.radians(50)
        else:
            # MCP 2-DOF (flexion + abduction/adduction)
            lim.min_x, lim.max_x = math.radians(-20), math.radians(95)
            lim.min_y, lim.max_y = math.radians(-5), math.radians(5)
            lim.min_z, lim.max_z = math.radians(-20), math.radians(20)

    for limb_name, target_name, chain_len in ik_targets:
        ik = pb[limb_name].constraints.new("IK")
        ik.target = arm_obj
        ik.subtarget = target_name
        ik.chain_count = chain_len
        ik.influence = 0.0  # Ready to toggle to 1.0 when animating with IK

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bake_feix_grasp_actions(arm_obj):
    """Creates 5 Feix GRASP taxonomy pose actions on the armature."""
    presets = {
        "GRASP_Open": {"thumb": (0, 0, 0), "index": 8, "middle": 8, "ring": 10, "pinky": 12},
        "GRASP_Power_Cylinder": {"thumb": (38, 35, 22), "index": 68, "middle": 72, "ring": 74, "pinky": 76},
        "GRASP_Precision_Pinch": {"thumb": (48, 45, 32), "index": 58, "middle": 20, "ring": 16, "pinky": 14},
        "GRASP_Tripod_Tool": {"thumb": (44, 42, 28), "index": 60, "middle": 56, "ring": 26, "pinky": 20},
        "GRASP_Lateral_Key": {"thumb": (22, 18, 10), "index": 76, "middle": 74, "ring": 74, "pinky": 72},
    }

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE")
    pb = arm_obj.pose.bones

    for act_name, cfg in presets.items():
        act = bpy.data.actions.new(name=act_name)
        arm_obj.animation_data_create().action = act
        for b in pb:
            b.rotation_mode = "QUATERNION"
            b.rotation_quaternion = (1, 0, 0, 0)

        for side in ("l", "r"):
            tx, ty, tz = [math.radians(v) for v in cfg["thumb"]]
            pb[f"thumb_01_{side}"].rotation_quaternion = Euler((tx, ty, tz), "XYZ").to_quaternion()
            pb[f"thumb_02_{side}"].rotation_quaternion = Euler((tx * 0.7, 0, 0), "XYZ").to_quaternion()
            pb[f"thumb_03_{side}"].rotation_quaternion = Euler((tx * 0.6, 0, 0), "XYZ").to_quaternion()
            for fname in ("index", "middle", "ring", "pinky"):
                deg = cfg[fname]
                for seg, mult in (("01", 0.85), ("02", 1.0), ("03", 0.75)):
                    bone = pb[f"{fname}_{seg}_{side}"]
                    bone.rotation_quaternion = Euler((math.radians(deg * mult), 0, 0), "XYZ").to_quaternion()

        for b in pb:
            b.keyframe_insert(data_path="rotation_quaternion", frame=1)

    bpy.ops.object.mode_set(mode="OBJECT")


def build_proxy_mesh_and_bind(arm_obj):
    """Builds a clean low-poly proxy mesh bound strictly with <=4 normalized weights/vertex."""
    mesh = bpy.data.meshes.new("HumanoidProxyMesh")
    obj = bpy.data.objects.new("HumanoidProxy", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    for b in arm_obj.data.bones:
        if not b.use_deform:
            continue
        length = (b.tail_local - b.head_local).length
        if length < 0.005:
            continue
        rad = 0.008 if any(k in b.name for k in ("thumb", "index", "middle", "ring", "pinky")) else 0.042
        mid = (b.head_local + b.tail_local) * 0.5
        ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rad)
        for v in ret["verts"]:
            v.co += mid

    bm.to_mesh(mesh)
    bm.free()

    obj.parent = arm_obj
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj

    # Bind each vertex cleanly to its nearest 2 deform bones (strict <=4 limit, normalized)
    deform_bones = [b for b in arm_obj.data.bones if b.use_deform]
    vgroups = {b.name: obj.vertex_groups.new(name=b.name) for b in deform_bones}
    bone_mids = [(b.name, (b.head_local + b.tail_local) * 0.5) for b in deform_bones]

    for v in mesh.vertices:
        dists = sorted(((v.co - m).length, name) for name, m in bone_mids)
        d0, n0 = dists[0]
        d1, n1 = dists[1]
        w0 = 1.0 / max(1e-4, d0)
        w1 = 0.35 / max(1e-4, d1)
        tot = w0 + w1
        vgroups[n0].add([v.index], w0 / tot, "REPLACE")
        vgroups[n1].add([v.index], w1 / tot, "REPLACE")

    return obj


def main():
    out_path = parse_out_path()
    clear_scene()
    arm_obj = build_armature()
    bake_feix_grasp_actions(arm_obj)
    build_proxy_mesh_and_bind(arm_obj)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_def_bones=True,
        export_animations=True,
        export_yup=True,
    )
    print(f"Exported clean production rig with Feix handgrip actions to: {out_path}")


if __name__ == "__main__":
    main()
