"""Sample fit, layer interfaces, detail motion, folding and exact reassembly."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];O=R/'renders/interior-v30';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v30.blend'));s=bpy.context.scene;s.frame_set(400);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();c=json.loads((O/'integration-config.json').read_text());parts=[bpy.data.objects[n] for n in c['new_mesh_names']];cache={}
def surface(o):
 if o.name not in cache:
  e=o.evaluated_get(d);m=e.to_mesh();cache[o.name]=([v.co.copy() for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);e.to_mesh_clear()
 vs,fs=cache[o.name];v=[o.matrix_world@p for p in vs];return {'v':v,'f':fs,'b':[(min(p[i] for p in v),max(p[i] for p in v)) for i in range(3)]}
def tree(a):
 if 'tree' not in a:a['tree']=BVHTree.FromPolygons(a['v'],a['f'])
 return a['tree']
def hit(a,b):
 if not all(a['b'][i][0]<b['b'][i][1]-1e-8 and b['b'][i][0]<a['b'][i][1]-1e-8 for i in range(3)):return 0
 return len(tree(a).overlap(tree(b)))
def family(o):
 while o.parent:
  if o.name in c['layer_roots']:return o.name
  o=o.parent
 return ''
def detailgroup(o):
 while o.parent:
  if o.name in c['tracks']:return o.name
  if o.name in c['layer_roots']:return 'fixed'
  o=o.parent
 return 'fixed'
# Exact mating interfaces are expected; report them separately.
def seat(a,b):
 names={a,b}
 if any(x.startswith('FC30_MOUNT_') for x in names) and any(x.startswith(('TR30_THREADED','TR30_BRASS')) for x in names):return True
 if any(x.startswith('FC30_TRAY_DOCK_') for x in names) and any(x.startswith(('TR30_DOCK_','TR30_CONNECTOR')) for x in names):return True
 if any(x.startswith('TH30_THERMAL_PAD') for x in names) and any(x.startswith(('FC30_PROCESSOR_HEATCAP','FC30_CPU_MARK')) for x in names):return True
 if any(x.startswith('TH30_SENSOR_CONTACT') for x in names) and any(x.startswith('FC30_THERMAL_SENSOR_POGO') for x in names):return True
 if any(x.startswith('FC30_IMU_DOCK_') for x in names) and any(x.startswith('FC30_IMU_') for x in names):return True
 if any(x.startswith('FC30_SERVICE_PLUG') for x in names) and any(x.startswith(('FC30_CONNECTOR_PIN','FC30_CAM_SOCKET','FC30_PWR_SOCKET','FC30_IO_SOCKET')) for x in names):return True
 if any(x.startswith('TR30_THREADED_POST') for x in names) and any(x.startswith('TR30_ISOLATION_SEAT') for x in names):return True
 if any(x.startswith('TR30_POST_SEAT_PIN') for x in names) and any(x.startswith('TR30_') for x in names):return True
 return False
fixednames=['BODY_SHELL_TOP','BODY_CRADLE','FRONT_VISOR_FRAME','FRONT_VISOR','REAR_FASCIA','CAMERA_HOUSING','BAT29_CARTRIDGE_TRAY']+[o.name for o in bpy.data.objects['INTERIOR_CHASSIS_ROOT'].children_recursive if o.type in {'MESH','CURVE','FONT'}]
fixed={n:surface(bpy.data.objects[n]) for n in fixednames};closed={o.name:surface(o) for o in parts};fit=[];cross=[];seats=[]
for o in parts:
 for n,b in fixed.items():
  h=hit(closed[o.name],b)
  if h:
   rec={'part':o.name,'other':n,'triangles':h}
   if o.name.startswith('TR30_') and n.startswith('CHASSIS_MOUNT'):seats.append(rec)
   else:fit.append(rec)
for i,o in enumerate(parts):
 for q in parts[i+1:]:
  if family(o)==family(q):continue
  h=hit(closed[o.name],closed[q.name])
  if h:(seats if seat(o.name,q.name) else cross).append({'part':o.name,'other':q.name,'triangles':h})
print('V30_ASSEMBLY',len(fit),len(cross),flush=True)
# Sample detail groups versus fixed same-layer parts, other groups and neighboring layers.
service=[];frames=[1091,1101,1125,1149,1173,1197,1221,1251,1275,1299,1323,1347,1371,1401,1425,1449,1473,1497,1521]
for fr in frames:
 s.frame_set(fr);bpy.context.view_layer.update();surfs={o.name:surface(o) for o in parts}
 for i,o in enumerate(parts):
  if detailgroup(o)=='fixed':continue
  for q in parts:
   if q==o or (family(o)==family(q) and detailgroup(o)==detailgroup(q)):continue
   if detailgroup(q)!='fixed' and q.name<o.name:continue
   h=hit(surfs[o.name],surfs[q.name])
   if h:
    rec={'frame':fr,'part':o.name,'other':q.name,'triangles':h}
    (seats if seat(o.name,q.name) else service).append(rec)
 print('V30_SERVICE',fr,len(service),flush=True)
# Existing fold is retained; test the refined layers against the major moving surfaces.
fold=[];moving=[p+t for t in ['FL','FR','RL','RR'] for p in ['ARM_','ARM_INLAY_','MOTOR_','MOTOR_BASE_','FOOT_PAD_']]+[f'BLADE_{t}_{k}' for t in ['FL','FR','RL','RR'] for k in [0,1]]
for fr in sorted(set(range(1,362,12))|{44,98,167,260,361}):
 s.frame_set(fr);bpy.context.view_layer.update()
 for n in moving:
  a=surface(bpy.data.objects[n])
  for name,b in closed.items():
   h=hit(a,b)
   if h:fold.append({'frame':fr,'moving':n,'part':name,'triangles':h})
s.frame_set(400);bpy.context.view_layer.update();before={o.name:list(v for row in o.matrix_world for v in row) for o in parts};s.frame_set(1671);bpy.context.view_layer.update();error=max(abs(a-b) for o in parts for a,b in zip(before[o.name],[v for row in o.matrix_world for v in row]))
def gap(upper,lower):return (closed[upper]['b'][2][0]-closed[lower]['b'][2][1])*1000
report={'shell_and_chassis_contacts':fit,'cross_layer_contacts':cross,'detail_motion_contacts':service,'intentional_seats':seats,'fold_contacts':fold,'fold_samples':35,'detail_frames':frames,'reassembly_matrix_error':error,'interfaces_mm':{'processor_to_pad':gap('TH30_THERMAL_PAD','FC30_PROCESSOR_HEATCAP'),'pad_to_copper':gap('TH30_COPPER_SPREADER','TH30_THERMAL_PAD'),'copper_to_cover':gap('TH30_RIBBED_COVER','TH30_COPPER_SPREADER'),'post_to_pcb':gap('FC30_MAIN_PCB','TR30_THREADED_POST'),'thermal_fin_to_battery':(fixed['BAT29_CARTRIDGE_TRAY']['b'][2][0]-closed['TH30_COOLING_FIN']['b'][2][1])*1000},'scope':'Sampled triangle contacts across refined layers, neighboring shell/chassis/battery, independent detail groups and major folding surfaces. Declared connector, fastener and compression seats are listed separately; this is a visual fit check.'}
(O/'fit-validation.json').write_text(json.dumps(report,indent=2));print('V30_FIT_DONE',len(fit),len(cross),len(service),len(fold),error,report['interfaces_mm'],flush=True)

report['pocket_floor_heights_mm']=[tree(closed['TR30_POCKETED_TRAY']).ray_cast(Vector((0,y/1000,.08)),Vector((0,0,-1)))[0].z*1000 for y in [-67,-24,29]]
report['passed']=not(fit or cross or service or fold) and error<1e-8 and all(abs(z-58.6)<.001 for z in report['pocket_floor_heights_mm'])
(O/'fit-validation.json').write_text(json.dumps(report,indent=2))
assert report['passed'], 'Resolve geometry contacts or pocket/reassembly failures before delivery'
