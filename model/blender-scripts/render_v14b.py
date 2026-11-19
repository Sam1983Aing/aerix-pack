"""Matched exterior inspection from either flank and from below the aircraft."""
from pathlib import Path
import runpy
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
VIEWS = {
    'left-wall': ((-.021, -.006, .028), (-.25, -.022, -.015), .135),
    'right-wall': ((.021, -.006, .028), (.25, -.022, -.015), .135),
    'belly': ((0, .002, .019), (-.116, -.165, -.105), .111),
}


def render_details(dest, prefix, preview=False, views=None):
    scene = bpy.context.scene
    scene.frame_set(1)
    devices = bpy.context.preferences.addons['cycles'].preferences
    devices.compute_device_type = 'METAL'
    devices.refresh_devices()
    for device in devices.devices:
        device.use = device.type == 'METAL'
    if any(d.use for d in devices.devices):
        scene.cycles.device = 'GPU'
    original = scene.camera
    camera = bpy.data.objects['Studio.camera.three-quarter'].copy()
    camera.data = camera.data.copy()
    scene.collection.objects.link(camera)
    scene.camera = camera
    floor = bpy.data.objects['Studio.floor']
    floor.hide_render = True
    scene.cycles.samples = 14 if preview else 40
    scene.render.resolution_percentage = 53 if preview else 100
    dest.mkdir(parents=True, exist_ok=True)
    for name, (center, offset, width) in (VIEWS if views is None else views).items():
        camera.location = Vector(center) + Vector(offset)
        camera.rotation_euler = (-Vector(offset)).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = width
        path = dest / f'{prefix}-{name}.png'
        temp = path.with_name('.writing-' + path.name)
        scene.render.filepath = str(temp)
        bpy.ops.render.render(write_still=True)
        temp.replace(path)
    bpy.data.objects.remove(camera, do_unlink=True)
    scene.camera = original
    floor.hide_render = False
    scene.render.resolution_percentage = 100
    scene.cycles.samples = 48


if __name__ == '__main__':
    version = Path(bpy.data.filepath).stem.removeprefix('drone-')
    assert version in ('v14a', 'v14b')
    dest = ROOT / ('teach/shots/v14b' if version == 'v14a' else 'renders/v14b')
    render_details(dest, version)
    if version == 'v14b':
        sys.path.insert(0, str(ROOT/'scripts'))
        try:
            runpy.run_path(str(ROOT / 'scripts/render_revision.py'), run_name='__main__')
        except SystemExit as end:
            if end.code:
                raise
        from v09_gear_views import render_photos
        render_photos(bpy.context.scene, version, False)
