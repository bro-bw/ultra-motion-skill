"""Run OUTSIDE Blender: MediaPipe Tasks CPU -> ums.pose.v1 JSON."""
import argparse
import json
import math
import os
from pathlib import Path

INDEX={'left_shoulder':11,'right_shoulder':12,'left_elbow':13,'right_elbow':14,
       'left_wrist':15,'right_wrist':16,'left_hip':23,'right_hip':24,
       'left_knee':25,'right_knee':26,'left_ankle':27,'right_ankle':28}

def extract(video, model, output, fps_override=None):
    import cv2
    import mediapipe as mp
    if not Path(video).is_file(): raise ValueError('Video file does not exist')
    if not Path(model).is_file(): raise ValueError('Download pose_landmarker_full.task first (see README)')
    if Path(output).exists(): raise ValueError('Output already exists; choose a new filename')
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened(): raise ValueError('Cannot decode video')
    fps=fps_override or cap.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or not 1<=fps<=240:
        cap.release(); raise ValueError('Invalid video FPS; use --fps')
    options=mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,num_poses=1,
        min_pose_detection_confidence=.5,min_tracking_confidence=.5)
    frames=[]; missing=0
    try:
        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
            while True:
                ok,bgr=cap.read()
                if not ok: break
                if len(frames)>=36000: raise ValueError('Video exceeds 36000 frames; split it first')
                image=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
                result=detector.detect_for_video(image,round(len(frames)*1000/fps))
                joints={}
                if result.pose_world_landmarks:
                    for name,index in INDEX.items():
                        p=result.pose_world_landmarks[0][index]
                        joints[name]=[p.x,-p.z,-p.y,min(p.visibility,p.presence)]
                else: missing+=1
                frames.append({'joints':joints})
                if len(frames)%100==0: print('Decoded',len(frames),'frames',flush=True)
    finally: cap.release()
    if len(frames)<2 or missing==len(frames): raise ValueError('No usable person detected')
    data={'schema':'ums.pose.v1','coordinates':'x_right_y_back_z_up_m','fps':fps,
          'source':Path(video).name,'estimator':'MediaPipe PoseLandmarker world landmarks',
          'root_motion':'hip_relative_no_global_translation','missing_frames':missing,'frames':frames}
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation prevents accidental replacement of an existing pose file.
    with out.open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,allow_nan=False)
    print('Saved',out,'frames:',len(frames),'missing:',missing)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',required=True); p.add_argument('--model',required=True)
    p.add_argument('--output',required=True); p.add_argument('--fps',type=float)
    a=p.parse_args()
    try: extract(a.video,a.model,a.output,a.fps)
    except Exception as exc: p.exit(1,'Extraction failed: '+str(exc)+'\n')
