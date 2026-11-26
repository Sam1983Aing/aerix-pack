"""Inspection export with baked crown microfinish. Source .blend is never overwritten."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v08.blend'))
s=bpy.context.scene;s.frame_set(1)
for o in list(bpy.data.objects):
 if o.hide_render or o.type in {'LIGHT','CAMERA'} or o.name=='STUDIO_GROUND' or o.name=='INTERNAL_ENVELOPES':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.context.scene.objects):
 if o.type in {'MESH','CURVE','FONT'}:
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
# Body-only UVs and baked roughness/normal retain the satin microfinish in the GLB.
body=bpy.data.objects['BODY_SHELL_TOP'];bpy.context.view_layer.objects.active=body;body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
mat=body.data.materials[0].copy();mat.name='Titanium body — baked V08';body.data.materials[0]=mat;ns=mat.node_tree.nodes;ls=mat.node_tree.links;p=ns.get('Principled BSDF')
s.render.engine='CYCLES';s.cycles.samples=8;s.render.bake.margin=12
baked={}
for kind in ['ROUGHNESS','NORMAL']:
 im=bpy.data.images.new('AERIX_V08_'+kind,1024,1024,alpha=False);im.colorspace_settings.name='Non-Color'
 node=ns.new('ShaderNodeTexImage');node.image=im;ns.active=node
 bpy.ops.object.bake(type=kind)
 im.pack();baked[kind]=node
# Attach baked maps after both bakes, avoiding circular texture inputs.
for socket in ['Roughness','Normal']:
 for link in list(p.inputs[socket].links):ls.remove(link)
ls.new(baked['ROUGHNESS'].outputs['Color'],p.inputs['Roughness']);nm=ns.new('ShaderNodeNormalMap');ls.new(baked['NORMAL'].outputs['Color'],nm.inputs['Color']);ls.new(nm.outputs['Normal'],p.inputs['Normal'])
body.select_set(False)
for m in bpy.data.materials:
 if m==mat or not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if not p:continue
 for slot in ['Roughness','Normal']:
  for link in list(p.inputs[slot].links):m.node_tree.links.remove(link)
 if m.name.startswith('Titanium'):p.inputs['Roughness'].default_value=.42
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/aerix-review-v08.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('V08_REVIEW_EXPORT_COMPLETE')
