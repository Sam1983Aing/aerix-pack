import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];out=R/'renders/exterior-v19';out.mkdir(exist_ok=True)
for version in [13,18]:
 bpy.ops.wm.open_mainfile(filepath=str(R/f'blender/aerix-exterior-v{version}.blend'));o=bpy.data.objects['BODY_CRADLE'].evaluated_get(bpy.context.evaluated_depsgraph_get());p=Vector((0,.1215,-.1));hits=[]
 for i in range(8):
  hit,loc,n,fi=o.ray_cast(p,Vector((0,0,1)))
  if not hit:break
  hits.append((tuple(loc),tuple(n)));p=loc+Vector((0,0,.00001))
 print('CENTRAL_HITS',version,hits,flush=True)
me=bpy.data.objects['BODY_CRADLE'].data
walls=[p for p in me.polygons if abs(p.center.x)<.0083 and abs(p.center.y-.1215)<.0038 and p.center.z<.0751 and abs(p.normal.z)<.2]
print('PORT_WALLS',len(walls),[(p.index,tuple(p.center),tuple(p.normal)) for p in walls[:5]],flush=True)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[p.index] for p in walls],context='FACES');boundary=[e for e in bm.edges if e.is_boundary];seen=set();loops=[]
for edge in boundary:
 if edge in seen:continue
 todo=[edge];group=[]
 while todo:
  e=todo.pop()
  if e in seen:continue
  seen.add(e);group.append(e);todo.extend(ee for v in e.verts for ee in v.link_edges if ee.is_boundary)
 vertices={v for e in group for v in e.verts};loops.append({'edges':len(group),'bounds':[[min(v.co[i] for v in vertices),max(v.co[i] for v in vertices)] for i in range(3)]})
print('REPAIR_BOUNDARIES',loops,flush=True);bm.free()
