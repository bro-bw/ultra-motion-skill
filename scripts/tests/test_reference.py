import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
import mix_reference as mix
core=mix.core

class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.a=core.demo_data(60); self.b=core.demo_data(20)
        for f in self.b['frames']:
            f['joints']['left_elbow']=[.4,-.15,.55,1]
            f['joints']['left_wrist']=[.55,-.3,.65,1]
    def test_zero_weight_identity(self):
        out=mix.blend(self.a,self.b,0)
        self.assertEqual(out['frames'],self.a['frames'])
    def test_mask_retains_legs_and_anchors(self):
        out=mix.blend(self.a,self.b,.6,fade=0)
        for a,b in zip(self.a['frames'],out['frames']):
            for j in core.JOINTS:
                if not j.endswith(('elbow','wrist')): self.assertEqual(a['joints'][j],b['joints'][j])
        self.assertNotEqual(out['frames'][30]['joints']['left_wrist'],self.a['frames'][30]['joints']['left_wrist'])
    def test_preserves_base_segment_lengths(self):
        out=mix.blend(self.a,self.b,.8,fade=0)
        for i in (0,29,59):
            for a,b in [('left_shoulder','left_elbow'),('left_elbow','left_wrist')]:
                points=lambda d:core.length(core.sub(d['frames'][i]['joints'][a][:3],d['frames'][i]['joints'][b][:3]))
                self.assertAlmostEqual(points(out),points(self.a),places=8)
    def test_selected_range_and_fade(self):
        out=mix.blend(self.a,self.b,.7,base_range=(10,40),ref_range=(2,15))
        for i in list(range(11))+list(range(40,60)):
            self.assertEqual(out['frames'][i],self.a['frames'][i])
    def test_phase_sampling_and_full_weight(self):
        out=mix.blend(self.a,self.b,1,fade=0)
        direction=lambda d,i:mix.unit(core.sub(d['frames'][i]['joints']['left_wrist'][:3],d['frames'][i]['joints']['left_elbow'][:3]))
        for x,y in zip(direction(out,59),direction(self.b,19)): self.assertAlmostEqual(x,y)
        self.assertEqual(len(out['frames']),60)
        self.assertEqual(out['fps'],self.a['fps'])
    def test_opposite_rejected(self):
        with self.assertRaises(ValueError): mix.direction_mix((1,0,0),(-1,0,0),.5)
    def test_invalid_range_and_weight(self):
        for kwargs in ({'weight':float('nan')},{'base_range':(5,5)},{'mask':'fingers'},{'fade':-1}):
            with self.assertRaises(ValueError): mix.blend(self.a,self.b,**kwargs)

if __name__=='__main__': unittest.main(verbosity=2)
