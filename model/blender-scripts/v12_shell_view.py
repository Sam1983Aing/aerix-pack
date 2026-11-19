"""Matched cameras for inspecting the side grille and the closed battery door."""
import bpy
from mathutils import Vector


def shell_detail_camera(scene,folded=False):
    scene.frame_set(121 if folded else 1)
    cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
    cam.data=cam.data.copy()
    scene.collection.objects.link(cam)
    target=Vector((.009,-.048,.038)) if not folded else Vector((0,-.013,.030))
    offset=Vector((.24,-.14,.083)) if not folded else Vector((.17,-.24,.120))
    cam.location=target+offset
    cam.rotation_euler=(-offset).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.092 if not folded else .208
    scene.camera=cam
    scene.cycles.samples=40
