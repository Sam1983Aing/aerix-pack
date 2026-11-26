import bpy
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-interior-v04.blend'))
s=bpy.context.scene
cam=bpy.data.objects['CAM_COMPUTER'];cam.data.ortho_scale=.38;cam.rotation_euler=(Vector((0,0,.14))-cam.location).to_track_quat('-Z','Y').to_euler()
p=bpy.data.materials['Optical element'].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.75,.92,.95,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.04;p.inputs['Transmission Weight'].default_value=1
s.frame_set(1);s.camera=bpy.data.objects['CAM_hero'];bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-interior-v04.blend'))
model=[o for o in bpy.data.objects if o.type in ['MESH','FONT','CURVE'] and o.name!='STUDIO_GROUND']
for view,fr,groups in [('computer',90,['FLIGHT_COMPUTER_ROOT','THERMAL_ROOT','INTERNAL_SUPPORT_ROOT']),('optics',210,['CAMERA_GIMBAL_ROOT'])]:
 show=set()
 for name in groups:
  ob=bpy.data.objects[name];show.add(ob);show.update(ob.children_recursive)
 for ob in model:ob.hide_render=ob not in show or (view=='optics' and ob.name.startswith('LENS_'))
 s.frame_set(fr);s.camera=bpy.data.objects['CAM_'+view.upper()];s.render.filepath=str(ROOT/'renders/interior-v04'/f'{view}.png');bpy.ops.render.render(write_still=True)
