import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'));s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();p=Vector((0,-.25,.038));d=Vector((0,1,0))
for i in range(15):
 hit,loc,n,fi,ob,m=s.ray_cast(deps,p,d)
 if not hit:break
 print('CENTER_RAY',ob.name,tuple(loc),ob.data.materials[0].name if ob.type=='MESH' else '')
 p=loc+d*.00002
for name in ['LENS_FRONT_ELEMENT','LENS_MIDDLE_ELEMENT']:bpy.data.objects[name].hide_render=True
s.camera=bpy.data.objects['CAM_main_camera'];s.cycles.samples=20;s.render.resolution_percentage=60;s.render.filepath=str(R/'renders/exterior-v17/optics-no-front-glass.png');bpy.ops.render.render(write_still=True)
