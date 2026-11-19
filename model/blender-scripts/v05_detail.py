import bpy
from mathutils import Vector

def set_detail_camera(scene):
    cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
    cam.data=cam.data.copy()
    scene.collection.objects.link(cam)
    target=Vector((0,.050,.0233))
    cam.location=target+Vector((.091,.245,-.008))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=.052
    scene.camera=cam
    bpy.data.objects['Studio.floor'].hide_render=True

    # A narrow studio softbox makes separate catchlights on the curved elements.
    # Only the dedicated macro uses this light; the five comparison views share V01 lighting.
    light=bpy.data.lights.new('Macro optical strip','AREA')
    light.shape='RECTANGLE'
    light.size=.020
    light.size_y=.010
    light.energy=.24
    strip=bpy.data.objects.new('Macro optical strip',light)
    scene.collection.objects.link(strip)
    strip.location=target+Vector((.017,.125,.036))
    strip.rotation_euler=(target-strip.location).to_track_quat('-Z','Y').to_euler()
