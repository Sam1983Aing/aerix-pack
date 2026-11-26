"""Remove the duplicate underside connector and weld the original curved shell closed."""
import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v19';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v13.blend'))
ev=bpy.data.objects['BODY_CRADLE'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
vs=[v.co.copy() for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];ns=[[me.corner_normals[i].vector.copy() for i in t.loops] for t in me.loop_triangles];tree=BVHTree.FromPolygons(vs,ts,all_triangles=True);ev.to_mesh_clear()
def skin(x,y,inner=False):
 p,n,i,d=tree.ray_cast(Vector((x,y,.059 if inner else -.1)),Vector((0,0,-1 if inner else 1)),1)
 if p is None:raise ValueError(('Missing source shell',x,y,inner))
 a,b,c=ts[i];return p.z,barycentric_transform(p,vs[a],vs[b],vs[c],*ns[i]).normalized()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'));s=bpy.context.scene
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith('BELLY_PORT_'):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
assert len(removed)==26,len(removed)
o=bpy.data.objects['BODY_CRADLE'];me=o.data
key=lambda p:tuple(round(c,10) for c in p)
facekey=lambda coords:tuple(sorted(key(p) for p in coords))
saved={facekey([me.vertices[i].co for i in p.vertices]):{key(me.vertices[me.loops[li].vertex_index].co):me.corner_normals[li].vector.copy() for li in p.loop_indices} for p in me.polygons}
sharp={tuple(sorted(key(me.vertices[i].co) for i in e.vertices)):e.use_edge_sharp for e in me.edges}
walls=[p.index for p in me.polygons if abs(p.center.x)<.0083 and abs(p.center.y-.1215)<.0038 and p.center.z<.0751 and abs(p.normal.z)<.2]
assert len(walls)==52,len(walls)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in walls],context='FACES')
boundary=[e for e in bm.edges if e.is_boundary];seen=set();loops=[]
for edge in boundary:
 if edge in seen:continue
 start=edge.verts[0];current=start;prev=None;loop=[]
 while True:
  loop.append(current);edges=[e for e in current.link_edges if e.is_boundary and e!=prev]
  e=next((e for e in edges if e not in seen),None)
  if e is None:raise ValueError('Broken repair boundary')
  seen.add(e);current=e.other_vert(current);prev=e
  if current==start:break
 loops.append(loop)
assert len(loops)==2 and all(len(v)==62 for v in loops),[len(v) for v in loops]
loops.sort(key=lambda v:sum(p.co.z for p in v)/len(v));boundary_keys={key(v.co) for loop in loops for v in loop};new_faces=[]
for inner,loop in enumerate(loops):
 area=sum(a.co.x*b.co.y-b.co.x*a.co.y for a,b in zip(loop,loop[1:]+loop[:1]))
 if (area>0)!=bool(inner):loop.reverse()
 n=len(loop);cx=sum(v.co.x for v in loop)/n;cy=sum(v.co.y for v in loop)/n;center=bm.verts.new((cx,cy,skin(cx,cy,inner)[0]));rings=[]
 for k in range(1,12):
  t=k/12;rings.append([])
  for v in loop:
   x=cx+(v.co.x-cx)*t;y=cy+(v.co.y-cy)*t;rings[-1].append(bm.verts.new((x,y,skin(x,y,inner)[0])))
 rings.append(loop)
 for j in range(n):new_faces.append(bm.faces.new((center,rings[0][j],rings[0][(j+1)%n])))
 for a,b in zip(rings,rings[1:]):
  for j in range(n):q=(j+1)%n;new_faces.append(bm.faces.new((a[j],b[j],b[q],a[q])))
for p in new_faces:p.smooth=True;p.material_index=0
bm.normal_update();assert all(e.is_manifold for e in bm.edges)
bm.to_mesh(me);bm.free();me.update()
normals=[]
for p in me.polygons:
 old=saved.get(facekey([me.vertices[i].co for i in p.vertices]))
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co;k=key(v)
  if old is not None and k not in boundary_keys:normal=old[k]
  else:normal=skin(v.x,v.y,p.normal.z>0)[1]
  normals.append(normal)
for e in me.edges:
 k=tuple(sorted(key(me.vertices[i].co) for i in e.vertices))
 if k in sharp:e.use_edge_sharp=sharp[k]
# BMesh changes corner normal coordinate bases when it rewrites edge indices.
# Re-encode the saved world-space vectors in those new bases; packed values cannot
# be copied between meshes with different topology.
me.normals_split_custom_set(normals)
me.update();o['charging_layout']='V19: single rear connector; underside aperture welded closed using original inner and outer shell curvature'
# A rear/underside view exposes both the retained connector and the continuous belly.
data=bpy.data.cameras.new('CAM_rear_underside');data.type='ORTHO';data.ortho_scale=.18;cam=bpy.data.objects.new('CAM_rear_underside',data);s.collection.objects.link(cam);cam.location=(.023,.34,-.18);cam.rotation_euler=(Vector((0,.111,.061))-cam.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'))
(OUT/'build-summary.json').write_text(json.dumps({'removed_objects':removed,'deleted_aperture_walls':len(walls),'new_shell_faces':len(new_faces),'welded_boundary_vertices':len(boundary_keys)},indent=2))
if '--preview' in sys.argv:
 s.cycles.samples=24;s.render.resolution_x=1300;s.render.resolution_y=1100;s.render.resolution_percentage=80;bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False;s.camera=cam;s.render.filepath=str(OUT/'rear-underside-preview.png');bpy.ops.render.render(write_still=True)
print('V19_BUILD_COMPLETE',flush=True)
