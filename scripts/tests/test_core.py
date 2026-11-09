import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('core',Path(__file__).parents[1]/'ultra_motion_studio'/'core.py')
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)

class CoreTests(unittest.TestCase):
    def test_default_and_stationary_contacts(self):
        frames,fps,repaired=core.prepare(core.demo_data())
        self.assertEqual((len(frames),fps,repaired),(90,30,0))
        self.assertTrue(all(core.contacts(frames,fps)['left']))
    def test_short_gap_interpolates(self):
        d=core.demo_data()
        del d['frames'][8]['joints']['left_wrist']
        frames,_,repaired=core.prepare(d,0)
        self.assertEqual(repaired,1)
        self.assertEqual(frames[8]['left_wrist'],core.mix(frames[7]['left_wrist'],frames[9]['left_wrist'],.5))
    def test_long_gap_rejected(self):
        d=core.demo_data()
        for f in d['frames'][10:30]: f['joints']['left_wrist'][3]=0
        with self.assertRaisesRegex(ValueError,'Tracking gap'): core.prepare(d)
    def test_nonfinite_rejected(self):
        d=core.demo_data(); d['frames'][0]['joints']['left_wrist'][0]=float('nan')
        with self.assertRaises(ValueError): core.prepare(d)
    def test_unknown_coordinate_system_rejected(self):
        d=core.demo_data(); d['coordinates']='screen'
        with self.assertRaises(ValueError): core.prepare(d)
    def test_smoothing_reduces_jitter(self):
        d=core.demo_data()
        for i,f in enumerate(d['frames']): f['joints']['left_wrist'][1]=.1*(-1)**i
        f,_,_=core.prepare(d)
        self.assertLess(sum(abs(x['left_wrist'][1]) for x in f),len(f)*.06)
    def test_no_smoothing_is_identity(self):
        d=core.demo_data(); f,_,_=core.prepare(d,0)
        self.assertEqual(tuple(d['frames'][3]['joints']['left_wrist'][:3]),f[3]['left_wrist'])
    def test_missing_entire_joint_rejected(self):
        d=core.demo_data()
        for f in d['frames']: del f['joints']['left_ankle']
        with self.assertRaises(ValueError): core.prepare(d)
    def test_bad_fps_rejected(self):
        for fps in (0,241,float('nan')):
            d=core.demo_data(); d['fps']=fps
            with self.assertRaises(ValueError): core.prepare(d)

if __name__=='__main__': unittest.main(verbosity=2)
