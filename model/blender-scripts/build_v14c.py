"""Fair the two lower tail corners and the hatch return in one continuous mesh."""
from pathlib import Path
from collections import defaultdict
import sys
import json

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from render_v14c import VIEWS, render_details

LEVEL = 2
TAIL_Y = -.05812
UPPER_Z = .0365


def ramp(lo, hi, x):
    t = max(0., min(1., (x-lo)/(hi-lo)))
    return t*t*(3-2*t)


def topology(mesh):
    trials = bmesh.new()
    trials.from_mesh(mesh)
    assert all(e.is_manifold and e.is_contiguous for e in trials.edges)
    trials.free()


def patch_surface(me, indices):
    src = sorted({v for i in indices for v in me.polygons[i].vertices})
    local = {v:k for k,v in enumerate(src)}
    polys = [me.polygons[i] for i in indices]
    patch = bpy.data.meshes.new('Rear corner working cage')
    patch.from_pydata([me.vertices[v].co for v in src], [],
                      [[local[v] for v in f.vertices] for f in polys])
    for mat in me.materials:
        patch.materials.append(mat)
    uv = patch.uv_layers.new(name='Finish UV')
    orig_uv = me.uv_layers.active.data
    for f,old in zip(patch.polygons,polys):
        f.material_index = old.material_index
        f.use_smooth = True
        for i,j in zip(f.loop_indices,old.loop_indices):
            uv.data[i].uv = orig_uv[j].uv
    obj = bpy.data.objects.new('Rear corner temporary subdivision',patch)
    bpy.context.scene.collection.objects.link(obj)
    m = obj.modifiers.new('Continuous tail surface','SUBSURF')
    m.levels = m.render_levels = LEVEL
    m.uv_smooth = 'NONE'
    def evaluated(kind):
        m.subdivision_type = kind
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(obj.evaluated_get(deps),depsgraph=deps)
    simple = evaluated('SIMPLE')
    smooth = evaluated('CATMULL_CLARK')
    assert len(simple.vertices)==len(smooth.vertices) and len(simple.loops)==len(smooth.loops)
    bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.meshes.remove(patch)
    return simple,smooth


def fair_hatch_path(mesh):
    """Carry both lips of the battery reveal together around the two rear bends."""
    from rill_shell import stations, U, skin
    aft = [r for r in stations if r[0]<=-59.2]
    path = ([skin(r,-1,.5) for r in reversed(aft)] +
            [skin(aft[0],u,.5) for u in U[1:]] +
            [skin(r,1,.5) for r in aft[1:]])
    path = np.asarray(path,dtype=float)
    arc = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
    s = np.linspace(0,arc[-1],501)
    p = np.array([np.interp(s,arc,path[:,k]) for k in range(3)]).T
    def guide(radius):
        sigma = radius/(s[1]-s[0])
        window = int(np.ceil(sigma*3))
        w = np.exp(-.5*(np.arange(-window,window+1)/sigma)**2); w/=w.sum()
        return np.array([np.convolve(np.pad(c,window,mode='edge'),w,mode='valid') for c in p.T]).T
    delta = guide(4.1)-guide(.95)
    delta *= np.minimum(1,.63/np.maximum(np.linalg.norm(delta,axis=1,keepdims=True),1e-12))
    delta *= np.array([ramp(0,7,min(at,s[-1]-at)) for at in s])[:,None]
    search = KDTree(len(p))
    for i,pt in enumerate(p):
        search.insert(pt,i)
    search.balance()
    for v in mesh.vertices:
        q = v.co*1000
        _,i,distance = search.find(q)
        if distance>=12:
            continue
        j = min(max(i,1),len(p)-2)
        # Continuous longitudinal interpolation even between stored samples.
        tangent = p[j+1]-p[j-1]
        f = float(np.dot(np.asarray(q)-p[j],tangent)/max(np.dot(tangent,tangent),1e-14))*2
        if f>=0:
            shift = delta[j]*(1-min(f,1)) + delta[j+1]*min(1,f)
        else:
            shift = delta[j]*(1+max(f,-1)) - delta[j-1]*max(-1,f)
        v.co += Vector(shift)*(.001*(1-ramp(2,12,distance)))
    mesh.update()


def fair_lower_roll(mesh):
    """Area-weighted surface fit in millimetres; extra seam loops carry no extra weight."""
    mesh.calc_loop_triangles()
    xyz = np.zeros((len(mesh.vertices),3),dtype='f')
    mesh.vertices.foreach_get('co',xyz.ravel())
    xyz = xyz.astype(float)*1000.
    triangles = np.array([tuple(t.vertices) for t in mesh.loop_triangles])
    a,b,c = (xyz[triangles[:,k]] for k in range(3))
    vector_area = np.cross(b-a,c-a)*.5
    area = np.linalg.norm(vector_area,axis=1)
    center = (a+b+c)/3
    spacing = .55
    # Bin the areas, first moments and normal vectors on a centered lattice.
    node = np.rint(center/spacing).astype(int)
    offset = node.min(axis=0)-10
    shape = tuple(node.max(axis=0)-offset+11)
    node -= offset
    moments = np.zeros((*shape,7))
    np.add.at(moments,tuple(node.T),np.column_stack((area,center*area[:,None],vector_area)))
    sigma = 1.6/spacing
    k = np.arange(-9,10)
    kernel = np.exp(-.5*(k/sigma)**2); kernel/=kernel.sum()
    for axis in range(3):
        moments=np.apply_along_axis(lambda line:np.convolve(line,kernel,mode='same'),axis,moments)
    lattice = xyz/spacing-offset
    lower = np.floor(lattice).astype(int)
    mix = lattice-lower
    at = np.zeros((len(xyz),7))
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                d = np.array((dx,dy,dz))
                weights = np.prod(np.where(d,mix,1-mix),axis=1)
                at += moments[tuple((lower+d).T)]*weights[:,None]
    avg = at[:,1:4]/np.maximum(at[:,:1],1e-12)
    normal = at[:,4:7]/np.maximum(np.linalg.norm(at[:,4:7],axis=1,keepdims=True),1e-12)
    original = np.zeros((len(xyz),3),dtype='f')
    mesh.vertices.foreach_get('normal',original.ravel())
    shift = np.sum((avg-xyz)*original,axis=1)
    # Limit the radius change on the foot-adjacent underside. Dissolve the
    # edit before the narrow hatch reveal or the previous shell patch.
    envelope = np.array([(1-ramp(19,26,p[2]))*(1-ramp(-63,-58.12,p[1])) for p in xyz])
    delta = original*(np.clip(shift,-.68,.18)*envelope)[:,None]*.001
    result = original*(1-.92*envelope[:,None]) + normal*(.92*envelope[:,None])
    result /= np.maximum(np.linalg.norm(result,axis=1,keepdims=True),1.e-12)
    return [Vector(v) for v in delta], [Vector(v) for v in result]


def fair_corners(obj):
    me = obj.data
    old_pos = [v.co.copy() for v in me.vertices]
    old_norm = [n.vector.copy() for n in me.corner_normals]
    uvlayer = me.uv_layers.active.data
    selected = [f.index for f in me.polygons
                if max(old_pos[i].y for i in f.vertices)<TAIL_Y and f.center.z<UPPER_Z]
    chosen = set(selected)
    counts = defaultdict(int)
    for i in selected:
        for e in me.polygons[i].edge_keys:
            counts[e] += 1
    boundary = {e for e,count in counts.items() if count==1}
    simple, smooth = patch_surface(me, selected)
    # Match the simple subdivision edge to the old neighbor. Each coarse edge
    # gets exactly 2^LEVEL pieces. The adjoining face receives the same IDs.
    border = {v for e in boundary for v in e}
    finder = KDTree(len(simple.vertices))
    for v in simple.vertices:
        finder.insert(v.co,v.index)
    finder.balance()
    points = list(old_pos)
    out_id = [None]*len(simple.vertices)
    for v in border:
        _,j,d = finder.find(old_pos[v])
        assert d<1.e-7,(v,d)
        out_id[j] = v
    for v in simple.vertices:
        if out_id[v.index] is None:
            out_id[v.index] = len(points)
            points.append(v.co.copy())
    stitches = {}
    on_edge = set()
    for a,b in boundary:
        line = []
        for k in range(1,2**LEVEL):
            _,j,d = finder.find(old_pos[a].lerp(old_pos[b],k/(2**LEVEL)))
            assert d<1.e-7,(a,b,d)
            line.append(out_id[j])
            on_edge.add(j)
        stitches[(a,b)] = line
        stitches[(b,a)] = list(reversed(line))
    # Smoothly run out the fairing at the original seam with the V14b
    # side panel and above the lower hatch. The boundary itself is exact.
    for v in border:
        on_edge.add(finder.find(old_pos[v])[1])
    # The lower groove is a real narrow profiled channel. The outer lip
    # and inner tip run together in the fine cage; its two sides keep their
    # separate material and curvature.
    fair_hatch_path(smooth)
    roll_delta, smooth_norm = fair_lower_roll(smooth)
    blend = []
    max_move = [0.,0.]
    for v,sv in zip(simple.vertices,smooth.vertices):
        p = v.co
        w = (1-ramp(-.0625,TAIL_Y,p.y))*(1-ramp(.0314,UPPER_Z,p.z))
        if v.index in on_edge:
            w = 0.
        q = p.lerp(sv.co+roll_delta[v.index],w)
        points[out_id[v.index]] = q
        blend.append(w)
        half = int(p.x>0)
        max_move[half] = max(max_move[half],(q-p).length*1000)

    patch_points = [points[k] for k in out_id]
    simple.calc_loop_triangles()
    reflected_tree = BVHTree.FromPolygons(patch_points,[tuple(t.vertices) for t in simple.loop_triangles],all_triangles=True)
    mirror_error = max(reflected_tree.find_nearest(Vector((-p.x,p.y,p.z)))[3]*1000
                       for p in patch_points if p.y<-.060 and p.z<.031)
    assert mirror_error < .015, mirror_error
    # The starting normals on the shared boundary and protected upper area
    # come from the old split normals, interpolated in its actual triangles.
    me.calc_loop_triangles()
    tris = [t for t in me.loop_triangles if t.polygon_index in chosen]
    corners = [tuple(t.loops) for t in tris]
    tri_ids = [tuple(t.vertices) for t in tris]
    tree = BVHTree.FromPolygons(old_pos,tri_ids,all_triangles=True)
    from mathutils.geometry import barycentric_transform
    guides = []
    for j,v in enumerate(simple.vertices):
        if blend[j]>.999999:
            guides.append(None)
            continue
        hit,_,i,_ = tree.find_nearest(v.co)
        tri = tri_ids[i]
        n = barycentric_transform(hit,*(old_pos[k] for k in tri),*(old_norm[k] for k in corners[i]))
        guides.append(n.normalized())

    faces, mats, uvs, normals, smooth_flags = [],[],[],[],[]
    def emit(ids,mat,texture,ns,shade):
        faces.append(ids); mats.append(mat); uvs.extend(texture)
        normals.extend(ns); smooth_flags.append(shade)
    for f in me.polygons:
        if f.index in chosen:
            continue
        ids = []; texture = []; ns = []
        loops = list(f.loop_indices)
        for step,k in enumerate(loops):
            h = loops[(step+1)%len(loops)]
            a,b = me.loops[k].vertex_index,me.loops[h].vertex_index
            ids.append(a); texture.append(uvlayer[k].uv.copy()); ns.append(old_norm[k])
            for sub,idx in enumerate(stitches.get((a,b),()),1):
                frac = sub/(2**LEVEL)
                ids.append(idx)
                texture.append(uvlayer[k].uv.lerp(uvlayer[h].uv,frac))
                ns.append(old_norm[k].lerp(old_norm[h],frac).normalized())
        emit(ids,f.material_index,texture,ns,f.use_smooth)
    patch_norm = [n if g is None else g.lerp(n,w).normalized()
                  for n,g,w in zip(smooth_norm,guides,blend)]
    for f in simple.polygons:
        ids = list(f.vertices)
        emit([out_id[i] for i in ids], f.material_index,
             [simple.uv_layers.active.data[k].uv.copy() for k in f.loop_indices],
             [patch_norm[i] for i in ids],True)
    # Compact the captured indices so the old rear cage is completely removed.
    used = sorted({v for face in faces for v in face})
    new_id = {v:i for i,v in enumerate(used)}
    final = bpy.data.meshes.new('RILL shell · faired rear corners')
    final.from_pydata([points[v] for v in used],[],[[new_id[v] for v in face] for face in faces])
    for mat in me.materials:
        final.materials.append(mat)
    final.polygons.foreach_set('material_index',np.array(mats,dtype=np.int32))
    final.polygons.foreach_set('use_smooth',np.array(smooth_flags,dtype=bool))
    final.uv_layers.new(name=me.uv_layers.active.name).data.foreach_set('uv',np.asarray(uvs,dtype='f').ravel())
    sharp = {tuple(sorted((new_id[a],new_id[b]))) for e in me.edges if e.use_edge_sharp
             for a,b in [e.vertices] if a in new_id and b in new_id and (min(a,b),max(a,b)) not in counts}
    for e in final.edges:
        e.use_edge_sharp = tuple(sorted(e.vertices)) in sharp
    assert not final.validate()
    final.update()
    final.normals_split_custom_set(normals)
    final.update()
    topology(final)
    obj.data = final
    for item in (simple,smooth):
        bpy.data.meshes.remove(item)
    assert abs(max_move[0]-max_move[1])<.025,max_move
    return {'coarse_rear_faces':len(selected),'subdivision_levels':LEVEL,
            'mirrored_vertex_to_surface_mm':round(mirror_error,6),
            'max_move_left_right_mm':[round(v,4) for v in max_move],
            'source_shell_faces':len(me.polygons),'finished_shell_faces':len(final.polygons)}


if __name__ == '__main__':
    assert Path(bpy.data.filepath).resolve()==ROOT/'blender/drone-v14b.blend'
    scene = bpy.context.scene
    scene.frame_set(1)
    group = bpy.data.collections['V14b | Aircraft']
    shell = group.objects['Shell.moulded_fuselage']
    report = fair_corners(shell)
    print('Rear corner pass',report,flush=True)
    if '--proof' in sys.argv:
        render_details(ROOT/'measurements','v14c-proof',preview=True,views=VIEWS)
    elif '--publish' in sys.argv:
        from check_v13_joints import check_joints
        from check_v09_gear import inspect_gear
        from v10_alignment import alignment
        report.update(check_joints(group))
        report['fold'] = inspect_gear(group)
        report['optical_center_xz_mm'] = alignment(group.objects)
        scene.frame_set(1)
        blend = ROOT/'blender/drone-v14c.blend'
        glb = ROOT/'exports/drone-v14c.glb'
        assert not blend.exists() and not glb.exists()
        group.name = 'V14c | Aircraft'
        group.objects['Drone.V14b'].name = 'Drone.V14c'
        bpy.ops.object.select_all(action='DESELECT')
        for o in group.objects:
            o.select_set(True)
        pending = ROOT/'exports/pending-v14c.glb'
        bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,export_tangents=True,
            export_texcoords=True,export_image_format='AUTO',export_animation_mode='NLA_TRACKS',export_animations=True,
            export_frame_range=True,export_force_sampling=True)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        pending.rename(glb)
        (ROOT/'measurements/v14c-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
