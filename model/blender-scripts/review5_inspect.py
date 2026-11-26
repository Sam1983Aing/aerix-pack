"""Read the approved aircraft and record closed components and projected outlines."""
from pathlib import Path
import hashlib
import json
import bmesh
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
src = root/'blender/drone-v14c.blend'
assert Path(bpy.data.filepath).resolve()==src
collection = bpy.data.collections['V14c | Aircraft']
bpy.context.scene.frame_set(1)
result = {}
outlines = {}
for obj in collection.objects:
    if obj.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    unseen=set(bm.verts); volumes=[]
    while unseen:
        seed=unseen.pop(); stack=[seed]; faces=set()
        while stack:
            v=stack.pop()
            faces.update(v.link_faces)
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:
                    stack.append(w); unseen.remove(w)
        volumes.append(len(faces))
    result[obj.name]={'connected_surface_components':len(volumes),'open_edges':sum(not e.is_manifold for e in bm.edges),
                      'local_volume_mm3':round(abs(bm.calc_volume(signed=True))*1e9,2),
                      'bounds_mm':[[round(fn(p[k] for p in verts)*1000,3) for k in range(3)] for fn in (min,max)]}
    if obj.name.startswith(('Shell.moulded','Gimbal.','Camera.block','Arm.','Motor.','Leg.')):
        # Sample boundary along the actual longitudinal axis; use the shell for layout registration.
        if obj.name=='Shell.moulded_fuselage':
            rows=[]
            for y in range(-73,65):
                hits=[]
                for e in obj.data.edges:
                    a,b=(verts[k] for k in e.vertices)
                    if min(a.y,b.y)<=y*.001<max(a.y,b.y):
                        p=a.lerp(b,(y*.001-a.y)/(b.y-a.y)); hits.append((1000*p.x,1000*p.z))
                if hits:
                    rows.append([y,*[round(fn(p[k] for p in hits),3) for k in (0,1) for fn in (min,max)]])
            outlines['shell_sections_y_xmin_xmax_zmin_zmax']=rows
    bm.free()
audit={'source':src.name,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
       'aircraft_meshes':len(result),'objects':result,**outlines}
(root/'measurements/review5-approved-exterior.json').write_text(json.dumps(audit,indent=2)+'\n')
print(audit['aircraft_meshes'], result['Shell.moulded_fuselage'], flush=True)
