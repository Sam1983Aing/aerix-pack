"""Export the six original review stages without changing their Blender sources.

Like the V07 review export, procedural finishes use scalar PBR approximations.
V04 includes its interior components in the assembled, static frame-1 pose.
"""
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    '01': 'aerix-blockout-v01.blend',
    '02': 'aerix-refinement-v02.blend',
    '03': 'aerix-exterior-v03.blend',
    '04': 'aerix-interior-v04.blend',
    '05': 'aerix-exterior-v05.blend',
    '06': 'aerix-exterior-v06.blend',
}
REPORT = ROOT / 'renders/early-versions'
REPORT.mkdir(parents=True, exist_ok=True)
report = []

for version, filename in SOURCES.items():
    source = ROOT / 'blender' / filename
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.scene.frame_set(1)
    for obj in list(bpy.data.objects):
        if (obj.hide_render or obj.type in {'LIGHT', 'CAMERA'}
                or obj.name in {'STUDIO_GROUND', 'INTERNAL_ENVELOPES'}):
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in list(bpy.context.scene.objects):
        if obj.type in {'MESH', 'CURVE', 'FONT'}:
            obj.hide_set(False)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target='MESH')
            obj.select_set(False)

    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        p = mat.node_tree.nodes.get('Principled BSDF')
        if not p:
            continue
        # Preserve constant materials in the early blockouts. For the later
        # procedural finish, use the midpoint of its authored roughness range.
        roughness = p.inputs['Roughness']
        if roughness.links:
            node = roughness.links[0].from_node
            if node.type == 'MAP_RANGE':
                roughness.default_value = (
                    node.inputs['To Min'].default_value
                    + node.inputs['To Max'].default_value
                ) / 2
        for slot in ['Roughness', 'Normal']:
            for link in list(p.inputs[slot].links):
                mat.node_tree.links.remove(link)

    destination = ROOT / 'exports' / f'aerix-review-v{version}.glb'
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format='GLB', export_apply=True,
        export_animations=False, export_current_frame=True,
        export_cameras=False, export_lights=False,
    )
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    report.append({
        'version': version, 'source': str(source.relative_to(ROOT)),
        'source_sha256': source_hash, 'source_unchanged': True,
        'frame': 1, 'animations_exported': False,
        'export': str(destination.relative_to(ROOT)),
        'bytes': destination.stat().st_size,
        'mesh_count': sum(o.type == 'MESH' for o in bpy.context.scene.objects),
        'object_names': sorted(o.name for o in bpy.context.scene.objects),
    })
    (REPORT / 'export-validation.json').write_text(json.dumps(report, indent=2))
    print(f'EARLY_REVIEW_EXPORT_COMPLETE V{version}', flush=True)
