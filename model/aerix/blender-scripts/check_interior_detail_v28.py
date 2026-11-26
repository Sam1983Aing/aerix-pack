"""Measure stack interfaces, roof containment and original folding transforms."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];O=R/'renders/interior-v28';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-folding-v27.blend'));s=bpy.context.scene
names=['ARM_'+t+'_ROOT' for t in ['FL','FR','RL','RR']]+['PROPELLER_'+t for t in ['FL','FR','RL','RR']]+[f'BLADE_FOLD_{t}_{k}' for t in ['FL','FR','RL','RR'] for k in [0,1]]+['ARM_RL_FOLD_PITCH','ARM_RR_FOLD_PITCH'];before={}
frames=[1,44,98,167,260,310,361]
for f in frames:
 s.frame_set(f);bpy.context.view_layer.update();before[f]={n:[v for row in bpy.data.objects[n].matrix_world for v in row] for n in names}
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v28.blend'));s=bpy.context.scene;maxerr=0
for f in frames:
 s.frame_set(f);bpy.context.view_layer.update()
 for n in names:maxerr=max(maxerr,max(abs(a-b) for a,b in zip(before[f][n],[v for row in bpy.data.objects[n].matrix_world for v in row])))
s.frame_set(400);bpy.context.view_layer.update();d=bpy.context.evaluated_depsgraph_get()
def bounds(n):
 o=bpy.data.objects[n];e=o.evaluated_get(d);v=[e.matrix_world@Vector(v) for v in e.bound_box];return [[min(v[i] for v in v),max(v[i] for v in v)] for i in range(3)]
bb={n:bounds(n) for n in ['BATTERY_TRAY','BATTERY_LID','THERMAL_COVER','COOLING_RIB','MAIN_PCB','PROCESSOR','THERMAL_PAD','SUPPORT_TRAY_BASE','BOARD_STANDOFF','SUPPORT_STANDOFF_SEAT','BOARD_MOUNT_SCREW','PCB_SCREW_SHAFT']}
shell=bpy.data.objects['BODY_SHELL_TOP'];e=shell.evaluated_get(d);m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in m.polygons]);e.to_mesh_clear()
battery=bb['BATTERY_LID'];clearances=[]
for i in range(11):
 for j in range(19):
  x=battery[0][0]+(battery[0][1]-battery[0][0])*i/10;y=battery[1][0]+(battery[1][1]-battery[1][0])*j/18
  p,n,idx,dist=tree.ray_cast(Vector((x,y,battery[2][1])),Vector((0,0,1)))
  assert p is not None,(x,y)
  clearances.append(dist)
report={'fold_transform_max_error':maxerr,'fold_frames':frames,'roof_battery_samples':len(clearances),'min_roof_clearance_mm':min(clearances)*1000,'thermal_rib_to_battery_mm':(bb['BATTERY_TRAY'][2][0]-bb['COOLING_RIB'][2][1])*1000,'processor_to_pad_mm':(bb['THERMAL_PAD'][2][0]-bb['PROCESSOR'][2][1])*1000,'pad_to_cover_mm':(bb['THERMAL_COVER'][2][0]-bb['THERMAL_PAD'][2][1])*1000,'standoff_to_pcb_mm':(bb['MAIN_PCB'][2][0]-bb['BOARD_STANDOFF'][2][1])*1000,'standoff_seat_overlap_mm':(bb['SUPPORT_STANDOFF_SEAT'][2][1]-bb['BOARD_STANDOFF'][2][0])*1000,'bounds_m':bb}
checks={'fold_motion_preserved':maxerr<1e-7,'roof_clearance_positive':min(clearances)>.0005,'battery_above_thermal_ribs':report['thermal_rib_to_battery_mm']>1,'thermal_pad_seated':abs(report['processor_to_pad_mm'])<.05 and abs(report['pad_to_cover_mm'])<.05,'pcb_standoffs_seated':abs(report['standoff_to_pcb_mm'])<.05};report['checks']=checks
(O/'detail-fit-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(checks.values()),checks
