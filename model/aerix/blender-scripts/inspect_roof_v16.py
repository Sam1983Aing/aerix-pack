import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v16.blend'));ob=bpy.data.objects['BODY_SHELL_TOP'];me=ob.data;count=ob['top_surface_vertices'];nf=ob['top_surface_faces']
bad=[p for p in me.polygons if all(i<count for i in p.vertices) and p.normal.z<-.000001]
print('TOP_ALL',len(bad),'FIRST',sum(p.normal.z<-.000001 for p in list(me.polygons)[:nf]),'RANGE',nf,len(me.polygons))
for p in bad[:12]:print('BAD',p.index,list(p.vertices),list(p.normal),[list(me.vertices[i].co) for i in p.vertices])
for p in list(me.polygons)[:nf]:
 if p.normal.z<-.000001:print('FIRST_NEG',p.index,list(p.vertices));break
