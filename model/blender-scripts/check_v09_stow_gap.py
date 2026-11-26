"""Bound the nearest front strut to fixed fuselage gap during the V08/V09 sweep."""
import json
from pathlib import Path
import sys
import bpy
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes
import check_v06_clearance as clearance


def check(version):
    bpy.ops.wm.open_mainfile(filepath=str(root/f'blender/drone-{version}.blend'))
    scene=bpy.context.scene
    scene.frame_set(1)
    meshes=local_meshes(bpy.data.collections[version.upper()+' | Aircraft'])
    fixed=bpy.data.objects['Shell.moulded_fuselage']
    tree=BVHTree.FromPolygons(*meshes[fixed.name],all_triangles=True)
    poses=[]
    seen=set()
    upper=float('inf')
    for f in range(1,122):
        scene.frame_set(f)
        for side in ('L','R'):
            name='Leg.front.'+side
            transform=fixed.matrix_world.inverted()@bpy.data.objects[name].matrix_world
            key=(name,tuple(v for row in transform for v in row))
            if key in seen: continue
            seen.add(key)
            verts,faces=meshes[name]
            pts=[transform@v for v in verts]
            nearest=min(tree.find_nearest(v)[3] for v in pts)
            upper=min(nearest,upper)
            poses.append((pts,faces))
    # Closest vertex-to-surface distance is an upper bound. Test a conservative
    # lower bound on whole triangles with the established subdivision check.
    for candidate in [i/4 for i in range(int(upper*4000),0,-1)]+[.10,.05,.01]:
        if candidate*.001>=upper: continue
        clearance.GAP=candidate*.001
        if all(clearance.clears(tree,*(pts[j] for j in face)) for pts,faces in poses for face in faces):
            return {'all_sampled_surfaces_at_least_mm':candidate,'nearest_sampled_vertex_at_most_mm':round(upper*1000,4)}
    return {'all_sampled_surfaces_at_least_mm':0,'nearest_sampled_vertex_at_most_mm':round(upper*1000,4)}


result={v:check(v) for v in ('v08','v09')}
(root/'measurements/v09-stow-gap.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
