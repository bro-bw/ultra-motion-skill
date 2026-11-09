"""Dependency-free pose validation, gap filling, smoothing and contact detection."""
import math

JOINTS = ('left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
          'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
          'left_knee', 'right_knee', 'left_ankle', 'right_ankle')

def add(a, b): return tuple(x+y for x, y in zip(a, b))
def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def length(a): return math.sqrt(sum(x*x for x in a))
def mix(a, b, t): return add(mul(a, 1-t), mul(b, t))

def prepare(data, smoothing=0.65, min_confidence=0.5, max_gap_seconds=0.5):
    if data.get('schema') != 'ums.pose.v1' or data.get('coordinates') != 'x_right_y_back_z_up_m':
        raise ValueError('Unsupported schema/coordinates; use the bundled video extractor.')
    fps = data.get('fps')
    if not isinstance(fps, (int, float)) or not math.isfinite(fps) or not 1 <= fps <= 240:
        raise ValueError('fps must be finite and between 1 and 240')
    raw = data.get('frames', [])
    if not 2 <= len(raw) <= 36000:
        raise ValueError('Expected 2..36000 frames (split long videos).')
    if not 0 <= smoothing <= 1:
        raise ValueError('Smoothing must be 0..1')
    frames = [{} for _ in raw]
    repaired = 0
    max_gap = max(1, int(fps * max_gap_seconds))
    for joint in JOINTS:
        values = []
        for frame in raw:
            p = frame.get('joints', {}).get(joint)
            if p is None:
                values.append(None)
                continue
            if not isinstance(p, list) or len(p) != 4 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in p):
                raise ValueError('Invalid [x,y,z,confidence] for ' + joint)
            if not 0 <= p[3] <= 1 or any(abs(x) > 100 for x in p[:3]):
                raise ValueError('Out-of-range landmark: ' + joint)
            values.append(tuple(p[:3]) if p[3] >= min_confidence else None)
        valid = [i for i, p in enumerate(values) if p is not None]
        if not valid:
            raise ValueError('No confident landmarks for ' + joint)
        i = 0
        while i < len(values):
            if values[i] is not None:
                i += 1
                continue
            start = i
            while i < len(values) and values[i] is None: i += 1
            if i-start > max_gap:
                raise ValueError('Tracking gap exceeds %.2fs: %s at frame %d' % (max_gap_seconds, joint, start+1))
            a = values[start-1] if start else values[i]
            b = values[i] if i < len(values) else a
            for k in range(start, i):
                values[k] = mix(a, b, (k-start+1)/(i-start+1))
                repaired += 1
        # Symmetric finite filter: no causal lag, 65% is blend strength.
        radius = max(1, round(fps * 0.067))
        for i, p in enumerate(values):
            window = values[max(0, i-radius):min(len(values), i+radius+1)]
            avg = tuple(sum(v[d] for v in window)/len(window) for d in range(3))
            frames[i][joint] = mix(p, avg, smoothing)
    return frames, fps, repaired

def contacts(frames, fps):
    """Hip-relative heuristic; not world-space camera motion recovery."""
    result = {}
    for side in ('left', 'right'):
        pts = [f[side+'_ankle'] for f in frames]
        floor = sorted(p[2] for p in pts)[max(0, int(len(pts)*0.1)-1)]
        flags = []
        for i, p in enumerate(pts):
            speed = length(sub(pts[min(i+1,len(pts)-1)], pts[max(0,i-1)]))*fps/(2 if 0 < i < len(pts)-1 else 1)
            flags.append(p[2] < floor + 0.055 and speed < 0.18)
        # Remove one-frame contacts.
        result[side] = [v and ((i > 0 and flags[i-1]) or (i+1 < len(flags) and flags[i+1])) for i,v in enumerate(flags)]
    return result

def demo_data(n=90):
    frames = []
    for i in range(n):
        t = i/(n-1)
        joints = {}
        for side, sign in [('left', 1), ('right', -1)]:
            wave = math.sin(t*math.pi*2)*0.12 if side == 'left' else 0
            points = {'shoulder':(.2*sign,0,.5),'elbow':(.45*sign,0,.35+wave),
                      'wrist':(.65*sign,-.08,.3+wave*2),'hip':(.1*sign,0,0),
                      'knee':(.1*sign,-.04,-.43),'ankle':(.1*sign,0,-.85)}
            for name,p in points.items(): joints[side+'_'+name] = list(p)+[1.0]
        frames.append({'joints':joints})
    return {'schema':'ums.pose.v1','coordinates':'x_right_y_back_z_up_m','fps':30,'frames':frames,
            'source':'Synthetic standing arm gesture; NOT inferred from video'}
