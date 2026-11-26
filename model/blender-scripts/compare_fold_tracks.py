"""Compare sampled rotations for every keyed node in the two GLB deliveries."""
import struct
import sys
import json
from math import sqrt,asin,degrees
from pathlib import Path

root=Path(__file__).resolve().parents[1]
def curves(path):
    raw=path.read_bytes()
    length=struct.unpack_from('<I',raw,12)[0]
    data=json.loads(raw[20:20+length])
    start=28+length
    def samples(index):
        acc=data['accessors'][index]
        view=data['bufferViews'][acc['bufferView']]
        assert acc['componentType']==5126 and 'byteStride' not in view
        offset=start+view.get('byteOffset',0)+acc.get('byteOffset',0)
        width={'SCALAR':1,'VEC4':4}[acc['type']]
        return [struct.unpack_from(f'<{width}f',raw,offset+4*width*i) for i in range(acc['count'])]
    animation,=data['animations']
    assert animation['name']=='Fold'
    tracks={}
    for channel in animation['channels']:
        target=channel['target']
        sampler=animation['samplers'][channel['sampler']]
        assert target['path']=='rotation' and sampler.get('interpolation','LINEAR')=='LINEAR'
        name=data['nodes'][target['node']]['name']
        tracks[name]=(samples(sampler['input']),samples(sampler['output']))
    return tracks

baseline=sys.argv[2] if len(sys.argv)>2 else 'v01'
revision=sys.argv[1] if len(sys.argv)>1 else 'v02'
old,new=(curves(root/f'exports/drone-{v}.glb') for v in (baseline,revision))
assert old.keys()==new.keys()
maximum=0
for name,(times,values) in old.items():
    t2,q2=new[name]
    assert times==t2
    for a,b in zip(values,q2):
        an,bn=sqrt(sum(x*x for x in a)),sqrt(sum(x*x for x in b))
        chord=min(sqrt(sum((x/an-sign*y/bn)**2 for x,y in zip(a,b))) for sign in (-1,1))
        maximum=max(maximum,degrees(4*asin(min(1,chord/2))))
print(f'{len(old)} matching track targets and time arrays. Maximum rotational difference {maximum:.9f} degrees.')
assert maximum<.001
