"""Compare optical geometry, V16 component meshes, mount stations and all fold poses."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
pivots = ['Gimbal.' + axis for axis in ('yaw', 'roll', 'pitch')]
optics = ['Camera.' + part for part in ('front_glass', 'inner_glass', 'iris', 'lens_barrel', 'receiver')]
stations = ['Gimbal.mount.' + side + '.shank' for side in ('L', 'R')]
stations += ['Gimbal.isolator.' + side + '.' + end for side in ('L','R') for end in ('back','front')]

def mesh_digest(obj):
    mesh = obj.data
    digest = hashlib.sha256()
    for seq, attr, count, dtype in [
        (mesh.vertices, 'co', 3, 'float32'), (mesh.loops, 'vertex_index', 1, 'int32'),
        (mesh.polygons, 'loop_total', 1, 'int32'), (mesh.polygons, 'material_index', 1, 'int32')]:
        block = np.empty(len(seq) * count, dtype=dtype)
        seq.foreach_get(attr, block)
        digest.update(block.tobytes())
    for mat in mesh.materials:
        digest.update(mat.name.encode('utf8') + bytes([0]))
    return digest.hexdigest()

def bounds(obj):
    points = np.array([obj.matrix_world @ v.co for v in obj.data.vertices]) * 1000
    return points.min(axis=0), points.max(axis=0)

def setup(version):
    scene = bpy.data.scenes[version + ' · Assembled']
    bpy.context.window.scene = scene
    scene.frame_set(1)
    aircraft = bpy.data.collections[version + ' | Aircraft']
    inside = bpy.data.collections[version + ' | Interior']
    existing = {o.name:mesh_digest(o) for o in inside.objects if o.get('Review 7 part')}
    lenses = {name:mesh_digest(scene.objects[name]) for name in optics}
    centres = {}
    for name in stations:
        lower, upper = bounds(scene.objects[name])
        centres[name] = (lower + upper)[:2] / 2
    origins = {name:list(scene.objects[name].matrix_world.translation * 1000) for name in pivots}
    tracks = sorted({o.name for o in aircraft.objects if o.type == 'MESH'} | set(pivots) | existing.keys())
    poses = []
    for i in range(1,122):
        scene.frame_set(i)
        poses.append(np.array([scene.objects[name].matrix_world for name in tracks]))
    return existing, lenses, centres, origins, tracks, poses

if __name__ == '__main__':
    assert Path(bpy.data.filepath).name == 'drone-v17.blend'
    current = setup('V17')
    bpy.ops.wm.open_mainfile(filepath=str(root / 'blender/drone-v16.blend'))
    approved = setup('V16')
    assert current[:2] == approved[:2] and current[3:5] == approved[3:5]
    assert all(np.array_equal(a,b) for a,b in zip(current[5], approved[5]))
    shift = max(float(np.linalg.norm(current[2][n] - approved[2][n])) for n in stations)
    assert shift < .001, shift
    report = {'baseline':'V16','battery_and_core_meshes_unchanged':len(current[0]),
              'unchanged_optical_meshes':optics, 'gimbal_pivots_xyz_mm':current[3],
              'screw_and_damper_axes_xy_mm':{n:xy.tolist() for n,xy in current[2].items()},
              'maximum_mount_axis_delta_mm':shift,
              'aircraft_mesh_pose_tracks':len(current[4]) - len(pivots) - len(current[0]),
              'total_pose_tracks':len(current[4]),'identical_frames':len(current[5])}
    (root / 'measurements/v17-registration.json').write_text(json.dumps(report,indent=2)+'\n')
    print('V17 REGISTRATION', report)

