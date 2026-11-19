"""A straight-on orthographic macro for comparing equal margins around the lens."""
import bpy
from mathutils import Vector
from v05_detail import set_detail_camera
from v10_alignment import midpoint


def front_macro(scene):
    set_detail_camera(scene)
    cam=scene.camera
    target=midpoint(bpy.data.objects['Camera.face_trim'])
    cam.location=target+Vector((0,.245,0))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.050
