"""Inspect the actual evaluated solids, independent of the Blender parenting hierarchy."""
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import json
import sys
import bpy
from mathutils.bvhtree import BVHTree
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]


class Solid:
    def __init__(self, vertices, faces):
        self.vertices=vertices
        self.faces=faces
        axes=list(zip(*vertices))
        self.lo=list(map(min,axes))
        self.hi=list(map(max,axes))
        self._tree=None

    @property
    def tree(self):
        if self._tree is None:
            self._tree=BVHTree.FromPolygons(self.vertices,self.faces,all_triangles=True)
        return self._tree

    def gap_box(self, other):
        return max(max(self.lo[i]-other.hi[i],other.lo[i]-self.hi[i]) for i in range(3))

    def contacts(self, other):
        if self.gap_box(other)>1e-8: return False
        if self.tree.overlap(other.tree): return True
        for a,b in ((self,other),(other,self)):
            if all(b.lo[i]-1e-8<=a.lo[i] and a.hi[i]<=b.hi[i]+1e-8 for i in range(3)):
                p=a.vertices[0]
                q,n,_,dist=b.tree.find_nearest(p)
                if dist<1e-8: return True
                if (p-q).dot(n)<0:
                    # At a concave crease either adjacent triangle can be the
                    # nearest. Its individual normal does not prove containment.
                    votes=0
                    for direction in ((1,.123,.245),(-.2,.1,-1),(-1,-.42,.3)):
                        ray=Vector(direction).normalized()
                        start=p
                        crossings=0
                        while True:
                            hit=b.tree.ray_cast(start,ray)[0]
                            if hit is None: break
                            start=hit+ray*1.e-7
                            crossings+=1
                        votes+=crossings%2
                    if votes>=2: return True
        return False


def local_meshes(group):
    out={}
    for obj in group.objects:
        if obj.type!='MESH': continue
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        mesh.calc_loop_triangles()
        out[obj.name]=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles])
        ev.to_mesh_clear()
    return out


def world_solids(meshes,cache):
    solids={}
    for name,(vs,fs) in meshes.items():
        mat=bpy.data.objects[name].matrix_world
        key=tuple(x for row in mat for x in row)
        if name not in cache or cache[name][0]!=key:
            cache[name]=(key,Solid([mat@v for v in vs],fs))
        solids[name]=cache[name][1]
    return solids


def physical_groups(names,pairs):
    graph=defaultdict(set)
    for a,b in pairs:
        graph[a].add(b)
        graph[b].add(a)
    remaining=set(names)
    groups=[]
    while remaining:
        wave={min(remaining)}
        reached=set()
        while wave:
            reached.update(wave)
            wave=set().union(*(graph[n] for n in wave))-reached
        remaining-=reached
        groups.append(sorted(reached))
    return sorted(groups,key=len,reverse=True)


def audit(group,frames):
    meshes=local_meshes(group)
    cache={}
    all_pairs=list(combinations(sorted(meshes),2))
    result=[]
    tested={}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        solids=world_solids(meshes,cache)
        contacts=[]
        for pair in all_pairs:
            a,b=(solids[n] for n in pair)
            if a.gap_box(b)>1e-8: continue
            previous=tested.get(pair)
            if previous is None or previous[0] is not a or previous[1] is not b:
                tested[pair]=(a,b,a.contacts(b))
            if tested[pair][2]: contacts.append(pair)
        row={'frame':frame,'contacts':contacts,'groups':physical_groups(meshes,contacts)}
        if frame in (1,121):
            row['size_mm']=[round(1000*(max(s.hi[i] for s in solids.values())-min(s.lo[i] for s in solids.values())),3) for i in (1,0,2)]
        result.append(row)
    bpy.context.scene.frame_set(1)
    return result


def widths(group):
    shells={n:m for n,m in local_meshes(group).items() if n.startswith('Shell.') or n=='Body.shell'}
    solids=world_solids(shells,{})
    result={}
    for y in [-60,-42,-12,10,38,53]:
        # Actual triangle intersections with this transverse station.
        xx=[]
        plane=y*.001
        for s in solids.values():
            for tri in s.faces:
                for ai,bi in ((0,1),(1,2),(2,0)):
                    a,b=s.vertices[tri[ai]],s.vertices[tri[bi]]
                    if min(a.y,b.y)<=plane<max(a.y,b.y):
                        xx.append(a.x+(b.x-a.x)*(plane-a.y)/(b.y-a.y))
        result[str(y)]=round(1000*(max(xx)-min(xx)),3)
    return result


def check_export():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/drone-v04.glb'))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    # The imported nodes have no dependency on the original Blender collection.
    class Imported:
        objects=meshes
    rows=audit(Imported,range(1,122))
    assert all(len(row['groups'])==1 for row in rows)
    native=json.loads((ROOT/'measurements/v04-audit.json').read_text())
    assert len(meshes)==native['mesh_count']
    for row,key in ((rows[0],'open_mm'),(rows[-1],'folded_mm')):
        assert max(abs(a-b) for a,b in zip(row['size_mm'],native[key]))<.0011
    output={'frames':len(rows),'meshes':len(meshes),'physical_groups_per_frame':[len(row['groups']) for row in rows],
            'open_mm':rows[0]['size_mm'],'folded_mm':rows[-1]['size_mm']}
    (ROOT/'measurements/v04-export-assembly.json').write_text(json.dumps(output,indent=2)+'\n')


if __name__=='__main__' and '--export' in sys.argv:
    check_export()
elif __name__=='__main__':
    for version in ('v01','v03'):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/drone-{version}.blend'))
        coll=bpy.data.collections[version.upper()+' | Aircraft']
        bpy.context.scene.frame_set(1)
        print('WIDTH',version,widths(coll),flush=True)
        if version=='v03':
            report=audit(coll,[1,47,84,121])
            for row in report:
                print('GROUPS',row['frame'],row['groups'],flush=True)
            (ROOT/'measurements/v03-attachment-baseline.json').write_text(json.dumps(report,indent=2))
