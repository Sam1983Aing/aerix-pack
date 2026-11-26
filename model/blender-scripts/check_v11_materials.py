"""Verify the PBR payload and compare V10/V11 geometry independently of UV splits."""
import io
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image

root=Path(__file__).resolve().parents[1]


def read_glb(version):
    raw=(root/f'exports/drone-{version}.glb').read_bytes()
    length=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+length]),raw[28+length:]


def array(asset,idx):
    spec,data=asset
    a=spec['accessors'][idx]
    view=spec['bufferViews'][a['bufferView']]
    dtype={5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    assert not view.get('byteStride')
    return np.frombuffer(data,dtype=dtype,count=width*a['count'],offset=view.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,width))


def triangle_attributes(asset,primitive):
    indices=array(asset,primitive['indices']).reshape(-1)
    parts=[array(asset,primitive['attributes'][key])[indices] for key in ('POSITION','NORMAL')]
    return np.hstack(parts).reshape(-1,3,6)


a,b=read_glb('v10'),read_glb('v11')
old,new=a[0],b[0]
nodes=lambda doc:{n['name'].replace('Drone.V10','Drone').replace('Drone.V11','Drone'):n for n in doc['nodes']}
left,right=nodes(old),nodes(new)
assert left.keys()==right.keys()
meshes=triangles=0
for name,n in left.items():
    m=right[name]
    for field in ('scale','rotation','translation','matrix'):
        assert np.allclose(n.get(field,[]),m.get(field,[]),rtol=0,atol=1e-7),(name,field)
    assert [old['nodes'][i]['name'] for i in n.get('children',[])]==[new['nodes'][i]['name'] for i in m.get('children',[])]
    if 'mesh' not in n: continue
    old_prims=old['meshes'][n['mesh']]['primitives']
    new_prims=new['meshes'][m['mesh']]['primitives']
    assert len(old_prims)==len(new_prims)
    for previous,updated in zip(old_prims,new_prims):
        t1,t2=triangle_attributes(a,previous),triangle_attributes(b,updated)
        assert t1.shape==t2.shape and np.allclose(t1,t2,rtol=0,atol=1e-6),name
        triangles+=len(t2)
    meshes+=1

data_maps={}
for image in new['images']:
    view=new['bufferViews'][image['bufferView']]
    start=view['byteOffset']
    with Image.open(io.BytesIO(b[1][start:start+view['byteLength']])) as im:
        assert im.size==(512,512) and im.mode in ('RGB','RGBA')
        arr=np.array(im)[:,:,:3]
        if image['name'].endswith('-mr'):
            assert arr[:,:,1].std()>1.2
            assert np.all(arr[:,:,2]==(255 if image['name'].startswith('turned') else 0))
        else:
            assert arr[:,:,2].mean()>245 and arr[:,:,0].std()>.5
    data_maps[image['name']]=view['byteLength']
assert len(data_maps)==6
finish={m['name']:m for m in new['materials']}
assert 'KHR_materials_iridescence' in finish['Basalt | front optical crown']['extensions']
for n in ('front','inner'):
    assert finish[f'Basalt | {n} optical crown']['extensions']['KHR_materials_transmission']['transmissionFactor']==1
mapped_count=0
for mesh in new['meshes']:
    for p in mesh['primitives']:
        m=new['materials'][p['material']]
        if 'normalTexture' in m:
            assert 'TEXCOORD_0' in p['attributes'],mesh['name']
            coords=array(b,p['attributes']['TEXCOORD_0'])
            assert np.isfinite(coords).all() and np.ptp(coords)>0
            mapped_count+=1
assert mapped_count>40
report={'meshes_matching_v10':meshes,'triangles_matching_v10':triangles,
        'node_transforms_and_parents_matching_v10':len(left),'embedded_texture_bytes':data_maps,
        'mapped_primitives':mapped_count,'material_count':len(finish),
        'glb_bytes':(root/'exports/drone-v11.glb').stat().st_size}
(root/'measurements/v11-materials.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
