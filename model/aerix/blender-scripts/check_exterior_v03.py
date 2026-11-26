"""Read-only structural checks on the saved v03 scene."""
import bpy, json
from mathutils import Vector
from pathlib import Path
bpy.context.view_layer.update()
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v.z for v in p),max(v.z for v in p)]
checks={}
for tag in ['FL','FR','RL','RR']:
 foot=bounds(bpy.data.objects['LANDING_FOOT_'+tag]); base=bounds(bpy.data.objects['MOTOR_BASE_'+tag])
 checks[tag+'_foot_connected']=foot[1]>=base[0]
 checks[tag+'_propeller_parent']=bpy.data.objects['PROPELLER_'+tag].parent.name=='ARM_'+tag+'_ROOT'
checks['shells_separate']=bpy.data.objects.get('BODY_SHELL_TOP') is not None and bpy.data.objects.get('BODY_CRADLE') is not None
checks['blade_count']=len([o for o in bpy.data.objects if o.name.startswith('BLADE_') and not o.name.startswith('BLADE_TIP_')])==8
checks['camera_group']=bpy.data.objects['CAMERA_HOUSING'].parent.name=='CAMERA_GIMBAL_ROOT'
for tag in ['FL','FR','RL','RR']:
 motor=bpy.data.objects['MOTOR_'+tag]
 expected_y=-.140 if tag.startswith('F') else .140
 checks[tag+'_motor_position']=abs(motor.matrix_world.translation.y-expected_y)<1e-6
 blade=bpy.data.objects['BLADE_'+tag+'_0']
 checks[tag+'_smooth_blade']=any(m.type=='SUBSURF' for m in blade.modifiers)
assert all(checks.values()),checks
out=Path(bpy.data.filepath).parents[1]/'renders/exterior-v03/structure-checks.json'
out.write_text(json.dumps(checks,indent=2))
print('SAVED_SCENE_CHECKS',json.dumps(checks))
