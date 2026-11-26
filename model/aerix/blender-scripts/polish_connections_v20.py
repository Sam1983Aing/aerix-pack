"""Correct shell-lip clearance and restore a fair, bilateral rear shoulder surface."""
import bpy,bmesh,math,ast,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v20';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'))
s=bpy.context.scene;ob=bpy.data.objects['BODY_CRADLE'];me=ob.data
for node in ast.parse((R/'scripts/blender/refine_body_v16.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'interpolator','smooth'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<profile helpers>','exec'))
seam=interpolator([(-.1355,.0940),(-.105,.0922),(-.060,.0920),(.028,.0920),(.077,.0911),(.128,.0900)])
old_normals=[n.vector.copy() for n in me.corner_normals]

oldcoords=[v.co.copy() for v in me.vertices]
me.calc_loop_triangles();surface=BVHTree.FromPolygons(oldcoords,[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
matched=0;largest=0
# The negative-X shoulder is the clean source in the side comparison. Project its
# opposite onto the mirrored surface, with a long blend into the unchanged belly.
# This does not copy loose pieces or alter either independent hinge pivot.
for v in me.vertices:
 p=v.co
 if p.x>.032 and .043<p.y<.119 and .058<p.z<.0908:
  q=Vector((-p.x,p.y,p.z));near,n,idx,d=surface.find_nearest(q)
  if d<.0008:
   near.x*=-1
   blend=smooth(.032,.045,p.x)*smooth(.043,.053,p.y)*(1-smooth(.109,.119,p.y))*smooth(.058,.065,p.z)
   shift=(near-p)*blend;v.co+=shift;largest=max(largest,shift.length);matched+=1
# Seat the upper chassis 0.45 mm inside the existing titanium wall, blending over
# the last 4 mm of the skirt. Previously this clearance oscillated around zero.
inset=0
for v in me.vertices:
 p=v.co
 if abs(p.x)>.028 and -.136<p.y<.130:
  amount=.00045*smooth(seam(p.y)-.0052,seam(p.y)-.0018,p.z)
  # Preserve the curved optical and rear-fascia seating regions.
  amount*=smooth(-.136,-.124,p.y)*(1-smooth(.116,.130,p.y))
  if amount>0:p.x-=math.copysign(amount,p.x);inset+=1
me.update()
# Reproject after the seam deformation as well, so irregular Boolean triangles
# along the socket cannot introduce a different transition on the opposite side.
me.calc_loop_triangles();fitted=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
for v in me.vertices:
 p=v.co
 if p.x>.032 and .043<p.y<.119 and .058<p.z<.0908:
  q=Vector((-p.x,p.y,p.z));near,n,idx,d=fitted.find_nearest(q)
  if d<.0008:
   near.x*=-1;blend=smooth(.032,.043,p.x)*smooth(.043,.053,p.y)*(1-smooth(.109,.119,p.y))*smooth(.058,.0655,p.z)
   v.co=v.co.lerp(near,blend)
me.update()
# Generate smooth normals from the repaired physical surface, retaining hard
# cylindrical socket edges. Preserve all previously approved underside normals.
if me.attributes.get('custom_normal'):me.attributes.remove(me.attributes['custom_normal'])
edge_faces={tuple(sorted(e.vertices)):[] for e in me.edges}
for p in me.polygons:
 for a,b in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):edge_faces[tuple(sorted((a,b)))].append(p)
for e in me.edges:
 if all(me.vertices[i].co.z>.0639 for i in e.vertices):
  faces=edge_faces[tuple(sorted(e.vertices))]
  e.use_edge_sharp=len(faces)!=2 or faces[0].normal.angle(faces[1].normal,0)>=math.radians(42)
for p in me.polygons:
 if p.center.z>.0639:p.use_smooth=True
me.update();auto=[n.vector.copy() for n in me.corner_normals];normals=[];changed=0
for p in me.polygons:
 for li in p.loop_indices:
  pos=me.vertices[me.loops[li].vertex_index].co
  t=smooth(.0620,.0655,pos.z)
  if t>0:
   n=old_normals[li].lerp(auto[li],t).normalized();changed+=1
  else:n=old_normals[li]
  normals.append(n)
me.normals_split_custom_set(normals)
me.update()
# Re-seat the slim rubber parting seals below the titanium lip, inside its edge.
for sign in [-1,1]:
 o=bpy.data.objects['SHELL_SEAM_'+str(sign)]
 for sp in o.data.splines:
  for p in sp.points:p.co.x+=sign*.00005;p.co.z-=.00035
 o.data.bevel_depth=.00013
ob['V20 seam clearance']='0.45 mm inset upper skirt; roof silhouette unchanged'
ob['V20 rear shoulder']='Mirrored surface projection, smoothed socket shoulders and preserved arm pivots'
for name,loc,target,scale in [
 ('seam_left',(-.45,.002,.080),(0,.002,.080),.315),
 ('seam_right',(.45,.002,.080),(0,.002,.080),.315),
 ('joint_left',(-.205,.019,.132),(-.059,.081,.076),.12),
 ('joint_right',(.205,.019,.132),(.059,.081,.076),.12),
 ('joint_low',(-.21,.011,.035),(-.060,.082,.066),.125)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.frame_set(1);s.camera=bpy.data.objects['CAM_hero'];bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'))
(OUT/'build-report.json').write_text(json.dumps({'matched_shoulder_vertices':matched,'max_shoulder_adjustment_m':largest,'inset_skirt_vertices':inset,'restored_upper_normals':changed},indent=2))
if '--preview' in sys.argv:
 s.cycles.samples=24;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=85
 bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
 for name in ['seam_left','seam_right','joint_left','joint_right','joint_low']:
  s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(OUT/(name+'-native.png'));bpy.ops.render.render(write_still=True)
print('V20_CONNECTIONS_COMPLETE',flush=True)
