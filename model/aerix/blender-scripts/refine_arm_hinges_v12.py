"""Sculpted arm beams and exposed folding pivots, using the approved arm close-ups."""
import bpy,math,ast,bmesh,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v11.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for filename,names in [('polish_exterior_v05.py',['material','finish','ring','curve','box','cyl','grain']),('refine_front_arms_v09.py',['mesh','lathe'])]:
 for node in ast.parse((ROOT/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
POD=bpy.data.materials['V09 satin molded graphite'];CAP=bpy.data.materials['V09 titanium arm cap'];DARK=bpy.data.materials['V09 deep recess'];BOLT=bpy.data.materials['V09 fastener gunmetal'];EDGE=bpy.data.materials['V09 machined edge']

def solid_outline(name,outline,z0,z1,mat,bevel=.0004):
 n=len(outline);vs=[(v.x,v.y,z) for z in (z0,z1) for v in outline]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 return mesh(name,vs,fs,mat,bevel=bevel)

def cut_hole(ob,loc,r,depth,vertices=96):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);cut=bpy.context.object
 # Apply the Boolean before the final edge radius and normals.
 mod=ob.modifiers.new('Physical recessed socket','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
 bpy.context.view_layer.objects.active=ob
 while list(ob.modifiers).index(mod)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

def smoothstep(a,b,t):
 u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)

for tag,sign,front in [('FL',-1,True),('FR',1,True),('RL',-1,False),('RR',1,False)]:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];bpy.context.view_layer.update()
 # Move the actual pivot clear of the shell, keeping every motor, blade and leg in world position.
 retained={o:o.matrix_world.copy() for o in arm.children}
 hinge=Vector((sign*(.085 if front else .076),-.089 if front else .086,.075))
 arm.location=hinge;bpy.context.view_layer.update()
 for ob,world in retained.items():ob.matrix_world=world
 bpy.context.view_layer.update()
 for name in ['ARM_'+tag,'ARM_INLAY_'+tag,'HINGE_'+tag,'HINGE_CAP_'+tag,'HINGE_SCREW_'+tag,'HINGE_SOCKET_'+tag,'HINGE_WASHER_'+tag]:
  ob=bpy.data.objects.get(name)
  if ob:bpy.data.objects.remove(ob,do_unlink=True)
 def attach(ob):ob.parent=arm;ob.matrix_parent_inverse=Matrix.Translation(-hinge);return ob
 pivot=Vector((hinge.x,hinge.y,0));motor=Vector((sign*.165,-.140 if front else .140,0))
 direction=(motor-pivot).normalized();across=Vector((-direction.y,direction.x,0));length=(motor-pivot).length
 def point(d,u,z=0):
  p=pivot+direction*d+across*u;p.z=z;return p
 # Fixed chassis saddle supports the axle beneath the rotating knuckle.
 # Its inboard tail disappears under the shell; its rounded outboard end stays visible.
 mount_outline=[point(-.024,-.0115)]
 for j in range(49):
  a=-math.pi/2+math.pi*j/48;mount_outline.append(point(.0144*math.cos(a),.0144*math.sin(a)))
 mount_outline.append(point(-.024,.0115))
 solid_outline('HINGE_CHASSIS_MOUNT_'+tag,mount_outline,.0578,.0622,POD,.00065)
 cyl('HINGE_FIXED_AXLE_'+tag,(hinge.x,hinge.y,.074),.0078,.027,DARK)
 ring('HINGE_LOWER_BEARING_'+tag,(hinge.x,hinge.y,.0627),.0135,.009,.00065,BOLT)
 # Hollow rotor collar with an actual narrow clearance above the fixed saddle.
 attach(lathe('HINGE_ROTATING_COLLAR_'+tag,[(.0137,.06325),(.0141,.064),(.0141,.0857),(.0138,.0884),(.0085,.0884),(.0085,.06325)],pivot,POD,root))
 attach(ring('HINGE_UPPER_SEAL_'+tag,(hinge.x,hinge.y,.08865),.0139,.0087,.00045,DARK))
 # D-shaped root cap, with a flat shoulder facing the long arm beam.
 outline=[point(.0172,-.0123),point(.0172,.0123),point(.003,.0141)]
 for j in range(49):
  a=math.pi/2+math.pi*j/48;outline.append(point(.0141*math.cos(a),.0141*math.sin(a)))
 outline.append(point(.003,-.0141))
 cap=solid_outline('HINGE_CAP_'+tag,outline,.0889,.0923,BOLT,.00045)
 cut_hole(cap,(hinge.x,hinge.y,.091),.0049,.010)
 for face in cap.data.polygons:
  if abs(face.normal.z)>.999:face.use_smooth=False
 attach(cap)
 # A stepped counterbore exposes a dark wall and the sunken machined washer.
 attach(ring('HINGE_COUNTERBORE_'+tag,(hinge.x,hinge.y,.0898),.0048,.0041,.0016,DARK))
 attach(ring('HINGE_WASHER_'+tag,(hinge.x,hinge.y,.08975),.0042,.00305,.00045,EDGE))
 screw=cyl('HINGE_SCREW_'+tag,(hinge.x,hinge.y,.0889),.0031,.0015,BOLT)
 cut_hole(screw,(hinge.x,hinge.y,.08975),.00135,.0015,6);attach(screw)
 attach(cyl('HINGE_SOCKET_'+tag,(hinge.x,hinge.y,.08885),.00132,.00012,DARK,vertices=6))
 # Small molded witness marks on the cap, following its edge (no additional branding).
 for j in range(2):
  pts=[point(.010+j*.0014,-.0098,.09236),point(.010+j*.0014,-.0078,.09236)]
  attach(curve('HINGE_WITNESS_'+tag+'_'+str(j),pts,.00010,DARK,root))
 # Curved shoulder cap seam, seated on the collar perimeter.
 pts=[point(.01425*math.cos(a),.01425*math.sin(a),.0865) for a in [math.pi/2+j*math.pi/48 for j in range(49)]]
 attach(curve('HINGE_COLLAR_REVEAL_'+tag,pts,.00013,DARK,root))
 # Continuous tapered beam: broad lower side face, rising root relief, and a swept shoulder.
 start=.0179;end=length-.0168;rows=49;vs=[];cvs=[]
 for k in range(rows):
  t=k/(rows-1);d=start+(end-start)*t
  w=.0254*(1-t)+.0228*t
  flare=1-smoothstep(0,.22,t)+smoothstep(.76,1,t)
  topw=w*(.285+.14*flare)
  # The titanium strip curves down and widens into both end shoulders.
  crest=.0910-.0007*flare+.0004*math.sin(math.pi*t)
  edgez=.0888-.0010*flare
  floor=.063+.0055*(1-smoothstep(.04,.21,t))+.001*t
  profile=[(-topw,crest-.0012),(topw,crest-.0012),(w*.496,.084+.0020*flare),(w*.515,.0815),(w*.485,floor+.001),(w*.40,floor),(-w*.40,floor),(-w*.485,floor+.001),(-w*.515,.0815),(-w*.496,.084+.0020*flare)]
  vs.extend(tuple(point(d,u,z)) for u,z in profile)
  capprofile=[(-topw,crest),(topw,crest),(topw+.00075,crest-.00028),(topw+.00115,crest-.0008),(topw+.00110,crest-.0012),(topw,crest-.0009),(-topw,crest-.0009),(-topw-.00110,crest-.0012),(-topw-.00115,crest-.0008),(-topw-.00075,crest-.00028)]
  cvs.extend(tuple(point(d,u,z)) for u,z in capprofile)
 def loft(name,verts,mat,bevel):
  n=10;fs=[tuple(range(n-1,-1,-1)),tuple((rows-1)*n+j for j in range(n))]
  for k in range(rows-1):
   for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
  ob=mesh(name,verts,fs,mat,bevel=bevel)
  # Smooth along each swept surface while retaining the deliberate section breaks.
  for mod in list(ob.modifiers):
   if mod.type=='WEIGHTED_NORMAL':ob.modifiers.remove(mod)
  weights=ob.data.attributes.new('bevel_weight_edge','FLOAT','EDGE')
  for edge in ob.data.edges:
   a,b=edge.vertices
   if a%n==b%n:
    edge.use_edge_sharp=True;weights.data[edge.index].value=1
  for mod in ob.modifiers:
   if mod.type=='BEVEL':mod.limit_method='WEIGHT'
  return attach(ob)
 loft('ARM_'+tag,vs,POD,.00035);loft('ARM_INLAY_'+tag,cvs,CAP,.00025)
 # A lower molded parting line terminates before the motor collar.
 for side in [-1,1]:
  pts=[]
  for k in range(30):
   t=.015+.94*k/29;d=start+(end-start)*t;w=.0254*(1-t)+.0228*t;floor=.063+.0055*(1-smoothstep(.04,.21,t))+.001*t
   pts.append(point(d,side*w*.483,floor+.00125))
  attach(curve('ARM_LOWER_SEAM_'+tag+'_'+str(side),pts,.00011,DARK,root))
 arm['joint_type']='Vertical folding pivot; fixed chassis saddle, rotating collar and arm'
 arm['refinement_version']='12';arm['axis']='local Z'

# Mirror the finished counterbore topology exactly across the center plane.
for left,right in [('FL','FR'),('RL','RR')]:
 source=bpy.data.objects['HINGE_CAP_'+left];target=bpy.data.objects['HINGE_CAP_'+right];target.data=source.data.copy()
 for v in target.data.vertices:v.co.x=-v.co.x
 bm=bmesh.new();bm.from_mesh(target.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(target.data);bm.free()

for name,loc,target,scale in [('front_arm_detail',(.19,-.39,.27),(.122,-.113,.083),.185),('front_hinge',(.14,-.30,.20),(.091,-.095,.084),.100),('rear_arm_detail',(.295,.020,.25),(.113,.11,.080),.185),('rear_hinge',(.215,.008,.215),(.079,.085,.079),.105)]:
 old=bpy.data.objects.get('CAM_'+name)
 if old:bpy.data.objects.remove(old,do_unlink=True)
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;ob=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.cycles.samples=48;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=24;s.render.resolution_percentage=75
views=['front_arm_detail','rear_hinge'] if preview else ['hero','front_arm_detail','front_hinge','rear_arm_detail','rear_hinge']
for name in views:
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v12'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V12_COMPLETE',flush=True)
