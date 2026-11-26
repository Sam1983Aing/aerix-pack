import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'))
for tag in ['FL','FR','RL','RR']:
 ob=bpy.data.objects['HINGE_CAP_'+tag]
 for face in ob.data.polygons:
  if abs(face.normal.z)>.999:face.use_smooth=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v12.blend'))
