import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v16.blend'))
for o in bpy.data.objects:
 if o.name.startswith(('CAMERA_','GIMBAL_','LENS_')):
  print(o.name,o.type,'parent',o.parent.name if o.parent else None,'loc',list(o.location),'world',list(o.matrix_world.translation),'dims',list(o.dimensions),'mods',[m.type for m in o.modifiers])
p=bpy.data.materials['Multi-coated lens glass'].node_tree.nodes.get('Principled BSDF');print('PRINCIPLED_INPUTS',[i.name for i in p.inputs])
