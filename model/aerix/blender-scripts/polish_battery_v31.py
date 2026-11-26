"""Bake battery-only finishes onto the shipped UVs; never re-export the drone geometry.

The GLB assembly step appends these lossless maps to the original binary. Blender
is used only for look development and texture baking, so its importer cannot
alter any shipped vertex, normal, pivot, or animation.
"""
import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/textures/battery-v31'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'site/assets/aerix-quality-v02.glb'))
scene = bpy.context.scene
scene.frame_set(0)
# Keep the battery and its parent chain in the editable finish master.
root = bpy.data.objects['BATTERY_ROOT']
keep = {root, *root.children_recursive}
parent = root.parent
while parent:
    keep.add(parent)
    parent = parent.parent
for ob in list(bpy.data.objects):
    ob.animation_data_clear()
    if ob not in keep:
        bpy.data.objects.remove(ob, do_unlink=True)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8
scene.render.bake.margin = 20
scene.render.bake.use_clear = True
scene.render.bake.normal_space = 'TANGENT'

def finish(name, slug, resolution, colors, rough, grain_scale, bump_depth, metal):
    mat = bpy.data.materials[name]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
    coord = nodes.new('ShaderNodeTexCoord')

    def noise(scale, detail=2, stretch=None):
        n = nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = .6
        vector = coord.outputs['Object']
        if stretch:
            v = nodes.new('ShaderNodeVectorMath'); v.operation = 'MULTIPLY'
            v.inputs[1].default_value = stretch
            links.new(vector, v.inputs[0]); vector = v.outputs['Vector']
        links.new(vector, n.inputs['Vector'])
        return n.outputs['Fac']

    def ramp(source, low, high):
        n = nodes.new('ShaderNodeValToRGB')
        n.color_ramp.elements[0].position = .18
        n.color_ramp.elements[0].color = (*low, 1)
        n.color_ramp.elements[1].position = .82
        n.color_ramp.elements[1].color = (*high, 1)
        links.new(source, n.inputs['Fac'])
        return n.outputs['Color']

    grain = noise(grain_scale)
    # A rolling direction in the laminate, without topology-driven anisotropy.
    variation = noise(480 if slug == 'foil' else 750, 2,
                      (1, .14, .8) if slug == 'foil' else (1, 1, 1))
    color = ramp(variation, *colors)
    r = ramp(grain, (rough[0],)*3, (rough[1],)*3)
    for socket in ['Base Color', 'Roughness', 'Normal']:
        for link in list(bsdf.inputs[socket].links): links.remove(link)
    links.new(color, bsdf.inputs['Base Color'])
    links.new(r, bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = metal
    anisotropy = bsdf.inputs.get('Anisotropic') or bsdf.inputs.get('Anisotropic IOR Level')
    if anisotropy: anisotropy.default_value = 0
    # Microscopic finish, plus a shallow millimetre-scale laminate ripple. The
    # rounded shoulders and crimped perimeter remain the original real geometry.
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .28
    bump.inputs['Distance'].default_value = bump_depth
    links.new(grain, bump.inputs['Height'])
    if slug == 'foil':
        pressed = noise(135, 2, (1, .24, 1))
        macro = nodes.new('ShaderNodeBump')
        macro.inputs['Strength'].default_value = .35
        macro.inputs['Distance'].default_value = .000055
        links.new(pressed, macro.inputs['Height'])
        links.new(bump.outputs['Normal'], macro.inputs['Normal'])
        links.new(macro.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    objects = [o for o in keep if o.type == 'MESH' and mat in o.data.materials[:]]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    images = {}
    for kind in ['color', 'roughness', 'normal']:
        im = bpy.data.images.new('AERIX_V31_' + slug + '_' + kind,
                                resolution, resolution, alpha=False)
        im.colorspace_settings.name = 'sRGB' if kind == 'color' else 'Non-Color'
        im.file_format = 'PNG'
        im.filepath_raw = str(OUT / f'{slug}-{kind}.png')
        node = nodes.new('ShaderNodeTexImage'); node.image = im
        nodes.active = node
        if kind == 'normal':
            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            bpy.ops.object.bake(type='NORMAL')
        else:
            emission = nodes.new('ShaderNodeEmission')
            links.new(color if kind == 'color' else r, emission.inputs['Color'])
            links.new(emission.outputs['Emission'], output.inputs['Surface'])
            bpy.ops.object.bake(type='EMIT')
            nodes.remove(emission)
        im.save(); im.pack()
        images[kind] = str(im.filepath_raw)
        print('BATTERY_V31_BAKED', slug, kind, resolution, flush=True)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return dict(source_material=name, slug=slug, resolution=resolution,
                metallic=metal, images=images, objects=[o.name for o in objects])

report = [
    finish('V29 laminated aluminum foil', 'foil', 4096,
           ((.255, .282, .311), (.345, .373, .404)), (.32, .43),
           6800, .000009, .76),
    finish('V29 microtextured graphite', 'graphite', 2048,
           ((.012, .017, .023), (.016, .022, .029)), (.34, .44),
           7800, .000015, .18),
    finish('V29 retention elastomer', 'elastomer', 1024,
           ((.008, .011, .015), (.013, .017, .022)), (.54, .65),
           10500, .000012, .015),
]
(OUT / 'bake-manifest.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'blender/aerix-battery-finish-v31.blend'))
print('BATTERY_V31_FINISH_MASTER_SAVED', flush=True)
