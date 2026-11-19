"""Fair the lower casting's highlights using its original mould coordinates."""
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from rill_shell import T, U, skin, stations
from render_v14b import render_details

assert Path(bpy.data.filepath).resolve() == ROOT / 'blender/drone-v14a.blend'
scene = bpy.context.scene
scene.frame_set(1)
group = bpy.data.collections['V14a | Aircraft']
shell = group.objects['Shell.moulded_fuselage']
mesh = shell.data
rows = [r for r in stations if -58.7 <= r[0] <= 64.1]
rim = ([(-1, t) for t in reversed(T) if t <= .74] + [(u, 0) for u in U[1:]]
       + [(1, t) for t in T if 0 < t <= .74])
rim_s = [u * (1 + t) for u, t in rim]


def read_cage(version):
    with bpy.data.libraries.load(str(ROOT / f'blender/drone-{version}.blend')) as (_, data):
        data.meshes = ['RILL shell · grilles and hatch']
    return data.meshes[0]


def mould_chart():
    # A material coordinate on the original coarse casting makes the guide
    # independent of the uneven triangle density around grilles and hinges.
    reference = read_cage('v12')
    search = KDTree(len(reference.vertices))
    for v in reference.vertices:
        search.insert(v.co * 1000, v.index)
    search.balance()
    ids = []
    for row in rows:
        line = []
        for u, t in rim:
            _, index, gap = search.find(skin(row, u, t))
            assert gap < .001
            line.append(index)
        ids.append(line)
    bpy.data.meshes.remove(reference)
    cage = read_cage('v14')
    points = [v.co.copy() for v in cage.vertices]
    uv = {index: Vector((r[0], s, 0))
          for r, line in zip(rows, ids) for s, index in zip(rim_s, line)}
    cells = {frozenset((ids[i][j], ids[i+1][j], ids[i][j+1], ids[i+1][j+1]))
             for i in range(len(rows)-1) for j in range(len(rim)-1)}
    faces = {p.index for p in cage.polygons if frozenset(p.vertices) in cells}
    assert len(faces) == len(cells)
    cage.calc_loop_triangles()
    tris = [tuple(t.vertices) for t in cage.loop_triangles if t.polygon_index in faces]
    bpy.data.meshes.remove(cage)
    grid = np.array([[points[k] for k in line] for line in ids]) * 1000
    return points, tris, uv, BVHTree.FromPolygons(points, tris, all_triangles=True), grid


def gaussian(field, axis, sigma):
    radius = int(np.ceil(3.5 * sigma))
    weights = np.exp(-.5 * (np.arange(-radius, radius+1) / sigma)**2)
    weights /= weights.sum()
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, radius, mode='edge'), weights, mode='valid'), axis, field)


def ramp(low, high, value):
    t = np.clip((value - low) / (high - low), 0, 1)
    return t*t*(3-2*t)


def highlight_guide(grid):
    ys = np.linspace(rows[0][0], rows[-1][0], 601)
    ss = np.linspace(rim_s[0], rim_s[-1], 641)
    coarse = np.array([[np.interp(ss, rim_s, row[:, d]) for d in range(3)] for row in grid])
    field = np.apply_along_axis(lambda line: np.interp(ys, [r[0] for r in rows], line), 0, coarse).transpose(0, 2, 1)
    long = (ys[-1] - ys[0]) / (len(ys)-1)
    cross = ss[1]-ss[0]
    guide = gaussian(field, 0, 5.5/long)
    # Fair the wall from the radiused return up to the parting line. The
    # guide omits local stow relief; the actual relief still accommodates
    # the moving arms. Keep a small crown in the vertical section.
    for sign in (-1, 1):
        wall = ss*sign >= 1
        t = (ss[wall]*sign-1)/.74
        low = guide[:, np.argmin(abs(ss-sign)), 0]
        high = guide[:, np.argmin(abs(ss-sign*1.74)), 0]
        guide[:,wall,0] = low[:,None]*(1-t) + high[:,None]*t + sign*.75*np.sin(np.pi*t)
    # Break only the lower return into a tight continuous roll. The belly
    # itself can take a broader blend around the start of the camera bay.
    broad = gaussian(guide, 1, .072/cross)
    tight = gaussian(guide, 1, .032/cross)
    blend = (1-ramp(.74,.98,abs(ss)))[None,:,None]
    guide = tight*(1-blend) + broad*blend
    du = np.gradient(guide, ys, axis=0)
    dv = np.gradient(guide, ss, axis=1)
    normals = np.cross(du, dv)
    normals /= np.maximum(1.e-12, np.linalg.norm(normals,axis=2,keepdims=True))
    # At the rear, the bearing pocket needs a gentle physical shoulder.
    # Fit a rounded cross section to that relief and use its own tangents
    # so raking light cannot break up on steep triangles.
    rear = gaussian(gaussian(field,0,4.8/long),1,.105/cross)
    radial = np.sign(ss)[None,:]
    dx = (rear[:,:,0]-field[:,:,0])*radial
    rear_shift = np.clip(dx,-3.0,.20)
    rear_mask = (ramp(-58.7,-53.8,ys)*(1-ramp(-37,-22,ys)))[:,None]
    rear_mask = rear_mask * (ramp(1.06,1.27,abs(ss))*(1-ramp(1.61,1.74,abs(ss))))[None,:]
    rear_pos = field.copy()
    rear_pos[:,:,0] += radial*rear_shift*rear_mask
    rear_normal_source = gaussian(gaussian(rear_pos,0,3.6/long),1,.075/cross)
    rear_n = np.cross(np.gradient(rear_normal_source,ys,axis=0), np.gradient(rear_normal_source,ss,axis=1))
    rear_n /= np.maximum(1.e-12, np.linalg.norm(rear_n,axis=2,keepdims=True))
    shade_rear = (1-ramp(-33,-20,ys))[:,None] * ramp(1.02,1.23,abs(ss))[None,:]
    normals = normals*(1-shade_rear[:,:,None]) + rear_n*shade_rear[:,:,None]
    # A separate short longitudinal blend rounds the corners in profile.
    profile_roll = gaussian(field, 0, 3.3/long)[:,:,2] - field[:,:,2]
    return ys, ss, normals, guide, profile_roll, rear_shift*rear_mask


def apply_guide():
    points, triangles, params, tree, grid = mould_chart()
    ys, ss, guide, fair, profile_roll, rear_shift = highlight_guide(grid)
    count = len(mesh.vertices)
    pos = np.zeros((count,3), dtype='f')
    mesh.vertices.foreach_get('co', pos.ravel())
    mapped = np.zeros((count,2))
    covered = np.zeros(count, dtype=bool)
    for v in mesh.vertices:
        nearest, _, face, dist = tree.find_nearest(v.co)
        if dist > .000049:
            continue
        tri = triangles[face]
        point = geometry.barycentric_transform(nearest, *(points[k] for k in tri), *(params[k] for k in tri))
        mapped[v.index] = point.x, point.y
        covered[v.index] = True
    y, s = mapped.T
    iy = np.clip((y-ys[0])/(ys[1]-ys[0]), 0, len(ys)-1.0001)
    js = np.clip((s-ss[0])/(ss[1]-ss[0]), 0, len(ss)-1.0001)
    i,j = iy.astype(int),js.astype(int)
    a,b = (iy-i)[:,None],(js-j)[:,None]
    target = ((1-a)*(1-b)*guide[i,j] + a*(1-b)*guide[i+1,j]
              + (1-a)*b*guide[i,j+1] + a*b*guide[i+1,j+1])
    weight = covered * ramp(-58.7,-54.5,y) * (1-ramp(54,64.1,y)) * (1-ramp(1.67,1.74,abs(s)))
    # Take down the two raised shelves. Work inward around the parked arms
    # and ease the displacement into the top seam and each end of the panel.
    side = np.sign(s)
    guide_x = ((1-a)*(1-b)*fair[i,j] + a*(1-b)*fair[i+1,j]
               + (1-a)*b*fair[i,j+1] + a*b*fair[i+1,j+1])[:,0]
    inset = 1.6 * np.tanh(np.maximum(abs(pos[:,0])*1000 - abs(guide_x), 0) / 1.6)
    wall = ramp(.96,1.11,abs(s)) * (1-ramp(1.61,1.74,abs(s)))
    wall *= ramp(-58.7,-51.8,y) * (1-ramp(34,47,y)) * covered
    z_delta = ((1-a[:,0])*(1-b[:,0])*profile_roll[i,j] + a[:,0]*(1-b[:,0])*profile_roll[i+1,j]
               + (1-a[:,0])*b[:,0]*profile_roll[i,j+1] + a[:,0]*b[:,0]*profile_roll[i+1,j+1])
    z_delta *= ramp(8,20,y)*(1-ramp(54,61,y))*ramp(.68,.95,abs(s))*(1-ramp(1.07,1.43,abs(s)))*covered
    # Limit the edge rounding on this close-up polish.
    z_delta = 1.0*np.tanh(z_delta/1.0)
    new_pos = pos.copy()
    rear_delta = ((1-a[:,0])*(1-b[:,0])*rear_shift[i,j] + a[:,0]*(1-b[:,0])*rear_shift[i+1,j]
                  + (1-a[:,0])*b[:,0]*rear_shift[i,j+1] + a[:,0]*b[:,0]*rear_shift[i+1,j+1])
    radial_delta = -inset*wall*ramp(-37,-22,y) + rear_delta*covered
    new_pos[:,0] += .001*side*radial_delta
    new_pos[:,2] += .001*z_delta
    if '--original-envelope' in sys.argv:
        delta = new_pos-pos
        lengths = np.linalg.norm(delta,axis=1,keepdims=True)
        new_pos = pos + delta*np.minimum(1,.0000045/np.maximum(lengths,1.e-12))
    old = np.zeros((len(mesh.loops),3), dtype='f')
    mesh.corner_normals.foreach_get('vector',old.ravel())
    vi = np.zeros(len(mesh.loops),dtype='i')
    mesh.loops.foreach_get('vertex_index',vi)
    w = weight[vi,None]
    normals = old*(1-w) + target[vi]*w
    normals /= np.maximum(1.e-12,np.linalg.norm(normals,axis=1,keepdims=True))
    mesh.vertices.foreach_set('co',new_pos.ravel())
    mesh.update()
    mesh.normals_split_custom_set(normals.tolist())
    mesh.update()
    after = np.zeros_like(pos)
    mesh.vertices.foreach_get('co',after.ravel())
    assert np.array_equal(new_pos,after)
    radial_move = side * (after[:,0]-pos[:,0])*1000
    return {'shaded_shell_vertices':int(np.count_nonzero(weight>.01)),
            'total_shell_vertices':count, 'max_local_inset_mm':round(float(-min(radial_move)),3),
            'max_local_outset_mm':round(float(max(radial_move)),3),
            'max_lower_profile_rounding_mm':round(float(1000*max(abs(after[:,2]-pos[:,2]))),3),
            'max_vertex_move_mm':round(float(1000*np.max(np.linalg.norm(after-pos,axis=1))),3)}


if __name__ == '__main__':
    report = apply_guide()
    print('Sidewall pass:', report,flush=True)
    if '--proof' in sys.argv:
        render_details(ROOT/'measurements', 'v14b-envelope' if '--original-envelope' in sys.argv else 'v14b-proof', preview=True)
    elif '--publish' in sys.argv or '--check' in sys.argv:
        from check_v13_joints import check_joints
        from check_v09_gear import inspect_gear
        from v10_alignment import alignment
        report.update(check_joints(group))
        report['fold'] = inspect_gear(group)
        report['optical_center_xz_mm'] = alignment(group.objects)
        scene.frame_set(1)
        if '--check' in sys.argv:
            print('Checked native fold', report, flush=True)
            sys.exit(0)
        blend = ROOT/'blender/drone-v14b.blend'
        glb = ROOT/'exports/drone-v14b.glb'
        assert not blend.exists() and not glb.exists()
        group.name = 'V14b | Aircraft'
        group.objects['Drone.V14a'].name = 'Drone.V14b'
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group.objects:
            obj.select_set(True)
        pending = ROOT/'exports/pending-v14b.glb'
        bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,export_tangents=True,
            export_texcoords=True,export_image_format='AUTO',export_animation_mode='NLA_TRACKS',export_animations=True,
            export_frame_range=True,export_force_sampling=True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        pending.rename(glb)
        (ROOT/'measurements/v14b-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
