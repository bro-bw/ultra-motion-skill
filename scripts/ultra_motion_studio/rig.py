"""Rest-axis aware FK baking on an isolated armature copy."""
import math
import bpy
from mathutils import Vector, Matrix
from . import core

ALIASES = {'spine': ('上半身','upper body','spine')}
for side,jp in [('left','左'),('right','右')]:
    for part, jpart, en in [('upper_arm','腕','arm'),('forearm','ひじ','elbow'),('thigh','足','leg'),('shin','ひざ','knee')]:
        ALIASES[side+'_'+part] = (jp+jpart, side+' '+en, side+'_'+part)

def mapping(obj, overrides=None):
    result = {}
    for role, aliases in ALIASES.items():
        if overrides and role in overrides:
            name = overrides[role]
            if name not in obj.pose.bones: raise ValueError('Mapped bone not found: '+name)
            result[role] = name
            continue
        for pb in obj.pose.bones:
            mb = getattr(pb, 'mmd_bone', None)
            names = (pb.name, getattr(mb,'name_j',''), getattr(mb,'name_e',''))
            if any(n.casefold() in [a.casefold() for a in aliases] for n in names):
                result[role] = pb.name
                break
    missing = set(ALIASES)-set(result)
    if missing: raise ValueError('Missing bone mapping: '+', '.join(sorted(missing)))
    if len(set(result.values())) != len(result): raise ValueError('A bone cannot fill multiple roles')
    for side in ('left','right'):
        for a,b in [('upper_arm','forearm'),('thigh','shin')]:
            if obj.pose.bones[result[side+'_'+a]] not in obj.pose.bones[result[side+'_'+b]].parent_recursive:
                raise ValueError('Invalid bone hierarchy: '+side+'_'+b)
    return result

def aim(pb, direction):
    if direction.length < 1e-7: return
    rest = pb.bone.matrix_local.to_quaternion()
    q = (rest @ Vector((0,1,0))).rotation_difference(direction.normalized()) @ rest
    desired = q.to_matrix().to_4x4()
    desired.translation = pb.head
    kwargs = {}
    if pb.parent:
        kwargs = {'parent_matrix':pb.parent.matrix, 'parent_matrix_local':pb.parent.bone.matrix_local}
    basis = pb.bone.convert_local_to_pose(desired, pb.bone.matrix_local, invert=True, **kwargs)
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = basis.to_quaternion()
    bpy.context.view_layer.update()

def knee_point(hip, ankle, hint, l1, l2):
    delta = ankle-hip
    distance = delta.length
    axis = delta.normalized() if distance > 1e-8 else Vector((0,0,-1))
    d = min(max(distance, abs(l1-l2)+1e-6), l1+l2-1e-6)
    along = (l1*l1-l2*l2+d*d)/(2*d)
    pole = hint-hip
    pole -= axis*pole.dot(axis)
    if pole.length < 1e-5:
        pole = Vector((0,-1,0))
        pole -= axis*pole.dot(axis)
    if pole.length < 1e-5: pole = axis.orthogonal()
    knee = hip+axis*along+pole.normalized()*math.sqrt(max(0,l1*l1-along*along))
    return knee, hip+axis*d, abs(distance-d)>1e-4

def bake(source, data, smoothing=.65, foot_lock=True, loop=False, start=1, overrides=None):
    frames, fps, repaired = core.prepare(data, smoothing)
    names = mapping(source, overrides)
    # Everything generated is isolated. Original mesh/armature/actions are untouched.
    obj = source.copy()
    obj.data = source.data.copy()
    obj.animation_data_clear()
    obj.name = source.name+'_UMS_Baked'
    bpy.context.collection.objects.link(obj)
    obj.show_in_front = True
    try:
        for c in list(obj.constraints): obj.constraints.remove(c)
        for pb in obj.pose.bones:
            for c in list(pb.constraints): pb.constraints.remove(c)
            pb.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()
        bones = {k:obj.pose.bones[v] for k,v in names.items()}
        first = frames[0]
        scale = sum(bones['left_'+p].length for p in ('thigh','shin')) / (core.length(core.sub(first['left_hip'],first['left_knee']))+core.length(core.sub(first['left_knee'],first['left_ankle'])))
        if not math.isfinite(scale) or scale <= 0: raise ValueError('Invalid source or target leg length')
        offsets = {s:bones[s+'_shin'].tail.copy()-Vector(first[s+'_ankle'])*scale for s in ('left','right')}
        flags = core.contacts(frames,fps)
        anchors = {}; clamped = 0; locked = 0; previous = {}
        obj.animation_data_create()
        action = bpy.data.actions.new('UMS_'+source.name)
        obj.animation_data.action = action
        action.use_fake_user = True
        # Source is fixed-rate. Fractional destination frames preserve video duration.
        target_fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        for i,f in enumerate(frames):
            for pb in obj.pose.bones: pb.matrix_basis = Matrix.Identity(4)
            bpy.context.view_layer.update()
            v = lambda key: Vector(f[key])
            aim(bones['spine'], (v('left_shoulder')+v('right_shoulder')-v('left_hip')-v('right_hip'))*.5)
            for side in ('left','right'):
                aim(bones[side+'_upper_arm'], v(side+'_elbow')-v(side+'_shoulder'))
                aim(bones[side+'_forearm'], v(side+'_wrist')-v(side+'_elbow'))
                thigh, shin = bones[side+'_thigh'], bones[side+'_shin']
                if foot_lock:
                    ankle = v(side+'_ankle')*scale+offsets[side]
                    if flags[side][i]:
                        if side not in anchors: anchors[side] = ankle.copy()
                        ankle = anchors[side]; locked += 1
                    else: anchors.pop(side,None)
                    hint = v(side+'_knee')*scale+offsets[side]
                    knee, ankle, clip = knee_point(thigh.head,ankle,hint,thigh.length,shin.length)
                    clamped += int(clip)
                    aim(thigh,knee-thigh.head)
                    aim(shin,ankle-shin.head)
                else:
                    aim(thigh,v(side+'_knee')-v(side+'_hip'))
                    aim(shin,v(side+'_ankle')-v(side+'_knee'))
            for role,pb in bones.items():
                q = pb.rotation_quaternion.copy()
                if role in previous and q.dot(previous[role]) < 0: q.negate()
                pb.rotation_quaternion = q
                previous[role] = q.copy()
                pb.keyframe_insert('rotation_quaternion', frame=start+i*target_fps/fps, group=pb.name)
        # Works with Blender 4.4+ layered actions and legacy actions.
        curves = []
        if hasattr(action,'layers') and len(action.layers):
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags: curves.extend(bag.fcurves)
        else: curves = list(action.fcurves)
        for fc in curves:
            for key in fc.keyframe_points: key.interpolation = 'LINEAR'
            if loop:
                # Explicit seam key over 0.2 seconds; modest motions only.
                fc.keyframe_points.insert(start+(len(frames)-1)*target_fps/fps+target_fps*.2, fc.keyframe_points[0].co.y).interpolation = 'LINEAR'
                fc.modifiers.new('CYCLES')
        report = {'frames':len(frames),'fps':fps,'repaired_landmarks':repaired,
                  'locked_foot_frames':locked,'unreachable_foot_frames':clamped,'mapping':names,
                  'smoothing':smoothing,'foot_lock':foot_lock,'loop':loop}
        import json
        obj['ums_report'] = json.dumps(report,ensure_ascii=False)
        bpy.context.view_layer.objects.active = obj
        for item in bpy.context.selected_objects: item.select_set(False)
        obj.select_set(True)
        bpy.context.scene.frame_set(start)
        return obj, report
    except Exception:
        armature = obj.data
        action = obj.animation_data.action if obj.animation_data else None
        bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.armatures.remove(armature)
        if action: bpy.data.actions.remove(action)
        raise

def demo_rig():
    data = bpy.data.armatures.new('UMS_Demo')
    obj = bpy.data.objects.new('UMS_Demo',data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,head,tail,parent=None):
        b = data.edit_bones.new(name); b.head=head; b.tail=tail
        if parent: b.parent=data.edit_bones[parent]
    bone('spine',(0,0,0),(0,0,.5))
    for s,sign in [('left',1),('right',-1)]:
        bone(s+'_upper_arm',(.2*sign,0,.5),(.45*sign,0,.35),'spine')
        bone(s+'_forearm',(.45*sign,0,.35),(.65*sign,-.08,.3),s+'_upper_arm')
        bone(s+'_thigh',(.1*sign,0,0),(.1*sign,-.04,-.43))
        bone(s+'_shin',(.1*sign,-.04,-.43),(.1*sign,0,-.85),s+'_thigh')
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj
