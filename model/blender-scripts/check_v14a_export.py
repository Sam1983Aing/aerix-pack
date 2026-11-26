"""Compare each exported fold frame with its V14 contacts; verify the saved optics."""
from pathlib import Path
import json
import sys
import bpy
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import audit
from check_v13_joints import check_joints
from v10_alignment import alignment

version = sys.argv[-1] if '--' in sys.argv else 'v14a'
assert version in ('v14a', 'v14b','v14c')
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/drone-v14.blend'))
base=audit(bpy.data.collections['V14 | Aircraft'],range(1,122))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(root/f'exports/drone-{version}.glb'))
scene=bpy.context.scene
actual=audit(scene,range(1,122))
removed_contacts=set()
for previous,current in zip(base,actual):
    assert len(current['groups'])==1,current['frame']
    removed_contacts.update(set(previous['contacts'])-set(current['contacts']))
    added=set(current['contacts'])-set(previous['contacts'])
    assert not added,(current['frame'],'new compared to V14',added)
    if 'size_mm' in previous: assert previous['size_mm']==current['size_mm']
result=check_joints(scene)
result['optical_center_xz_mm']=alignment(scene.objects)
native=json.loads((root/f'measurements/{version}-native-audit.json').read_text())
for k,v in result.items():
    if k!='optical_center_xz_mm': assert v==native[k],(k,v,native[k])
assert all(max(map(abs,v))<.001 for v in result['optical_center_xz_mm'].values())
result.update(frames_compared_to_v14=len(actual),removed_contact_pairs=sorted(removed_contacts),new_contacts=0,disconnected_frames=0)
(root/f'measurements/{version}-export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('Checked all frame contact pairs, both camera bearings, the centered optics and both front hinges.')
