"""Motherboard look development and fine assembly details, preserving source meshes.
Only maps and explicitly named additive details are exported. Packaging keeps the
original battery/exterior/other-interior payload and animation tracks untouched.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).resolve().parents[2]; O=R/'exports/textures/motherboard-v32'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'site/assets/aerix-battery-finish-v31.glb'))
s=bpy.context.scene;s.frame_set(0)
root=bpy.data.objects['FLIGHT_COMPUTER_ROOT']; keep={root,*root.children_recursive}
p=root.parent
while p:keep.add(p);p=p.parent
for o in list(bpy.data.objects):
    o.animation_data_clear()
    if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='CYCLES';s.cycles.samples=12;s.render.bake.margin=16;s.render.bake.use_clear=True

def setup(name):
    m=bpy.data.materials[name];n=m.node_tree.nodes;l=m.node_tree.links
    p=next(x for x in n if x.type=='BSDF_PRINCIPLED');out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
    for sock in ['Base Color','Metallic','Roughness','Normal']:
        for a in list(p.inputs[sock].links):l.remove(a)
    return m,n,l,p,out
def node_math(n,l,op,a,b):
    q=n.new('ShaderNodeMath');q.operation=op
    for i,v in enumerate([a,b]):
        if isinstance(v,(float,int)):q.inputs[i].default_value=v
        else:l.new(v,q.inputs[i])
    return q.outputs[0]
def mix(n,l,f,a,b):
    q=n.new('ShaderNodeMixRGB');q.blend_type='MIX'
    for i,v in enumerate([f,a,b]):
        if isinstance(v,(float,int)):q.inputs[i].default_value=v if i==0 else (v,v,v,1)
        elif isinstance(v,(tuple,list)):q.inputs[i].default_value=(*v,1)
        else:l.new(v,q.inputs[i])
    return q.outputs[0]
def noise(n,l,vector,scale,stretch=None):
    if stretch:
        q=n.new('ShaderNodeVectorMath');q.operation='MULTIPLY';l.new(vector,q.inputs[0]);q.inputs[1].default_value=stretch;vector=q.outputs[0]
    q=n.new('ShaderNodeTexNoise');q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=2
    l.new(vector,q.inputs['Vector']);return q.outputs['Fac']
def range01(n,l,v,a,b):return node_math(n,l,'ADD',node_math(n,l,'MULTIPLY',v,b-a),a)

def bake(m,slug,res,sockets):
    n=m.node_tree.nodes;l=m.node_tree.links;p=next(x for x in n if x.type=='BSDF_PRINCIPLED');out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
    obs=[o for o in keep if o.type=='MESH' and m in o.data.materials[:]]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    for kind,source in [*sockets.items(),('normal',None)]:
        im=bpy.data.images.new('AERIX_V32_'+slug+'_'+kind,res,res,alpha=False)
        im.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color'
        im.filepath_raw=str(O/f'{slug}-{kind}.png');im.file_format='PNG'
        tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
        if kind=='normal':l.new(p.outputs['BSDF'],out.inputs['Surface']);bpy.ops.object.bake(type='NORMAL')
        else:
            emit=n.new('ShaderNodeEmission');l.new(source,emit.inputs['Color']);l.new(emit.outputs[0],out.inputs['Surface'])
            bpy.ops.object.bake(type='EMIT');n.remove(emit)
        im.save();im.pack();print('CORE_V32_BAKED',slug,kind,res,flush=True)
    l.new(p.outputs['BSDF'],out.inputs['Surface'])
    return {'source_material':m.name,'slug':slug,'resolution':res,'maps':list(sockets)+['normal'],'objects':[o.name for o in obs]}

# Planar artwork is baked onto the existing packed UVs, including daughterboard
# and radio substrate. World XY coordinates match the original authored layout.
m,n,l,p,out=setup('V30 deep green soldermask');geo=n.new('ShaderNodeNewGeometry')
pos=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],pos.inputs[0])
normal=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],normal.inputs[0])
uv=n.new('ShaderNodeCombineXYZ')
l.new(range01(n,l,pos.outputs['X'],.5,.5+1/.074),uv.inputs['X'])
l.new(range01(n,l,pos.outputs['Y'],.089/.144,.089/.144+1/.144),uv.inputs['Y'])
back=node_math(n,l,'LESS_THAN',normal.outputs['Z'],0)
side=node_math(n,l,'LESS_THAN',node_math(n,l,'ABSOLUTE',normal.outputs['Z'],0),.6)
def circuit(name):
    im=bpy.data.images.load(str(O/f'circuit-{name}.png'),check_existing=True)
    im.colorspace_settings.name='sRGB' if name in ['top','back'] else 'Non-Color'
    im.pack();tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector']);return tex.outputs['Color']
color=mix(n,l,back,circuit('top'),circuit('back'))
height=mix(n,l,back,circuit('height'),circuit('back-height'))
metal=mix(n,l,back,circuit('metal'),circuit('back-metal'))
grain=noise(n,l,geo.outputs['Position'],14500)
# Exposed edge laminate: thin resin/fibre layers, restrained at sub-millimetre scale.
lam=node_math(n,l,'SINE',node_math(n,l,'MULTIPLY',pos.outputs['Z'],25000),0)
edge=mix(n,l,range01(n,l,lam,.25,.75),(.018,.031,.017),(.034,.049,.025))
color=mix(n,l,side,color,edge)
rough=mix(n,l,metal,range01(n,l,grain,.47,.59),.32)
metal=mix(n,l,side,metal,.025)
micro=n.new('ShaderNodeBump');micro.inputs['Strength'].default_value=.22;micro.inputs['Distance'].default_value=.000004;l.new(grain,micro.inputs['Height'])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.42;bump.inputs['Distance'].default_value=.000036
l.new(height,bump.inputs['Height']);l.new(micro.outputs['Normal'],bump.inputs['Normal']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
l.new(color,p.inputs['Base Color']);l.new(rough,p.inputs['Roughness']);l.new(metal,p.inputs['Metallic'])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.0012;ao.samples=16
occlusion=range01(n,l,ao.outputs['AO'],.72,1)
reports=[bake(m,'soldermask',4096,{'color':color,'roughness':rough,'metallic':metal,'occlusion':occlusion})]

# The shield and processor lid stay metallic, with a fine satin brushed finish.
m,n,l,p,out=setup('V30 satin bead blasted aluminum');coord=n.new('ShaderNodeTexCoord')
grain=noise(n,l,coord.outputs['Object'],17000,(1,.05,1));fine=noise(n,l,coord.outputs['Object'],23000)
color=mix(n,l,grain,(.24,.27,.29),(.30,.33,.35));rough=range01(n,l,grain,.43,.55)
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.000004
l.new(fine,bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
l.new(color,p.inputs['Base Color']);l.new(rough,p.inputs['Roughness']);p.inputs['Metallic'].default_value=.82
reports.append(bake(m,'shield',2048,{'color':color,'roughness':rough}))

# Keep the editable native master in step with the browser finish parameters.
for name,col,metal,lo,hi in json.loads((R/'scripts/web/core-finish-settings.json').read_text()):
    m,n,l,p,out=setup('V30 '+name);coord=n.new('ShaderNodeTexCoord')
    grain=noise(n,l,coord.outputs['Object'],21000)
    l.new(range01(n,l,grain,lo,hi),p.inputs['Roughness'])
    p.inputs['Base Color'].default_value=(*[v*.94 for v in col],1)
    p.inputs['Metallic'].default_value=metal
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.000003
    l.new(grain,bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
for name,col,rough in [('silkscreen ink',(.39,.48,.39),.68),('laser etched marking',(.020,.025,.028),.66)]:
    m,n,l,p,out=setup('V30 '+name);p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=0

# Native additive details; all original component shapes remain intact.
new=[]
def mat(name,col,metal=0,rough=.65):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
ink=mat('V32 chip laser marking',(.23,.28,.29));darkink=mat('V32 metal laser marking',(.024,.030,.035),0,.66);mold=mat('V32 molded connector detail',(.25,.24,.20),0,.61);dot=mat('V32 molded index mark',(.042,.050,.055),0,.7);steel=mat('V32 coax collar',(.22,.25,.27),.83,.36)
def attach(o,tag,material,parent):
    o.name='FC32_'+tag;o.data.materials.append(material)
    world=o.matrix_world.copy();o.parent=bpy.data.objects[parent];o.matrix_world=world
    o['attachTo']=parent;new.append(o);return o
def text(tag,body,x,y,z,size,parent='FLIGHT_COMPUTER_ROOT'):
    c=bpy.data.curves.new(tag,'FONT');c.body=body;c.size=size/1000;c.align_x='CENTER';c.extrude=.0000015;c.space_character=1.05
    o=bpy.data.objects.new(tag,c);s.collection.objects.link(o);o.location=(x/1000,y/1000,z/1000);bpy.context.view_layer.update();return attach(o,tag,ink,parent)
def box(tag,x,y,z,w,d,h,material,parent='FLIGHT_COMPUTER_ROOT'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x/1000,y/1000,z/1000));o=bpy.context.object;o.dimensions=Vector((w,d,h))/1000;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Micro edge radius','BEVEL');mod.width=min(w,d,h)/6000;mod.segments=3
    mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return attach(o,tag,material,parent)
def disk(tag,x,y,z,r,material,parent='FLIGHT_COMPUTER_ROOT'):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r/1000,depth=.000012,location=(x/1000,y/1000,z/1000));return attach(bpy.context.object,tag,material,parent)
for i,yy in enumerate([-52,-24]):
    text('MEMORY_LOT',f'AX / MEMORY\n0926 — {i+1:02}',24,yy-4.3,67.108,.68)
    disk('MEMORY_INDEX',19.5,yy-7,67.108,.28,dot)
for k,(x,y,w,h) in enumerate(json.loads((O/'layout.json').read_text())['packages'][:9]):
    text('IC_LOT','0926',x,y-h*.33,66.809,.42)
    disk('IC_INDEX',x-w/2+.55,y-h/2+.55,66.807,.18,dot)
for o in [text('CAP_LOT','FLIGHT PROCESSOR / 01',0,-47.6,69.006,.65,'FC30_PROCESSOR_CAP_ROOT'),text('SHIELD_LOT','AERIX / RF SHIELD',-15,15.7,69.511,.65,'FC30_SHIELD_ROOT')]:
    o.data.materials[0]=darkink
text('IMU_LOT','AX / IMU',-23,-70.0,68.706,.48,'FC30_IMU_ROOT')
disk('IMU_INDEX',-25.2,-70.2,68.705,.20,dot,'FC30_IMU_ROOT')
for x in [-23,0,23]:
    # Fine molding part line and shallow ejector marks on the connector roof.
    for sx in [-1,1]:
        box('SOCKET_MOLD_LINE',x+sx*5.4,-86,68.907,.08,3.0,.025,mold)
        disk('SOCKET_MOLD_INDEX',x+sx*4.6,-85.4,68.904,.30,mold)
    text('SOCKET_PIN_1','1',x-4.0,-85.8,68.914,.62)
    for j in range(4):box('PLUG_GRIP',x+(j-1.5)*1.5,-89.4,68.0,.28,1.1,.11,dot,'FC30_HARNESS_ROOT')
for x in [3,8]:
    bpy.ops.mesh.primitive_torus_add(major_radius=.00081,minor_radius=.000045,major_segments=48,minor_segments=8,location=(x/1000,.038,.06633))
    attach(bpy.context.object,'COAX_CRIMP_COLLAR',steel,'FLIGHT_COMPUTER_ROOT')

(O/'bake-manifest.json').write_text(json.dumps(reports,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-flightcore-finish-v32.blend'))
# Export only new details with their world matrices. The packager attaches each
# to the named existing pivot using its closed-pose inverse world matrix.
bpy.ops.object.select_all(action='DESELECT')
for o in new:
    world=o.matrix_world.copy();o.parent=None;o.matrix_world=world;o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/aerix-flightcore-details-v32.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True,export_cameras=False,export_lights=False)
print('CORE_V32_FINISHED',len(new),flush=True)
