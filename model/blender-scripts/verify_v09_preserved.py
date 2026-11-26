"""Compare the rig and previously approved surfaces in successive viewer exports."""
import json
from pathlib import Path
import struct
import sys
import numpy as np
root=Path(__file__).resolve().parents[1]


class Aircraft:
    def __init__(self,v):
        raw=(root/f'exports/drone-{v}.glb').read_bytes()
        size=struct.unpack_from('<I',raw,12)[0]
        self.data=json.loads(raw[20:20+size])
        self.buffer=raw[28+size:]
        self.nodes={('Drone' if n['name'].lower()=='drone.'+v else n['name']):n for n in self.data['nodes']}
    def attribute(self,k):
        a=self.data['accessors'][k]
        view=self.data['bufferViews'][a['bufferView']]
        size={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1}[a['type']]
        dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        return np.frombuffer(self.buffer,dtype,count=a['count']*size,offset=view.get('byteOffset',0)+a.get('byteOffset',0))
    def mesh(self,n): return self.data['meshes'][n['mesh']]['primitives']


revision=sys.argv[1] if len(sys.argv)>1 else 'v09'
prior,changed={'v09':('v08','Leg.'),'v10':('v09','Camera.'),'v12':('v11','Shell.moulded_fuselage'),
               'v14c':('v14b',('Shell.moulded_fuselage',)), 'v14b':('v14a',('Shell.moulded_fuselage',)), 'v14a':('v14',('Shell.moulded_fuselage','Camera.block','Camera.lens_barrel','Camera.face_trim')),'v14':('v13',()),'v13':('v12',('Shell.moulded_fuselage','Gimbal.pitch_cover.','Arm.F','Hinge.socket.F','Hinge.pin.F'))}[revision]
old,new=Aircraft(prior),Aircraft(revision)
removed={'Hinge.bracket.FL','Hinge.bracket.FR'} if revision=='v13' else set()
assert old.nodes.keys()-removed==new.nodes.keys()
surfaces=0
for name,a in old.nodes.items():
    if name in removed: continue
    b=new.nodes[name]
    # glTF permits the identity transform to be omitted. Blender may emit
    # an explicit near-unit scale after decomposing the same joint matrix.
    for key,default in [('translation',(0,0,0)),('rotation',(0,0,0,1)),('scale',(1,1,1)),('matrix',np.eye(4).flatten())]:
        tolerance=3.e-6 if revision in ('v14','v14a','v14b','v14c') and key=='scale' else 1.e-7
        assert np.allclose(a.get(key,default),b.get(key,default),rtol=0,atol=tolerance),(name,key)
    def children(src,n):
        return {src.data['nodes'][j]['name'] for j in n.get('children',[])}
    assert children(old,a)-removed==children(new,b),name
    if 'mesh' not in a or name.startswith(changed): continue
    m,n=old.mesh(a),new.mesh(b)
    assert len(m)==len(n),name
    for x,y in zip(m,n):
        assert x['attributes'].keys()==y['attributes'].keys()
        for k in x['attributes']:
            assert np.allclose(old.attribute(x['attributes'][k]),new.attribute(y['attributes'][k]),rtol=0,atol=1e-6),(name,k)
        assert np.array_equal(old.attribute(x['indices']),new.attribute(y['indices'])),name
    surfaces+=1
print(f'{surfaces} meshes outside {changed} match {prior.upper()}. Local transforms and parenting match for all {len(new.nodes)} retained nodes.')

if revision in ('v14','v14a','v14b','v14c'):
    for field in ('materials','textures','samplers'):
        assert old.data[field]==new.data[field],field
    for name,source in old.nodes.items():
        if 'mesh' in source:
            assert [p['material'] for p in old.mesh(source)]==[p['material'] for p in new.mesh(new.nodes[name])],name
    def images(asset):
        result={}
        for im in asset.data['images']:
            view=asset.data['bufferViews'][im['bufferView']]
            start=view.get('byteOffset',0)
            result[im['name']]=asset.buffer[start:start+view['byteLength']]
        return result
    assert images(old)==images(new)
    print(f"{len(new.data['materials'])} materials, their primitive assignments, and all {len(new.data['images'])} embedded texture images match.")
