"""Add fitted fictional internals and reversible exploded key states to v03."""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v03.blend'))
scene=bpy.context.scene; scene.cycles.samples=48
root=bpy.data.objects['DRONE_ROOT']
TI=bpy.data.materials['Titanium — provisional']; BLACK=bpy.data.materials['Graphite']; SILVER=bpy.data.materials['Machined motor alloy']; COPPER=bpy.data.materials['Copper accent']
def mat(name,color,metal=0,rough=.35):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
 return m
PCB=mat('PCB dark green',(.015,.075,.045),.2,.42); GOLD=mat('Gold contacts',(.6,.38,.10),.75,.25); CERAMIC=mat('Electronic ceramic',(.25,.24,.20),.1,.45)
FOIL=mat('Battery foil',(.43,.47,.5),.8,.3); OPTIC=mat('Optical element',(.75,.92,.95),0,.04)
OPTIC.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=1.0

def group(name,parent=root):
 o=bpy.data.objects.new(name,None); scene.collection.objects.link(o); o.parent=parent; return o

def finish(o,name,material,parent,bevel=0):
 o.name=name; o.parent=parent; o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Machined edge','BEVEL'); mod.width=bevel; mod.segments=3
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Normals','WEIGHTED_NORMAL'); return o

def box(name,loc,size,material,parent,bevel=.0006):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,name,material,parent,bevel)
def cyl(name,loc,r,depth,material,parent,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc)
 o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 return finish(o,name,material,parent,.00025)
def torus(name,loc,r,material,parent):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.0007,major_segments=64,minor_segments=12,location=loc,rotation=(math.pi/2,0,0))
 return finish(bpy.context.object,name,material,parent)
# Remove envelopes only; exterior meshes remain intact.
for name in ['BATTERY_ENVELOPE','PCB_ENVELOPE','INTERNAL_ENVELOPES']:
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
# Structural support, electronics, thermal cover and battery are distinct assemblies.
support=group('INTERNAL_SUPPORT_ROOT'); board=group('FLIGHT_COMPUTER_ROOT'); thermal=group('THERMAL_ROOT'); battery=group('BATTERY_ROOT')
box('SUPPORT_TRAY',(0,.015,.053),(.078,.150,.0025),SILVER,support)
for x in [-.033,.033]:
 for y in [-.050,.080]:
  cyl('BOARD_STANDOFF',(x,y,.056),.0025,.0035,BLACK,support)
  cyl('BOARD_MOUNT_SCREW',(x,y,.062),.0016,.001,SILVER,board)
box('MAIN_PCB',(0,.015,.060),(.074,.144,.0016),PCB,board)
box('PROCESSOR_SUBSTRATE',(0,-.007,.062),(.025,.025,.002),BLACK,board)
box('PROCESSOR',(0,-.007,.064),(.022,.022,.002),SILVER,board)
for y in [-.020,.005]:box('MEMORY',( .024,y,.062),(.012,.018,.002),BLACK,board)
box('RADIO_SHIELD',(-.015,.058,.063),(.025,.026,.005),SILVER,board)
box('IMU_REGION',(-.023,-.036,.062),(.013,.013,.002),PCB,board)
box('IMU_PACKAGE',(-.023,-.036,.064),(.006,.006,.002),BLACK,board)
random.seed(7)
for i in range(95):
 x=random.uniform(-.032,.032); y=random.uniform(-.050,.080)
 if abs(x)<.015 and -.024<y<.010:continue
 if x>.015 and -.033<y<.018:continue
 if x<0 and .038<y<.075:continue
 if x<-.013 and y<-.023:continue
 size=random.choice([.0012,.0015,.002])
 box('SMD_'+str(i),(x,y,.0615),(size,size*1.7,.00065),CERAMIC if i%3 else BLACK,board,.00012)
 for sign in [-1,1]:box('SOLDER_'+str(i)+'_'+str(sign),(x,y+sign*size*.9,.0614),(size,.00035,.00035),SILVER,board,.0001)
for x in [-.025,0,.025]:
 box('EDGE_CONNECTOR',(x,-.055,.063),(.014,.006,.004),CERAMIC,board)
 for k in range(5):box('CONNECTOR_PIN',(x+(k-2)*.002,-.058,.063),(.0007,.003,.0007),GOLD,board,.0001)
box('THERMAL_PAD',(0,-.007,.067),(.020,.020,.002),CERAMIC,thermal)
box('THERMAL_COVER',(0,.014,.071),(.067,.130,.003),SILVER,thermal)
for x in [-.024,-.016,-.008,0,.008,.016,.024]:box('COOLING_RIB',(x,.020,.073),(.002,.104,.0015),SILVER,thermal,.0004)
# Battery is a hollow cartridge with a removable lid and cell subassemblies.
box('BATTERY_TRAY',(0,.014,.081),(.073,.138,.002),BLACK,battery)
for x in [-.036,.036]:box('BATTERY_SIDE',(x,.014,.092),(.002,.138,.022),BLACK,battery)
for y in [-.054,.082]:box('BATTERY_END',(0,y,.092),(.073,.002,.022),BLACK,battery)
lid=group('BATTERY_LID_ROOT',battery)
box('BATTERY_LID',(0,.014,.105),(.074,.140,.003),BLACK,lid,.0015)
for x in [-.019,.019]:box('BATTERY_LID_RECESS',(x,.014,.1065),(.001,.110,.0003),BLACK,lid,.0001)
cells=[]
for i in range(4):
 g=group('CELL_'+str(i+1)+'_ROOT',battery); cells.append(g)
 z=.084+i*.0046
 box('POUCH_CELL_'+str(i+1),(0,.020,z),(.065,.117,.0038),FOIL,g,.0011)
 for x in [-.032,.032]:box('CELL_EDGE_'+str(i)+'_'+str(x),(x,.020,z),(.0006,.116,.0013),SILVER,g,.0002)
 for x in [-.010,.010]:box('CELL_TAB_'+str(i)+'_'+str(x),(x,-.043,z),(.004,.010,.0006),COPPER,g,.0001)
box('BATTERY_BMS',(0,-.045,.101),(.059,.014,.0014),PCB,battery)
for x in [-.020,-.010,0,.010,.020]:box('BMS_CHIP',(x,-.045,.102),(.006,.007,.0015),BLACK,battery)
box('BATTERY_CONNECTOR',(0,-.056,.094),(.025,.004,.009),BLACK,battery)
for i in range(8):box('BATTERY_CONTACT',((i-3.5)*.0026,-.0585,.094),(.001,.0007,.004),GOLD,battery,.0001)
# Nest wordmark under moving shell, preserving its assembled transform.
shell=bpy.data.objects['BODY_SHELL_TOP']; word=bpy.data.objects['AERIX_WORDMARK']; word.parent=shell
# Optical train, with individually transformable cells along -Y.
gimbal=bpy.data.objects['CAMERA_GIMBAL_ROOT']
optics=group('OPTICS_ROOT',gimbal); optical_groups=[]
for i,(name,y,r) in enumerate([('FRONT_WINDOW',-.176,.014),('FRONT_CELL',-.169,.0128),('REAR_CELL',-.158,.011),('IR_CUT_FILTER',-.148,.0085),('CMOS_SENSOR',-.140,.008)]):
 g=group('OPTICS_'+name+'_ROOT',optics); optical_groups.append(g)
 if i<3:
  torus('OPTICS_'+name+'_RIM',(0,y,.035),r,BLACK,g)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,y,.035)); o=bpy.context.object; o.scale=(r*.94,.0012,r*.94); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); finish(o,'OPTICS_'+name+'_GLASS',OPTIC,g)
 elif i==3:box('IR_CUT_FILTER',(0,y,.035),(.016,.0007,.014),OPTIC,g,.0002)
 else:
  box('SENSOR_PCB',(0,y,.035),(.022,.0015,.019),PCB,g)
  box('CMOS_SENSOR',(0,y-.001,.035),(.014,.0005,.010),OPTIC,g,.0001)
# Existing visible lens parts stay for normal hero; hide during macro optics preview only.
legacy_optics=[o for o in bpy.data.objects if o.name.startswith(('LENS_'))]
# Reversible key states, stored on the same source model.
def keys(o,states):
 for frame,loc in states:
  o.location=loc; o.keyframe_insert(data_path='location',frame=frame)
 o['assembled_location']=[0.,0.,0.]
 o['exploded_location']=list(states[1][1])
keys(shell,[(1,(0,0,0)),(90,(0,0,.25)),(210,(0,0,.25)),(300,(0,0,0))])
keys(battery,[(1,(0,0,0)),(90,(0,.018,.16)),(210,(0,.018,.16)),(300,(0,0,0))])
keys(thermal,[(1,(0,0,0)),(90,(0,0,.12)),(210,(0,0,.12)),(300,(0,0,0))])
keys(board,[(1,(0,0,0)),(90,(0,0,.075)),(210,(0,0,.075)),(300,(0,0,0))])
keys(support,[(1,(0,0,0)),(90,(0,0,.025)),(210,(0,0,.025)),(300,(0,0,0))])
keys(gimbal,[(1,(0,0,0)),(90,(0,-.06,.006)),(210,(0,-.06,.006)),(300,(0,0,0))])
keys(lid,[(1,(0,0,0)),(90,(0,0,0)),(150,(0,0,.09)),(210,(0,0,.09)),(300,(0,0,0))])
for i,g in enumerate(cells):keys(g,[(1,(0,0,0)),(90,(0,0,0)),(150,(0,0,.018+i*.016)),(210,(0,0,.018+i*.016)),(300,(0,0,0))])
for i,g in enumerate(optical_groups):keys(g,[(1,(0,0,0)),(150,(0,0,0)),(210,(0,-(5-i)*.026,0)),(300,(0,0,0))])
scene.frame_start=1;scene.frame_end=300
for fr,name in [(1,'ASSEMBLED'),(90,'BODY_EXPLODED'),(150,'BATTERY_CUTAWAY'),(210,'OPTICS_EXPANDED'),(300,'REASSEMBLED')]:scene.timeline_markers.new(name,frame=fr)
# Verify physical stack order and bounds used for this visual design.
assert .053+.00125 < .060-.0008
assert .065 < .071-.0015
assert .07375 < .080
assert .101 < .1035
report={'stack_clearances_m':{'support_to_pcb':.00495,'chip_to_thermal_cover':.0045,'thermal_to_battery':.00625},'battery_cartridge_m':[.075,.141,.027],'cell_count':4,'key_states':[1,90,150,210,300],'note':'Conceptual stack fit and assembly bounds; not a complete mesh collision or engineering certification.'}
(ROOT/'renders/interior-v04/validation.json').write_text(json.dumps(report,indent=2))
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def camera(name,loc,target,scale):
 d=bpy.data.cameras.new(name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,target);return o
cams={
 'assembled':bpy.data.objects['CAM_hero'],
 'exploded':camera('CAM_EXPLODED',(.46,-.72,.54),(0,0,.19),.83),
 'battery':camera('CAM_BATTERY',(.27,-.40,.54),(0,.02,.32),.34),
 'computer':camera('CAM_COMPUTER',(.20,-.28,.36),(0,0,.14),.38),
 'optics':camera('CAM_OPTICS',(.24,-.43,.15),(0,-.28,.041),.26)}
def descendants(o):return {o,*o.children_recursive}
model=[o for o in bpy.data.objects if o.type in ['MESH','FONT','CURVE'] and o.name!='STUDIO_GROUND']
# Separate scene presentation from asset animation. All model parts visible in saved scene.
for o in model:o.hide_render=False
scene.frame_set(1);scene.camera=cams['assembled']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-interior-v04.blend'))
for view,frame,show in [('assembled',1,None),('exploded',90,None),('battery',150,descendants(battery)),('computer',90,descendants(board)|descendants(thermal)|descendants(support)),('optics',210,descendants(gimbal))]:
 scene.frame_set(frame);scene.camera=cams[view]
 for o in model:o.hide_render=show is not None and o not in show
 if view=='optics':
  for o in legacy_optics:o.hide_render=True
 scene.render.filepath=str(ROOT/'renders/interior-v04'/f'{view}.png');bpy.ops.render.render(write_still=True)
print('INTERIOR_V04_COMPLETE')
