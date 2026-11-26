"""Reference-led underside: fitted service panel, downward optics and detailed arm roots."""
import bpy,math,ast,bmesh,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for filename,names in [('polish_exterior_v05.py',['material','finish','ring','curve','box','cyl','grain']),('refine_front_arms_v09.py',['mesh','lathe'])]:
 for node in ast.parse((ROOT/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
BLACK=bpy.data.materials['Graphite'];POD=bpy.data.materials['V09 satin molded graphite'];DARK=bpy.data.materials['V09 deep recess'];BOLT=bpy.data.materials['V09 fastener gunmetal'];EDGE=bpy.data.materials['V09 machined edge'];GOLD=bpy.data.materials['V09 champagne blade tip']
PANEL=material('V14 fine textured access panels',(.013,.016,.019),.08,.46);grain(PANEL,720,.09,.000012,(.43,.48))
OPTIC=material('V14 downward optical coating',(.005,.015,.018),.32,.13);p=OPTIC.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.55;p.inputs['Coat Roughness'].default_value=.10
for ob in list(bpy.data.objects):
 if ob.name.startswith(('BELLY_','DOWN_SENSOR_')):bpy.data.objects.remove(ob,do_unlink=True)
cradle=bpy.data.objects['BODY_CRADLE'];bpy.context.view_layer.objects.active=cradle
for mod in list(cradle.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.update()

def sampler(ob):
 deps=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(ob,deps);world=ob.matrix_world.copy();inv=world.inverted()
 def sample(x,y):
  hit,n,i,d=tree.ray_cast(inv@Vector((x,y,-.10)),inv.to_3x3()@Vector((0,0,1)),1)
  if hit is None:raise ValueError(('Underside fit missed',ob.name,x,y))
  return (world@hit).z
 return sample
floor=sampler(cradle)

def rounded(w,l,r,cx=0,cy=0,steps=12):
 pts=[]
 for x,y,a0 in [(w/2-r,l/2-r,0),(-w/2+r,l/2-r,90),(-w/2+r,-l/2+r,180),(w/2-r,-l/2+r,270)]:
  for j in range(steps+1):a=math.radians(a0+j*90/steps);pts.append((cx+x+r*math.cos(a),cy+y+r*math.sin(a)))
 return pts

def densify(pts,counts=None):
 dense=[]
 for i,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
  steps=counts[i] if counts is not None else max(1,math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/.0018))
  dense.extend((a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps) for j in range(steps))
 return dense

def slab(name,pts,z0,z1,mat,bevel=0):
 n=len(pts);vs=[(x,y,z) for z in [z0,z1] for x,y in pts];fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 return mesh(name,vs,fs,mat,bevel=bevel)

def fitted(name,pts,zfn,mat,thickness=.0012,layers=18):
 # Dense concentric quad strips follow the actual curved belly, including the middle of each panel.
 pts=densify(pts);n=len(pts);cx=sum(p[0] for p in pts)/n;cy=sum(p[1] for p in pts)/n;xy=[(cx,cy)]
 for k in range(1,layers+1):
  t=k/layers;xy.extend((cx+(x-cx)*t,cy+(y-cy)*t) for x,y in pts)
 count=len(xy);vs=[(x,y,zfn(x,y)+dz) for dz in [0,thickness] for x,y in xy];fs=[]
 front=[(0,1+(j+1)%n,1+j) for j in range(n)]
 for k in range(layers-1):
  a=1+k*n;b=a+n
  for j in range(n):q=(j+1)%n;front.append((a+j,a+q,b+q,b+j))
 fs.extend(front);fs.extend(tuple(count+i for i in reversed(f)) for f in front)
 last=1+(layers-1)*n
 for j in range(n):q=(j+1)%n;fs.append((last+j,last+q,count+last+q,count+last+j))
 ob=mesh(name,vs,fs,mat,bevel=.00009)
 for mod in list(ob.modifiers):
  if mod.type=='WEIGHTED_NORMAL':ob.modifiers.remove(mod)
 return ob

def subtract(ob,cut):
 bpy.context.view_layer.objects.active=ob
 mod=ob.modifiers.new('Physical underside recess','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
 while list(ob.modifiers).index(mod)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
 bpy.ops.object.modifier_apply(modifier=mod.name)
 # Boolean cutters must not introduce empty material slots.
 mat=ob.data.materials[0];ob.data.materials.clear();ob.data.materials.append(mat)
 for p in ob.data.polygons:p.material_index=0

def rect_cut(objects,w,l,r,x,y,z0=.025,z1=.069):
 cut=slab('TEMP_BOTTOM_CUT',rounded(w,l,r,x,y),z0,z1,DARK)
 for mod in list(cut.modifiers):cut.modifiers.remove(mod)
 for ob in objects:subtract(ob,cut)
 bpy.data.objects.remove(cut,do_unlink=True)

def round_cut(objects,x,y,r,z0,z1,vertices=96):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=z1-z0,location=(x,y,(z0+z1)/2));cut=bpy.context.object
 for ob in objects:subtract(ob,cut)
 bpy.data.objects.remove(cut,do_unlink=True)

def bent_rim(name,op,ip,zfn,depth,mat):
 assert len(op)==len(ip)
 counts=[max(1,math.ceil(max(math.dist(op[i],op[(i+1)%len(op)]),math.dist(ip[i],ip[(i+1)%len(ip)]))/.0018)) for i in range(len(op))]
 op=densify(op,counts);ip=densify(ip,counts);n=len(op);vs=[]
 for pts,dz in [(op,0),(op,depth),(ip,0),(ip,depth)]:vs.extend((x,y,zfn(x,y)+dz) for x,y in pts)
 fs=[]
 for j in range(n):q=(j+1)%n;fs.extend([(j,q,n+q,n+j),(2*n+q,2*n+j,3*n+j,3*n+q),(j,2*n+j,2*n+q,q),(n+j,n+q,3*n+q,3*n+j)])
 assert all(0<=v<len(vs) for f in fs for v in f),(name,len(vs))
 ob=mesh(name,vs,fs,mat,bevel=.00008)
 for mod in list(ob.modifiers):
  if mod.type=='WEIGHTED_NORMAL':ob.modifiers.remove(mod)
 return ob

# Fitted central spine with an actual aperture and a separate removable service panel.
spine=fitted('BELLY_SPINE',rounded(.087,.198,.013,0,-.015),lambda x,y:floor(x,y)-.00055,POD)
rect_cut([cradle,spine],.0648,.1248,.0085,0,-.012,z1=.063)
door=fitted('BELLY_SERVICE_PANEL',rounded(.0638,.1238,.008,0,-.012),lambda x,y:floor(x,y)-.00058,PANEL,thickness=.0020)
# Dark recessed return behind the service-panel seam; the opening remains real.
bent_rim('BELLY_PANEL_REVEAL',rounded(.06475,.12475,.00845,0,-.012),rounded(.0636,.1236,.0079,0,-.012),lambda x,y:floor(x,y)+.0001,.0018,DARK)
# Shaped surround groups the two optical modules into one coherent sensor bridge.
bridge=fitted('BELLY_SENSOR_BRIDGE',rounded(.084,.030,.011,0,.0695),lambda x,y:floor(x,y)-.00080,POD)
for sign in [-1,1]:
 x=sign*.025;y=.0695
 round_cut([cradle,spine,bridge],x,y,.0096,.025,.062)
 samples=[floor(x+.0108*math.cos(j*math.tau/32),y+.0108*math.sin(j*math.tau/32)) for j in range(32)];face=min(samples)-.00085
 # Hollow stepped housing faces downward, with concentric baffles and a dark coated front element.
 lathe('DOWN_SENSOR_HOUSING_'+str(sign),[(.0108,face+.0014),(.0105,face),(.0093,face-.00012),(.0075,face+.0003),(.0074,face+.0045),(.0103,face+.0045)],(x,y,0),POD,root)
 ring('DOWN_SENSOR_EDGE_'+str(sign),(x,y,face+.00022),.00915,.00865,.00032,BOLT)
 ring('DOWN_SENSOR_RETAINING_'+str(sign),(x,y,face+.00085),.00855,.00685,.0011,DARK)
 for j,r in enumerate([.00675,.00570,.00485]):ring('DOWN_SENSOR_BAFFLE_'+str(sign)+'_'+str(j),(x,y,face+.00105+j*.00048),r,r-.00040,.00035,BOLT if j==0 else DARK)
 cyl('DOWN_SENSOR_DARK_BACK_'+str(sign),(x,y,face+.0030),.0067,.001,DARK)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(x,y,face+.0017));ob=bpy.context.object;ob.scale=(.00455,.00455,.00065);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(ob,'DOWN_SENSOR_COATED_GLASS_'+str(sign),OPTIC)
 ring('DOWN_SENSOR_INNER_TRACE_'+str(sign),(x,y,face+.00112),.0038,.00364,.00012,DARK)

# Recessed underside service connector and its two curved cooling slots.
porty=.1215;pad=fitted('BELLY_PORT_PAD',rounded(.027,.022,.0045,0,porty),lambda x,y:floor(x,y)-.00042,POD)
rect_cut([cradle,pad],.0164,.0073,.0032,0,porty,z1=.075)
portface=min(floor(x,porty+dy) for x in [-.009,0,.009] for dy in [-.004,0,.004])-.0007
for name,outer,inner,z,depth,mat in [('MOUNT',(.0198,.0113,.0038),(.0159,.0068,.0029),portface,.003,POD),('LINER',(.0159,.0068,.0029),(.0134,.0048,.0021),portface+.00040,.003,DARK),('METAL',(.0138,.0052,.00225),(.01265,.00415,.0017),portface+.00062,.0028,EDGE)]:
 bent_rim('BELLY_PORT_'+name,rounded(*outer,0,porty),rounded(*inner,0,porty),lambda x,y,z=z:z,depth,mat)
slab('BELLY_PORT_CAVITY',rounded(.0145,.0058,.0024,0,porty),portface+.0040,portface+.0048,DARK)
slab('BELLY_PORT_TONGUE',rounded(.0094,.00072,.00030,0,porty),portface+.0016,portface+.0038,DARK)
for k in range(10):
 xx=(k-4.5)*.00077
 for sign in [-1,1]:box('BELLY_PORT_CONTACT_'+str(k)+'_'+str(sign),(xx,porty+sign*.00039,portface+.00255),(.00031,.00010,.0015),GOLD,bevel=.00003)
# Note: contacts and cavity are constructed once; the layer loop above only builds its three nested rims.
for sign in [-1,1]:
 x=sign*.0328;y=.1215;w=.019;l=.0036
 rect_cut([cradle],w,l,.0017,x,y,z1=.074)
 bent_rim('BELLY_VENT_TUNNEL_'+str(sign),rounded(w+.0004,l+.0004,.0019,x,y),rounded(w-.0008,l-.0008,.0013,x,y),lambda xx,yy:floor(xx,yy)-.00015,.0040,POD)
 fitted('BELLY_VENT_BACK_'+str(sign),rounded(w-.0002,l-.0002,.0016,x,y),lambda xx,yy:floor(xx,yy)+.0035,DARK,thickness=.0005,layers=5)
 for j in range(4):
  xx=x+(j-1.5)*.0038;box('BELLY_VENT_BAFFLE_'+str(sign)+'_'+str(j),(xx,y,floor(xx,y)+.0026),(.0004,.0026,.0011),DARK,bevel=.0001)

# Cut panel rims retain their dense surface normals without tiny Boolean-edge bevel artifacts.
for panel in [spine,bridge]:
 for mod in list(panel.modifiers):
  if mod.type=='BEVEL':panel.modifiers.remove(mod)

# Small front belly access returns and molded bumper ribs, as on the reference.
for sign in [-1,1]:
 pts=rounded(.0115,.024,.0038,sign*.038,-.099)
 fitted('BELLY_FRONT_ACCESS_'+str(sign),pts,lambda x,y:floor(x,y)-.00036,PANEL,thickness=.0009,layers=7)
 pts=rounded(.0035,.021,.0017,sign*.033,-.116)
 fitted('BELLY_BUMPER_RIB_'+str(sign),pts,lambda x,y:floor(x,y)-.0011,POD,thickness=.0015,layers=7)

# Underside details on all four arm-to-body connections and long arm inserts.
for tag,sign,front in [('FL',-1,True),('FR',1,True),('RL',-1,False),('RR',1,False)]:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];hinge=arm.location.copy();pivot=Vector((hinge.x,hinge.y,0));motor=Vector((sign*.165,-.140 if front else .140,0));direction=(motor-pivot).normalized();across=Vector((-direction.y,direction.x,0));length=(motor-pivot).length
 receiver=bpy.data.objects['HINGE_CHASSIS_MOUNT_'+tag] if front else cradle
 sample_mount=sampler(receiver);beam=bpy.data.objects['ARM_'+tag];sample_beam=sampler(beam)
 def point(d,u):
  p=pivot+direction*d+across*u;return p.x,p.y
 z0=sample_mount(hinge.x,hinge.y)
 round_cut([receiver],hinge.x,hinge.y,.0045,z0-.0008,z0+.0045)
 ring('HINGE_UNDER_COUNTERBORE_'+tag,(hinge.x,hinge.y,z0+.0010),.0044,.00375,.0017,DARK)
 ring('HINGE_UNDER_WASHER_'+tag,(hinge.x,hinge.y,z0+.00082),.0038,.0027,.00040,EDGE)
 bolt=cyl('HINGE_UNDER_SCREW_'+tag,(hinge.x,hinge.y,z0+.00155),.00275,.00110,BOLT)
 round_cut([bolt],hinge.x,hinge.y,.00115,z0+.0007,z0+.00155,6)
 cyl('HINGE_UNDER_HEX_'+tag,(hinge.x,hinge.y,z0+.00156),.00112,.00012,DARK,vertices=6)
 # Small paired keeper pads belong to the fixed mount and stay clear of the rotating arm beam.
 for k,side in enumerate([-1,1]):
  local=rounded(.0058,.0034,.0008,.0035,side*.0084);pts=[point(d,u) for d,u in local]
  fitted('HINGE_UNDER_KEEPER_'+tag+'_'+str(k),pts,lambda x,y:sample_mount(x,y)-.00045,POD,thickness=.0010,layers=6)
 # A fine curved parting line follows the outer half of the lower bearing cup.
 pts=[]
 for j in range(49):
  a=-math.pi/2+math.pi*j/48;x,y=point(.0117*math.cos(a),.0117*math.sin(a));pts.append((x,y,sample_mount(x,y)-.0001))
 curve('HINGE_UNDER_PARTING_'+tag,pts,.00010,DARK,root)
 # Long recessed-looking molded inserts follow the tapered arm's actual lower surface.
 d0=.032;d1=length-.023;mid=(d0+d1)/2;panel_length=d1-d0
 local=rounded(panel_length,.0134,.0023,mid,0);pts=[point(d,u) for d,u in local]
 frame=fitted('ARM_UNDER_FRAME_'+tag,pts,lambda x,y:sample_beam(x,y)-.00035,DARK,thickness=.00065,layers=10)
 local=rounded(panel_length-.0010,.0124,.0019,mid,0);pts=[point(d,u) for d,u in local]
 insert=fitted('ARM_UNDER_INSERT_'+tag,pts,lambda x,y:sample_beam(x,y)-.00020,PANEL,thickness=.00065,layers=10)
 for ob in [frame,insert]:ob.parent=arm;ob.matrix_parent_inverse=Matrix.Translation(-hinge)

# Preserve the receiver finishes after all real recess cuts.
for ob in [cradle]+[bpy.data.objects['HINGE_CHASSIS_MOUNT_'+tag] for tag in ['FL','FR']]:
 mat=BLACK if ob==cradle else POD;ob.data.materials.clear();ob.data.materials.append(mat)
 for p in ob.data.polygons:
  p.material_index=0
  p.use_smooth=True
  if ob!=cradle and abs(p.normal.z)>.999999:p.use_smooth=False
cradle['underside_refinement']='V14: service door, sensor apertures, connector, vents and recessed pivot hardware'
# Dedicated underside lighting is only used for these inspection renders.
fill=bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'];fill.location=(-.18,-.14,-.22);fill.data.energy=1.8;fill.data.size=.22;fill.rotation_euler=(Vector((0,0,.050))-fill.location).to_track_quat('-Z','Y').to_euler();fill.hide_render=True
for name,loc,target,scale in [('underside_full',(0,.010,-.60),(0,.010,.06),.76),('underside_body',(0,.001,-.48),(0,.001,.060),.42),('underside_oblique',(.25,.20,-.32),(0,.020,.055),.385),('underside_sensors',(.018,.072,-.24),(0,.070,.045),.119),('underside_rear_joint',(.20,.025,-.15),(.075,.087,.055),.132),('underside_front_joint',(.22,-.14,-.15),(.092,-.095,.06),.145)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;ob=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(ob);ob.location=loc;forward=(Vector(target)-ob.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward).normalized();ob.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=20;s.render.resolution_percentage=70
views=['underside_body','underside_rear_joint','underside_sensors'] if preview else ['hero','underside_full','underside_body','underside_oblique','underside_sensors','underside_rear_joint','underside_front_joint']
for name in views:
 s.render.resolution_x=1200 if name=='underside_body' else 1536;s.render.resolution_y=1500 if name=='underside_body' else 1024
 s.camera=bpy.data.objects['CAM_'+name];under=name!='hero';bpy.data.objects['STUDIO_GROUND'].hide_render=under;fill.hide_render=not under;s.render.filepath=str(ROOT/'renders/exterior-v14'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V14_COMPLETE')
