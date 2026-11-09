"""Blender background entry point. Run with --python-exit-code 1."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bpy
from ultra_motion_studio import core,rig

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pose'); p.add_argument('--armature')
    p.add_argument('--output',required=True); p.add_argument('--mapping')
    p.add_argument('--smoothing',type=float,default=65)
    p.add_argument('--no-foot-lock',action='store_true'); p.add_argument('--loop',action='store_true')
    p.add_argument('--demo',action='store_true'); p.add_argument('--vmd')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=Path(args.output).resolve()
    if out.suffix.lower()!='.blend': raise ValueError('Output must end in .blend')
    report_path=out.with_suffix('.report.json')
    for path in [out,report_path]+([Path(args.vmd)] if args.vmd else []):
        if path.exists(): raise ValueError('Output exists: '+str(path))
    if args.demo:
        source=rig.demo_rig(); data=core.demo_data()
    else:
        if not args.pose: raise ValueError('--pose is required unless --demo is used')
        with open(args.pose,encoding='utf-8-sig') as f: data=json.load(f)
        candidates=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
        source=bpy.data.objects.get(args.armature) if args.armature else (candidates[0] if len(candidates)==1 else None)
        if source is None or source.type!='ARMATURE': raise ValueError('Specify --armature with the target armature object name')
    overrides=None
    if args.mapping:
        with open(args.mapping,encoding='utf-8-sig') as f: overrides=json.load(f)
    obj,report=rig.bake(source,data,args.smoothing/100,not args.no_foot_lock,args.loop,overrides=overrides)
    report['input_source']=data.get('source','unspecified')
    if 'mix_report' in data: report['reference_mix']=data['mix_report']
    # Duplicate meshes so the saved result can be previewed without changing originals.
    for original in list(bpy.context.scene.objects):
        if original.type!='MESH': continue
        if not any(m.type=='ARMATURE' and m.object==source for m in original.modifiers): continue
        mesh=original.copy(); mesh.data=original.data.copy(); mesh.animation_data_clear()
        bpy.context.collection.objects.link(mesh); mesh.name=original.name+'_UMS'
        world=mesh.matrix_world.copy()
        if mesh.parent==source: mesh.parent=obj; mesh.matrix_world=world
        for modifier in mesh.modifiers:
            if modifier.type=='ARMATURE' and modifier.object==source: modifier.object=obj
        original.hide_render=True; original.hide_set(True)
    source.hide_render=True; source.hide_set(True)
    target_fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
    bpy.context.scene.frame_end=round(1+(report['frames']-1)*target_fps/report['fps']+(target_fps*.2 if args.loop else 0))
    bpy.context.scene.frame_set(1)
    out.parent.mkdir(parents=True,exist_ok=True)
    report['vmd_export']='not_requested'
    if args.vmd:
        try:
            bpy.ops.mmd_tools.export_vmd(filepath=str(Path(args.vmd).resolve()))
            report['vmd_export']='exported; verify in target MMD with leg IK disabled'
        except Exception as exc:
            report['vmd_export']='FAILED: '+str(exc)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('UMS_OUTPUT '+str(out)); print(json.dumps(report,ensure_ascii=False))
    if report['vmd_export'].startswith('FAILED'): raise RuntimeError(report['vmd_export'])

if __name__=='__main__': main()
