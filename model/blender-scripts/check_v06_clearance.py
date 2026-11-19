"""Certify a distance margin around the reshaped sleeve skin on every fold frame.

A sphere encloses each triangle. If the nearest opposing surface is farther
than its radius plus the requested gap, the entire triangle clears that gap.
Subdivide ambiguous triangles along their longest edge.
"""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import local_meshes

GAP=.002  # metres; retain any pre-existing tighter fit by leaving that skin untouched


def clears(tree,a,b,c,depth=0):
    center=(a+b+c)/3
    radius=max((p-center).length for p in (a,b,c))
    hit=tree.find_nearest(center,radius+GAP+.0000001)
    if hit[0] is None:return True
    if hit[3]<GAP or depth==20:return False
    edges=[(a,b,c),(b,c,a),(c,a,b)]
    u,v,w=max(edges,key=lambda e:(e[0]-e[1]).length_squared)
    mid=(u+v)/2
    return clears(tree,u,mid,w,depth+1) and clears(tree,mid,v,w,depth+1)


def protected_skin(group,original):
    local=local_meshes(group)
    trees={n:BVHTree.FromPolygons(vs,fs,all_triangles=True) for n,(vs,fs) in local.items()}
    sleeves={}
    for name,old in original.items():
        vs,fs=local[name]
        changed={i for i,(a,b) in enumerate(zip(vs,old)) if (a-b).length>1e-9}
        patches=[]
        for ring in range(17):
            faces=[f for f in fs if any(i in changed for i in f) and min(f)//64==ring]
            if not faces:continue
            points={i for f in faces for i in f}
            center=sum((vs[i] for i in points),Vector())/len(points)
            radius=max((vs[i]-center).length for i in points)
            patches.append((ring,center,radius,faces))
        sleeves[name]=patches
    # Cache repeated relative poses, e.g. between a sleeve and its own blades
    # once the blades have finished parking.
    passed=set()
    for frame in range(1,122):
        bpy.context.scene.frame_set(frame)
        matrices={n:bpy.data.objects[n].matrix_world.copy() for n in local}
        inverses={n:m.inverted() for n,m in matrices.items()}
        for name,patches in sleeves.items():
            code=name[-2:]
            mates={name,'Motor.'+code,'Hinge.mount.'+code,'Hinge.pin.'+code}
            if code[0]=='F': mates.add('Leg.front.'+code[-1])
            for other,tree in trees.items():
                if other in mates:continue
                transform=inverses[other]@matrices[name]
                key=(name,other,tuple(round(v,8) for row in transform for v in row))
                if key in passed:continue
                vs=local[name][0]
                for ring,c,r,faces in patches:
                    if tree.find_nearest(transform@c,r+GAP+.0000001)[0] is None:continue
                    verts={i:transform@vs[i] for f in faces for i in f}
                    for f in faces:
                        if not clears(tree,*(verts[i] for i in f)):
                            raise ValueError(('Sleeve clearance',frame,name,other,ring,f))
                passed.add(key)
    bpy.context.scene.frame_set(1)
    return GAP*1000


if __name__=='__main__':
    # Reverse the comparison: the corresponding old faces must also clear the
    # same margin. Any closer V05 passage then uses identical sleeve surfaces.
    version=Path(bpy.data.filepath).stem.removeprefix('drone-')
    prior={'v06':'v05','v07':'v06'}[version]
    assert Path(bpy.data.filepath).resolve()==ROOT/f'blender/drone-{version}.blend'
    group=bpy.data.collections[version.upper()+' | Aircraft']
    revised={o.name:[v.co.copy() for v in o.data.vertices] for o in group.objects if o.name.startswith('Arm.')}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/drone-{prior}.blend'))
    floor=protected_skin(bpy.data.collections[prior.upper()+' | Aircraft'],revised)
    results={f'{prior}_corresponding_skin_clearance_floor_mm':floor,'frames_checked':121}
    (ROOT/f'measurements/{version}-baseline-clearance.json').write_text(json.dumps(results,indent=2)+'\n')
