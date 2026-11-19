"""Matched close-ups at the three angles called out in the exterior review."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
VIEWS={
    'front-trim': ((0,.06,.020),(.004,.210,0),.040),
    'side-contour': ((-.021,.001,.026),(-.24,-.016,-.010),.125),
    'lower-cheek': ((-.017,.029,.024),(-.165,.066,-.175),.074)
}
def render_details(dest, prefix, preview=False):
    scene=bpy.context.scene
    scene.frame_set(1)
    camera=bpy.data.objects['Studio.camera.three-quarter'].copy()
    camera.data=camera.data.copy()
    scene.collection.objects.link(camera)
    dest.mkdir(parents=True,exist_ok=True)
    for name,(point,offset,width) in VIEWS.items():
        if '--side-only' in sys.argv and name!='side-contour': continue
        scene.camera=camera
        camera.location=Vector(point)+Vector(offset)
        camera.rotation_euler=(-Vector(offset)).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=width
        bpy.data.objects['Studio.floor'].hide_render=name in ('lower-cheek','side-contour')
        scene.cycles.samples=12 if preview else 36
        scene.render.resolution_percentage=55 if preview else 100
        target=dest/(prefix+'-'+name+'.png')
        temp=target.with_name('.writing-'+target.name)
        scene.render.filepath=str(temp)
        bpy.ops.render.render(write_still=True)
        temp.replace(target)

if __name__=='__main__':
    v=Path(bpy.data.filepath).stem.removeprefix('drone-')
    assert v in ('v14','v14a')
    dest=root/('teach/shots/v14a' if v=='v14' else 'renders/v14a')
    render_details(dest,'before-v14' if v=='v14' else v)
