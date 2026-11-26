import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v07.blend'))
bpy.context.scene.frame_set(1)
# Export a temporary evaluated scene; preserve the editable source file.
for o in list(bpy.data.objects):
 if o.hide_render or o.type in {'LIGHT','CAMERA'} or o.name=='STUDIO_GROUND' or o.name=='INTERNAL_ENVELOPES':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.context.scene.objects):
 if o.type in {'MESH','CURVE','FONT'}:
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
# Procedural roughness is approximated for this inspection export.
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if not p:continue
 for slot in ['Roughness','Normal']:
  for link in list(p.inputs[slot].links):m.node_tree.links.remove(link)
 if m.name.startswith('Titanium'):p.inputs['Roughness'].default_value=.47
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/aerix-review-v07.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('REVIEW_EXPORT_COMPLETE')
