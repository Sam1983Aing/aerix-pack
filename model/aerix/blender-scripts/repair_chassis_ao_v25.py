"""Bake contact shading over every chassis material region, preserving exported UVs.

The main export's emission bake left unlit pixels in the static rim regions.
Filtering those pixels across material boundaries caused dashed black seams.
Rebake the exact exported mesh with one AO shader, then replace only the red
channel of its packed ORM image. Geometry and the roughness/metallic channels stay intact.
"""
import bpy,json,struct,array
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v25';path=R/'exports/aerix-review-v25.glb'
raw=path.read_bytes();jsize=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+jsize]);start=20+jsize;bsize,bkind=struct.unpack_from('<II',raw,start);binary=raw[start+8:start+8+bsize]
mat=next(m for m in g['materials'] if m.get('name')=='V25 baked structural chassis');texture=mat['occlusionTexture']['index'];image_index=g['textures'][texture]['source'];oldview=g['bufferViews'][g['images'][image_index]['bufferView']];a=oldview.get('byteOffset',0);oldpng=binary[a:a+oldview['byteLength']];oldpath=OUT/'chassis-orm-before.png';oldpath.write_bytes(oldpng)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.bake.margin=10;s.render.bake.margin_type='EXTEND'
root=bpy.data.objects.get('BODY_CRADLE');assert root
objects=[root] if root.type=='MESH' else [o for o in root.children_recursive if o.type=='MESH'];assert objects
original=bpy.data.images.load(str(oldpath));original.colorspace_settings.name='Non-Color';width,height=original.size
im=bpy.data.images.new('V25 complete chassis AO',width,height,alpha=False);im.colorspace_settings.name='Non-Color'
material=bpy.data.materials.new('V25 temporary uniform AO');material.use_nodes=True;n=material.node_tree.nodes;l=material.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.006;ao.samples=32;emission=n.new('ShaderNodeEmission');l.new(ao.outputs['Color'],emission.inputs['Color']);l.new(emission.outputs[0],out.inputs['Surface']);tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
bpy.ops.object.select_all(action='DESELECT')
for o in objects:
 o.data.materials.clear();o.data.materials.append(material)
 for p in o.data.polygons:p.material_index=0
 o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.bake(type='EMIT');im.filepath_raw=str(OUT/'chassis-ao-complete.png');im.file_format='PNG';im.save()
pixels=array.array('f',[0])*(width*height*4);ao_pixels=array.array('f',[0])*len(pixels);original.pixels.foreach_get(pixels);im.pixels.foreach_get(ao_pixels);before_gb=array.array('f',(pixels[i] for i in range(len(pixels)) if i%4 in [1,2]))
for i in range(0,len(pixels),4):pixels[i]=ao_pixels[i]
original.pixels.foreach_set(pixels);original.filepath_raw=str(OUT/'chassis-orm-complete.png');original.file_format='PNG';original.save()
verify=bpy.data.images.load(str(OUT/'chassis-orm-complete.png'),check_existing=False);verify.colorspace_settings.name='Non-Color';vp=array.array('f',[0])*len(pixels);verify.pixels.foreach_get(vp);after_gb=array.array('f',(vp[i] for i in range(len(vp)) if i%4 in [1,2]));error=max(abs(a-b) for a,b in zip(before_gb,after_gb));assert error<1/255+.00001,error
png=(OUT/'chassis-orm-complete.png').read_bytes();offset=(len(binary)+3)//4*4;binary+=b'\0'*(offset-len(binary))+png;binary+=b'\0'*((-len(binary))%4);g['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(png)});g['images'][image_index]['bufferView']=len(g['bufferViews'])-1;g['buffers'][0]['byteLength']=len(binary)
encoded=json.dumps(g,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);payload=struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary;path.write_bytes(payload)
report={'chassis_objects':len(objects),'texture_resolution':[width,height],'only_orm_red_channel_rebaked':True,'maximum_roughness_metallic_channel_error':error,'old_binary_bytes_preserved':binary[:bsize]==raw[start+8:start+8+bsize],'bytes':len(payload)};(OUT/'ao-repair-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
