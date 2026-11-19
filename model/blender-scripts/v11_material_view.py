"""Match the V10 and V11 material close-ups in the existing inspection studio."""
import bpy
from mathutils import Vector


def material_camera(scene):
    camera=bpy.data.objects['Studio.camera.three-quarter'].copy()
    camera.data=camera.data.copy()
    scene.collection.objects.link(camera)
    target=Vector((.082,.038,.046))
    camera.location=target+Vector((.17,.24,.128))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=.058
    scene.camera=camera
    scene.cycles.samples=56
