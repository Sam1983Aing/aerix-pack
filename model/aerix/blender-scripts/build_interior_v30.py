"""Refine thermal, computer and tray inside the preserved V29 drone."""
import bpy,bmesh,json,math,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];O=R/'renders/interior-v30';O.mkdir(exist_ok=True)
SOURCE=R/'blender/aerix-interior-v29.blend';sourcehash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(400);bpy.context.view_layer.update()
rootnames=['THERMAL_ROOT','FLIGHT_COMPUTER_ROOT','INTERNAL_SUPPORT_ROOT'];roots={n:bpy.data.objects[n] for n in rootnames};oldparts=[o.name for r in roots.values() for o in r.children_recursive if o.type in {'MESH','CURVE','FONT'}]
def snapshot():
 d=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in oldparts or o.name.startswith(('TH30_','FC30_','TR30_')) or o.name=='STUDIO_GROUND':continue
  e=o.evaluated_get(d);m=e.to_mesh();out[o.name]=hashlib.sha256(repr(([tuple(e.matrix_world@v.co) for v in m.vertices],[tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],[q.name if q else None for q in m.materials])).encode()).hexdigest();e.to_mesh_clear()
 return out
before=snapshot()
for n in oldparts:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
new=[];interfaces=[];surface_report=[]

def group(n,parent):
 o=bpy.data.objects.new(n,None);s.collection.objects.link(o);o.parent=parent;return o
thermal=roots['THERMAL_ROOT'];board=roots['FLIGHT_COMPUTER_ROOT'];trayroot=roots['INTERNAL_SUPPORT_ROOT']
plateRoot=group('TH30_PLATE_ROOT',thermal);spreaderRoot=group('TH30_SPREADER_ROOT',thermal);padRoot=group('TH30_PAD_ROOT',thermal)
shieldRoot=group('FC30_SHIELD_ROOT',board);capRoot=group('FC30_PROCESSOR_CAP_ROOT',board);imuRoot=group('FC30_IMU_ROOT',board);harnessRoot=group('FC30_HARNESS_ROOT',board)
postsRoot=group('TR30_POSTS_ROOT',trayroot);loomRoot=group('TR30_LOOM_ROOT',trayroot)

def material(n,c,metal,rough,grain=None,directional=False):
 m=bpy.data.materials.new('V30 '+n);m.diffuse_color=(*c,1);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if grain:
  scale,depth,low,high=grain;coord=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=2
  if directional:
   stretch=nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(1,.035,1);links.new(coord.outputs['Object'],stretch.inputs[0]);links.new(stretch.outputs[0],noise.inputs['Vector'])
  else:links.new(coord.outputs['Object'],noise.inputs['Vector'])
  ramp=nodes.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=low;ramp.inputs['To Max'].default_value=high;links.new(noise.outputs['Fac'],ramp.inputs['Value']);links.new(ramp.outputs['Result'],p.inputs['Roughness'])
  bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=depth;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
AL=material('satin bead blasted aluminum',(.39,.43,.46),.83,.31,(10000,.000006,.27,.37))
MILL=material('fine machined aluminum',(.34,.39,.42),.85,.30,(19000,.000004,.26,.36),True)
CU=material('brushed copper spreader',(.58,.245,.10),.88,.29,(16000,.000003,.24,.34),True)
MASK=material('deep green soldermask',(.008,.060,.035),.12,.35,(18000,.000002,.30,.40))
RUBBER=material('isolation elastomer',(.010,.015,.019),.01,.53,(19000,.000005,.47,.59))
WIRE=material('black silicone insulation',(.008,.012,.016),.02,.38,(18000,.000003,.34,.43))
BRAID=material('woven loom sleeve',(.012,.018,.022),.08,.48,(27000,.000009,.40,.55))
RED=material('muted red silicone',(.32,.014,.011),0,.4,(16000,.000003,.36,.45))
CHIP=material('molded semiconductor',(.012,.016,.022),.06,.40)
GOLD=material('gold plated terminals',(.63,.38,.09),.84,.25)
SOLDER=material('silver solder',(.49,.53,.55),.89,.24)
STEEL=material('dark satin fasteners',(.14,.18,.21),.85,.3)
CERAMIC=material('warm ceramic',(.34,.30,.23),.05,.42)
WHITE=material('connector polymer',(.60,.58,.50),0,.38)
INK=material('silkscreen ink',(.57,.65,.57),.02,.48)
ETCH=material('laser etched marking',(.018,.023,.028),0,.55)
TRACE=material('covered copper traces',(.014,.082,.047),.24,.34)
FLEX=material('polyimide flex',(.43,.16,.018),.27,.35)

def P(p):return Vector(p)/1000

def keep(o,parent):
 # Every new service root is identity in the assembled pose. Avoid rebuilding the
 # whole dependency graph for each small passive or connector pin.
 w=o.matrix_basis.copy();ancestor=parent
 while ancestor.name not in rootnames:ancestor=ancestor.parent
 parent_world=roots[ancestor.name].matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=parent_world.inverted()@w

def finish(o,n,mat,parent,bevel=0):
 o.name=n;o.data.materials.append(mat)
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
  if bevel:m=o.modifiers.new('Precision edge radius','BEVEL');m.width=bevel/1000;m.segments=4
  m=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');m.keep_sharp=True
 keep(o,parent);new.append(o);return o

def box(n,p,size,mat,parent,bevel=.25):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(p));o=bpy.context.object;o.dimensions=Vector(size)/1000;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,mat,parent,bevel)

def cyl(n,p,r,h,mat,parent,axis='Z',bevel=.08):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r/1000,depth=h/1000,location=P(p));o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return finish(o,n,mat,parent,bevel)

def apply(o):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)

def cut(o,c):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Machined pocket','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);new.remove(c);bpy.data.objects.remove(c,do_unlink=True)

def flat_finish(o):
 apply(o);me=o.data;me.update();ns=[tuple(n.vector) for n in me.corner_normals];planes={};count=0
 for f in me.polygons:
  if f.area>2e-6 and max(abs(x) for x in f.normal)>.99999:
   axis=max(range(3),key=lambda i:abs(f.normal[i]));n=Vector((0,0,0));n[axis]=1 if f.normal[axis]>0 else -1
   for li in f.loop_indices:
    ns[li]=tuple(n);vi=me.loops[li].vertex_index
    if vi not in planes or planes[vi][0]<f.area:planes[vi]=(f.area,n)
   count+=1
 for f in me.polygons:
  if max(abs(x) for x in f.normal)>.99999:continue
  for li in f.loop_indices:
   p=planes.get(me.loops[li].vertex_index)
   if p and f.normal.dot(p[1])>.8:ns[li]=tuple(p[1])
 me.normals_split_custom_set(ns);surface_report.append({'object':o.name,'planar_faces':count})

def line(n,points,r,mat,parent,smooth=True):
 d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=16;d.bevel_depth=r/1000;d.bevel_resolution=3
 if smooth:
  sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
  for q,p in zip(sp.bezier_points,points):q.co=P(p);q.handle_left_type='AUTO';q.handle_right_type='AUTO'
 else:
  sp=d.splines.new('POLY');sp.points.add(len(points)-1)
  for q,p in zip(sp.points,points):q.co=(*P(p),1)
 o=bpy.data.objects.new(n,d);s.collection.objects.link(o);return finish(o,n,mat,parent)

def label(n,body,p,size,parent,mat=INK):
 d=bpy.data.curves.new(n,'FONT');d.body=body;d.size=size/1000;d.extrude=.000004;d.align_x='CENTER';o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=P(p);return finish(o,n,mat,parent)

def ring(n,p,ro,ri,h,mat,parent):
 N=48;v=[]
 for z in [-h/2,h/2]:
  for r in [ro,ri]:
   for i in range(N):a=i*math.tau/N;v.append(P((p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+z)))
 f=[]
 for i in range(N):j=(i+1)%N;f.extend([(i,j,2*N+j,2*N+i),(N+j,N+i,3*N+i,3*N+j),(2*N+i,2*N+j,3*N+j,3*N+i),(j,i,N+i,N+j)])
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);s.collection.objects.link(o);return finish(o,n,mat,parent,.04)

def screw(n,p,parent,r=1.5,h=.7):
 head=cyl(n,p,r,h,STEEL,parent);apply(head);N=60;v=[]
 for zz in [-h*.2,h]:
  for k in range(N):a=k*math.tau/N;rr=r*(.46+.09*math.cos(6*a));v.append(P((p[0]+rr*math.cos(a),p[1]+rr*math.sin(a),p[2]+zz)))
 f=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new('socket');me.from_pydata(v,[],f);me.update();c=bpy.data.objects.new('socket',me);s.collection.objects.link(c);finish(c,n+'_CUT',STEEL,parent);cut(head,c);flat_finish(head);return head

# Layer 2: preserve the measured thermal interface at 69–71 mm and maximum height 75.25.
plate=box('TH30_RIBBED_COVER',(0,-18,72.25),(67,130,2.5),AL,plateRoot,.8);apply(plate)
for x in [-29.5,29.5]:
 for y in [-78,42]:
  c=cyl('TH30_BORE',(x,y,73.25),1.9,2.0,AL,plateRoot);apply(c);cut(plate,c);screw('TH30_CAPTIVE_SCREW',(x,y,73.12),plateRoot,1.38,.58)
  cyl('TH30_SCREW_SHAFT',(x,y,70.8),.78,4.0,STEEL,plateRoot)
for i in range(9):
 x=-24+i*6;box('TH30_COOLING_FIN',(x,-14,74.10),(1.85,105,2.20),AL,plateRoot,.65)
# Sensor and paired leads remain on the cover, ending on underside mating pads.
box('TH30_SENSOR_PACKAGE',(29.8,-53,73.9),(3.2,5.3,.8),STEEL,plateRoot,.25)
for i,mat in enumerate([WIRE,RED]):
 line('TH30_SENSOR_LEAD',[(29.7+i*.5,-55.4,73.8),(29.7+i*.5,-68,73.8),(26.5+i*.6,-74,73.8),(26.5+i*.6,-76,73.8)],.20,mat,plateRoot)
 cyl('TH30_SENSOR_CONTACT',(26.5+i*.6,-76,70.82),.42,.12,GOLD,plateRoot)
for y in [-60,-68]:box('TH30_SENSOR_CLIP',(30,-1+y,74.05),(2.0,1.3,.55),RUBBER,plateRoot,.18)
box('TH30_SENSOR_TERMINAL',(26.8,-76,73.88),(2.3,2.3,.9),WHITE,plateRoot,.22)
for i in range(2):box('TH30_SENSOR_TERMINAL_PIN',(26.5+i*.6,-76,74.34),(.22,.70,.10),GOLD,plateRoot,.03)
label('TH30_MARK','AERIX',(0,-76,73.51),3.3,plateRoot,ETCH)
spreader=box('TH30_COPPER_SPREADER',(0,-39,70.60),(24,24,.80),CU,spreaderRoot,.4)
pad=box('TH30_THERMAL_PAD',(0,-39,69.60),(20,20,1.20),RUBBER,padRoot,.20)
flat_finish(plate)

# Layer 3: fitted multilayer board and real mounting holes.
pcb=box('FC30_MAIN_PCB',(0,-17,64),(74,144,1.6),MASK,board,.75);apply(pcb)
mounts=[(x,y) for x in [-33,33] for y in [-82,48]]
for x,y in mounts:
 c=cyl('FC30_MOUNT_HOLE',(x,y,64),1.55,5,MASK,board);apply(c);cut(pcb,c)
 ring('FC30_MOUNT_PLATING',(x,y,64.84),2.5,1.56,.08,GOLD,board)
 screw('FC30_MOUNT_SCREW',(x,y,65.45),board,1.28,.64);cyl('FC30_MOUNT_SHAFT',(x,y,63.7),.75,3.0,STEEL,board)
for x in [-23,0,23]:
 c=box('FC30_SERVICE_RELIEF',(x,-89.2,64),(11.2,4.0,5),MASK,board,.35);apply(c);cut(pcb,c)
flat_finish(pcb)
print('V30_BUILD thermal and PCB shell',flush=True)
# Surface landmarks stay at the original processor/memory/radio/IMU positions.
box('FC30_PROCESSOR_SUBSTRATE',(0,-39,65.7),(25,25,1.6),CHIP,board,.35)
box('FC30_PROCESSOR_DIE',(0,-39,67.10),(19.4,19.4,1.20),CHIP,board,.3)
box('FC30_PROCESSOR_HEATCAP',(0,-39,68.35),(22,22,1.30),AL,capRoot,.7)
label('FC30_CPU_MARK','AERIX',(0,-39.8,69.005),3.0,capRoot,ETCH)
for axis in [0,1]:
 for sign in [-1,1]:
  for i in range(22):
   xy=[(i-10.5)*1.00,sign*12.65];xy=xy if axis==0 else xy[::-1];box('FC30_CPU_PAD',(xy[0],xy[1]-39,65.01),(.45,.45,.20),GOLD,board,.06)
for k,yy in enumerate([-52,-24]):
 box('FC30_MEMORY',(24,yy,66.05),(12,18,2.10),CHIP,board,.35);label('FC30_MEMORY_MARK','M'+str(k+1),(24,yy,67.11),1.7,board)
 for side in [-1,1]:
  for i in range(12):box('FC30_MEMORY_LAND',(24+side*6.10,yy+(i-5.5)*1.2,65.0),(.55,.5,.22),SOLDER,board,.06)
# Radio shield uses a hollow can rather than a solid block.
radio=box('FC30_RADIO_CAN',(-15,26,67.7),(25,26,3.6),AL,shieldRoot,.65);apply(radio)
c=box('FC30_RADIO_CAN_CUT',(-15,26,65.65),(23.8,24.8,6.4),AL,shieldRoot,.3);apply(c);cut(radio,c);flat_finish(radio)
box('FC30_RADIO_MODULE',(-15,26,65.5),(23.6,24.6,1.25),MASK,board,.35)
box('FC30_RADIO_CHIP',(-15,26,67.0),(11,11,1.7),CHIP,board,.3)
label('FC30_RADIO_MARK','RF / 01',(-15,25,69.51),2.3,shieldRoot,ETCH)
# IMU daughterboard on four small isolating seats, with an explicit docking header.
for x in [-27.7,-18.3]:
 for y in [-72.7,-63.3]:cyl('FC30_IMU_SEAT',(x,y,65.25),.8,.8,RUBBER,board)
box('FC30_IMU_BOARD',(-23,-68,66.15),(13,13,1.0),MASK,imuRoot,.35)
box('FC30_IMU_PACKAGE',(-23,-68,67.7),(6,6,2.0),CHIP,imuRoot,.35)
label('FC30_IMU_MARK','IMU',(-23,-73.4,66.66),1.5,imuRoot)
for i in range(5):
 cyl('FC30_IMU_DOCK_PIN',(-27+i*2,-63.1,65.35),.22,1.1,GOLD,board);ring('FC30_IMU_DOCK_SOCKET',(-27+i*2,-63.1,66.05),.40,.24,.7,GOLD,imuRoot)
# Primary power-management packages, separated from the thermal contact zone.
chipzones=[]
for k,(x,y,w,h) in enumerate([(-23,-45,5,7),(-23,-23,5,7),(-14,-8,6,6),(0,-8,6,7),(14,2,5,6),(25,15,5,7),(25,34,5,6),(4,31,5,6),(2,-69,5,5)]):
 box('FC30_AUX_IC',(x,y,66.0),(w,h,1.6),CHIP,board,.23);chipzones.append((x,y,w+3,h+3));label('FC30_IC_ID','U'+str(k+2),(x,y-.5,66.81),1.05,board)
 for sign in [-1,1]:
  for j in range(5):box('FC30_IC_LEAD',(x+sign*(w/2+.3),y+(j-2)*h/6,65.1),(.75,.40,.25),SOLDER,board,.06)
# A deterministic layout of passives respects every package, connector and mounting keepout.
keepouts=[(0,-39,30,30),(24,-52,17,23),(24,-24,17,23),(-15,26,30,31),(-23,-68,17,17),(0,-85,70,13),(32,3,7,100),(15,45,27,12),(28,-76,10,8),(0,8,40,6)]+chipzones+[(x,y,9,9) for x,y in mounts]
def clear(x,y,w,h):return all(abs(x-a)>(w+c)/2 or abs(y-b)>(h+d)/2 for a,b,c,d in keepouts)
random.seed(30);passive_count=0
for y in range(-77,50,7):
 for x in range(-29,31,6):
  if not clear(x,y,3.2,3.5):continue
  w=1.15 if random.random()<.65 else 1.65;h=2.05;box('FC30_PASSIVE',(x,y,65.35),(w,h,.7),CERAMIC if passive_count%3 else CHIP,board,.09)
  for sign in [-1,1]:box('FC30_SOLDER_FILLET',(x,y+sign*1.0,65.05),(w+.12,.55,.28),SOLDER,board,.10)
  if passive_count%4==0:label('FC30_DESIGNATOR','C'+str(passive_count+1),(x,y+2.2,64.84),.9,board)
  passive_count+=1
# Ordered fine traces radiate from the core and terminate at gold via annuli.
for side in [-1,1]:
 for k in range(12):
  x=side*(13.8+k*.48);yy=-49+k*1.7;end=yy+13.0+k*.45
  line('FC30_MASKED_TRACE',[(side*12.9,yy,64.824),(x,yy,64.824),(x,end,64.824),(x+side*1.3,end+1.3,64.824)],.055,TRACE,board,False)
  ring('FC30_VIA',(x+side*1.3,end+1.3,64.84),.23,.105,.08,GOLD,board)
for x in [-29,-9,10,28]:
 for y in [-58,-2,9,43]:
  if clear(x,y,1.2,1.2):cyl('FC30_TEST_PAD',(x,y,64.87),.45,.12,GOLD,board)
label('FC30_BOARD_MARK','AERIX / FLIGHT CORE',(0,7,64.85),2.2,board)
label('FC30_BOARD_REV','FC-01  REV B',(4,49,64.85),1.6,board)
# Two coax runs start at RF connectors and end on separate on-board antenna sockets.
for i,x in enumerate([3.0,8.0]):
 cyl('FC30_COAX_SOURCE',(x,38,65.45),1.15,1.1,GOLD,board);cyl('FC30_COAX_PLUG',(x,38,66.05),.95,.55,GOLD,board)
 endx=30+i*1.35
 line('FC30_ANTENNA_COAX',[(x,38.5,66.1),(x+7,44,66.1),(endx,41,66.1),(endx,20,66.1),(endx,-2,66.1)],.37,WIRE,board)
 cyl('FC30_ANTENNA_SOCKET',(endx,-2,65.8),.80,1.0,GOLD,board);label('FC30_ANT_LABEL','ANT'+str(i+1),(x,34.5,64.85),1.2,board)
for y in [28,12]:box('FC30_COAX_CLIP',(30.6,y,66.2),(3.6,2.7,1.6),RUBBER,board,.35)
# Cover sensor mates vertically with two compliant board contacts.
for i in range(2):
 x=26.5+i*.6;cyl('FC30_THERMAL_SENSOR_POGO',(x,-76,68.0),.20,5.6,GOLD,board);box('FC30_POGO_INSULATOR',(x,-76,66.0),(.55,1.2,2.4),CHIP,board,.1)
# Front connectors, detachable plugs, camera flex and short board-to-tray service looms.
portxs=[-23,0,23]
for k,(x,tag) in enumerate(zip(portxs,['CAM','PWR','I/O'])):
 socket=box('FC30_'+tag.replace('/','')+'_SOCKET',(x,-86,67.0),(13,5.2,3.8),WHITE,board,.45);apply(socket)
 cutbox=box('FC30_SOCKET_CUT',(x,-88.7,67.0),(10.8,3.0,2.1),CHIP,board,.2);apply(cutbox);cut(socket,cutbox);flat_finish(socket)
 for j in range(6):box('FC30_CONNECTOR_PIN',(x+(j-2.5)*1.45,-88,66.85),(.35,2.5,.35),GOLD,board,.05)
 box('FC30_SERVICE_PLUG',(x,-89.2,67.0),(10.5,2.5,1.95),CHIP,harnessRoot,.25)
 label('FC30_PORT_LABEL',tag,(x,-81.7,64.85),1.7,board)
 # Vertical terminal plugs dock into the tray; all pigtails travel with the board.
 box('FC30_TRAY_DOCK_PLUG',(x,-89.0,62.8),(9.7,3.2,1.8),CHIP,harnessRoot,.25)
 for j in range(4):cyl('FC30_TRAY_DOCK_PIN',(x+(j-1.5)*1.8,-89,61.9),.25,1.4,GOLD,harnessRoot)
 if k==0:
  # Continuous laminated camera flex, curved in Y/Z, with fine copper lanes.
  rows=[]
  for j in range(33):
   t=j/32;u=1-t;yy=u*u*u*(-90.2)+3*u*u*t*(-94.0)+3*u*t*t*(-94.0)+t*t*t*(-90.3);zz=u*u*u*67+3*u*u*t*67+3*u*t*t*62.8+t*t*t*62.8
   dy=3*u*u*(-3.8)+3*t*t*3.7;dz=6*u*t*(-4.2);normal=Vector((-dz,dy)).normalized();rows.append((yy,zz,normal))
  verts=[]
  for sign in [-1,1]:
   for yy,zz,n in rows:
    for xx in [x-3.65,x+3.65]:verts.append(P((xx,yy+sign*n.x*.07,zz+sign*n.y*.07)))
  N=len(rows)*2;faces=[]
  for j in range(len(rows)-1):
   a=2*j;b=a+2;faces.extend([(a,b,b+1,a+1),(N+a+1,N+b+1,N+b,N+a),(a,N+a,N+b,b),(a+1,b+1,N+b+1,N+a+1)])
  faces.extend([(0,1,N+1,N),(N-2,2*N-2,2*N-1,N-1)])
  me=bpy.data.meshes.new('Camera flex laminate');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new('flex',me);s.collection.objects.link(o);finish(o,'FC30_CAMERA_FLEX',FLEX,harnessRoot)
  for j in range(8):line('FC30_FLEX_COPPER_LANE',[(x+(j-3.5)*.82,yy+n.x*.085,zz+n.y*.085) for yy,zz,n in rows],.045,GOLD,harnessRoot,False)

 else:
  for j in range(4):
   xx=x+(j-1.5)*1.25;line('FC30_SERVICE_PIGTAIL',[(xx,-90.2,67),(xx,-93.1,65.5),(xx,-92.0,63),(xx,-90.2,62.8)],.32,RED if k==1 and j==1 else WIRE,harnessRoot)

print('V30_BUILD populated computer',len(new),flush=True)
# Layer 4: one continuous pocketed tray, genuine bores, isolators and supported wiring.
base=box('TR30_POCKETED_TRAY',(0,-17,59.0),(78,150,3.0),AL,trayroot,.8);apply(base)
# Three broad central pockets with rounded ends preserve the perimeter and cross ribs.
for y,length in [(-67,34),(-24,46),(29,46)]:
 c=box('TR30_POCKET_CUT',(0,y,60.5),(48,length,3.8),MILL,trayroot,.9);apply(c);cut(base,c)
# Long side channels leave material beneath each loom.
for x in [-30.0,30.0]:
 c=box('TR30_CHANNEL_CUT',(x,-15,60.5),(6.7,119,3.5),MILL,trayroot,1.7);apply(c);cut(base,c)
for x,y in mounts:
 c=cyl('TR30_MOUNT_BORE',(x,y,59),1.6,7,MILL,trayroot);apply(c);cut(base,c)
 ring('TR30_ISOLATION_SEAT',(x,y,60.60),3.25,1.61,.70,RUBBER,trayroot)
 ring('TR30_THREADED_POST',(x,y,62.05),2.6,1.04,2.30,AL,postsRoot)
 ring('TR30_BRASS_INSERT',(x,y,62.4),1.32,.91,1.40,GOLD,postsRoot)
 # Fine helical thread relief remains inside the real bore.
 pts=[]
 for t in range(181):a=math.tau*t/60;pts.append((x+.96*math.cos(a),y+.96*math.sin(a),61.7+1.05*t/180))
 line('TR30_INSERT_THREAD',pts,.065,GOLD,postsRoot,False)
 cyl('TR30_POST_SEAT_PIN',(x,y,59.5),.75,2.2,STEEL,postsRoot)
 # Distinct chassis hold-down screws avoid the PCB mount axis.
 xx=x+(-3.4 if x>0 else 3.4);screw('TR30_CHASSIS_SCREW',(xx,y+3.7,60.22),trayroot,1.15,.52)
for x in portxs:
 c=box('TR30_BRACKET_POCKET',(x,-89,60.7),(12.85,5.8,4.9),MILL,trayroot,.4);apply(c);cut(base,c)
base.data.materials.append(MILL)
for face in base.data.polygons:
 if abs(face.normal.z)>.99 and (base.matrix_world@face.center).z<.0604:face.material_index=1
flat_finish(base)
print('V30_BUILD tray pockets',flush=True)
# Mating receivers sit below the three board plugs and remain on the tray.
for x in portxs:
 bracket=box('TR30_CONNECTOR_BRACKET',(x,-89,60.0),(12.3,5.2,2.9),AL,loomRoot,.4);apply(bracket)
 c=box('TR30_RECEIVER_RECESS',(x,-89,61.7),(10.4,3.7,3.5),WHITE,loomRoot,.3);apply(c);cut(bracket,c);flat_finish(bracket)
 receiver=box('TR30_DOCK_RECEIVER',(x,-89,61.0),(10.2,3.55,1.60),WHITE,loomRoot,.3);apply(receiver)
 for j in range(4):
  xx=x+(j-1.5)*1.8;c=cyl('TR30_DOCK_HOLE',(xx,-89,61.8),.37,2.4,GOLD,loomRoot);apply(c);cut(receiver,c)
  ring('TR30_DOCK_SOCKET',(xx,-89,61.1),.46,.31,1.2,GOLD,loomRoot)
 flat_finish(receiver)
# Side wiring terminates in the front receivers and rear grommet blocks.
for sign in [-1,1]:
 x=sign*30.0
 for j,mat in enumerate([WIRE,RED]):
  xx=x+sign*(j-.5)*1.0
  line('TR30_ROUTED_WIRE',[(sign*23,-87.5,61.2),(sign*23,-79,61.2),(sign*25.5,-76.5,61.2),(xx,-73,61.2),(xx,-69,59.75),(xx,-50,59.7),(xx,-20,59.7),(xx,24,59.7),(xx,39.5,60.0)],.34,mat,loomRoot)
 box('TR30_FRONT_HARNESS_CLIP',(sign*25.5,-76.5,61.15),(2.0,2.5,1.3),RUBBER,loomRoot,.30)
 line('TR30_BRAIDED_SLEEVE',[(x,-72,59.75),(x,-58,59.75),(x,-22,59.75),(x,19,59.75)],.9,BRAID,loomRoot)
 for yy in [-67,-38,2,25]:box('TR30_LOOM_CLIP',(x,yy,60.1),(4.2,3.0,1.7),RUBBER,loomRoot,.45)
 box('TR30_REAR_GROMMET',(x,41,60.6),(5,5,2.8),RUBBER,loomRoot,.8)
 box('TR30_REAR_TERMINAL',(x,43,60.6),(3.5,2.0,1.7),CHIP,loomRoot,.25)
 for j in range(2):box('TR30_REAR_CONTACT',(x+(j-.5)*1.1,44.05,60.6),(.50,.30,.8),GOLD,loomRoot,.08)
# The center receiver feeds an orderly short crossover in the front pocket.
for i,mat in enumerate([WIRE,RED]):line('TR30_CENTER_FEED',[(i-.5,-87.5,61.2),(i-.5,-83,61.2),(12,-81+i,61.2),(23,-83+i,61.2),(23,-87.5,61.2)],.32,mat,loomRoot)
label('TR30_MARK','AERIX / STRUCTURAL CORE',(0,53.6,60.51),1.7,trayroot,ETCH)

# Detail clips are independent of the preserved body, battery, folding and optical clips.
def ease(u,a,b):
 t=max(0,min(1,(u-a)/(b-a)));return t*t*(3-2*t)
detail={
 'Thermal_detail':[(plateRoot,(0,0,.034),0,.50),(spreaderRoot,(0,0,.015),.30,.78)],
 'Computer_detail':[(shieldRoot,(0,0,.018),0,.50),(capRoot,(0,0,.012),.18,.66),(imuRoot,(0,0,.008),.35,.80),(harnessRoot,(0,-.007,0),.0,.30)],
 'Tray_detail':[(postsRoot,(0,0,.009),0,.55),(loomRoot,(0,0,.007),.28,.85)]}
tracks={}
for clip,items in detail.items():
 start={'Thermal_detail':1101,'Computer_detail':1251,'Tray_detail':1401}[clip]
 for o,offset,a,b in items:
  points=[list(Vector(offset)*ease(k/120,a,b)) for k in range(121)];tracks[o.name]={'clip':clip,'samples':points}
  for fr,v in [(1,(0,0,0)),(400,(0,0,0)),(971,(0,0,0)),(start-1,(0,0,0)),*[(start+k,p) for k,p in enumerate(points)],(1551,points[-1]),*[(1551+k,list(Vector(offset)*ease(1-k/120,a,b))) for k in range(1,121)]]:
   o.location=v;o.keyframe_insert(data_path='location',frame=fr)
  if o.animation_data and o.animation_data.action:
   for layer in o.animation_data.action.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for f in bag.fcurves:
       for k in f.keyframe_points:k.interpolation='LINEAR'
# A later native service sequence first separates the body; V29's original timeline is untouched.
for name,offset in [('SHELL_REVEAL_ROOT',(0,0,.285)),('BATTERY_ROOT',(0,.016,.210)),('THERMAL_ROOT',(0,0,.150)),('FLIGHT_COMPUTER_ROOT',(0,0,.095)),('INTERNAL_SUPPORT_ROOT',(0,0,.040)),('CAMERA_GIMBAL_ROOT',(0,-.050,-.004))]:
 o=bpy.data.objects[name];s.frame_set(400);base=o.location.copy()
 for fr,m in [(1001,0),(1091,1),(1551,1),(1671,0)]:o.location=base+Vector(offset)*m;o.keyframe_insert(data_path='location',frame=fr)
s.frame_end=1671
for title,fr in [('V30 ASSEMBLED',400),('V30 BODY EXPLODED',1091),('V30 THERMAL DETAIL',1221),('V30 COMPUTER DETAIL',1371),('V30 TRAY DETAIL',1521),('V30 REASSEMBLED',1671)]:s.timeline_markers.new(title,frame=fr)
s.frame_set(400);bpy.context.view_layer.update();after=snapshot();checks={'unmodified_battery_exterior_optics_chassis':before==after,'v29_source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sourcehash};assert all(checks.values()),checks
hierarchy={o.name:{'parent':o.parent.name if o.parent else None,'local_matrix':[v for row in o.matrix_local for v in row]} for o in s.objects if o.type not in {'LIGHT','CAMERA'} and not o.hide_render and o.name!='STUDIO_GROUND'}
config={'old_parts':oldparts,'new_mesh_names':[o.name for o in new],'tracks':tracks,'hierarchy':hierarchy,'checks':checks,'source_sha256':sourcehash,'materials':[m.name for m in [AL,MILL,CU,MASK,RUBBER,WIRE,BRAID,RED]],'layer_roots':rootnames,'passive_count':passive_count}
(O/'integration-config.json').write_text(json.dumps(config,indent=2));(O/'surface-validation.json').write_text(json.dumps({'planar_corrections':surface_report},indent=2));s['interior_v30_notes']='Layers 2, 3 and 4 refined inside V29. Visual study with native materials, docked service wiring and independent detail clips.'
s.frame_set(400);bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-interior-v30.blend'));print('V30_MASTER',checks,'new_parts',len(new),'passives',passive_count,flush=True)
