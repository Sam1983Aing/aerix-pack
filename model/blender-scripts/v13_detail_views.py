"""Matched detail cameras for reviewing the camera cheeks and both front hinge seats."""
import bpy
from mathutils import Vector

def detail_view(scene, name):
    scene.frame_set(1)
    camera=bpy.data.objects['Studio.camera.three-quarter'].copy()
    camera.data=camera.data.copy()
    scene.collection.objects.link(camera)
    if name=='camera-sides':
        target=Vector((0,.058,.020))
        offset=Vector((.068,.26,.012))
        width=.052
    else:
        sign=-1 if name.endswith('left') else 1
        target=Vector((sign*.0305,.015,.0365))
        offset=Vector((sign*.177,-.048,-.052))
        width=.048
    camera.location=target+offset
    camera.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=width
    scene.camera=camera
    bpy.data.objects['Studio.floor'].hide_render=True
    scene.cycles.samples=36

DETAILS=('camera-sides','front-root-left','front-root-right')
