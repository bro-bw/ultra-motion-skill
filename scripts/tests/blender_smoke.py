"""blender --background --factory-startup --python tests/blender_smoke.py"""
import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import bpy
from mathutils import Vector
import ultra_motion_studio as ums
from ultra_motion_studio import core,rig

ums.register()
s=bpy.context.scene.ums_settings
assert s.smoothing==65 and s.foot_lock and not s.loop
src=rig.demo_rig()
constraint=src.pose.bones['left_shin'].constraints.new('LIMIT_ROTATION')
obj,report=rig.bake(src,core.demo_data())
assert obj!=src and src.animation_data is None
assert len(src.pose.bones['left_shin'].constraints)==1
assert len(obj.pose.bones['left_shin'].constraints)==0
assert report['locked_foot_frames']==180
assert obj.animation_data.action is not None
base=None; max_drift=0
for frame in range(1,73):
    bpy.context.scene.frame_set(frame)
    p=obj.pose.bones['left_shin'].tail.copy()
    if base is None: base=p
    max_drift=max(max_drift,(p-base).length)
assert max_drift<1e-5, max_drift
# Parent-space conversion: the actual limb points along the requested world direction.
pb=obj.pose.bones['left_forearm']
direction=Vector((.3,-.2,.1))
rig.aim(pb,direction)
assert (pb.tail-pb.head).normalized().dot(direction.normalized())>.9999
# Reach clamping is finite and explicitly reported.
k,a,clamped=rig.knee_point(Vector((0,0,0)),Vector((0,0,-10)),Vector((0,-1,-1)),.5,.5)
assert clamped and a.length<1.00001
# Failed inputs leave scene unchanged.
before=len(bpy.data.objects)
try: rig.bake(src,{'schema':'bad'})
except ValueError: pass
else: raise AssertionError('Invalid data accepted')
assert len(bpy.data.objects)==before
# Japanese names map without requiring mmd_tools to be installed.
for role,name in list(rig.mapping(src).items()): src.pose.bones[name].name=rig.ALIASES[role][0]
assert len(rig.mapping(src))==9
looped,_=rig.bake(src,core.demo_data(),loop=True)
assert all(any(m.type=='CYCLES' for m in fc.modifiers) for fc in looped.animation_data.action.fcurves)
ums.unregister(); ums.register(); ums.unregister()
print('UMS_SMOKE_PASS '+json.dumps({'blender':bpy.app.version_string,'max_stationary_foot_drift':max_drift,'report':report},ensure_ascii=False))
