"""Check that all 70 physical grille openings also reach the backing in the GLB."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import struct
import numpy as np

root=Path(__file__).resolve().parents[1]
blob=(root/'exports/drone-v12.glb').read_bytes()
length=struct.unpack_from('<I',blob,12)[0]
doc=json.loads(blob[20:20+length])
buffer=blob[28+length:]


def read(index,width):
    a=doc['accessors'][index]
    view=doc['bufferViews'][a['bufferView']]
    dtype={5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
    return np.frombuffer(buffer,dtype=dtype,count=width*a['count'],
                         offset=view.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)


node=next(n for n in doc['nodes'] if n['name']=='Shell.moulded_fuselage')
triangles=[]
for primitive in doc['meshes'][node['mesh']]['primitives']:
    vertices=read(primitive['attributes']['POSITION'],3)*1000
    indices=read(primitive['indices'],1).reshape((-1,3))
    triangles.append(vertices[indices])
    if doc['materials'][primitive['material']]['name']=='Basalt | gimbal carbon casting':
        grille=vertices[indices]
edges=Counter()
for triangle in grille:
    for i,p in enumerate(triangle):
        edges[tuple(sorted((tuple(p),tuple(triangle[i-1]))))]+=1
boundary=defaultdict(set)
for (a,b),count in edges.items():
    if count==1:
        boundary[a].add(b)
        boundary[b].add(a)
assert all(len(links)==2 for links in boundary.values())
centers=[]
while boundary:
    first=next(iter(boundary))
    connected=[]
    current=first
    previous=None
    while current in boundary:
        connected.append(current)
        links=boundary.pop(current)
        following=next(v for v in links if v!=previous)
        previous,current=current,following
    assert current==first
    if len(connected)==6:
        centers.append(np.mean(connected,axis=0))
assert len(centers)==70 and sum(p[0]>0 for p in centers)==35

# Intersect rays parallel to X against the entire shell in the YZ projection.
a,b,c=np.concatenate(triangles).astype(np.float64).transpose(1,0,2)
ab,ac=b-a,c-a
def cross(v,w):
    return v[:,1]*w[:,2]-v[:,2]*w[:,1]
det=cross(ab,ac)
valid=np.abs(det)>1e-9
det[~valid]=1
distances=[]
for p in centers:
    u=cross(p-a,ac)/det
    v=cross(ab,p-a)/det
    hit=valid & (u>=-1.e-7) & (v>=-1.e-7) & (u+v<=1.0000001)
    side=np.sign(p[0])
    first_x=np.max(side*(a[:,0]+u*ab[:,0]+v*ac[:,0])[hit])
    distances.append(side*p[0]-first_x)
assert .72<min(distances)<=max(distances)<.95,(min(distances),max(distances))
print(f'{len(centers)} open perforations. Backing lies {min(distances):.3f}–{max(distances):.3f} mm behind the visible grille face.')
