import sys,json,tempfile
from pathlib import Path
root=Path(__file__).parents[1]
sys.path[:0]=[str(root),str(root/'tools')]
import bpy
from ultra_motion_studio import core,rig
from sample_action import sample
from mix_reference import blend

source=rig.demo_rig()
ref,report=rig.bake(source,core.demo_data())
sampled=sample(ref,1,72)
assert len(sampled['frames'])==72
assert sampled['fps']==24
frames,_,_=core.prepare(sampled,0)
assert all(abs((f['left_hip'][i]+f['right_hip'][i])*.5)<1e-7 for f in frames for i in range(3))
# Translation and units: hip recentering removes object translation, unit scale is explicit.
ref.location.x=17
scaled=sample(ref,1,72,.01)
for j in core.JOINTS:
    for a,b in zip(sampled['frames'][30]['joints'][j][:3],scaled['frames'][30]['joints'][j][:3]):
        assert abs(a*.01-b)<1e-6
ref.location.x=0
rotated=sample(ref,1,72,yaw=180)
for a,b in zip(sampled['frames'][30]['joints']['left_wrist'][:2],rotated['frames'][30]['joints']['left_wrist'][:2]):
    assert abs(a+b)<1e-5
# Constraints are evaluated before sampling, not stripped.
c=ref.pose.bones['left_forearm'].constraints.new('COPY_LOCATION')
c.target=source; c.subtarget='right_forearm'; c.target_space='WORLD'; c.owner_space='WORLD'
constrained=sample(ref,1,72)
assert abs(constrained['frames'][30]['joints']['left_elbow'][0]-sampled['frames'][30]['joints']['left_elbow'][0])>.1
ref.pose.bones['left_forearm'].constraints.remove(c)
mixed=blend(core.demo_data(),sampled,.35)
result,report=rig.bake(source,mixed)
assert result.animation_data.action and report['frames']==90
assert len(result.animation_data.action.fcurves)==36
print('UMS_REFERENCE_PASS '+json.dumps({'blender':bpy.app.version_string,'sampled_frames':72,'mixed_frames':90,'channels':36,'tests':['hip recenter','unit scale','facing yaw','evaluated constraints','sample-mix-rebake']}))
