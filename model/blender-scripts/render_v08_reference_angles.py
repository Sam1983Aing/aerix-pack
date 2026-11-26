"""Two additional transparent renders for private comparison with the DJI gallery."""
import bpy
from mathutils import Vector,Quaternion
from math import radians
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=bpy.context.scene
cam=bpy.data.objects['Studio.camera.three-quarter'].copy()
cam.data=cam.data.copy()
s.collection.objects.link(cam)
s.camera=cam
cam.data.type='PERSP'
cam.data.lens=50
s.render.film_transparent=True
s.render.image_settings.color_mode='RGBA'
s.render.resolution_x=1550
s.render.resolution_y=950
s.cycles.samples=18
bpy.data.objects['Studio.floor'].hide_render=True
for name,frame,direction,radius,roll in [('near-level',1,(-.37,.925,-.045),.628,-2),('folded',121,(-.68,.94,.42),.450,0)]:
    target=Vector((0,-.006,.027))
    cam.location=target+Vector(direction).normalized()*radius
    cam.rotation_euler=((target-cam.location).to_track_quat('-Z','Y')@Quaternion((0,0,1),radians(roll))).to_euler()
    cam.data.lens=72 if name=='near-level' else 77
    s.frame_set(frame)
    s.render.filepath=str(root/f'references/real/mini-2/v08-{name}-render.png')
    bpy.ops.render.render(write_still=True)
