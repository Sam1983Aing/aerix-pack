"""Verify the saved studio cameras and the folding model in both deliveries."""
import sys
import json
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v13_joints import check_joints
from check_v09_gear import inspect_gear
from v13_detail_views import detail_view

def cameras():
    return {o.name:(list(o.matrix_world.to_translation()), list(o.matrix_world.to_quaternion()),o.data.type,o.data.ortho_scale)
            for o in bpy.context.scene.objects if o.type=='CAMERA'}
def check(group):
    result=check_joints(group)
    result['fold']=inspect_gear(group)
    return result

scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v14.blend'
studio=scene.objects['Studio.floor'].users_collection[0]
scene.frame_set(1)
rig=json.loads((root/'viewer/v14-studio.json').read_text())
assert sum(1 for o in studio.objects if o.type=='LIGHT')==len(rig['panels'])
for p in rig['panels']:
    lamp=studio.objects['Studio.'+p['name']]
    assert abs(lamp.data.energy-p['watts'])<1e-5
    assert abs(lamp.data.size-p['width'])<1e-6 and abs(lamp.data.size_y-p['height'])<1e-6
    assert (lamp.location-Vector(p['position'])).length<1e-6
    aim=lamp.matrix_world.to_quaternion()@Vector((0,0,-1))
    assert aim.dot((Vector(p['aim'])-lamp.location).normalized())>.999999
actual=cameras()
result=check(bpy.data.collections['V14 | Aircraft'])
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/drone-v13.blend'))
scene=bpy.context.scene
detail_view(scene,'camera-sides')
scene.camera.name='Studio.camera.lens'
bpy.context.view_layer.update()
previous=cameras()
assert previous.keys()==actual.keys()
for name,cam in actual.items():
    assert cam==previous[name],name

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(root/'exports/drone-v14.glb'))
exported=check(bpy.context.scene)
assert result==exported
approved=json.loads((root/'measurements/v13-native-audit.json').read_text())
assert all(value==approved[key] for key,value in result.items())
result['matching_camera_names']=sorted(actual)
result['studio_panel_count']=len(rig['panels'])
(root/'measurements/v14-studio-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified five overview cameras, the lens macro, the light rig and native/exported folding.')
