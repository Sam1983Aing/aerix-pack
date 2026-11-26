"""Adapt V04 internals to untouched V27 exterior; author independent reveal actions."""
import bpy,math,json,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];OUT=R/'renders/interior-v28';OUT.mkdir(exist_ok=True)
sources=[R/'blender/aerix-folding-v27.blend',R/'blender/aerix-interior-v04.blend',R/'blender/aerix-exterior-v25.blend',R/'exports/aerix-review-v27.glb']
hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
# Save only the reusable assemblies into an append library; no old exterior or actions.
bpy.ops.wm.open_mainfile(filepath=str(sources[1]));bpy.context.scene.frame_set(1)
rootnames=['INTERNAL_SUPPORT_ROOT','FLIGHT_COMPUTER_ROOT','THERMAL_ROOT','BATTERY_ROOT','OPTICS_IR_CUT_FILTER_ROOT','OPTICS_CMOS_SENSOR_ROOT']
parts=set()
for n in rootnames:
 o=bpy.data.objects[n];o.parent=None;parts.add(o);parts.update(o.children_recursive)
for o in parts:o.animation_data_clear()
names=[o.name for o in parts];bpy.data.libraries.write('/tmp/aerix-v28-internals.blend',parts)
bpy.ops.wm.open_mainfile(filepath=str(sources[0]));s=bpy.context.scene;s.frame_set(1);root=bpy.data.objects['DRONE_ROOT'];bpy.context.view_layer.update()
def snap():
 d=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type not in {'MESH','FONT','CURVE'} or o.hide_render or o.name=='STUDIO_GROUND':continue
  e=o.evaluated_get(d);m=e.to_mesh();out[o.name]={'vertices':[tuple(e.matrix_world@v.co) for v in m.vertices],'signature':hashlib.sha256(repr(([tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],[q.name if q else None for q in m.materials])).encode()).hexdigest()};e.to_mesh_clear()
 return out
before=snap();original_names=set(bpy.data.objects.keys());original_actions={o.name:o.animation_data.action.name for o in s.objects if o.animation_data and o.animation_data.action}
with bpy.data.libraries.load('/tmp/aerix-v28-internals.blend',link=False) as (src,dst):dst.objects=names
for o in dst.objects:
 if o:s.collection.objects.link(o)
for n in rootnames:bpy.data.objects[n].parent=root
bpy.context.view_layer.update()
def keep(o,parent):
 w=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_world=w

def group(n,parent=root):
 o=bpy.data.objects.new(n,None);s.collection.objects.link(o);o.parent=parent;o.empty_display_size=.008;return o
# Normalize reused geometry into the same world-space authoring contract as the exterior.
for name in rootnames:
 g=bpy.data.objects[name]
 for o in g.children_recursive:
  if o.type!='MESH':continue
  w=o.matrix_world.copy();o.data=o.data.copy();o.data.transform(w);o.matrix_world=Matrix.Identity(4)
 # Move actual geometry instead of retaining transforms from the obsolete scene.
 for o in g.children_recursive:
  if o.type!='MESH':continue
  for v in o.data.vertices:
   if name=='BATTERY_ROOT':v.co.x*=1.1;v.co.y=v.co.y*1.08-.012;v.co.z-=.002
   elif name=='OPTICS_IR_CUT_FILTER_ROOT':v.co.y-=.014;v.co.z+=.003
   elif name=='OPTICS_CMOS_SENSOR_ROOT':v.co.x*=.82;v.co.y-=.016;v.co.z=.038+(v.co.z-.035)*.82
   else:v.co.y-=.012;v.co.z+=.006 if name=='INTERNAL_SUPPORT_ROOT' else .004 if name=='FLIGHT_COMPUTER_ROOT' else .0015
# Reuse current optical glass/barrels; append only filter and sensor behind them, inside the well.
pitch=bpy.data.objects['CAMERA_PITCH_ROOT'];filterroot=bpy.data.objects['OPTICS_IR_CUT_FILTER_ROOT'];sensorroot=bpy.data.objects['OPTICS_CMOS_SENSOR_ROOT']
keep(filterroot,pitch);keep(sensorroot,pitch)
# New material family for interior close-ups; no changes to original materials.
def mat(n,c,metal=0,rough=.35):
 m=bpy.data.materials.new('V28 '+n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
BLACK=mat('satin cartridge',(.012,.017,.021),.18,.34);METAL=mat('machined support',(.31,.36,.39),.8,.29);DARK=mat('mounting polymer',(.018,.022,.026),.1,.43);GOLD=mat('contact gold',(.54,.31,.07),.78,.27);PCB=mat('multilayer solder mask',(.012,.043,.033),.25,.4);INK=mat('board silkscreen',(.57,.63,.55),.05,.5);TRACE=mat('covered copper traces',(.025,.081,.057),.35,.34);COPPER=mat('polyimide flex',(.35,.12,.026),.3,.39)
battery=bpy.data.objects['BATTERY_ROOT'];board=bpy.data.objects['FLIGHT_COMPUTER_ROOT'];support=bpy.data.objects['INTERNAL_SUPPORT_ROOT'];thermal=bpy.data.objects['THERMAL_ROOT']
for g in [battery,board,thermal,support,filterroot,sensorroot]:
 for o in g.children_recursive:
  if o.type!='MESH':continue
  if o.name.startswith(('BATTERY_SIDE','BATTERY_END','BATTERY_LID','BATTERY_TRAY','BATTERY_CONNECTOR')):o.data.materials.clear();o.data.materials.append(BLACK)
  elif o.name.startswith(('SUPPORT_TRAY','THERMAL_COVER','COOLING_RIB')):o.data.materials.clear();o.data.materials.append(METAL)
  elif o.name.startswith(('MAIN_PCB','SENSOR_PCB')):o.data.materials.clear();o.data.materials.append(PCB)
def finish(o,n,m,parent,bevel=0):
 o.name=n;o.data.materials.append(m)
 if bevel:b=o.modifiers.new('Finished edge','BEVEL');b.width=bevel;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Surface normals','WEIGHTED_NORMAL');bpy.context.view_layer.update();keep(o,parent);return o

def box(n,p,size,m,parent=root,bevel=.0005):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,parent,bevel)
def cyl(n,p,r,depth,m,parent=root,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=p);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 return finish(o,n,m,parent,.00015)
def line(n,points,r,m,parent):
 d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.resolution_u=12;d.bevel_depth=r;d.bevel_resolution=3;sp=d.splines.new('POLY');sp.points.add(len(points)-1)
 for q,p in zip(sp.points,points):q.co=(*p,1)
 o=bpy.data.objects.new(n,d);s.collection.objects.link(o);d.materials.append(m);bpy.context.view_layer.update();keep(o,parent);return o

def label(n,text,p,size,parent,m=INK):
 d=bpy.data.curves.new(n,'FONT');d.body=text;d.size=size;d.extrude=.000005;d.align_x='CENTER';o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=p;d.materials.append(m);bpy.context.view_layer.update();keep(o,parent);return o
# Exact interface heights: four standoffs seat against the PCB underside.
for o in support.children:
 if o.name.startswith('BOARD_STANDOFF'):
  for v in o.data.vertices:v.co.z=.0612+(v.co.z-.062)*1.13
# Thermal pad connects processor top at 69 mm with cover underside at 71 mm.
o=bpy.data.objects['THERMAL_PAD'];zs=[v.co.z for v in o.data.vertices];mid=(min(zs)+max(zs))/2
for v in o.data.vertices:v.co.z+=.070-mid
# Open pocketed tray with longitudinal and transverse ribs, matching existing mounting coordinates.
old=bpy.data.objects['SUPPORT_TRAY'];bpy.data.objects.remove(old,do_unlink=True)
box('SUPPORT_TRAY_BASE',(0,.003,.058),(.078,.150,.001),METAL,support)
for x in [-.037,.037]:box('SUPPORT_EDGE_RAIL',(x,.003,.059),(.004,.150,.003),METAL,support)
for y in [-.070,-.025,.025,.076]:box('SUPPORT_CROSS_RIB',(0,y,.059),(.070,.003,.003),METAL,support)
for x in [-.020,.020]:box('SUPPORT_SPINE',(x,.003,.0588),(.0015,.143,.0018),METAL,support)
for x in [-.033,.033]:
 for y in [-.062,.068]:
  cyl('SUPPORT_STANDOFF_SEAT',(x,y,.058875),.0038,.00075,METAL,support)
  cyl('PCB_SCREW_SHAFT',(x,y,.0651),.00115,.0016,METAL,board)
# Chassis-mounted bosses and cartridge guides remain in the body when upper layers separate.
fixed=group('INTERIOR_CHASSIS_ROOT')
for x in [-.033,.033]:
 for y in [-.062,.068]:
  cyl('CHASSIS_MOUNT_BOSS',(x,y,.053),.0038,.009,DARK,fixed)
  cyl('CHASSIS_MOUNT_INSERT',(x,y,.057),.0022,.001,GOLD,fixed)
for x in [-.043,.043]:
 box('BATTERY_GUIDE_RAIL',(x,.002,.083),(.002,.139,.008),DARK,fixed)
 box('BATTERY_GUIDE_TOP',(x,.002,.087),(.0025,.136,.001),BLACK,fixed)
for x in [-.052,.052]:
 for y in [-.080,.047]:
  box('INNER_SHELL_TAB',(x,y,.088),(.011,.012,.002),DARK,fixed)
  cyl('INNER_SHELL_CAPTIVE_SCREW',(x,y,.089),.0018,.001,METAL,fixed)
# Hidden internal wiring routes and anchor saddles, with no arm attachments crossing an explosion.
for sign in [-1,1]:
 x=sign*.048
 line('CHASSIS_POWER_LOOM',[(x,-.095,.060),(x,-.066,.064),(x,-.025,.068),(x,.040,.068),(sign*.040,.077,.068)],.00085,BLACK,fixed)
 for y in [-.055,.006,.050]:box('LOOM_CLIP',(x,y,.068),(.005,.004,.002),DARK,fixed)
# Board graphics and orderly low-relief traces around existing major packages.
label('PCB_LABEL','AERIX  /  FLIGHT CORE',(0,.038,.06486),.003,board)
label('PCB_REV','FC-01     REV A',(0,.066,.06486),.002,board)
label('PROCESSOR_ETCH','AERIX',(0,-.019,.06905),.003,board,METAL)
for x in [-.033,.033]:
 for y in [-.062,.068]:
  bpy.ops.mesh.primitive_torus_add(major_radius=.0022,minor_radius=.00035,major_segments=32,minor_segments=8,location=(x,y,.0649));finish(bpy.context.object,'PCB_MOUNT_PLATING',GOLD,board)
for sign in [-1,1]:
 for k in range(8):
  x=sign*(.017+k*.0016);yy=.004+k*.0023
  line('PCB_MASKED_TRACE',[(sign*.013,yy,.06484),(x,yy,.06484),(x,yy+.019,.06484),(x+sign*.002,yy+.021,.06484)],.000085,TRACE,board)
for i in range(12):
 x=-.028+i*.005
 cyl('PCB_TEST_POINT',(x,-.052,.0649),.0005,.0001,GOLD,board)
# Battery housing seam, end fasteners and restrained identification.
lid=bpy.data.objects['BATTERY_LID_ROOT']
label('BATTERY_ID','AERIX',(0,-.025,.1046),.006,lid)
label('BATTERY_SERVICE_ID','POWER MODULE  /  01',(0,.034,.1046),.0024,lid,INK)
for x in [-.035,.035]:
 for y in [-.057,.070]:cyl('BATTERY_LID_FASTENER',(x,y,.10465),.0013,.0003,METAL,lid)
for i in range(4):
 g=bpy.data.objects['CELL_'+str(i+1)+'_ROOT'];z=.084+i*.0046-.002+.00195
 for y in [-.020,.044]:box('CELL_INSULATION_BAND',(0,y,z),(.070,.007,.00016),DARK,g,.0001)
# Frame the sensor and IR filter without placing the old oversized duplicate barrel inside the new lens.
for x in [-.0084,.0084]:box('SENSOR_FRAME_SIDE',(x,-.1563,.038),(.0008,.002,.0168),DARK,sensorroot,.00015)
for z in [.030,.046]:box('SENSOR_FRAME_END',(0,-.1563,z),(.0176,.002,.0008),DARK,sensorroot,.00015)
# Simple rear flex ribbon lives ahead of the existing opaque rear bulkhead at -148 mm.
box('SENSOR_FLEX_TAIL',(0,-.1525,.031),(.010,.004,.0002),COPPER,sensorroot,.0001)
# Move the body stack 20 mm forward to clear the real V27 rear shoulder webs.
for assembly in [support,board,thermal,battery,fixed]:assembly.location.y-=.020
bpy.context.view_layer.update()
# Shell, camera and optical stage roots preserve every original world-space vertex.
shellservice=group('SHELL_SERVICE_ROOT')
shellroot=group('SHELL_REVEAL_ROOT',shellservice)
for name in ['BODY_SHELL_TOP','AERIX_WORDMARK']:
 keep(bpy.data.objects[name],shellroot)
optical=[]
for name,parts in [
 ('OPTICS_WINDOW_REVEAL_ROOT',['LENS_BARREL','LENS_OUTER_EDGE','LENS_FRONT_SEAL','LENS_INNER_RETAINING_RING','LENS_FRONT_ELEMENT']+[f'LENS_MICRO_RIB_{i}' for i in range(6)]),
 ('OPTICS_FRONT_CELL_REVEAL_ROOT',['LENS_MIDDLE_ELEMENT','LENS_INTERNAL_BAFFLE_0','LENS_INTERNAL_EDGE_0','LENS_INTERNAL_BAFFLE_1','LENS_INTERNAL_EDGE_1']),
 ('OPTICS_REAR_CELL_REVEAL_ROOT',['LENS_REAR_COATED_ELEMENT','LENS_INTERNAL_BAFFLE_2','LENS_INTERNAL_EDGE_2','LENS_INTERNAL_BAFFLE_3','LENS_INTERNAL_EDGE_3']),
 ('OPTICS_IRIS_REVEAL_ROOT',['LENS_APERTURE','LENS_DEEP_OPTICAL_CORE']+[f'LENS_IRIS_LEAF_{i}' for i in range(9)])]:
 g=group(name,pitch);bpy.context.view_layer.update()
 for name in parts:keep(bpy.data.objects[name],g)
 optical.append(g)
optical.extend([filterroot,sensorroot])
# Store three independent reveal clips as object actions, offset from the original folding timeline.
# Folding 1–361; body reveal 401–521; battery 551–671; optics 701–821; reassembly 851–971.
tracks={};bases={}
def keys(o,clip,offset,start,end):
 base=o.location.copy();bases.setdefault(o.name,list(base));o['assembled_location']=list(base);o['reveal_offset']=list(offset);o['reveal_clip']=clip
 for fr,mul in [(1,0),(361,0),(start,0),(end,1),(851,1),(971,0)]:
  o.location=base+Vector(offset)*mul;o.keyframe_insert(data_path='location',frame=fr,group=clip)
 tracks[o.name]={'clip':clip,'base':list(base),'offset':list(offset),'start':start,'end':end}
keys(shellroot,'Body_reveal',(0,0,.285),401,521)
keys(battery,'Body_reveal',(0,.016,.210),401,521)
keys(thermal,'Body_reveal',(0,0,.150),401,521)
keys(board,'Body_reveal',(0,0,.095),401,521)
keys(support,'Body_reveal',(0,0,.040),401,521)
keys(bpy.data.objects['CAMERA_GIMBAL_ROOT'],'Body_reveal',(0,-.050,-.004),401,521)
keys(shellservice,'Battery_reveal',(0,0,.170),551,671)
keys(lid,'Battery_reveal',(0,0,.110),551,671)
for i in range(4):keys(bpy.data.objects[f'CELL_{i+1}_ROOT'],'Battery_reveal',(0,0,.016+i*.021),551,671)
for i,g in enumerate(optical):keys(g,'Optics_reveal',(0,-(.130-i*.020),0),701,821)
# Preserve the folding curves but return them to deployed before interior inspection.
for name in original_actions:
 o=bpy.data.objects[name];q=o.rotation_quaternion.copy()
 s.frame_set(1);deployed=o.rotation_quaternion.copy();s.frame_set(361);folded=o.rotation_quaternion.copy()
 for fr,rot in [(381,folded),(400,deployed),(971,deployed)]:o.rotation_quaternion=rot;o.keyframe_insert(data_path='rotation_quaternion',frame=fr)
s.frame_set(1);bpy.context.view_layer.update();after=snap()
maxerror=max((Vector(a)-Vector(b)).length for n,item in before.items() for a,b in zip(item['vertices'],after[n]['vertices']))
checks={'all_690_exterior_objects_retained':set(before)<=set(after),'original_geometry_normals_materials_unchanged':all(v['signature']==after[n]['signature'] for n,v in before.items()),'assembled_exterior_vertices_preserved':maxerror<1e-7,'original_sources_unchanged':all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(R))] for p in sources)}
assert all(checks.values()),checks
s.frame_end=971
for label,fr in [('V28 BODY ASSEMBLED',400),('V28 BODY EXPLODED',521),('V28 BATTERY LAYERS',671),('V28 OPTICAL LAYERS',821),('V28 REASSEMBLED',971)]:s.timeline_markers.new(label,frame=fr)
s['interior_notes']='V28 fitted visual proposal. V27 exterior retained exactly; V04 body internals adapted; approved lens retained and grouped with new filter/sensor. Not engineering validation.'
# Save review transforms and the native hierarchy for exact exterior GLB reparenting.
s.frame_set(1);bpy.context.view_layer.update();hierarchy={o.name:{'parent':o.parent.name if o.parent else None,'local_matrix':[v for row in o.matrix_local for v in row]} for o in s.objects if o.type not in {'LIGHT','CAMERA'} and not o.hide_render and o.name!='STUDIO_GROUND'}
newnames=[o.name for o in s.objects if o.name not in original_names and o.type in {'MESH','CURVE','FONT'}]
(OUT/'integration-config.json').write_text(json.dumps({'tracks':tracks,'hierarchy':hierarchy,'new_mesh_names':newnames,'checks':checks,'source_hashes':hashes,'max_exterior_vertex_error_m':maxerror},indent=2))
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(400)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-interior-v28.blend'))
print('V28_MASTER_SAVED',checks,'added',len(newnames),flush=True)
# Export only new internal geometry plus normalized ancestor transforms to a merge asset.
bpy.ops.object.select_all(action='DESELECT')
for name in newnames:
 o=bpy.data.objects[name];o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/aerix-interior-additions-v28.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
print('V28_ADDITIONS_EXPORTED',flush=True)
