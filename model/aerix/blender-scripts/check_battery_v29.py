"""Check V29 battery fit, moving service parts and exact reassembly."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];O=R/'renders/battery-v29';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v29.blend'));s=bpy.context.scene;s.frame_set(400);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get();root=bpy.data.objects['BATTERY_ROOT'];parts=[o for o in root.children_recursive if o.type in {'MESH','CURVE','FONT'}]
geometry={}
def cache(o):
 if o.name not in geometry:
  e=o.evaluated_get(d);m=e.to_mesh();geometry[o.name]=([v.co.copy() for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);e.to_mesh_clear()
 return geometry[o.name]
def surf(o):
 vs,fs=cache(o);v=[o.matrix_world@p for p in vs];return {'v':v,'f':fs,'b':[(min(p[i] for p in v),max(p[i] for p in v)) for i in range(3)]}
def tree(a):
 if 't' not in a:a['t']=BVHTree.FromPolygons(a['v'],a['f'])
 return a['t']
def hit(a,b):
 if not all(a['b'][i][0]<b['b'][i][1] and b['b'][i][0]<a['b'][i][1] for i in range(3)):return 0
 return len(tree(a).overlap(tree(b)))
staticnames=['BODY_SHELL_TOP','BODY_CRADLE','FRONT_VISOR_FRAME','FRONT_VISOR','REAR_FASCIA','MAIN_PCB','THERMAL_COVER']+[o.name for o in s.objects if o.name.startswith(('COOLING_RIB','BATTERY_GUIDE','INNER_SHELL','CHASSIS_POWER'))]
static={n:surf(bpy.data.objects[n]) for n in staticnames};closed={o.name:surf(o) for o in parts};fit=[]
for name,a in closed.items():
 for n,b in static.items():
  h=hit(a,b)
  if h:fit.append({'battery':name,'other':n,'triangles':h})
print('CLOSED_FIT',fit,flush=True)
# Minimum positive roof clearance above the entire top lid footprint, with corner rays omitted outside its rounded outline.
lid=closed['BAT29_TOP_LID'];roof=tree(static['BODY_SHELL_TOP']);roofgaps=[];misses=[]
for i in range(15):
 for j in range(27):
  x=lid['b'][0][0]+(lid['b'][0][1]-lid['b'][0][0])*i/14;y=lid['b'][1][0]+(lid['b'][1][1]-lid['b'][1][0])*j/26
  p,n,idx,dist=roof.ray_cast(Vector((x,y,lid['b'][2][1])),Vector((0,0,1)))
  if p is not None:roofgaps.append(dist)
  else:misses.append([x,y])
# Moving cells, lid and side cover versus the stationary cartridge/BMS/harness, and versus one another.
def groupof(o):
 q=o
 while q.parent and q.parent!=root:q=q.parent
 return q.name if q.name in ['BATTERY_LID_ROOT','BATTERY_SIDE_COVER_ROOT'] or q.name.startswith('CELL_') else 'fixed'
moving=[o for o in parts if groupof(o)!='fixed'];fixed=[o for o in parts if groupof(o)=='fixed'];service=[];seats=[]
frames=[551,563,575,587,599,609,615,623,635,647,659,671]
for frame in frames:
 s.frame_set(frame);bpy.context.view_layer.update();fx={o.name:surf(o) for o in fixed};mv={o.name:surf(o) for o in moving}
 for i,o in enumerate(moving):
  a=mv[o.name]
  for other in fixed:
   h=hit(a,fx[other.name])
   if not h:continue
   # Explicit intended seats: cell retention band compresses its foam pad; screws seat in bores; side cover sits against gasket/return.
   seating=(o.name.startswith('BAT29_CELL_BAND') and other.name=='BAT29_CELL_FOAM_FLOOR') or (o.name.startswith('BAT29_LID_TORX') and other.name.startswith(('BAT29_LID_BOSS','BAT29_BOSS_INSERT'))) or (groupof(o)=='BATTERY_SIDE_COVER_ROOT' and other.name.startswith(('BAT29_SIDE_PANEL_')))
   rec={'frame':frame,'moving':o.name,'fixed':other.name,'triangles':h}
   (seats if seating else service).append(rec)
  for other in moving[i+1:]:
   if groupof(o)==groupof(other):continue
   h=hit(a,mv[other.name])
   if h:service.append({'frame':frame,'moving':o.name,'other_moving':other.name,'triangles':h})
 print('SERVICE_FRAME',frame,'hits',len(service),flush=True)
# Major arm and blade motions against the assembled battery envelope.
fold=[];names=[p+t for t in ['FL','FR','RL','RR'] for p in ['ARM_','ARM_INLAY_','MOTOR_','MOTOR_BASE_','FOOT_PAD_']]+[f'BLADE_{t}_{k}' for t in ['FL','FR','RL','RR'] for k in [0,1]]
for frame in sorted(set(range(1,362,12))|{44,98,167,260,361}):
 s.frame_set(frame);bpy.context.view_layer.update()
 for n in names:
  a=surf(bpy.data.objects[n])
  for name,b in closed.items():
   h=hit(a,b)
   if h:fold.append({'frame':frame,'moving':n,'battery':name,'triangles':h})
s.frame_set(400);bpy.context.view_layer.update();before={o.name:[v for row in o.matrix_world for v in row] for o in parts};s.frame_set(971);bpy.context.view_layer.update();err=max(abs(a-b) for o in parts for a,b in zip(before[o.name],[v for row in o.matrix_world for v in row]))
report={'closed_surface_contacts':fit,'service_motion_contacts':service,'intentional_seating_contacts':seats,'service_frames':frames,'fold_surface_contacts':fold,'fold_samples':35,'roof_samples':len(roofgaps),'roof_min_clearance_mm':min(roofgaps)*1000,'roof_missed_rays':misses,'exact_reassembly_matrix_error':err,'scope':'Triangle surfaces sampled on cartridge and service parts, major exterior folding surfaces, nearby internal layers and lid-to-roof rays. Intentional fastener/gasket/foam seats are reported separately. This is a visual fit check, not engineering certification.'}
(O/'fit-validation.json').write_text(json.dumps(report,indent=2));print('V29_FIT',len(fit),len(service),len(fold),'roof_mm',min(roofgaps)*1000,'reassembly',err,flush=True)
