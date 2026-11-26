"""Reproducible AERIX blockout. Units metres; nose = -Y; up = +Z."""
import bpy, math, json, bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.cycles.use_denoising=True
scene.render.resolution_x=1100; scene.render.resolution_y=850; scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.18,.21,.25,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX'

def mat(name,color,metal=0,rough=.35):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
TI=mat('Titanium — provisional',(.43,.40,.35),.7,.32)
BLACK=mat('Graphite',(.035,.042,.047),.25,.36)
SILVER=mat('Machined motor alloy',(.52,.56,.59),.8,.26)
COPPER=mat('Copper accent',(.43,.23,.10),.8,.3)
GLASS=mat('Optics placeholder',(.015,.075,.09),.6,.13)
WHITE=mat('Status light',(.7,.86,1),.1,.25)
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
sections=[(-.111,.032,.077,.009),(-.105,.046,.080,.013),(-.085,.050,.083,.022),(-.035,.048,.086,.028),(.025,.041,.086,.029),(.076,.039,.084,.022),(.105,.034,.081,.012),(.111,.027,.080,.006)]

def shell(name,upper=True):
 verts=[]; n=17
 for y,w,z,h in sections:
  for j in range(n):
   t=math.pi*j/(n-1)
   x=-w*math.cos(t)
   depth=.017+.020*max(0,1-(y/.12)**4)
   zz=z+h*(math.sin(t)**.65) if upper else z-depth*(math.sin(t)**.45)
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
box('FRONT_VISOR',(0,-.108,.077),(.079,.010,.019),BLACK,bevel=.006)
for s in [-1,1]:
 cyl('FRONT_SENSOR_'+('L' if s<0 else 'R'),(s*.030,-.115,.077),.0058,.003,BLACK,axis='Y')
 cyl('SENSOR_GLASS_'+str(s),(s*.030,-.117,.077),.0038,.001,GLASS,axis='Y')
box('STATUS_LIGHT',(0,-.114,.084),(.013,.001,.0018),WHITE,bevel=.0005)
# Each pivot retains independent hierarchy for later folding and explosion.
motors=[]
for tag,y,hy in [('F',-.120,-.067),('R',.120,.069)]:
 for side,s in [('L',-1),('R',1)]:
  label=tag+side; g=group('ARM_'+label+'_ROOT')
  hinge=(s*.044,hy,.074); end=(s*.155,y,.075)
  g.location=hinge
  # Geometry created in world coordinates, then inverse-parent to hinge root.
  parts=[]
  parts.append(cyl('HINGE_'+label,hinge,.011,.018,BLACK))
  parts.append(cyl('HINGE_CAP_'+label,(hinge[0],hinge[1],.084),.008,.0015,SILVER))
  parts.append(beam('ARM_'+label,hinge,end,.018,.018,BLACK))
  parts.append(beam('ARM_INLAY_'+label,(hinge[0],hinge[1],.084),(end[0],end[1],.085),.014,.002,TI))
  parts.append(cyl('MOTOR_BASE_'+label,end,.014,.022,BLACK))
  parts.append(cyl('MOTOR_'+label,(end[0],end[1],.092),.013,.014,SILVER))
  parts.append(cyl('MOTOR_ACCENT_'+label,(end[0],end[1],.100),.011,.002,COPPER))
  parts.append(cyl('MOTOR_HUB_'+label,(end[0],end[1],.105),.007,.008,BLACK))
  parts.append(box('LANDING_FOOT_'+label,(end[0],end[1],.037),(.008,.011,.057),BLACK,bevel=.003))
  for o in parts: o.parent=g; o.matrix_parent_inverse=__import__('mathutils').Matrix.Translation(Vector(hinge)*-1)
  prop=group('PROPELLER_'+label,g); prop.location=Vector((end[0],end[1],.111))-Vector(hinge)
  prop.rotation_euler.z=math.radians(60 if tag=='F' else -55)*s
  for k in range(2):
   # Tapered swept blade profile with rounded bevels.
   outline=[(.006,-.003),(.024,-.008),(.058,-.009),(.079,-.004),(.081,0),(.076,.003),(.032,.003),(.009,.004)]
   vs=[(x*(-1 if k else 1),y*1.4*(-1 if k else 1),z) for z in [-.00065,.00065] for x,y in outline]
   nn=len(outline); fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,nn*2))]+[(j,(j+1)%nn,(j+1)%nn+nn,j+nn) for j in range(nn)]
   me=bpy.data.meshes.new('blade'); me.from_pydata(vs,[],fs); me.update(); ob=bpy.data.objects.new('BLADE_'+label+'_'+str(k),me); scene.collection.objects.link(ob); finish(ob,ob.name,BLACK,prop,.0007)
  motors.append((end[0],end[1]))
# Gimbal and lens reserve the characteristic suspended front silhouette.
gimbal=group('CAMERA_GIMBAL_ROOT')
box('GIMBAL_MOUNT',(0,-.084,.051),(.035,.021,.009),BLACK,gimbal)
for s in [-1,1]:
 box('GIMBAL_YOKE_'+str(s),(s*.024,-.095,.035),(.006,.024,.033),BLACK,gimbal,.003)
 cyl('GIMBAL_PIVOT_'+str(s),(s*.026,-.106,.032),.011,.006,BLACK,gimbal,'X')
box('CAMERA_HOUSING',(0,-.109,.031),(.041,.036,.034),BLACK,gimbal,.009)
cyl('LENS_BARREL',(0,-.130,.031),.015,.012,BLACK,gimbal,'Y')
cyl('LENS_RING',(0,-.137,.031),.0128,.003,SILVER,gimbal,'Y')
cyl('LENS_GLASS',(0,-.139,.031),.0115,.001,GLASS,gimbal,'Y')
# Internal proxies intentionally hidden from exterior review renders.
reserve=group('INTERNAL_ENVELOPES')
for name,loc,size in [('BATTERY_ENVELOPE',(0,.015,.080),(.058,.115,.023)),('PCB_ENVELOPE',(0,.010,.063),(.061,.135,.003))]:
 o=box(name,loc,size,RESERVE,reserve,.002); o.hide_render=True; o.display_type='WIRE'
# Ground and studio setup.
floor=box('STUDIO_GROUND',(0,0,-.003),(200,200,.006),mat('Studio',(.07,.085,.10),0,.7),None,0)
def aim(o,at): o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('KEY',(.25,-.35,.65),5,.5),('FILL',(-.4,-.1,.35),2,.45),('RIM',(.15,.45,.5),7,.4)]:
 data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size
 o=bpy.data.objects.new(name,data); scene.collection.objects.link(o); o.location=loc; aim(o,(0,0,.05))
views={'hero':((.44,-.62,.47),.64),'front':((0,-1,.065),.57),'rear':((0,1,.065),.57),'left':((-1,0,.065),.51),'right':((1,0,.065),.51),'top':((0,0,1),.61),'bottom':((0,0,-1),.61)}
for name,(loc,scale) in views.items():
 data=bpy.data.cameras.new('CAM_'+name); data.type='ORTHO'; data.ortho_scale=scale
 o=bpy.data.objects.new('CAM_'+name,data); scene.collection.objects.link(o); o.location=loc; aim(o,(0,0,.061)); data.lens=55
scene.camera=bpy.data.objects['CAM_hero']
# Recalculate mesh normals for consistent exterior shading.
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(obj.data); bm.free()
# Basic deterministic geometric validation, not inferred engineering measurements.
clearance=min(math.dist(a,b) for i,a in enumerate(motors) for b in motors[i+1:])-.162
assert clearance>0, 'Rotor sweep overlap'
assert len([o for o in bpy.data.objects if o.name.startswith('BLADE_')])==8
report={'units':'metres','body_length':.222,'max_body_width':.100,'motor_span_x':.310,'motor_span_y':.240,'rotor_diameter':.162,'minimum_rotor_disk_clearance':round(clearance,4),'blade_count':8,'mesh_count':sum(o.type=='MESH' for o in bpy.data.objects),'note':'Concept dimensions; not a manufactured drone specification.'}
(ROOT/'renders/blockout/validation.json').write_text(json.dumps(report,indent=2))
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
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-blockout-v01.blend'))
for name in views:
 scene.camera=bpy.data.objects['CAM_'+name]; floor.hide_render=name!='hero'
 scene.render.filepath=str(ROOT/'renders/blockout'/f'{name}.png'); bpy.ops.render.render(write_still=True)
print('BLOCKOUT_COMPLETE',json.dumps(report))
