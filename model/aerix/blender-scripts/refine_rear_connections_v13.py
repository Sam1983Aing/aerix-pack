"""Nest the rear pivots in structural chassis shoulders; close top and underside gaps."""
import bpy,math,ast,bmesh,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for filename,names in [('polish_exterior_v05.py',['material','finish','ring','curve','box','cyl','grain']),('refine_front_arms_v09.py',['mesh','lathe']),('refine_arm_hinges_v12.py',['smoothstep'])]:
 for node in ast.parse((ROOT/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
BLACK=bpy.data.materials['Graphite'];POD=bpy.data.materials['V09 satin molded graphite'];DARK=bpy.data.materials['V09 deep recess'];BOLT=bpy.data.materials['V09 fastener gunmetal'];CAP=bpy.data.materials['V09 titanium arm cap']
cradle=bpy.data.objects['BODY_CRADLE']
# Apply only the existing subdivision and shell wall, preserving their evaluated surface.
bpy.context.view_layer.objects.active=cradle
for mod in list(cradle.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
mounts=[]
for tag,sign in [('RL',-1),('RR',1)]:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];old=arm.location.copy();new=Vector((sign*.070,.086,.075));motor=Vector((sign*.165,.140,0));oldpivot=Vector((old.x,old.y,0));pivot=Vector((new.x,new.y,0))
 olddir=(motor-oldpivot).normalized();direction=(motor-pivot).normalized();across=Vector((-direction.y,direction.x,0));delta=math.atan2(direction.y,direction.x)-math.atan2(olddir.y,olddir.x)
 bpy.context.view_layer.update();keep={o:o.matrix_world.copy() for o in arm.children};arm.location=new;bpy.context.view_layer.update()
 for ob,world in keep.items():ob.matrix_world=world
 bpy.context.view_layer.update()
 transform=Matrix.Translation(new)@Matrix.Rotation(delta,4,'Z')@Matrix.Translation(-old)
 # Move the rear hinge hardware only; motor, rotor and landing gear remain in world position.
 for ob in list(bpy.data.objects):
  if ob.name.startswith('HINGE_') and ('_'+tag in ob.name):
   if ob.name=='HINGE_CHASSIS_MOUNT_'+tag:bpy.data.objects.remove(ob,do_unlink=True)
   else:ob.matrix_world=transform@ob.matrix_world
 # Extend and realign the existing swept beam surfaces, preserving their section profiles.
 oldlength=(motor-oldpivot).length;length=(motor-pivot).length;oldcross=Vector((-olddir.y,olddir.x,0))
 def remap(p):
  xy=Vector((p.x,p.y,0))-oldpivot;d=xy.dot(olddir);u=xy.dot(oldcross);t=(d-.0179)/(oldlength-.0168-.0179);q=pivot+direction*(.0179+t*(length-.0168-.0179))+across*u;q.z=p.z;return q
 for name in ['ARM_'+tag,'ARM_INLAY_'+tag,'ARM_LOWER_SEAM_'+tag+'_-1','ARM_LOWER_SEAM_'+tag+'_1']:
  ob=bpy.data.objects[name];world=ob.matrix_world.copy();inv=world.inverted();ob.data=ob.data.copy()
  if ob.type=='MESH':
   for v in ob.data.vertices:v.co=inv@remap(world@v.co)
  else:
   for sp in ob.data.splines:
    for p in sp.points:p.co=(*(inv@remap(world@Vector(p.co[:3]))),p.co.w)
 def point(d,u,z):
  v=pivot+direction*d+across*u;v.z=z;return v
 # A rounded structural cup, with a deep tail embedded through the actual chassis wall.
 # The bottom rises toward the axle; there is no thin cantilevered mounting tab.
 outlines=[]
 for z,rad,inboard,halfwidth in [(.0520,.0118,-.040,.0138),(.0530,.0135,-.040,.0150),(.0586,.0147,-.038,.0160),(.06195,.0147,-.037,.0160)]:
  outline=[point(inboard,-halfwidth,z)]
  for j in range(65):
   a=-math.pi/2+math.pi*j/64;outline.append(point(rad*math.cos(a),rad*math.sin(a),z))
  outline.append(point(inboard,halfwidth,z));outlines.append(outline)
 n=len(outlines[0]);vs=[tuple(v) for row in outlines for v in row];fs=[tuple(range(n-1,-1,-1)),tuple((len(outlines)-1)*n+j for j in range(n))]
 for k in range(len(outlines)-1):
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
 lower=mesh('REAR_MOUNT_LOWER_'+tag,vs,fs,BLACK,bevel=.00075);mounts.append(lower)
 # A rounded, tapered haunch grows out of the curved belly; the socket is cut after union.
 # Most of the root is embedded in the chassis, leaving a small molded shoulder outside.
 center=Vector((sign*.046,.0825,.070));rx,ry,rz=.031,.022,.0192;n=80;rows=33;vs=[]
 for k in range(rows):
  phi=-math.pi/2+.0001+(math.pi-.0002)*k/(rows-1)
  for j in range(n):
   a=math.tau*j/n
   cp=math.cos(phi);sp=math.sin(phi);ca=math.cos(a);sa=math.sin(a)
   power=.83
   v=center+Vector((rx*math.copysign(abs(cp*ca)**power,cp*ca),ry*math.copysign(abs(cp*sa)**power,cp*sa),rz*math.copysign(abs(sp)**power,sp)))
   vs.append(tuple(v))
 fs=[tuple(range(n-1,-1,-1)),tuple((rows-1)*n+j for j in range(n))]
 for k in range(rows-1):
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
 shoulder=mesh('REAR_MOUNT_SHOULDER_'+tag,vs,fs,BLACK)
 for mod in list(shoulder.modifiers):shoulder.modifiers.remove(mod)
 mounts.append(shoulder)
 # Fixed axle and bearing remain chassis children, while the arm pivots retain their separate hierarchy.
 arm['refinement_version']='13';arm['joint_type']='Rear folding collar nested in an integrated chassis shoulder'

# Union the four overlapping support solids into the cradle, yielding one connected structural mesh.
for support in mounts:
 bpy.context.view_layer.objects.active=support
 for mod in list(support.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.context.view_layer.objects.active=cradle
 mod=cradle.modifiers.new('Integrated rear structural shoulder','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=support
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(support,do_unlink=True)
# Cut continuous circular seats through the original wall as well as the added shoulders.
for tag,sign in [('RL',-1),('RR',1)]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.01485,depth=.038,location=(sign*.070,.086,.08135));cut=bpy.context.object
 bpy.context.view_layer.objects.active=cradle;mod=cradle.modifiers.new('Rear collar socket clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

# Boolean cutters may add empty slots; the integrated structure uses the chassis finish throughout.
cradle.data.materials.clear();cradle.data.materials.append(BLACK)
for face in cradle.data.polygons:face.material_index=0

# Local fillets where the rear shoulders meet the rounded belly. Do not bevel the rest of the body.
weights=cradle.data.attributes.get('bevel_weight_edge') or cradle.data.attributes.new('bevel_weight_edge','FLOAT','EDGE')
bm=bmesh.new();bm.from_mesh(cradle.data);bm.normal_update();bm.edges.ensure_lookup_table();bm.verts.ensure_lookup_table()
for e in bm.edges:
 mid=(e.verts[0].co+e.verts[1].co)/2
 if len(e.link_faces)==2 and .039<abs(mid.x)<.061 and .042<mid.y<.115 and .047<mid.z<.089:
  if e.calc_face_angle(0)>.35:weights.data[e.index].value=1
bm.free()
mod=cradle.modifiers.new('Rear shoulder junction fillets','BEVEL');mod.width=.00065;mod.segments=3;mod.limit_method='WEIGHT'
cradle['rear_mounts']='V13: connected Boolean unions through the cradle wall; collar clearances retained'

for name,loc,target,scale in [('rear_connection',(.205,.005,.186),(.067,.084,.074),.119),('rear_connections_top',(0,.086,.50),(0,.086,.075),.219),('rear_connections_under',(0,.086,-.40),(0,.086,.065),.219),('rear_connection_low',(.23,.02,-.058),(.066,.087,.063),.133)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;ob=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
light=bpy.data.lights.new('Rear underside inspection fill','AREA');light.energy=6;light.shape='DISK';light.size=.32
fill=bpy.data.objects.new('LIGHT_REAR_INSPECTION_UNDER',light);s.collection.objects.link(fill);fill.location=(.02,.06,-.18);fill.rotation_euler=(Vector((0,.085,.065))-fill.location).to_track_quat('-Z','Y').to_euler();fill.hide_render=True
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=20;s.render.resolution_percentage=70
for name in (['rear_connection','rear_connections_under','rear_connections_top'] if preview else ['hero','rear_connection','rear_connections_under','rear_connections_top','rear_connection_low']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v13'/(name+('-preview' if preview else '')+'.png'))
 # Underneath views should not be obscured by the studio floor.
 ground=bpy.data.objects['STUDIO_GROUND'];ground.hide_render=name in ['rear_connections_under','rear_connection_low'];fill.hide_render=not ground.hide_render
 bpy.ops.render.render(write_still=True)
print('V13_COMPLETE')
