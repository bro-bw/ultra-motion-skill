"""Explicit phase-aligned limb-direction mixing, not learned style transfer."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

spec=importlib.util.spec_from_file_location('ums_core',Path(__file__).parents[1]/'ultra_motion_studio/core.py')
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

def unit(v):
    n=core.length(v)
    if n<1e-7: raise ValueError('Zero-length limb in pose')
    return core.mul(v,1/n)

def direction_mix(a,b,w):
    a,b=unit(a),unit(b)
    dot=max(-1,min(1,sum(x*y for x,y in zip(a,b))))
    if dot < -.999:
        raise ValueError('Opposite limb directions: check facing/mirroring or choose a closer reference')
    if dot > .999: return unit(core.mix(a,b,w))
    theta=math.acos(dot)
    return core.add(core.mul(a,math.sin((1-w)*theta)/math.sin(theta)),core.mul(b,math.sin(w*theta)/math.sin(theta)))

def blend(base,reference,weight=.35,mask='arms',base_range=None,ref_range=None,fade=.15):
    if not math.isfinite(weight) or not 0<=weight<=1: raise ValueError('weight must be 0..1')
    if not math.isfinite(fade) or not 0<=fade<=.5: raise ValueError('fade must be 0..0.5 of selected interval')
    if mask not in ('arms','legs','all'): raise ValueError('mask must be arms/legs/all')
    bf,fps,bfix=core.prepare(base,0); rf,rfps,rfix=core.prepare(reference,0)
    bs,be=base_range or (0,len(bf)-1); rs,re=ref_range or (0,len(rf)-1)
    if not (0<=bs<be<len(bf) and 0<=rs<re<len(rf)): raise ValueError('Invalid inclusive frame range')
    output=[]
    for i,frame in enumerate(bf):
        f=dict(frame)
        if bs<=i<=be and weight>0:
            phase=(i-bs)/(be-bs)
            pos=rs+phase*(re-rs); lo=int(pos); hi=min(lo+1,re)
            r={j:core.mix(rf[lo][j],rf[hi][j],pos-lo) for j in core.JOINTS}
            envelope=1 if fade==0 else min(1,phase/fade,(1-phase)/fade)
            w=weight*envelope
            if w>0:
                for side in ('left','right'):
                    chains=[]
                    if mask in ('arms','all'): chains.append(('shoulder','elbow','wrist'))
                    if mask in ('legs','all'): chains.append(('hip','knee','ankle'))
                    for chain in chains:
                        for a,b in zip(chain,chain[1:]):
                            a,b=side+'_'+a,side+'_'+b
                            base_v=core.sub(frame[b],frame[a]); ref_v=core.sub(r[b],r[a])
                            d=direction_mix(base_v,ref_v,w)
                            f[b]=core.add(f[a],core.mul(d,core.length(base_v)))
        output.append({'joints':{j:list(f[j])+[1.0] for j in core.JOINTS}})
    return {'schema':'ums.pose.v1','coordinates':base['coordinates'],'fps':fps,'frames':output,
            'source':'Explicit reference limb-direction mix; not automatic semantic alignment',
            'mix_report':{'weight':weight,'mask':mask,'base_range':[bs,be],'reference_range':[rs,re],
                          'fade_fraction':fade,'base_fps':fps,'reference_fps':rfps,
                          'base_repaired_landmarks':bfix,'reference_repaired_landmarks':rfix,
                          'confidence_policy':'Output confidence=1 marks processed data, not estimator certainty',
                          'root_motion':'unchanged from base; hip/shoulder positions retained',
                          'alignment':'Selected ranges linearly aligned by normalized phase'}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True); p.add_argument('--reference',required=True)
    p.add_argument('--output',required=True); p.add_argument('--weight',type=float,default=.35)
    p.add_argument('--mask',choices=['arms','legs','all'],default='arms')
    p.add_argument('--base-range',nargs=2,type=int); p.add_argument('--ref-range',nargs=2,type=int)
    p.add_argument('--fade',type=float,default=.15)
    a=p.parse_args()
    base=Path(a.base); ref=Path(a.reference); out=Path(a.output)
    if out.exists(): raise ValueError('Output exists; choose a new filename')
    result=blend(json.loads(base.read_text(encoding='utf-8-sig')),json.loads(ref.read_text(encoding='utf-8-sig')),
                 a.weight,a.mask,a.base_range,a.ref_range,a.fade)
    result['mix_report']['inputs']=[{'name':x.name,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in (base,ref)]
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,allow_nan=False)
    print(json.dumps(result['mix_report'],ensure_ascii=False))

if __name__=='__main__': main()
