"""Seat the front chassis under the titanium lip and finish the narrow metal edge."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v22';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v21.blend'))
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
roof=bpy.data.objects['BODY_SHELL_TOP'];rm=roof.data;boundary=list(roof['top_boundary_edges']);segments=[]
for ia,ib in zip(boundary[::2],boundary[1::2]):
 a=rm.vertices[ia].co.copy();b=rm.vertices[ib].co.copy()
 if min(a.y,b.y)>-.118:continue
 d=Vector((b.x-a.x,b.y-a.y));n=Vector((d.y,-d.x)).normalized();mid=(a+b)*.5
 if n.dot(Vector((mid.x,mid.y)))<0:n.negate()
 segments.append((a,b,d,n))
def nearest(p):
 best=None
 for a,b,d,n in segments:
  t=max(0,min(1,Vector((p.x-a.x,p.y-a.y)).dot(d)/d.length_squared));q=a.lerp(b,t)
  dist=(Vector((p.x-q.x,p.y-q.y))).length_squared
  if best is None or dist<best[0]:best=(dist,q,n)
 return best
ob=bpy.data.objects['BODY_CRADLE'];me=ob.data;old_normals=[n.vector.copy() for n in me.corner_normals];changed={};maximum=0
for v in me.vertices:
 p=v.co
 if p.y>=-.124 or p.z<=.088:continue
 dist,q,n=nearest(p)
 # Complement V20's side inset; the setback continues around the curved nose.
 w=(1-smooth(-.136,-.124,p.y))*smooth(q.z-.0052,q.z-.0018,p.z)
 w*=1-smooth(.004,.009,math.sqrt(dist))
 if w<=0:continue
 delta=Vector((-n.x*.00050*w,-n.y*.00050*w,0));v.co+=delta;changed[v.index]=w;maximum=max(maximum,delta.length)
me.update()
if me.attributes.get('custom_normal'):me.attributes.remove(me.attributes['custom_normal'])
me.update();auto=[n.vector.copy() for n in me.corner_normals];normals=[]
for li,loop in enumerate(me.loops):
 p=me.vertices[loop.vertex_index].co;w=(1-smooth(-.132,-.120,p.y))*smooth(.0875,.091,p.z)
 normals.append(old_normals[li].lerp(auto[li],w).normalized() if w else old_normals[li])
me.normals_split_custom_set(normals);me.update()
# Narrow vertical metal strips cannot resolve the broad shell's texture bake at
# macro scale. Give the visible front return an even satin machined finish.
finish=rm.materials[0].copy();finish.name='V22 satin titanium front edge';p=finish.node_tree.nodes.get('Principled BSDF')
for socket in ['Normal','Roughness']:
 for link in list(p.inputs[socket].links):finish.node_tree.links.remove(link)
p.inputs['Roughness'].default_value=.42
rm.materials.append(finish);slot=len(rm.materials)-1;edge_faces=[]
for face in rm.polygons:
 if face.index<int(roof['top_surface_faces'])*2:continue
 if max(rm.vertices[i].co.y for i in face.vertices)<-.1235:
  face.material_index=slot;face.use_smooth=True;edge_faces.append(face.index)
rm.update()
# Match the visor's shading normals to its original bowed surface. The radial
# fan's averaged normals created a small cross-shaped highlight at its center.
visor=bpy.data.objects['FRONT_VISOR'];vm=visor.data;vn=[n.vector.copy() for n in vm.corner_normals];visor_faces=0
def nose_y(x):return -.1355-.016*math.sqrt(max(.000001,1-(x/.0672)**2))
for face in vm.polygons:
 if all(abs(vm.vertices[i].co.y-nose_y(vm.vertices[i].co.x)-.0030)<.00015 for i in face.vertices) and face.normal.y<-.65:
  face.use_smooth=True;visor_faces+=1
  for li in face.loop_indices:
   x=vm.vertices[vm.loops[li].vertex_index].co.x;deriv=.016*x/(.0672**2*math.sqrt(max(.000001,1-(x/.0672)**2)))
   vn[li]=Vector((deriv,-1,0)).normalized()
vm.normals_split_custom_set(vn);vm.update()
visor['V22 front highlight']='Analytical normals on bowed front surface; lens apertures and all geometry preserved'
ob['V22 front lip clearance']='0.50 mm inward normal offset, blended into V20 side setback; stereo optics unchanged'
roof['V22 front edge finish']='Satin material and continuous side-wall normals; roof silhouette unchanged'
s=bpy.context.scene
for name,loc,target,scale in [
 ('front_finish',(0,-.48,.133),(0,-.147,.086),.163),
 ('front_left_finish',(-.23,-.42,.16),(-.026,-.137,.091),.17),
 ('front_right_finish',(.23,-.42,.16),(.026,-.137,.091),.17)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.frame_set(1);s.camera=bpy.data.objects['CAM_front_finish']
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'))
(OUT/'build-report.json').write_text(json.dumps({'inset_chassis_vertices':len(changed),'maximum_inset_mm':maximum*1000,'front_edge_faces':len(edge_faces),'visor_faces_with_surface_normals':visor_faces,'other_geometry_edited':False},indent=2))
print('V22_FRONT_FINISH_COMPLETE',flush=True)
