"""Current inspection GLB, including baked front-arm finishes and preserved pivots."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v09.blend'))
s=bpy.context.scene;s.frame_set(1)
for o in list(bpy.data.objects):
 if o.hide_render or o.type in {'LIGHT','CAMERA'} or o.name in {'STUDIO_GROUND','INTERNAL_ENVELOPES'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in list(s.objects):
 if o.type in {'MESH','CURVE','FONT'}:
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
s.render.engine='CYCLES';s.cycles.samples=4;s.render.bake.margin=10
baked_materials=set()
def bake(label,objects,source,res):
 bpy.ops.object.select_all(action='DESELECT')
 material=source.copy();material.name='V09 baked '+label;baked_materials.add(material)
 for o in objects:
  o.select_set(True)
  for i,m in enumerate(o.data.materials):
   if m==source:o.data.materials[i]=material
 bpy.context.view_layer.objects.active=objects[0]
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 ns=material.node_tree.nodes;ls=material.node_tree.links;p=ns.get('Principled BSDF');nodes={}
 extra_materials={m for o in objects for m in o.data.materials if m!=material}
 for kind in ['ROUGHNESS','NORMAL']:
  im=bpy.data.images.new('AERIX_V09_'+label+'_'+kind,res,res,alpha=False);im.colorspace_settings.name='Non-Color'
  n=ns.new('ShaderNodeTexImage');n.image=im;ns.active=n;nodes[kind]=n;extras=[]
  for m in extra_materials:
   q=m.node_tree.nodes.new('ShaderNodeTexImage');q.image=im;m.node_tree.nodes.active=q;extras.append((m,q))
  bpy.ops.object.bake(type=kind);im.pack()
  for m,q in extras:m.node_tree.nodes.remove(q)
 for socket in ['Roughness','Normal']:
  for link in list(p.inputs[socket].links):ls.remove(link)
 ls.new(nodes['ROUGHNESS'].outputs['Color'],p.inputs['Roughness']);nm=ns.new('ShaderNodeNormalMap');ls.new(nodes['NORMAL'].outputs['Color'],nm.inputs['Color']);ls.new(nm.outputs['Normal'],p.inputs['Normal'])
 print('BAKED',label,flush=True)
body=bpy.data.objects['BODY_SHELL_TOP'];bake('titanium body',[body],body.data.materials[0],1024)
for label,name,res in [('blade composite','V09 fine matte blade composite',1024),('molded graphite','V09 satin molded graphite',1024),('motor alloy','V09 satin turned motor alloy',1024),('arm cap','V09 titanium arm cap',512)]:
 source=bpy.data.materials[name];objects=[o for o in s.objects if o.type=='MESH' and source.name in o.data.materials];bake(label,objects,source,res)
for m in bpy.data.materials:
 if m in baked_materials or not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF')
 if not p:continue
 for socket in ['Roughness','Normal']:
  for link in list(p.inputs[socket].links):m.node_tree.links.remove(link)
 if m.name.startswith('Titanium'):p.inputs['Roughness'].default_value=.42
bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports/aerix-review-v09.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('V09_REVIEW_EXPORT_COMPLETE',flush=True)
