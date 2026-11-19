"""Author the V11 finishes and real-scale UVs on the approved V10 aircraft."""
from math import atan2, tau
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from io_scene_gltf2.blender.imp.pbrMetallicRoughness import get_settings_group

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v11_material_view import material_camera
from v10_camera_view import front_macro

assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v10.blend'
scene=bpy.context.scene
scene.frame_set(1)
group=bpy.data.collections['V10 | Aircraft']
mats=bpy.data.materials
period=.0128
images={}
for path in sorted((root/'blender/materials-v11').glob('*.png')):
    im=bpy.data.images.load(str(path),check_existing=True)
    im.colorspace_settings.name='Non-Color'
    im.pack()
    im.filepath='//materials-v11/'+path.name
    images[path.stem]=im
assert len(images)==6


def surface(name,rgb,roughness,metallic=0,**settings):
    mat=mats.get(name) or mats.new(name)
    mat.use_nodes=True
    mat.diffuse_color=(*rgb,1)
    mat.roughness=roughness
    mat.metallic=metallic
    shader=mat.node_tree.nodes['Principled BSDF']
    settings.update({'Base Color':mat.diffuse_color,'Roughness':roughness,'Metallic':metallic})
    for key,value in settings.items():
        shader.inputs[key].default_value=value
    return mat


def grain(mat,family,strength,mapped_roughness=True):
    tree=mat.node_tree
    bs=tree.nodes['Principled BSDF']
    def sample(map_name,xy):
        node=tree.nodes.new('ShaderNodeTexImage')
        node.image=images[family+'-'+map_name]
        node.location=xy
        node.label=node.image.name
        return node.outputs['Color']
    normal=tree.nodes.new('ShaderNodeNormalMap')
    normal.location=(-230,-200)
    normal.inputs['Strength'].default_value=strength
    tree.links.new(sample('normal',(-550,-240)),normal.inputs['Color'])
    tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    if mapped_roughness:
        channels=tree.nodes.new('ShaderNodeSeparateColor')
        channels.location=(-230,150)
        tree.links.new(sample('mr',(-550,150)),channels.inputs[0])
        tree.links.new(channels.outputs['Green'],bs.inputs['Roughness'])
        tree.links.new(channels.outputs['Blue'],bs.inputs['Metallic'])
    return mat


shell=grain(surface('RILL | warm ceramic grey',(.287,.300,.283),.404),'mold',.57)
shoulder=grain(surface('RILL | sloping upper shoulder',(.265,.276,.259),.404),'mold',.57)
lower=grain(surface('RILL | lower casing',(.213,.224,.212),.404),'mold',.66)
rubber=grain(surface('RILL | graphite elastomer',(.015,.017,.017),.7,**{'IOR':1.46}),'rubber',.92)
metal=grain(surface('RILL | satin aluminium',(.47,.485,.48),.293,1),'turned',.35)
motor_metal=grain(surface('RILL | smoke anodized motor bell',(.29,.313,.32),.293,1),'turned',.46)
bezel=surface('RILL | graphite camera bezel',(.078,.087,.090),.32,.85)
screw=surface('RILL | black oxide fastener',(.056,.061,.064),.32,.94)
gasket=surface('RILL | spindle seal',(.012,.015,.016),.49,**{'IOR':1.46})
window=surface('RILL | smoke indicator lens',(.028,.043,.045),.14,**{'Coat Weight':.30,'Coat Roughness':.08})
surface('RILL | joint shadow',(.045,.049,.047),.56)
surface('RILL | intake depth',(.007,.009,.010),.74)
surface('RILL | stator winding',(.51,.205,.078),.285,.94,**{'Coat Weight':.15,'Coat Roughness':.19})
blade=grain(surface('RILL | carbon blade',(.016,.019,.021),.41,
                    **{'Specular IOR Level':.21}),'mold',.24,False)
surface('RILL | signal orange',(.735,.146,.030),.40)
surface('RILL | wordmark',(.078,.087,.084),.53)
case=grain(surface('Basalt | camera graphite',(.020,.024,.026),.37,**{'Specular IOR Level':.30}),'mold',.20,False)
surface('Basalt | gimbal carbon casting',(.035,.039,.042),.43,.13)
surface('Basalt | satin pitch bearing',(.24,.258,.263),.31,.97)
surface('Basalt | matte interior baffles',(.003,.004,.005),.82)
surface('Basalt | machined graphite edge',(.095,.105,.112),.235,.98)
surface('Basalt | turned black barrel',(.034,.038,.042),.31,.92)
surface('Basalt | diaphragm leaves',(.035,.037,.042),.39,.63)
surface('Basalt | receiver surface',(.013,.032,.039),.19,.44)

front=surface('Basalt | front optical crown',(.987,.992,.998),.016,**{
    'IOR':1.52,'Transmission Weight':1,'Thin Film IOR':1.38,'Thin Film Thickness':112,
    'Coat Weight':0,'Coat Tint':(1,1,1,1)})
film=front.node_tree.nodes.new('ShaderNodeGroup')
film.node_tree=get_settings_group()
film.location=(-280,-420)
film.inputs['Iridescence Factor'].default_value=1
film.inputs['Iridescence Thickness Minimum'].default_value=112
surface('Basalt | inner optical crown',(.893,.963,.947),.026,**{
    'IOR':1.61,'Transmission Weight':1,'Coat Weight':0})


def material_uvs(obj,motor):
    """Metric projections for fine stochastic grain; continuous lathe UVs on motor rims."""
    me=obj.data
    uv=me.uv_layers.active or me.uv_layers.new(name='Finish UV')
    matrix=obj.matrix_world.copy()
    coords=[matrix@v.co for v in me.vertices]
    if motor:
        ring=coords[:48]
        center=sum(ring,Vector())/len(ring)
    normal_matrix=matrix.to_3x3().inverted().transposed()
    for p in me.polygons:
        n=normal_matrix@p.normal
        axis=max(range(3),key=lambda i:abs(n[i]))
        horizontal,vertical=((1,2),(2,0),(0,1))[axis]
        sign=1 if n[axis]>=0 else -1
        turned=motor and me.materials[p.material_index]==motor_metal and len(p.vertices)==4
        if turned:
            angles=[(atan2(coords[i].y-center.y,coords[i].x-center.x)/tau)%1 for i in p.vertices]
            crosses=max(angles)-min(angles)>.5
        for k,loop in enumerate(p.loop_indices):
            pos=coords[me.loops[loop].vertex_index]
            if turned:
                angle=angles[k]+int(crosses and angles[k]<.5)
                radius=((pos.x-center.x)**2+(pos.y-center.y)**2)**.5
                # Four whole repeats around the 16 mm bell. V follows the lathed profile.
                uv.data[loop].uv=(4*angle,(pos.z+(.008-radius))/period)
            else:
                uv.data[loop].uv=(sign*pos[horizontal]/period,pos[vertical]/period)
    me.update()


mapped={shell,shoulder,lower,rubber,metal,motor_metal,blade,case}
for obj in group.objects:
    if obj.type!='MESH': continue
    motor=obj.name.startswith('Motor.') and not obj.name.startswith('Motor.stator.')
    for slot in obj.material_slots:
        if obj.name=='Camera.face_trim' and slot.material==metal: slot.material=bezel
        if motor and slot.material==metal: slot.material=motor_metal
        if motor and slot.material==rubber: slot.material=gasket
        if obj.name.startswith('Propeller.screw.') and slot.material==rubber: slot.material=screw
        if obj.name.startswith('Leg.window.') and slot.material==rubber: slot.material=window
        if obj.name.startswith('Hinge.pin.') and slot.material==rubber: slot.material=screw
    if any(m in mapped for m in obj.data.materials):
        material_uvs(obj,motor)
bpy.context.view_layer.update()

if '--preview' in sys.argv:
    scene.render.resolution_percentage=60
    scene.cycles.samples=20
    def preview(label):
        scene.render.filepath=str(root/f'measurements/v11-preview-{label}.png')
        bpy.ops.render.render(write_still=True)
    scene.camera=bpy.data.objects['Studio.camera.three-quarter']
    preview('three-quarter')
    material_camera(scene)
    scene.cycles.samples=32
    preview('material')
    front_macro(scene)
    preview('lens')
else:
    blend=root/'blender/drone-v11.blend'
    glb=root/'exports/drone-v11.glb'
    assert not blend.exists() and not glb.exists()
    group.name='V11 | Aircraft'
    group.objects['Drone.V10'].name='Drone.V11'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects: obj.select_set(True)
    pending=root/'exports/pending-v11.glb'
    bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
        export_texcoords=True,export_tangents=True,export_image_format='AUTO',
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
