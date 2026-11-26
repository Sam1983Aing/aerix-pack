"""Close-up cameras shared by the V08/V09 teaching shots, and V09 photo comparisons."""
from math import radians
from pathlib import Path
import sys
import bpy
from mathutils import Vector,Matrix,Quaternion
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))


def gear_detail_camera(scene,part):
    cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
    cam.data=cam.data.copy()
    scene.collection.objects.link(cam)
    target,offset,scale={
        'front':((.086,.038,.025),(.25,.18,.067),.138),
        'rear':((.013,-.055,.0075),(.24,-.15,.012),.062)
    }[part]
    target=Vector(target)
    cam.location=target+Vector(offset)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale
    scene.camera=cam
    return cam


def render_photos(scene,version,preview):
    from v09_photo_camera import axes,solve,W,H
    cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
    cam.data=cam.data.copy()
    scene.collection.objects.link(cam)
    scene.camera=cam
    cam.data.type='PERSP'
    cam.data.sensor_fit='HORIZONTAL'
    cam.data.sensor_width=36
    scene.render.film_transparent=True
    scene.render.image_settings.color_mode='RGBA'
    scene.render.resolution_percentage=65 if preview else 100
    scene.cycles.samples=8 if preview else 24
    bpy.data.objects['Studio.floor'].hide_render=True
    dest=root/'measurements' if preview else root/'references/real/mini-2'
    def render(label):
        scene.render.filepath=str(dest/f'{version}-{label}-render.png')
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    p=solve()
    right,up,forward=axes(p)
    cam.location=Vector(p[:3])*.001
    cam.rotation_euler=Matrix([list(right),list(up),list(-forward)]).transposed().to_euler()
    cam.data.lens=p[6]*cam.data.sensor_width/W
    scene.render.resolution_x,scene.render.resolution_y=W,H
    render('open-side')
    # Retain V08's folded photo camera so the gear change can also be compared directly.
    scene.frame_set(121)
    scene.render.resolution_x,scene.render.resolution_y=1550,950
    target=Vector((0,-.006,.027))
    cam.location=target+Vector((-.68,.94,.42)).normalized()*.450
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=77
    render('folded')


if __name__=='__main__':
    scene=bpy.context.scene
    version=Path(bpy.data.filepath).stem.removeprefix('drone-')
    preview='--preview' in sys.argv
    if '--photos' in sys.argv:
        render_photos(scene,'v09-preview' if preview else version,preview)
    else:
        scene.frame_set(1)
        scene.cycles.samples=10 if preview else 32
        scene.render.resolution_percentage=55 if preview else 100
        for part in ('front','rear'):
            gear_detail_camera(scene,part)
            if preview:
                dest=root/f'measurements/v09-preview-{part}-gear.png'
            elif version=='v08':
                dest=root/f'teach/shots/v09/before-v08-{part}-gear-closeup.png'
            else:
                dest=root/f'renders/{version}/{version}-{part}-gear-closeup.png'
            dest.parent.mkdir(exist_ok=True,parents=True)
            scene.render.filepath=str(dest)
            bpy.ops.render.render(write_still=True)
