"""Give the fair roof a uniform vertical wall, avoiding inward-offset folds at end corners."""
import bpy,bmesh,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
s=bpy.context.scene;ob=bpy.data.objects['BODY_SHELL_TOP'];old=ob.data
# Run after refine_body_v16; the native edit mesh is a single top surface.
assert len(old.vertices)==36381
coords=[tuple(v.co) for v in old.vertices];faces=[tuple(p.vertices) for p in old.polygons];count=len(coords)
bm=bmesh.new();bm.from_mesh(old);bm.verts.ensure_lookup_table();boundary=[(e.verts[0].index,e.verts[1].index) for e in bm.edges if e.is_boundary];bm.free()
verts=coords+[(x,y,z-.0016) for x,y,z in coords]
allfaces=faces+[tuple(count+i for i in reversed(f)) for f in faces]+[(a,b,b+count,a+count) for a,b in boundary]
me=bpy.data.meshes.new('V16 fair roof with constant vertical wall');me.from_pydata(verts,[],allfaces);me.update();me.materials.append(old.materials[0]);ob.data=me
for mod in list(ob.modifiers):ob.modifiers.remove(mod)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for p in me.polygons:p.use_smooth=p.index<len(faces)*2
border={tuple(sorted(e)) for e in boundary}|{tuple(sorted((a+count,b+count))) for a,b in boundary}
for e in me.edges:e.use_edge_sharp=tuple(sorted(e.vertices)) in border
ob['top_surface_vertices']=count;ob['top_surface_faces']=len(faces);ob['top_boundary_edges']=[i for edge in boundary for i in edge]
s.camera=bpy.data.objects['CAM_hero'];bpy.data.objects['STUDIO_GROUND'].hide_render=False;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
if '--preview' in sys.argv:
 s.cycles.samples=24;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=70
 for name in ['nose_embedded','roof_rear']:
  s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v16'/(name+'-edge-preview.png'));bpy.ops.render.render(write_still=True)
