"""Build the V14 studio on the approved V13 aircraft. Run with the V13 blend open."""
import json
import sys
from math import cos, pi, sin, tau
from pathlib import Path

import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'scripts'))
from v13_detail_views import detail_view

assert Path(bpy.data.filepath).resolve() == root / 'blender/drone-v13.blend'
scene = bpy.context.scene
scene.frame_set(1)
aircraft = bpy.data.collections['V13 | Aircraft']
floor = bpy.data.objects['Studio.floor']
studio = floor.users_collection[0]
rig = json.loads((root / 'viewer/v14-studio.json').read_text())

# A continuous sweep has no horizon line in the four orthographic elevations.
# Keep the original floor object's fold animation and the camera transforms.
rings = [(0.15, 0), (0.71, 0)]
for i in range(1, 25):
    angle = i*pi/48
    rings.append((0.71 + 0.16*sin(angle), 0.16*(1-cos(angle))))
rings.append((0.87, 0.78))
n = 128
vertices = [(0, 0, 0)]
vertices.extend((r*cos(i*tau/n), r*sin(i*tau/n), z) for r,z in rings for i in range(n))
faces = [(0, 1+i, 1+(i+1)%n) for i in range(n)]
for row in range(len(rings)-1):
    inner = 1+row*n
    faces.extend((inner+i, inner+n+i, inner+n+(i+1)%n, inner+(i+1)%n) for i in range(n))
mesh = bpy.data.meshes.new('Slate seamless sweep')
mesh.from_pydata(vertices, [], faces)
mesh.update()
for poly in mesh.polygons:
    poly.use_smooth = True
floor.data = mesh
surface = bpy.data.materials.new('Studio | matte blue slate')
surface.diffuse_color = (*rig['floor'], 1)
surface.use_nodes = True
bsdf = surface.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = surface.diffuse_color
bsdf.inputs['Roughness'].default_value = 0.87
bsdf.inputs['Specular IOR Level'].default_value = 0.12
bsdf.inputs['Emission Color'].default_value = (*rig['floor'], 1)
bsdf.inputs['Emission Strength'].default_value = 0.40
mesh.materials.append(surface)

for obj in list(studio.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)
for panel in rig['panels']:
    lamp = bpy.data.lights.new(panel['name'], 'AREA')
    lamp.shape = 'RECTANGLE'
    lamp.size, lamp.size_y = panel['width'], panel['height']
    lamp.energy = panel['watts']
    lamp.color = panel['color']
    obj = bpy.data.objects.new('Studio.'+panel['name'], lamp)
    studio.objects.link(obj)
    obj.location = panel['position']
    obj.rotation_euler = (Vector(panel['aim'])-obj.location).to_track_quat('-Z', 'Y').to_euler()
    obj.hide_set(True)

bg = scene.world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (*rig['world'], 1)
bg.inputs['Strength'].default_value = rig['worldStrength']
# Horizontal orthographic cameras can see below the tabletop. Give these
# rays a continuous studio background, including the area below the feet.
# Physical floor contact and reflections still contribute to the aircraft.
tree = surface.node_tree
incoming = tree.nodes.new('ShaderNodeNewGeometry')
direction = tree.nodes.new('ShaderNodeSeparateXYZ')
tree.links.new(incoming.outputs['Incoming'], direction.inputs[0])
absolute = tree.nodes.new('ShaderNodeMath')
absolute.operation = 'ABSOLUTE'
tree.links.new(direction.outputs['Z'], absolute.inputs[0])
level = tree.nodes.new('ShaderNodeMath')
level.operation = 'LESS_THAN'
tree.links.new(absolute.outputs[0], level.inputs[0])
level.inputs[1].default_value = 0.00001
path = tree.nodes.new('ShaderNodeLightPath')
camera_level = tree.nodes.new('ShaderNodeMath')
camera_level.operation = 'MULTIPLY'
tree.links.new(path.outputs['Is Camera Ray'], camera_level.inputs[0])
tree.links.new(level.outputs[0], camera_level.inputs[1])
mix = tree.nodes.new('ShaderNodeMixShader')
tree.links.new(camera_level.outputs[0], mix.inputs[0])
tree.links.new(bsdf.outputs[0], mix.inputs[1])
tree.links.new(tree.nodes.new('ShaderNodeBsdfTransparent').outputs[0], mix.inputs[2])
tree.links.new(mix.outputs[0], tree.nodes['Material Output'].inputs['Surface'])

world = scene.world.node_tree
window = world.nodes.new('ShaderNodeTexCoord')
height = world.nodes.new('ShaderNodeSeparateXYZ')
world.links.new(window.outputs['Window'], height.inputs[0])
tones = world.nodes.new('ShaderNodeValToRGB')
tones.color_ramp.elements[0].color = (0.033,0.043,0.055,1)
tones.color_ramp.elements[1].color = (0.095,0.121,0.144,1)
world.links.new(height.outputs['Y'], tones.inputs[0])
plate = world.nodes.new('ShaderNodeBackground')
world.links.new(tones.outputs[0], plate.inputs[0])
world_mix = world.nodes.new('ShaderNodeMixShader')
world.links.new(world.nodes.new('ShaderNodeLightPath').outputs['Is Camera Ray'], world_mix.inputs[0])
world.links.new(bg.outputs[0], world_mix.inputs[1])
world.links.new(plate.outputs[0], world_mix.inputs[2])
world.links.new(world_mix.outputs[0], world.nodes['World Output'].inputs['Surface'])
scene.view_settings.exposure = -0.24
scene.world.name = 'Slate studio' 
scene.cycles.use_denoising = True
scene.cycles.adaptive_threshold = 0.025
scene.cycles.samples = 48
# Record the identical V13 macro position as a selectable camera in the master.
detail_view(scene, 'camera-sides')
macro = scene.camera
macro.name = 'Studio.camera.lens'
for collection in list(macro.users_collection):
    collection.objects.unlink(macro)
studio.objects.link(macro)
macro.hide_set(True)
floor.hide_render = False
scene.camera = bpy.data.objects['Studio.camera.three-quarter']
scene.cycles.samples = 48

if '--preview' in sys.argv:
    scene.render.resolution_percentage = 47
    scene.cycles.samples = 14
    for frame, cam, name in [(1, 'three-quarter','open'), (121,'three-quarter','folded'), (1,'lens','lens'), (1,'front','front')]:
        scene.frame_set(frame)
        scene.camera = bpy.data.objects['Studio.camera.'+cam]
        scene.render.filepath = str(root / f'measurements/v14-proof-{name}.png')
        bpy.ops.render.render(write_still=True)
else:
    blend = root / 'blender/drone-v14.blend'
    glb = root / 'exports/drone-v14.glb'
    assert not blend.exists() and not glb.exists()
    aircraft.name = 'V14 | Aircraft'
    aircraft.objects['Drone.V13'].name = 'Drone.V14'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in aircraft.objects:
        obj.select_set(True)
    pending = root / 'exports/pending-v14.glb'
    bpy.ops.export_scene.gltf(filepath=str(pending), use_selection=True, export_apply=True,
        export_texcoords=True, export_tangents=True, export_image_format='AUTO',
        export_animation_mode='NLA_TRACKS', export_animations=True, export_frame_range=True, export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    scene.camera = bpy.data.objects['Studio.camera.three-quarter']
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
