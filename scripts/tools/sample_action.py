"""Sample an already imported, evaluated reference armature into UMS pose JSON."""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import bpy
from mathutils import Matrix
from ultra_motion_studio import core,rig

def sample(obj,start,end,meters_per_unit=1.0,yaw=0,mapping=None):
    if not 0<meters_per_unit<=100 or not math.isfinite(meters_per_unit): raise ValueError('Invalid unit scale')
    if not math.isfinite(yaw): raise ValueError('Invalid facing rotation')
    if not 2<=end-start+1<=36000: raise ValueError('Expected 2..36000 sample frames')
    # Explicit 12-joint mapping supports FBX/BVH conventions without guessing their bone axes.
    if mapping is None:
        roles=rig.mapping(obj)
        mapping={}
        for side in ('left','right'):
            for joint,role,point in [('shoulder','upper_arm','head'),('elbow','forearm','head'),('wrist','forearm','tail'),
                                     ('hip','thigh','head'),('knee','shin','head'),('ankle','shin','tail')]:
                mapping[side+'_'+joint]={'bone':roles[side+'_'+role],'point':point}
    for j in core.JOINTS:
        entry=mapping.get(j,{})
        if entry.get('bone') not in obj.pose.bones or entry.get('point') not in ('head','tail'):
            raise ValueError('Invalid head/tail mapping for '+j)
    turn=Matrix.Rotation(math.radians(yaw),3,'Z')
    frames=[]; scene=bpy.context.scene
    old_frame,old_subframe=scene.frame_current,scene.frame_subframe
    try:
        for frame in range(start,end+1):
            scene.frame_set(frame)
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            points={j:turn@(ev.matrix_world@getattr(ev.pose.bones[mapping[j]['bone']],mapping[j]['point']))*meters_per_unit for j in core.JOINTS}
            origin=(points['left_hip']+points['right_hip'])*.5
            frames.append({'joints':{j:list(points[j]-origin)+[1.0] for j in core.JOINTS}})
    finally: scene.frame_set(old_frame,subframe=old_subframe)
    result={'schema':'ums.pose.v1','coordinates':'x_right_y_back_z_up_m',
            'fps':scene.render.fps/scene.render.fps_base,'frames':frames,
            'source':obj.name,'sampling':{'frames':[start,end],'meters_per_blender_world_unit':meters_per_unit,
            'yaw_degrees':yaw,'mapping':mapping,'root_motion':'removed per-frame hip midpoint',
            'note':'Evaluated pose including constraints. Requires world Z-up and manually verified facing.'}}
    core.prepare(result,0)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--armature',required=True); p.add_argument('--start',type=int,required=True)
    p.add_argument('--end',type=int,required=True); p.add_argument('--output',required=True)
    p.add_argument('--meters-per-unit',type=float,default=1); p.add_argument('--yaw',type=float,default=0)
    p.add_argument('--mapping')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=Path(a.output)
    if out.exists(): raise ValueError('Output exists')
    obj=bpy.data.objects.get(a.armature)
    if obj is None or obj.type!='ARMATURE': raise ValueError('Armature not found')
    mapping=json.loads(Path(a.mapping).read_text(encoding='utf-8-sig')) if a.mapping else None
    data=sample(obj,a.start,a.end,a.meters_per_unit,a.yaw,mapping)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,allow_nan=False)
    print('UMS_REFERENCE_SAMPLED '+str(out))

if __name__=='__main__': main()
