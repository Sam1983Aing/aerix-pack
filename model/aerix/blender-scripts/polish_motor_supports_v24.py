"""Replace only the scalloped subdivided motor-base caps with even rolled shoulders."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'))
mat=bpy.data.materials.new('V24 smooth satin motor support');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value=(.009,.011,.013,1)
p.inputs['Metallic'].default_value=.16;p.inputs['Roughness'].default_value=.36
reports=[]
for tag in ['FL','FR','RL','RR']:
 o=bpy.data.objects['MOTOR_BASE_'+tag];deps=bpy.context.evaluated_depsgraph_get()
 ev=o.evaluated_get(deps);old=ev.to_mesh()
 cx=-.165 if tag.endswith('L') else .165;cy=-.140 if tag.startswith('F') else .140
 keep=[v.index for v in old.vertices if v.co.z<.08130]
 boundary=[i for i in keep if old.vertices[i].co.z>.08120]
 assert len(boundary)==160
 boundary.sort(key=lambda i:math.atan2(old.vertices[i].co.y-cy,old.vertices[i].co.x-cx))
 remap={i:j for j,i in enumerate(keep)}
 verts=[tuple(old.vertices[i].co) for i in keep];faces=[];normals=[]
 for f in old.polygons:
  if all(i in remap for i in f.vertices):
   faces.append(tuple(remap[i] for i in f.vertices))
   normals.extend(tuple(old.corner_normals[j].vector) for j in f.loop_indices)
 # The lower legs, side-wall coordinates, and their existing normals stay intact.
 n=len(boundary);z0=sum(old.vertices[i].co.z for i in boundary)/n
 rx=max(abs(old.vertices[i].co.x-cx) for i in boundary)
 ry=max(abs(old.vertices[i].co.y-cy) for i in boundary)
 angles=[math.atan2((old.vertices[i].co.y-cy)/ry,(old.vertices[i].co.x-cx)/rx) for i in boundary]
 start_normals=[old.vertices[i].normal.copy() for i in boundary]
 ring=[remap[i] for i in boundary];prev_normals=start_normals
 ztop=.08505;rtop=.01685
 # Cubic tangent roll: match the old gently tapered wall, finish flat under the seal.
 def curve(r,t):
  points=[Vector((r,z0)),Vector((r-.000090,z0+.00150)),Vector((rtop+.00110,ztop)),Vector((rtop,ztop))]
  a,b,c,d=points;u=1-t
  return a*u**3+b*(3*u*u*t)+c*(3*u*t*t)+d*t**3,(b-a)*(3*u*u)+(c-b)*(6*u*t)+(d-c)*(3*t*t)
 for j in range(1,25):
  t=j/24;(xr,z),dx=curve(rx,t);(yr,_),dy=curve(ry,t)
  new=[];ns=[]
  for k,a in enumerate(angles):
   ca=math.cos(a);sa=math.sin(a)
   new.append(len(verts));verts.append((cx+xr*ca,cy+yr*sa,z))
   tangent_angle=Vector((-xr*sa,yr*ca,0));tangent_roll=Vector((dx.x*ca,dy.x*sa,dx.y))
   no=tangent_angle.cross(tangent_roll).normalized()
   if j<4:no=start_normals[k].lerp(no,j/4).normalized()
   ns.append(no)
  for k in range(n):
   k1=(k+1)%n;faces.append((ring[k],ring[k1],new[k1],new[k]))
   normals.extend(tuple(q) for q in [prev_normals[k],prev_normals[k1],ns[k1],ns[k]])
  ring=new;prev_normals=ns
 # A truly planar hidden seating face avoids the n-gon subdivision pole that caused ripples.
 faces.append(tuple(ring));normals.extend([(0,0,1)]*n)
 old_count=len(old.vertices);ev.to_mesh_clear()
 me=bpy.data.meshes.new(o.name+'_even_shoulder');me.from_pydata(verts,[],faces);me.update()
 for f in me.polygons:f.use_smooth=True
 me.materials.append(mat);me.normals_split_custom_set(normals)
 o.modifiers.clear();o.data=me
 o['V24_finish']='Even tangent shoulder; lower evaluated leg preserved; static satin geometry normals'
 reports.append(dict(name=o.name,old_vertices=old_count,new_vertices=len(verts),preserved_lower_vertices=len(keep),shoulder_start_z=z0,seal_seating_z=ztop,angular_samples=n,roll_segments=24))
 # Native close-ups share the same scale for all four arms.
 name='CAM_support_'+tag
 camera=bpy.data.objects.new(name,bpy.data.cameras.new(name));bpy.context.scene.collection.objects.link(camera)
 target=Vector((cx,cy,.0815));direction=Vector((-1 if tag.endswith('L') else 1,-.35 if tag.startswith('F') else .35,.08)).normalized()
 camera.location=target+direction*.082;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=55;camera.data.clip_start=.001
bpy.context.scene.camera=bpy.data.objects['CAM_support_FR']
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'))
(R/'renders/exterior-v24/build.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports),flush=True)
if '--preview' in sys.argv:
 for o in list(bpy.data.objects):
  if o.hide_render or o.type in {'LIGHT','CAMERA'} or o.name in {'STUDIO_GROUND','INTERNAL_ENVELOPES'}:bpy.data.objects.remove(o,do_unlink=True)
 for material in bpy.data.materials:
  if material.use_nodes:
   bsdf=material.node_tree.nodes.get('Principled BSDF')
   if bsdf:
    for socket in ['Normal','Roughness']:
     for link in list(bsdf.inputs[socket].links):material.node_tree.links.remove(link)
 bpy.ops.export_scene.gltf(filepath=str(R/'exports/aerix-motor-support-v24-preview.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('V24_MOTOR_SUPPORT_POLISH_COMPLETE',flush=True)
