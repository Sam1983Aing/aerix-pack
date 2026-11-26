"""Compare the saved visible triangle soups to the approved blend independently."""
from pathlib import Path
from collections import Counter
import sys,json,hashlib
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
revision=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert revision in ('v15','v16','v17','v18')
interior_collection='V15 | Interior blockout' if revision=='v15' else revision.upper()+' | Interior'
root=Path(__file__).resolve().parents[1]
names=['Shell.roof_cover','Shell.middle_frame','Shell.belly_cover','Shell.battery_door']
def data(objects,revision):
    result={}
    for obj in objects:
        if obj.type!='MESH':continue
        name='Shell.moulded_fuselage' if obj.name in names else obj.name
        m=obj.data;m.calc_loop_triangles()
        verts=[tuple(obj.matrix_world@v.co) for v in m.vertices]
        srcmats=[s.name for s in m.materials]
        out=result.setdefault(name,Counter())
        for t in m.loop_triangles:
            material=srcmats[t.material_index]
            if revision and material in ('RILL | inner moulding','RILL | carrier polymer'):continue
            pts=tuple(sorted(verts[i] for i in t.vertices))
            out[(material,pts)]+=1
    return result
bpy.context.window.scene=bpy.data.scenes[revision.upper()+' · Assembled'];bpy.context.scene.frame_set(1)
current=data(bpy.data.collections[revision.upper()+' | Aircraft'].objects,True)
base_file=root/'blender/drone-v14c.blend'
bpy.ops.wm.open_mainfile(filepath=str(base_file));bpy.context.scene.frame_set(1)
base=data(bpy.data.collections['V14c | Aircraft'].objects,False)
assert current.keys()==base.keys()
def residual(source,other):
    if not source:return 0.
    vertices=[];faces=[]
    for mat,t in other:
        i=len(vertices);vertices.extend(t);faces.append((i,i+1,i+2))
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    largest=0.
    for mat,t in source:
        a,b,c=map(Vector,t)
        for i in range(9):
            for j in range(9-i):
                p=a+(b-a)*i/8+(c-a)*j/8
                largest=max(largest,tree.find_nearest(p)[3])
    return largest*1000
rows={}
for name,old in base.items():
    new=current[name];a=old-new;b=new-old
    val=max(residual(a,new),residual(b,old))
    rows[name]={'approved_triangles':sum(old.values()),'exact_triangle_and_material_matches':sum((old&new).values()),
                'different_old_new':[sum(a.values()),sum(b.values())],'residual_mm':round(val,8)}
    if a or b:print(name,rows[name])
    assert val<=.05,(name,val)
report={'approved_sha256':hashlib.sha256(base_file.read_bytes()).hexdigest(),'objects_compared':len(rows),
        'approved_surface_triangles':sum(r['approved_triangles'] for r in rows.values()),
        'exact_matches':sum(r['exact_triangle_and_material_matches'] for r in rows.values()),
        'max_residual_mm':max(r['residual_mm'] for r in rows.values()),'by_mesh':rows}
(root/f'measurements/{revision}-exterior.json').write_text(json.dumps(report,indent=2)+'\n')
print('EXTERIOR',report['approved_surface_triangles'],report['exact_matches'],report['max_residual_mm'])

