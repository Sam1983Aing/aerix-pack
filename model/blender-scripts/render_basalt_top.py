"""Render a surface-only Basalt reference in memory, using the V01 top camera."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve() == root / 'blender/drone-v01.blend'
scene = bpy.context.scene
scene.frame_set(1)
scene.camera = bpy.data.objects['Studio.camera.top']


def finish(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    surface = mat.node_tree.nodes['Principled BSDF']
    surface.inputs['Base Color'].default_value = (*color, 1)
    surface.inputs['Metallic'].default_value = metallic
    surface.inputs['Roughness'].default_value = roughness
    return mat


deck = finish('Dry charcoal magnesium', (.033,.034,.036), .69,.38)
structure = finish('Black sleeves', (.012,.013,.014), .43,.46)
blades = finish('Satin white blades', (.75,.75,.745), .11,.39)
hubs = finish('Titanium buttons', (.39,.39,.38), .88,.32)
copper = finish('Muted copper', (.34,.16,.088), .82,.37)
tree = deck.node_tree
position = tree.nodes.new('ShaderNodeNewGeometry').outputs['Position']
xyz = tree.nodes.new('ShaderNodeSeparateXYZ')
tree.links.new(position, xyz.inputs[0])


def math_node(operation, *values):
    node = tree.nodes.new('ShaderNodeMath')
    node.operation = operation
    for i, value in enumerate(values):
        if isinstance(value,(int,float)):
            node.inputs[i].default_value = value
        else:
            tree.links.new(value,node.inputs[i])
    return node.outputs[0]


# Signed masks in world meters keep these finish marks on the existing surface.
distance_to_joint = math_node('ABSOLUTE', math_node('SUBTRACT',xyz.outputs['Y'],.034))
joint = math_node('LESS_THAN',distance_to_joint,.00028)
screw_x = math_node('SUBTRACT', math_node('ABSOLUTE',xyz.outputs['X']),.012)
screw_y = math_node('ADD',xyz.outputs['Y'],.059)
radius_sq = math_node('ADD',math_node('MULTIPLY',screw_x,screw_x),math_node('MULTIPLY',screw_y,screw_y))
rim = math_node('LESS_THAN',radius_sq,.00145**2)
center = math_node('LESS_THAN',radius_sq,.0008**2)
mask = math_node('MAXIMUM',joint, math_node('SUBTRACT',rim,center))
mix = tree.nodes.new('ShaderNodeMixRGB')
mix.inputs[1].default_value=(.033,.034,.036,1)
mix.inputs[2].default_value=(.003,.003,.003,1)
tree.links.new(mask,mix.inputs[0])
bs = tree.nodes['Principled BSDF']
tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
bump=tree.nodes.new('ShaderNodeBump')
bump.invert=True
bump.inputs['Strength'].default_value=.45
bump.inputs['Distance'].default_value=.00018
tree.links.new(mask,bump.inputs['Height'])
tree.links.new(bump.outputs[0],bs.inputs['Normal'])

for obj in bpy.data.collections['V01 | Aircraft'].objects:
    if obj.type != 'MESH': continue
    mat=structure
    if obj.name=='Body.shell': mat=deck
    elif obj.name.startswith('Propeller.blade.'): mat=blades
    elif obj.name.startswith('Propeller.cap.'): mat=hubs
    elif obj.name.startswith('Hinge.pin.'): mat=copper
    obj.data.materials[0]=mat
scene.cycles.samples=36
scene.render.filepath=str(root/'concepts/02-basalt/orthographic/top.png')
bpy.ops.render.render(write_still=True)
