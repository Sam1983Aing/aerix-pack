"""V29: detailed serviceable battery cartridge inside the preserved V28 drone."""
import bpy,bmesh,math,json,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];O=R/'renders/battery-v29';O.mkdir(exist_ok=True)
SOURCE=R/'blender/aerix-interior-v28.blend';sourcehash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(400);battery=bpy.data.objects['BATTERY_ROOT'];bpy.context.view_layer.update()
oldparts=[o.name for o in battery.children_recursive if o.type in {'MESH','FONT','CURVE'}]
def snapshot():
 d=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type not in {'MESH','FONT','CURVE'} or o.hide_render or o.name in oldparts or o.name.startswith('BAT29_') or o.name=='STUDIO_GROUND':continue
  e=o.evaluated_get(d);m=e.to_mesh();out[o.name]=hashlib.sha256(repr(([tuple(e.matrix_world@v.co) for v in m.vertices],[tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],[q.name if q else None for q in m.materials])).encode()).hexdigest();e.to_mesh_clear()
 return out
before=snapshot();roots={o.name:o for o in battery.children_recursive if o.type=='EMPTY'}
for name in oldparts:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for o in roots.values():o.animation_data_clear();o.location=(0,0,0)
lid=roots['BATTERY_LID_ROOT'];cells=[roots[f'CELL_{i+1}_ROOT'] for i in range(4)]
def group(n):o=bpy.data.objects.new(n,None);s.collection.objects.link(o);o.parent=battery;return o
side=group('BATTERY_SIDE_COVER_ROOT');BMS=group('BATTERY_BMS_ROOT');loom=group('BATTERY_LOOM_ROOT');new=[]
# All modeling dimensions below are mm, relative to V28 cartridge center and lower face.
def P(p):return (p[0]/1000,(p[1]+3.12)/1000,(p[2]+78)/1000)
def make_mat(name,col,metal,rough,grain=None):
 m=bpy.data.materials.new('V29 '+name);m.diffuse_color=(*col,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if grain:
  scale,depth,low,high=grain;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.65
  coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],tex.inputs['Vector'])
  ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.15;ramp.inputs['From Max'].default_value=.85;ramp.inputs['To Min'].default_value=low;ramp.inputs['To Max'].default_value=high;l.new(tex.outputs['Fac'],ramp.inputs['Value']);l.new(ramp.outputs['Result'],p.inputs['Roughness'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=depth;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
CASE=make_mat('microtextured graphite',(.011,.016,.021),.08,.40,(6000,.000020,.35,.47))
EDGE=make_mat('satin recessed edge',(.012,.016,.020),.26,.30)
RUBBER=make_mat('retention elastomer',(.007,.010,.013),.02,.52,(19000,.000006,.46,.57))
FOIL=make_mat('laminated aluminum foil',(.52,.56,.60),.88,.27,(21000,.000004,.23,.32));p=FOIL.node_tree.nodes.get('Principled BSDF');
# Isotropic laminate avoids a false radial highlight from the pouch's radial topology.
if p.inputs.get('Anisotropic'):p.inputs['Anisotropic'].default_value=0.0
GOLD=make_mat('gold plated contact',(.63,.37,.085),.83,.25)
STEEL=make_mat('satin fastener',(.20,.24,.28),.88,.29)
PCB=make_mat('BMS green soldermask',(.009,.052,.031),.15,.32,(21000,.000002,.29,.38))
CHIP=make_mat('molded chip package',(.008,.012,.016),.03,.42,(25000,.000002,.38,.46))
CERAMIC=make_mat('capacitor ceramic',(.29,.26,.20),.05,.41)
SOLDER=make_mat('solder fillet',(.44,.48,.51),.87,.22)
WIRE=make_mat('black wire insulation',(.008,.012,.016),0,.39,(17000,.000003,.35,.43))
RED=make_mat('muted red silicone',(.33,.015,.013),0,.4,(15000,.000003,.37,.44))
COPPER=make_mat('cell terminal copper',(.53,.22,.062),.82,.27)
AMBER=make_mat('amber polyimide insulation',(.39,.14,.016),.16,.35)
INK=make_mat('laser marking',(.43,.49,.53),.18,.46)
WHITE=make_mat('connector polymer',(.57,.56,.48),.02,.37)
TRACE=make_mat('covered BMS traces',(.019,.078,.049),.22,.35)

def finish(o,n,mat,parent=battery,bevel=0,segments=4):
 o.name='BAT29_'+n;o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.data.materials.append(mat)
 if bevel:m=o.modifiers.new('Precision edge radius','BEVEL');m.width=bevel/1000;m.segments=segments
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
  m=o.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=45
 new.append(o);return o

def box(n,center,size,mat=CASE,parent=battery,bevel=.4):
 bpy.ops.mesh.primitive_cube_add(size=1,location=P(center));o=bpy.context.object;o.dimensions=[v/1000 for v in size];bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,mat,parent,bevel)
def cyl(n,center,r,depth,mat=STEEL,parent=battery,axis='Z',verts=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r/1000,depth=depth/1000,location=P(center));o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return finish(o,n,mat,parent,.09)
def apply(o):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
def cut(o,cutter):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Machined opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);new.remove(cutter);bpy.data.objects.remove(cutter,do_unlink=True)
def norm(o):
 m=o.modifiers.new('Finished face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50

def curve(n,points,r,mat=WIRE,parent=loom):
 d=bpy.data.curves.new('BAT29_'+n,'CURVE');d.dimensions='3D';d.resolution_u=20;d.bevel_depth=r/1000;d.bevel_resolution=4;sp=d.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for q,p in zip(sp.bezier_points,points):q.co=P(p);q.handle_left_type='AUTO';q.handle_right_type='AUTO'
 o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);finish(o,n,mat,parent);return o

def outline(w,l,r,steps=16):
 out=[]
 for cx,cy,angle in [(w/2-r,l/2-r,0),(-w/2+r,l/2-r,90),(-w/2+r,-l/2+r,180),(w/2-r,-l/2+r,270)]:
  for j in range(steps):a=math.radians(angle+j*90/steps);out.append((cx+r*math.cos(a),cy+r*math.sin(a)))
 return out

def ring(n,w,l,rad,z,h,width,mat,parent=battery):
 outer=outline(w,l,rad);inner=outline(w-2*width,l-2*width,max(.1,rad-width));N=len(outer);v=[P((x,y,zz)) for zz in [z-h/2,z+h/2] for loop in [outer,inner] for x,y in loop];f=[]
 for j in range(N):q=(j+1)%N;f.extend([(j,q,2*N+q,2*N+j),(N+q,N+j,3*N+j,3*N+q),(2*N+j,2*N+q,3*N+q,3*N+j),(q,j,N+j,N+q)])
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);s.collection.objects.link(o);return finish(o,n,mat,parent,.04)

def text(n,body,pos,size,parent=lid):
 d=bpy.data.curves.new(n,'FONT');d.body=body;d.size=size/1000;d.align_x='CENTER';d.extrude=.000008;d.bevel_depth=.000003;o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=P(pos);return finish(o,n,INK,parent)
# Continuous hollow shell and removable side cover. V28's outer envelope is retained.
tray=box('CARTRIDGE_TRAY',(0,0,12.15),(80,149.6,24.3),CASE,bevel=1.5);apply(tray)
cavity=box('CAVITY_CUT',(0,0,20),(76.4,146.0,37.2),EDGE,bevel=.9);apply(cavity);cut(tray,cavity)
window=box('SIDE_SERVICE_CUT',(40,0,17),(6,127,28.4),EDGE,bevel=.65);apply(window);cut(tray,window)
# Side opening lower sill at 2.8 mm; cover leaves a fine 0.15 mm reveal.
cover=box('SIDE_SERVICE_COVER',(39.40,0,13.6),(1.20,126.65,21.3),CASE,side,.5);apply(cover)
# A slim inner return supports the gasket behind the removable service panel.
for y in [-64,64]:box('SIDE_PANEL_SEAT',(38.2,y,13.4),(2.6,2.0,20.6),EDGE)
box('SIDE_PANEL_BOTTOM_RETURN',(38.4,0,2.8),(2.6,125,.9),EDGE)
for y in [-62.2,62.2]:box('SIDE_PANEL_SEAL_END',(38.85,y,13.6),(.45,.55,20.9),RUBBER)
for z in [3.35,23.85]:box('SIDE_PANEL_SEAL_RAIL',(38.85,0,z),(.45,124.0,.45),RUBBER)
# Port opening through front shell, separate keyed socket shroud and recessed contacts.
portcut=box('PORT_CUT',(0,-74.5,11),(25.6,8,7.5),EDGE,bevel=.65);apply(portcut);cut(tray,portcut);norm(tray)
port=box('KEYED_PORT_SHROUD',(0,-75.0,11),(28.5,4.5,9.4),EDGE,bevel=.9);apply(port)
well=box('PORT_WELL',(0,-77,11),(24.2,4.2,6.8),EDGE,bevel=.45);apply(well);cut(port,well);norm(port)
box('CONTACT_CARRIER',(0,-75.25,11),(23.5,.8,6.3),CHIP,bevel=.35)
# Asymmetric upper key distinguishes the connector's orientation.
box('PORT_POLARIZING_KEY',(-10.6,-76.4,13.4),(2.0,1.3,1.0),EDGE,bevel=.15)
for i in range(8):
 x=(i-3.5)*2.5
 box('GOLD_CONTACT_'+str(i),(x,-75.78,11),(.88,.33,4.1),GOLD,bevel=.19)
 box('CONTACT_BACK_'+str(i),(x,-73.0,11),(.65,1.9,1.0),COPPER,bevel=.16)
# Lid, shallow inset channels, under-lid gasket and genuine recessed screw sockets.
plate=box('TOP_LID',(0,0,25.55),(81.0,150.6,1.90),CASE,lid,.85);apply(plate)
for x in [-18.5,18.5]:
 groove=box('LID_CHANNEL_CUT',(x,1.5,26.55),(.34,116,.38),EDGE,lid,.16);apply(groove);cut(plate,groove)
for x in [-37.6,37.6]:box('LID_LOCATOR_SIDE',(x,0,24.45),(.65,116,.65),EDGE,lid,.20)
for y in [-72.2,72.2]:box('LID_LOCATOR_END',(0,y,24.45),(63,.65,.65),EDGE,lid,.20)
ring('LID_COMPRESSION_GASKET',78.1,147.8,1.5,24.43,.32,.55,RUBBER)
# Screw mesh with actual six-lobed recess, no painted fake circles.
def screw(n,x,y,z,parent=lid,axis='Z'):
 head=cyl(n,(x,y,z),1.45,.58,STEEL,parent,axis);apply(head)
 v=[];N=72
 for zz in [-.16,.5]:
  # vertices authored below using the requested axis
  for k in range(N):
   a=k*math.tau/N;r=.66+.13*math.cos(6*a);u=r*math.cos(a);vv=r*math.sin(a)
   v.append(P((x+u,y+vv,z+zz) if axis=='Z' else (x+zz,y+u,z+vv)))
 f=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 me=bpy.data.meshes.new('socket');me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('socket',me);s.collection.objects.link(o);finish(o,'SOCKET_CUT',EDGE,parent);cut(head,o);norm(head)
 # Captive shaft extends from head into its seat.
 if axis=='Z':cyl(n+'_SHAFT',(x,y,z-1.35),.70,2.3,STEEL,parent)
 return head
for x in [-35.5,35.5]:
 for y in [-68,68]:
  bore=cyl('LID_COUNTERBORE',(x,y,26.52),1.85,1.2,EDGE,lid);apply(bore);cut(plate,bore)
  screw('LID_TORX',x,y,26.08)
  cyl('LID_BOSS_PILLAR',(x,y,9.4),1.75,16.0,CASE)
  boss=cyl('LID_BOSS',(x,y,20.7),2.6,7.2,CASE);apply(boss)
  hole=cyl('BOSS_BORE',(x,y,24),.86,6,EDGE);apply(hole);cut(boss,hole);norm(boss)
  cyl('BOSS_INSERT',(x,y,23.35),1.02,1.2,GOLD)
for y in [-56,56]:
 bore=cyl('SIDE_COUNTERBORE',(40.1,y,13.6),1.7,1.2,EDGE,side,'X');apply(bore);cut(cover,bore);screw('SIDE_TORX',39.77,y,13.6,side,'X')
norm(cover);norm(plate)
text('WORDMARK','AERIX',(0,-18,26.52),5.0)
text('SERVICE_MARK','POWER MODULE  /  01',(0,40,26.52),1.8)
# Bottom pads and left/right guides support four independently removable pouch cells.
box('CELL_FOAM_FLOOR',(0,6,1.85),(67.0,119.5,.9),RUBBER,bevel=.4)
for x in [-34.0,34.0]:box('CELL_GUIDE',(x,6,6.0),(1.0,120,8.0),EDGE,bevel=.35)
# Finite foil pouch with rounded shoulders and restrained crimp wrinkles confined to its margin.
def pouch(index,parent):
 zc=4.2+4.5*index;yc=6.0;raw=outline(66,118,2.2,16);profile=[]
 for a,b in zip(raw,raw[1:]+raw[:1]):
  count=max(1,math.ceil(math.dist(a,b)/1.4))
  for j in range(count):profile.append((a[0]+(b[0]-a[0])*j/count,a[1]+(b[1]-a[1])*j/count))
 N=len(profile);ts=sorted(set([.003+.897*k/24 for k in range(25)]+[.90+.10*k/32 for k in range(33)]));rings=len(ts)-1;v=[]
 for sideZ in [1,-1]:
  for k in range(rings+1):
   t=ts[k]
   for j,(x,y) in enumerate(profile):
    a=math.tau*j/N;distance=min(33-abs(x*t),59-abs(y*t));edge=max(0,min(1,(2.4-distance)/1.8));edge=edge*edge*(3-2*edge);height=1.82*(1-edge)+.24*edge
    wrinkle=.050*math.sin(a*83+index*.7)*math.sin(a*29+.7)*max(0,1-distance/4)*(1-.6*edge)
    v.append(P((x*t,y*t+yc,zc+sideZ*(height+wrinkle))))
 f=[];C=(rings+1)*N
 for offset,reverse in [(0,False),(C,True)]:
  f.append(tuple(offset+j for j in (range(N-1,-1,-1) if not reverse else range(N))))
  for k in range(rings):
   for j in range(N):q=(j+1)%N;face=(offset+k*N+j,offset+k*N+q,offset+(k+1)*N+q,offset+(k+1)*N+j);f.append(tuple(reversed(face)) if reverse else face)
 for j in range(N):q=(j+1)%N;f.append((rings*N+j,C+rings*N+j,C+rings*N+q,rings*N+q))
 me=bpy.data.meshes.new('Pouch foil');me.from_pydata(v,[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new('Pouch',me);s.collection.objects.link(o);finish(o,'POUCH_CELL_'+str(index+1),FOIL,parent)
 for m in list(o.modifiers):o.modifiers.remove(m)
 # Closed bands conform to the foil shoulder instead of floating over its edge.
 for yy in [-22,38]:
  cross=[]
  for signZ in [1,-1]:
   xs=[-33+66*j/100 for j in range(101)]
   if signZ<0:xs.reverse()
   for xx in xs:
    dist=33-abs(xx);t=max(0,min(1,(2.4-dist)/1.8));t=t*t*(3-2*t);h=1.82*(1-t)+.24*t
    cross.append((xx,signZ*(h+.055)))
   cross.append((33.10 if signZ>0 else -33.10,0))
  count=len(cross);verts=[]
  for yband in [yy-3,yy+3]:
   for outer in [False,True]:
    for xx,zz in cross:verts.append(P((xx+(math.copysign(.055,xx) if outer else 0),yband,zc+zz+(math.copysign(.14,zz) if outer else 0))))
  faces=[]
  for j in range(count):
   q=(j+1)%count;faces.extend([(j,q,2*count+q,2*count+j),(count+q,count+j,3*count+j,3*count+q),(q,j,count+j,count+q),(2*count+j,2*count+q,3*count+q,3*count+j)])
  me=bpy.data.meshes.new('Conforming band');me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new('band',me);s.collection.objects.link(o);finish(o,'CELL_BAND_WRAP',RUBBER,parent)
 for x in [-10,10]:
  box('CELL_TERMINAL',(x,-55.0,zc),(4.2,6.0,.22),COPPER,parent,.10)
  box('TAB_INSULATION',(x,-52.0,zc+.17),(4.5,2.4,.16),AMBER,parent,.12)
  # Stationary split contact shoe. The terminal slides rearward out before lifting.
  for dz in [-.22,.22]:box('CELL_CONTACT_SPRING',(x,-57.45,zc+dz),(4.5,2.1,.18),GOLD,BMS,.10)
  box('CELL_CONTACT_INSULATOR',(x,-58.45,zc),(5.4,.80,1.25),CHIP,BMS,.18)
  box('CELL_CONTACT_BACK',(x,-58.95,zc),(3.0,.50,.55),COPPER,BMS,.10)
for i,g in enumerate(cells):pouch(i,g)
# Battery management board fits the front bay, ahead of every moving pouch-cell tab.
pcb=box('BMS_PCB',(-2,-66.05,15.2),(62,11.5,1.2),PCB,BMS,.45)
for x in [-28,24]:
 cyl('BMS_SUPPORT',(x,-66.05,13.3),1.4,2.6,EDGE,BMS)
 cyl('BMS_FIXING',(x,-66.05,16.1),.82,.50,STEEL,BMS)
for x,w in [(-18,6.4),(-7,6.6),(5,5.0),(15,4.5)]:
 box('BMS_CHIP',(x,-65.0,17.0),(w,4.0,1.8),CHIP,BMS,.22)
 for sign in [-1,1]:
  for k in range(5):box('BMS_IC_LEAD',(x+(k-2)*w/6,-65.0+sign*2.2,16.15),(.36,.90,.22),SOLDER,BMS,.08)
random.seed(29)
for row,y in enumerate([-70.1,-61.95]):
 for i in range(18):
  x=-26+i*2.72
  if i in [0,17]:continue
  box('BMS_PASSIVE',(x,y,16.17),(.9,1.20,.62),CERAMIC if i%3 else CHIP,BMS,.08)
  for sign in [-1,1]:box('BMS_SOLDER',(x,y+sign*.60,15.95),(.91,.32,.23),SOLDER,BMS,.08)
for i in range(6):cyl('BMS_TEST_PAD',(-23+i*7.4,-68.7,15.86),.36,.08,GOLD,BMS)
for i in range(7):
 x=-24+i*6.5;curve('BMS_MASKED_TRACE',[(x,-68.9,15.81),(x+1.6,-68.9,15.81),(x+2.7,-67.8,15.81),(x+2.7,-67,15.81)],.07,TRACE,BMS)
# Small front power terminals and right-side keyed harness plug.
for x in [-25,-20]:
 box('POWER_TERMINAL',(x,-70.0,17.2),(3.0,2.3,2.1),CHIP,BMS,.35)
 box('POWER_TERMINAL_CONTACT',(x,-71.1,17.2),(1.2,.3,.8),COPPER,BMS,.12)
plug=box('BMS_BALANCE_SOCKET',(27.6,-64,17.0),(5.0,5.1,2.5),WHITE,BMS,.35)
box('BALANCE_PLUG_INSERT',(28.1,-60.9,17),(4.2,1.5,1.6),CHIP,BMS,.18)
for i in range(4):box('BALANCE_SOCKET_PIN',(26.7+i*.75,-61.8,17),(.3,1.8,.3),GOLD,BMS,.08)
curve('POWER_RED',[(3.7,-73,11),(-9,-72.8,11),(-17,-72.4,13),(-20,-71.1,17.2)],.62,RED)
curve('POWER_BLACK',[(-3.7,-73,11),(-15,-73,11),(-24,-72.8,13),(-25,-71.1,17.2)],.62,WIRE)
for x in [-8,-15]:box('POWER_LEAD_CLIP',(x,-72.25,11.2),(2.5,2.1,1.0),RUBBER,loom,.3)
# Four clipped sense wires connect the fixed contact shoes to the management board.
for i in range(4):
 z=4.2+4.5*i;xx=26.7+i*.75
 curve('CELL_SENSE_WIRE_'+str(i),[(10,-59.2,z),(19+i*1.0,-59.35,z),(31.4+i*.62,-57,z),(33.8+i*.60,-54.5,12.5),(32.8+i*.35,-59.0,16.9),(xx,-60.2,17)],.26,WIRE)
# Two long service/temperature leads follow the side channel to a seated rear sensor.
for i,mat in enumerate([WIRE,RED]):
 curve('SIDE_SERVICE_LEAD_'+str(i),[(29.0,-63,16.0),(35.6+i*.9,-52,6.0),(35.6+i*.9,-28,4.0),(35.6+i*.9,24,4.0),(35.6+i*.9,59,2.0),(31.0+i*.7,64.0,2.0),(29.0+i*.7,69.7,2.0),(30+i*.9,70.4,5.5)],.36,mat)
for yy in [-37,-8,24,50]:box('SIDE_LOOM_CLIP',(36.1,yy,4.3),(3.4,3.2,1.7),RUBBER,loom,.5)
box('REAR_TEMPERATURE_SENSOR',(30.5,71.3,5.5),(3.5,3.0,2.0),CHIP,loom,.45)
# Small floor ribs guide the harness but do not enter the cell sweep.
for y in [-34,5,43]:box('HARNESS_CHANNEL_SEAT',(36.2,y,2.6),(3.6,10,.75),EDGE)
# Keep machined planar faces exactly flat after booleans; smooth their adjoining bevels.
# Area-weighted normals alone can tilt the fragmented wall beside the connector.
normal_report=[]
for o in [tray,cover,plate,port]:
 apply(o);me=o.data;me.update();normals=[tuple(n.vector) for n in me.corner_normals];planes={};count=0
 for face in me.polygons:
  if face.area>2e-6 and max(abs(v) for v in face.normal)>.99999:
   axis=max(range(3),key=lambda i:abs(face.normal[i]));n=Vector([0.,0.,0.]);n[axis]=1. if face.normal[axis]>0 else -1.
   for li in face.loop_indices:
    normals[li]=tuple(n);vi=me.loops[li].vertex_index
    if vi not in planes or planes[vi][0]<face.area:planes[vi]=(face.area,n)
   count+=1
 for face in me.polygons:
  if max(abs(v) for v in face.normal)>.99999:continue
  for li in face.loop_indices:
   near=planes.get(me.loops[li].vertex_index)
   if near and face.normal.dot(near[1])>.80:normals[li]=tuple(near[1])
 me.normals_split_custom_set(normals);me.update();normal_report.append({'object':o.name,'planar_faces_corrected':count})
(O/'surface-validation.json').write_text(json.dumps({'flat_face_normals':normal_report,'foil_reflection':'Isotropic laminate; no radial tangent highlight'},indent=2))
# Closed source view first; battery reveal explicitly undocks contacts before cell lift.
tracks={}
def ease(u,a,b):
 t=max(0,min(1,(u-a)/(b-a)));return t*t*(3-2*t)
def pose(name,u):
 if name=='BATTERY_LID_ROOT':return (0,0,.110*ease(u,0,.30))
 if name=='BATTERY_SIDE_COVER_ROOT':return (.013*ease(u,.12,.35),0,0)
 if name=='SHELL_SERVICE_ROOT':return (0,0,.170*ease(u,0,.30))
 i=int(name[5])-1
 return (0,.0035*ease(u,.32,.48),(.027+i*.020)*ease(u,.50,.96))
for o in [lid,side,*cells,bpy.data.objects['SHELL_SERVICE_ROOT']]:
 o.animation_data_clear();samples=[pose(o.name,k/120) for k in range(121)];tracks[o.name]=[list(p) for p in samples]
 for fr,loc in [(1,(0,0,0)),(400,(0,0,0)),*[(551+k,p) for k,p in enumerate(samples)],(851,samples[-1]),*[(851+k,pose(o.name,1-k/120)) for k in range(1,121)]]:
  o.location=loc;o.keyframe_insert(data_path='location',frame=fr)
 o['assembled_location']=[0.,0.,0.];o['reveal_clip']='Battery_reveal';o['reveal_sequence']='lid off, side panel clears, cell contacts undock rearward, cells lift; wiring stays on tray'
 if o.animation_data and o.animation_data.action:
  for layer in o.animation_data.action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:
      for key in f.keyframe_points:key.interpolation='LINEAR'
s.frame_set(400);bpy.context.view_layer.update();after=snapshot();checks={'all_non_battery_geometry_materials_unchanged':before==after,'v28_source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sourcehash};assert all(checks.values()),checks
hierarchy={o.name:{'parent':o.parent.name if o.parent else None,'local_matrix':[v for row in o.matrix_local for v in row]} for o in s.objects if o.type not in {'LIGHT','CAMERA'} and not o.hide_render and o.name!='STUDIO_GROUND'}
(O/'battery-config.json').write_text(json.dumps({'old_battery_parts':oldparts,'new_mesh_names':[o.name for o in new],'tracks':tracks,'hierarchy':hierarchy,'checks':checks,'source_sha256':sourcehash,'materials':[m.name for m in [CASE,FOIL,RUBBER,PCB,WIRE,RED]]},indent=2))
s['battery_v29_notes']='Polished enclosed cartridge with four finite foil cells, BMS, docked terminal shoes, seated harnesses and removable side cover. Reversible service sequence; visual study.'
s.frame_set(400);bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-interior-v29.blend'));print('V29_BATTERY_MASTER',checks,'new_parts',len(new),flush=True)
