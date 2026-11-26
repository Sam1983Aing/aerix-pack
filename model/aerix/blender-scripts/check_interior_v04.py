import bpy, json
from pathlib import Path
s=bpy.context.scene
names=['BODY_SHELL_TOP','BATTERY_ROOT','THERMAL_ROOT','FLIGHT_COMPUTER_ROOT','INTERNAL_SUPPORT_ROOT','CAMERA_GIMBAL_ROOT','BATTERY_LID_ROOT']+[f'CELL_{i}_ROOT' for i in range(1,5)]+['OPTICS_'+n+'_ROOT' for n in ['FRONT_WINDOW','FRONT_CELL','REAR_CELL','IR_CUT_FILTER','CMOS_SENSOR']]
s.frame_set(1);a={n:tuple(bpy.data.objects[n].matrix_world.translation) for n in names}
s.frame_set(300);b={n:tuple(bpy.data.objects[n].matrix_world.translation) for n in names}
checks={'all_groups_return_to_assembled':all(max(abs(x-y) for x,y in zip(a[n],b[n]))<1e-7 for n in names),'four_pouch_cells':len([o for o in bpy.data.objects if o.name.startswith('POUCH_CELL_')])==4,'five_optical_groups':len([o for o in bpy.data.objects if o.name.startswith('OPTICS_') and o.name.endswith('_ROOT') and o.name!='OPTICS_ROOT'])==5}
s.frame_set(90)
checks['shell_above_battery']=bpy.data.objects['BODY_SHELL_TOP'].location.z>bpy.data.objects['BATTERY_ROOT'].location.z
checks['battery_lid_still_closed_at_body_explosion']=bpy.data.objects['BATTERY_LID_ROOT'].location.length<1e-7
assert all(checks.values()),checks
out=Path(bpy.data.filepath).parents[1]/'renders/interior-v04/animation-checks.json';out.write_text(json.dumps(checks,indent=2))
print('INTERIOR_CHECKS',checks)
