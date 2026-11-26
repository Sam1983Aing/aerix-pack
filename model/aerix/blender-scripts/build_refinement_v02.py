"""AERIX v02: fuller silhouette and first exterior refinement. Units metres; nose = -Y; up = +Z."""
import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES'; scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.render.resolution_x=1536; scene.render.resolution_y=1024; scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.18,.21,.25,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX'

def mat(name,color,metal=0,rough=.35):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
TI=mat('Titanium — provisional',(.32,.29,.245),.72,.4)
BLACK=mat('Graphite',(.013,.017,.021),.22,.32)
SILVER=mat('Machined motor alloy',(.52,.56,.59),.8,.26)
COPPER=mat('Copper accent',(.43,.23,.10),.8,.3)
GLASS=mat('Optics placeholder',(.015,.075,.09),.6,.13)
WHITE=mat('Status light',(.7,.86,1),.1,.25)
nodes=TI.node_tree.nodes; links=TI.node_tree.links
noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=1600; noise.inputs['Detail'].default_value=2
bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.13; bump.inputs['Distance'].default_value=.00007
links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
RESERVE=mat('Internal envelope',(.18,.35,.29),0,.6)

root=bpy.data.objects.new('DRONE_ROOT',None); scene.collection.objects.link(root)
def group(name,parent=root):
 o=bpy.data.objects.new(name,None); scene.collection.objects.link(o); o.parent=parent; return o

def finish(o,name,material,parent=root,bevel=0):
 o.name=name; o.data.materials.append(material); o.parent=parent
 if bevel:
  mod=o.modifiers.new('Edge radius','BEVEL'); mod.width=bevel; mod.segments=3
 for p in o.data.polygons: p.use_smooth=True
 if o.type=='MESH':
  mod=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
 return o

def box(name,loc,size,material,parent=root,bevel=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object
 o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,material,parent,bevel)

def cyl(name,loc,r,depth,material,parent=root,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc)
 o=bpy.context.object
 if axis=='Y': o.rotation_euler.x=math.pi/2
 if axis=='X': o.rotation_euler.y=math.pi/2
 return finish(o,name,material,parent,.0007)

def beam(name,a,b,width,height,material,parent=root):
 mid=(Vector(a)+Vector(b))/2; o=box(name,mid,(width,(Vector(b)-Vector(a)).length,height),material,parent,.003)
 o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Y','Z').to_euler(); return o

# Longitudinal section stations: y, half-width, seam z, crown height.
sections=[(-.139,.045,.085,.004),(-.136,.056,.085,.007),(-.127,.064,.087,.014),(-.104,.069,.089,.025),(-.067,.070,.091,.031),(-.018,.066,.093,.033),(.028,.060,.093,.033),(.060,.054,.092,.030),(.080,.054,.091,.027),(.097,.059,.090,.023),(.115,.055,.089,.019),(.134,.045,.087,.008),(.138,.038,.087,.003)]

def shell(name,upper=True):
 verts=[]; n=17
 for y,w,z,h in sections:
  for j in range(n):
   t=math.pi*j/(n-1)
   x=-w*math.cos(t)
   depth=.024+.025*max(0,1-(y/.15)**6)
   roof=(1-.20*abs(math.cos(t))**2-.80*abs(math.cos(t))**6)
   zz=z+h*roof if upper else z-depth*(math.sin(t)**.45)
   verts.append((x,y,zz))
 faces=[]
 for i in range(len(sections)-1):
  for j in range(n-1):
   a=i*n+j; faces.append((a,a+1,a+n+1,a+n) if upper else (a+n,a+n+1,a+1,a))
 faces.extend([tuple(range(n-1,-1,-1)),tuple((len(sections)-1)*n+j for j in range(n))])
 mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
 o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o); finish(o,name,TI if upper else BLACK)
 sub=o.modifiers.new('Continuous body contours','SUBSURF'); sub.levels=2
 solid=o.modifiers.new('Shell wall','SOLIDIFY'); solid.thickness=.0018
 return o
shell('BODY_SHELL_TOP'); shell('BODY_CRADLE',False)
# Front visor and optical landmarks.
box('FRONT_VISOR',(0,-.137,.082),(.116,.013,.026),BLACK,bevel=.006)
for s in [-1,1]:
 cyl('FRONT_SENSOR_'+('L' if s<0 else 'R'),(s*.044,-.145,.082),.008,.003,BLACK,axis='Y')
 cyl('SENSOR_GLASS_'+str(s),(s*.044,-.147,.082),.0058,.001,GLASS,axis='Y')
box('STATUS_LIGHT',(0,-.145,.092),(.016,.001,.0018),WHITE,bevel=.0005)
# Each pivot retains independent hierarchy for later folding and explosion.
motors=[]
for tag,y,hy in [('F',-.140,-.089),('R',.140,.086)]:
 for side,s in [('L',-1),('R',1)]:
  label=tag+side; g=group('ARM_'+label+'_ROOT')
  hinge=(s*.064,hy,.075); end=(s*.165,y,.075)
  g.location=hinge
  # Geometry created in world coordinates, then inverse-parent to hinge root.
  parts=[]
  parts.append(cyl('HINGE_'+label,hinge,.015,.024,BLACK))
  parts.append(cyl('HINGE_CAP_'+label,(hinge[0],hinge[1],.088),.011,.0015,SILVER))
  parts.append(beam('ARM_'+label,hinge,end,.026,.025,BLACK))
  parts.append(beam('ARM_INLAY_'+label,(hinge[0],hinge[1],.089),(end[0],end[1],.089),.021,.003,TI))
  parts.append(cyl('MOTOR_BASE_'+label,end,.018,.026,BLACK))
  parts.append(cyl('MOTOR_'+label,(end[0],end[1],.095),.017,.016,SILVER))
  parts.append(cyl('MOTOR_ACCENT_'+label,(end[0],end[1],.105),.015,.002,COPPER))
  parts.append(cyl('MOTOR_HUB_'+label,(end[0],end[1],.112),.008,.009,BLACK))
  parts.append(box('LANDING_FOOT_'+label,(end[0],end[1],.0395),(.012,.016,.055),BLACK,bevel=.003))
  for o in parts: o.parent=g; o.matrix_parent_inverse=__import__('mathutils').Matrix.Translation(Vector(hinge)*-1)
  prop=group('PROPELLER_'+label,g); prop.location=Vector((end[0],end[1],.121))-Vector(hinge)
  prop.rotation_euler.z=math.radians(78 if tag=='F' else -12)*s
  for k in range(2):
   # Tapered swept blade profile with rounded bevels.
   outline=[(.006,-.003),(.023,-.008),(.051,-.010),(.080,-.008),(.093,-.004),(.096,-.001),(.094,.002),(.086,.003),(.039,.004),(.009,.004)]
   vs=[(x*(-1 if k else 1),y*1.4*(-1 if k else 1),z) for z in [-.00065,.00065] for x,y in outline]
   nn=len(outline); fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,nn*2))]+[(j,(j+1)%nn,(j+1)%nn+nn,j+nn) for j in range(nn)]
   me=bpy.data.meshes.new('blade'); me.from_pydata(vs,[],fs); me.update(); ob=bpy.data.objects.new('BLADE_'+label+'_'+str(k),me); scene.collection.objects.link(ob); finish(ob,ob.name,BLACK,prop,.0007)
  motors.append((end[0],end[1]))
# Gimbal and lens reserve the characteristic suspended front silhouette.
gimbal=group('CAMERA_GIMBAL_ROOT')
box('GIMBAL_MOUNT',(0,-.110,.051),(.045,.027,.010),BLACK,gimbal)
for s in [-1,1]:
 box('GIMBAL_YOKE_'+str(s),(s*.030,-.125,.036),(.007,.030,.035),BLACK,gimbal,.003)
 cyl('GIMBAL_PIVOT_'+str(s),(s*.032,-.139,.035),.014,.007,BLACK,gimbal,'X')
box('CAMERA_HOUSING',(0,-.139,.035),(.051,.046,.041),BLACK,gimbal,.009)
cyl('LENS_BARREL',(0,-.166,.035),.019,.014,BLACK,gimbal,'Y')
cyl('LENS_RING',(0,-.174,.035),.0165,.003,BLACK,gimbal,'Y')
cyl('LENS_GLASS',(0,-.175,.035),.0148,.001,GLASS,gimbal,'Y')
# Motor collars, vents, hinge screws and propeller bridges.
for tag in ['F','R']:
 for side in ['L','R']:
  label=tag+side; g=bpy.data.objects['ARM_'+label+'_ROOT']; motor=bpy.data.objects['MOTOR_'+label]
  pos=motor.location.copy()
  def attach(o):
   o.parent=g; o.matrix_parent_inverse=g.matrix_parent_inverse.copy(); o.matrix_parent_inverse=__import__('mathutils').Matrix.Translation(-g.location)
  for z,r,material in [(.087,.0175,BLACK),(.103,.0176,SILVER),(.114,.014,BLACK)]:
   o=cyl('COLLAR_'+label+'_'+str(z),(pos.x,pos.y,z),r,.0015,material); attach(o)
  for j in range(8):
   a=j*math.tau/8
   o=box('MOTOR_VENT_STRUT_'+label+'_'+str(j),(pos.x+.012*math.cos(a),pos.y+.012*math.sin(a),.110),(.002,.002,.008),BLACK,bevel=.0004); attach(o)
  o=cyl('HINGE_SCREW_'+label,(g.location.x,g.location.y,.090),.003,.002,BLACK); attach(o)
  prop=bpy.data.objects['PROPELLER_'+label]
  o=box('PROP_BRIDGE_'+label,(0,0,.001),(.030,.009,.004),BLACK,prop,.003)
  for xx in [-.010,0,.010]:
   cyl('PROP_BOLT_'+label+'_'+str(xx),(xx,0,.004),.0024,.0015,SILVER,prop)
  # Tip inlays lie on blade surface, avoiding text.
  for sign in [-1,1]:
   o=box('BLADE_TIP_'+label+'_'+str(sign),(sign*.088,-sign*.003,.0009),(.0015,.009,.00035),COPPER,prop,.0002)
# Optical rings with a recessed pupil instead of a flat opaque disc.
for r,yy in [(.0138,-.176),(.012,-.1758),(.009,-.1756)]:
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.00045,major_segments=64,minor_segments=12,location=(0,yy,.035),rotation=(math.pi/2,0,0))
 finish(bpy.context.object,'LENS_RETAINING_'+str(r),BLACK,gimbal)
cyl('LENS_INNER_GLASS',(0,-.1757,.035),.0082,.0006,GLASS,gimbal,'Y')
cyl('LENS_PUPIL',(0,-.176,.035),.0045,.0005,BLACK,gimbal,'Y')
# Small on-product wordmark only.
font=bpy.data.curves.new('AERIX_wordmark','FONT'); font.body='AERIX'; font.align_x='CENTER'; font.size=.009; font.extrude=.000015
word=bpy.data.objects.new('AERIX_WORDMARK',font); scene.collection.objects.link(word); word.parent=root; word.location=(0,-.087,.119); word.rotation_euler.x=math.radians(18); font.materials.append(BLACK)

# Internal proxies intentionally hidden from exterior review renders.
reserve=group('INTERNAL_ENVELOPES')
for name,loc,size in [('BATTERY_ENVELOPE',(0,.015,.085),(.080,.145,.027)),('PCB_ENVELOPE',(0,.010,.064),(.083,.16,.003))]:
 o=box(name,loc,size,RESERVE,reserve,.002); o.hide_render=True; o.display_type='WIRE'
# Ground and studio setup.
floor=box('STUDIO_GROUND',(0,0,.009),(200,200,.006),mat('Studio',(.023,.026,.030),0,.7),None,0)
def aim(o,at): o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('KEY',(.25,-.35,.65),5,.5),('FILL',(-.4,-.1,.35),2,.45),('RIM',(.15,.45,.5),7,.4)]:
 data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size
 o=bpy.data.objects.new(name,data); scene.collection.objects.link(o); o.location=loc; aim(o,(0,0,.05))
views={'hero':((.33,-.70,.53),.66),'front':((0,-1,.065),.61),'rear':((0,1,.065),.61),'left':((-1,0,.065),.56),'right':((1,0,.065),.56),'top':((0,0,1),.80),'bottom':((0,0,-1),.80)}
for name,(loc,scale) in views.items():
 data=bpy.data.cameras.new('CAM_'+name); data.type='ORTHO'; data.ortho_scale=scale
 o=bpy.data.objects.new('CAM_'+name,data); scene.collection.objects.link(o); o.location=loc; aim(o,(0,0,.061)); data.lens=55
scene.camera=bpy.data.objects['CAM_hero']
# Recalculate mesh normals for consistent exterior shading.
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
# Basic deterministic geometric validation, not inferred engineering measurements.
clearance=min(math.dist(a,b) for i,a in enumerate(motors) for b in motors[i+1:])-.192
assert clearance>0, 'Rotor sweep overlap'
assert len([o for o in bpy.data.objects if o.name.startswith('BLADE_') and not o.name.startswith('BLADE_TIP_')])==8
report={'units':'metres','body_length':.277,'max_body_width':.140,'motor_span_x':.330,'motor_span_y':.280,'rotor_diameter':.192,'minimum_rotor_disk_clearance':round(clearance,4),'blade_count':8,'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects),'note':'Concept dimensions; not a manufactured drone specification.'}
(ROOT/'renders/refinement-v02/validation.json').write_text(json.dumps(report,indent=2))
# Make model selected and frame a sensible viewport on open.
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type=='MESH' and o!=floor: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['BODY_SHELL_TOP']
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=.7; area.spaces.active.region_3d.view_location=Vector((0,0,.06))
   area.spaces.active.clip_start=.001
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-refinement-v02.blend'))
data=bpy.data.lights.new('BOTTOM_REVIEW_FILL','AREA'); data.energy=3; data.size=.45
under=bpy.data.objects.new('BOTTOM_REVIEW_FILL',data); scene.collection.objects.link(under); under.location=(0,0,-.4); aim(under,(0,0,.05))
for name in views:
 under.hide_render=name!='bottom'
 scene.camera=bpy.data.objects['CAM_'+name]; floor.hide_render=name!='hero'
 scene.render.filepath=str(ROOT/'renders/refinement-v02'/f'{name}.png'); bpy.ops.render.render(write_still=True)
print('BLOCKOUT_COMPLETE',json.dumps(report))
