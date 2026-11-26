import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'));me=bpy.data.objects['BODY_CRADLE'].data
print('ATTRIBUTES',[(a.name,a.domain,a.data_type) for a in me.attributes],flush=True)
old=[n.vector.copy() for n in me.corner_normals]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'));me=bpy.data.objects['BODY_CRADLE'].data
dif=[]
for p in me.polygons:
 if p.center.z<.061:continue
 for li in p.loop_indices:
  err=(old[li]-me.corner_normals[li].vector).length
  if err>.0002:dif.append((err,tuple(p.center),tuple(me.vertices[me.loops[li].vertex_index].co)))
print('UPPER_DIFF',sorted(dif,reverse=True)[:12],len(dif),flush=True)
for name in ['BELLY_VENT_TUNNEL_1']:
 me=bpy.data.objects[name].data
 for p in me.polygons:
  for li in p.loop_indices:
   if me.corner_normals[li].vector.length<.99:print('BAD_LOOP',p.index,tuple(p.center),tuple(p.normal),p.area,tuple(me.corner_normals[li].vector),flush=True)
