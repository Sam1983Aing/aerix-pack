"""Centre the existing glass, barrel, sensor and the matching bore in the V09 camera."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v10_alignment import STACK,midpoint,alignment
from check_v09_gear import inspect_gear
from check_v04_assembly import audit

assert Path(bpy.data.filepath)==root/'blender/drone-v09.blend'
scene=bpy.context.scene
scene.frame_set(1)
group=bpy.data.collections['V09 | Aircraft']
objects=group.objects
before=alignment(objects)
bezel=midpoint(objects['Camera.face_trim'])
delta=bezel-midpoint(objects['Camera.lens_barrel'])
delta.y=0  # Preserve axial positions, lens curvature, air spaces and barrel seats.
assert abs(delta.x*1000-3.672)<.002 and abs(delta.z)<1e-7
block=objects['Camera.block']
# V05 authored eight 96-point exterior sections and four circular bore sections.
# V08 offset just the latter. Check their centres before adjusting the aperture.
assert len(block.data.vertices)==12*96
rings=[list(block.data.vertices)[i*96:(i+1)*96] for i in range(12)]
for i,ring in enumerate(rings):
    center=midpoint(block,ring)
    assert abs(center.x+(delta.x if i>=8 else 0)-bezel.x)<.000001
    assert abs(center.z-bezel.z)<.000001
for name in (*STACK,'Camera.block'):
    o=objects[name]
    movement=o.matrix_world.to_3x3().inverted()@delta
    vertices=list(o.data.vertices)[8*96:] if o==block else o.data.vertices
    for v in vertices: v.co+=movement
    o.data.update()
bpy.context.view_layer.update()
after=alignment(objects)
assert all(max(map(abs,offset))<.001 for offset in after.values()),after
for ring in rings[8:]:
    assert abs(midpoint(block,ring).x-bezel.x)<1e-7
report=inspect_gear(group)
# The camera's fixed optical seats can be inspected in its neutral pose; the
# complete fold has already been tested for new contacts by inspect_gear.
contacts=set(audit(group,[1])[0]['contacts'])
for a,b in [('Camera.block',STACK[0])]+[(STACK[0],part) for part in STACK[1:]]:
    assert tuple(sorted((a,b))) in contacts,(a,b)
report.update(before_xz_mm=before,after_xz_mm=after,correction_mm=round(delta.x*1000,4))
print(json.dumps(report,indent=2),flush=True)
blend=root/'blender/drone-v10.blend'
glb=root/'exports/drone-v10.glb'
assert not blend.exists() and not glb.exists()
group.name='V10 | Aircraft'
objects['Drone.V09'].name='Drone.V10'
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for obj in group.objects: obj.select_set(True)
pending=root/'exports/pending-v10.glb'
bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
    export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
pending.rename(glb)
(root/'measurements/v10-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
