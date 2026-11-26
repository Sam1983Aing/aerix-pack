"""Render the saved revision in the V01 studio, including its detail close-up."""
from pathlib import Path
import bpy
import sys
from mathutils import Vector

root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
version=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert version in ('v02','v03','v04','v05','v06','v07','v08','v09','v10','v11','v12','v13','v14','v14a','v14b','v14c') and Path(bpy.data.filepath).resolve()==root/'blender'/f'drone-{version}.blend'
dest=root/'renders'/version
dest.mkdir(parents=True,exist_ok=True)


def render(name):
    target=dest/f'{version}-{name}.png'
    if target.exists(): return
    # Publish only a complete PNG. Interrupted jobs can resume safely.
    temp=target.with_name('.writing-'+target.name)
    scene.render.filepath=str(temp)
    bpy.ops.render.render(write_still=True)
    temp.replace(target)


def rear_attachment_camera():
    cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
    cam.data=cam.data.copy()
    scene.collection.objects.link(cam)
    target=Vector((0,-.044,.018))
    cam.location=target+Vector((.106,-.22,-.058))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.125
    scene.camera=cam
    bpy.data.objects['Studio.floor'].hide_render=True


sys.path.insert(0,str(root/'scripts'))
from v05_detail import set_detail_camera
if '--before-front-joints' in sys.argv:
    from v13_detail_views import DETAILS,detail_view
    assert version=='v12'
    for name in DETAILS:
        if '--roots-only' in sys.argv and not name.startswith('front-root'): continue
        detail_view(scene,name)
        scene.render.filepath=str(root/f'teach/shots/v13/before-v12-{name}-closeup.png')
        bpy.ops.render.render(write_still=True)
    sys.exit(0)

if '--before-hatch' in sys.argv:
    from v12_shell_view import shell_detail_camera
    assert version=='v11'
    for name,folded in [('hatch-closeup',False),('folded-hatch',True)]:
        shell_detail_camera(scene,folded)
        scene.render.filepath=str(root/f'teach/shots/v12/before-v11-{name}.png')
        bpy.ops.render.render(write_still=True)
    sys.exit(0)

if '--before-materials' in sys.argv:
    from v11_material_view import material_camera
    assert version=='v10'
    scene.frame_set(1)
    material_camera(scene)
    scene.render.filepath=str(root/'teach/shots/v11/before-v10-material-closeup.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

if '--before-alignment' in sys.argv:
    from v10_camera_view import front_macro
    assert version=='v09'
    scene.frame_set(1)
    front_macro(scene)
    scene.cycles.samples=40
    scene.render.filepath=str(root/'teach/shots/v10/before-v09-camera-closeup.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

if '--before-gimbal' in sys.argv:
    assert version=='v04'
    scene.frame_set(1)
    set_detail_camera(scene)
    scene.cycles.samples=56
    scene.render.filepath=str(root/'teach/shots/v05/before-v04-gimbal-closeup.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

if '--before-attachments' in sys.argv:
    assert version=='v03'
    scene.frame_set(1)
    rear_attachment_camera()
    scene.render.filepath=str(root/'teach/shots/v04/before-v03-rear-attachments-closeup.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)


if version in ('v14','v14a','v14b','v14c'):
    for frame,pose in ((1,'unfolded'),(121,'folded')):
        scene.frame_set(frame)
        scene.camera=bpy.data.objects['Studio.camera.three-quarter']
        render(pose+'-three-quarter')
    scene.frame_set(1)
    scene.camera=bpy.data.objects['Studio.camera.lens']
    scene.cycles.samples=72
    render('lens-closeup')
    scene.cycles.samples=28

for frame,pose in ((1,'unfolded'),(121,'folded')):
    scene.frame_set(frame)
    for view in ('three-quarter','side','front','back','top'):
        scene.camera=bpy.data.objects['Studio.camera.'+view]
        render(f'{pose}-{view}')
scene.frame_set(1)
if version in ('v14','v14a','v14b','v14c'):
    sys.exit(0)
if version=='v13':
    from v13_detail_views import DETAILS,detail_view
    for name in DETAILS:
        detail_view(scene,name)
        render(name+'-closeup')
    sys.exit(0)
if version=='v12':
    from v12_shell_view import shell_detail_camera
    for name,folded in [('hatch-closeup',False),('folded-hatch',True)]:
        shell_detail_camera(scene,folded)
        render(name)
    sys.exit(0)
if version=='v11':
    from v11_material_view import material_camera
    material_camera(scene)
    render('material-closeup')
if version in ('v10','v11'):
    from v10_camera_view import front_macro
    front_macro(scene)
    scene.cycles.samples=40
    render('camera-closeup')
    sys.exit(0)
if version=='v09':
    from v09_gear_views import gear_detail_camera
    scene.cycles.samples=32
    for part in ('front','rear'):
        gear_detail_camera(scene,part)
        render(f'{part}-gear-closeup')
    sys.exit(0)
if version=='v05':
    set_detail_camera(scene)
    scene.cycles.samples=72
    render('gimbal-closeup')
    sys.exit(0)
cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
cam.data=cam.data.copy()
scene.collection.objects.link(cam)
if version=='v02':
    cam.location+=Vector((0,.010,.013))
    cam.data.ortho_scale=.164
elif version=='v08':
    # Compact nose, inset intake and the connection from the shoulder to the camera bay.
    target=Vector((0,.032,.033))
    cam.location=target+Vector((-.14,.24,.092))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.158
elif version=='v07':
    # The rear sleeve, its cuff and the entrance into the motor are visible together.
    target=Vector((.053,-.039,.026))
    cam.location=target+Vector((.07,-.13,.33))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.094
elif version in ('v03','v06'):
    # Look from the side and slightly aft so the stationary blades do not
    # mask the front moving cuff as they do in the locked three-quarter view.
    target=Vector((.046,.044,.039))
    cam.location=target+Vector((.29,-.14,.105))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.124
else:
    target=Vector((.091,.075,.050))
    cam.location=target+Vector((.15,.22,.165))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.063
scene.camera=cam
render({'v02':'shell-closeup','v03':'arm-hinge-closeup','v04':'motor-propeller-closeup','v06':'arm-closeup','v07':'rear-arm-closeup','v08':'nose-shoulder-closeup'}[version])
if version=='v04':
    rear_attachment_camera()
    render('rear-attachments-closeup')
