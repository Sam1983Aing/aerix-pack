"""Partition the approved triangles and trim their seam returns to a common inner casting."""
from collections import defaultdict
from heapq import heappop, heappush
from math import cos, sin, pi
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from rill_shell import skin, stations, U, T

def tree(mesh):
    mesh.calc_loop_triangles()
    return BVHTree.FromPolygons([v.co.copy() for v in mesh.vertices],
                                [t.vertices[:] for t in mesh.loop_triangles],all_triangles=True)

def partition(mesh):
    bm=bmesh.new(); bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    near=KDTree(len(bm.verts))
    for v in bm.verts: near.insert(v.co,v.index)
    near.balance()
    def flood(seed, blocked):
        found={seed}; queue=[seed]
        while queue:
            for e in queue.pop().edges:
                for f in e.link_faces:
                    if f not in found and not blocked(e,f):
                        queue.append(f); found.add(f)
        return {f.index for f in found}
    faces=list(bm.faces)
    def seed(p):return min(faces,key=lambda f:(f.calc_center_median()-Vector(p)*.001).length_squared)
    door=flood(seed((0,-68,47.9)),lambda e,f:f.material_index==2)
    assert 4000<len(door)<10000,len(door)
    def loop(guide):
        nodes=[near.find(p*.001)[1] for p in guide]
        edges=set()
        for a,b in zip(nodes,nodes[1:]+nodes[:1]):
            if a==b:continue
            start=bm.verts[a].co; direct=bm.verts[b].co-start
            d2=max(direct.length_squared,1e-16)
            dist={a:0}; prev={}; heap=[(0,a)]
            while heap:
                cost,i=heappop(heap)
                if i==b:break
                if cost!=dist[i]:continue
                for e in bm.verts[i].link_edges:
                    other=e.other_vert(bm.verts[i]); j=other.index
                    t=max(0,min(1,(other.co-start).dot(direct)/d2))
                    dev=(other.co-start-t*direct).length
                    nc=cost+e.calc_length()*(1+dev*3500)
                    if nc<dist.get(j,1e8):
                        dist[j]=nc;prev[j]=(i,e.index);heappush(heap,(nc,j))
            i=b
            while i!=a:
                i,k=prev[i];edges.symmetric_difference_update((k,))
        return edges
    # The V12 cosmetic reveal ends above the battery sill. Carry its actual
    # door return below the pack, following the reference rear opening. Keep
    # every existing surface triangle, including the shallow exterior groove.
    tail=[r for r in stations if r[0]<=-64]
    levels=[.22,.22,.30,.50]
    apron=([skin(r,1,t) for r,t in zip(tail,levels)]+
           [skin(tail[-1],1,t) for t in T if t>.50]+[skin(tail[-1],u,1) for u in U[-2::-1]]+
           [skin(tail[-1],-1,t) for t in reversed(T) if .50<=t<1]+
           [skin(r,-1,t) for r,t in reversed(list(zip(tail[:-1],levels[:-1])))]+
           [skin(tail[0],u,.22) for u in U[1:-1]])
    apron_edges=loop(apron)
    door.update(flood(seed((0,-68,47.9)),lambda e,f:e.index in apron_edges))
    front=[r for r in stations if r[0]>=-59.2]
    guide=([skin(r,1,.77) for r in front]+[skin(front[-1],u,.77) for u in U[-2::-1]]
           +[skin(r,-1,.77) for r in front[-2::-1]]+[skin(front[0],-1,v) for v in T if v>.77]
           +[skin(front[0],u,1) for u in U[1:]]+[skin(front[0],1,v) for v in reversed(T) if .77<v<1])
    border=loop(guide)
    roof=flood(seed((0,-10,53.4)),lambda e,f:e.index in border)-door
    bot=[r for r in stations if -64<=r[0]<=9]
    near_us=[u for u in U if abs(u)<=.97]
    guide=([skin(r,.97,0) for r in bot]+[skin(bot[-1],u,0) for u in reversed(near_us[:-1])]
           +[skin(r,-.97,0) for r in bot[-2::-1]]+[skin(bot[0],u,0) for u in near_us[1:-1]])
    border=loop(guide)
    belly=flood(seed((0,-23,10.4)),lambda e,f:e.index in border)
    assert 300<len(roof)<30000 and 180<len(belly)<70000,(len(roof),len(belly))
    assert not (belly & (roof|door))
    allfaces=set(range(len(faces)))
    parts={'Shell.roof_cover':roof,'Shell.battery_door':door,'Shell.belly_cover':belly,
           'Shell.middle_frame':allfaces-roof-door-belly}
    bm.free()
    return parts

def cavity(mesh,collection,mat):
    """Radial sections of the actual skin. Recesses clip the cavity locally."""
    bvh=tree(mesh)
    pts=[]; faces=[]; origins=[]
    # The stepped nose bay needs a high origin so each ray begins inside the canopy.
    table=[(-72.25,33),(-68,32),(-30,33),(12,34),(26,39),(39,44),(60,43),(62.5,43)]
    ys=np.unique(np.r_[np.arange(-72.25,62.51,.8),[y for y,z in table],62.5])
    count=112
    for y in ys:
        z=float(np.interp(y,*zip(*table)));base=Vector((0,y,z))*.001
        for k in range(count):
            phi=k*2*pi/count
            direction=Vector((cos(phi),0,sin(phi)))
            hit,normal,idx,distance=bvh.ray_cast(base,direction,.12)
            assert hit is not None,(y,k)
            # Account for grazing incidence, and reserve extra backing behind the grille.
            allowance=.00078
            if -54<y<-32 and abs(hit.x)>.016 and hit.z>.041:
                allowance=.00115
            shrink=allowance/max(.19,abs(normal.dot(direction)))
            pts.append(base+direction*max(distance-shrink,.0002))
            origins.append(base)
    for r in range(len(ys)-1):
        for i in range(count):
            a=r*count+i;b=r*count+(i+1)%count
            faces.extend([(a,a+count,b+count),(a,b+count,b)])
    faces.extend([tuple(range(count)),tuple(reversed(range(len(pts)-count,len(pts))))])
    # Neighbouring rays can hit opposite sides of a fold or intake. Pull a
    # small neighbourhood inward where a loft triangle would bridge the recess.
    orig=np.array(origins); xyz=np.array(pts)
    ray=xyz-orig; ray/=np.linalg.norm(ray,axis=1)[:,None]
    radius=np.linalg.norm(xyz-orig,axis=1).reshape(-1,count)
    for step in range(48):
        xyz=orig+ray*radius.reshape(-1,1)
        check=BVHTree.FromPolygons(xyz.tolist(),faces)
        crossings=bvh.overlap(check)
        if not crossings:break
        if step==47:raise ValueError(('unresolved inner wall',len(crossings)))
        patch=np.zeros(radius.shape,dtype=float)
        ids={v for _,j in crossings for v in faces[j]}
        patch.flat[list(ids)]=.0008
        for _ in range(3):
            left=np.vstack([patch[:1],patch[:-1]])
            right=np.vstack([patch[1:],patch[-1:]])
            patch=np.maximum.reduce((patch,left*.73,right*.73,np.roll(patch,1,1)*.73,np.roll(patch,-1,1)*.73))
        radius=np.maximum(.00015,radius-patch)
    # Fair the nose cavity over the deep gimbal cheek returns. The conservative
    # neighbourhood gives continuous tool-side radii across occluded ray hits.
    original_radius=radius.copy()
    envelope=radius.copy()
    for _ in range(2):
        envelope=np.minimum.reduce((envelope,np.roll(envelope,1,1),np.roll(envelope,-1,1),
                         np.vstack((envelope[:1],envelope[:-1])),np.vstack((envelope[1:],envelope[-1:]))))
    fair=envelope
    for _ in range(14):
        fair=(4*fair+np.roll(fair,1,1)+np.roll(fair,-1,1)+np.vstack((fair[:1],fair[:-1]))+
              np.vstack((fair[1:],fair[-1:])))/8
    influence=np.clip((ys-15)/8,0,1)[:,None]
    for retreat in range(16):
        radius=original_radius*(1-influence)+(fair-retreat*.00018)*influence
        pts=(orig+ray*np.maximum(radius,.00015).reshape(-1,1)).tolist()
        if not bvh.overlap(BVHTree.FromPolygons(pts,faces)):break
    else:raise ValueError('Nose liner intersects the approved skin')
    m=bpy.data.meshes.new('Temporary inner casting volume');m.from_pydata(pts,[],faces);m.update()
    b=bmesh.new();b.from_mesh(m);bmesh.ops.recalc_face_normals(b,faces=b.faces);b.to_mesh(m);b.free()
    o=bpy.data.objects.new(m.name,m);collection.objects.link(o);m.materials.append(mat)
    return o

def split_shell(shell,coll,mat):
    src=shell.data
    labels=partition(src)
    source_tree=tree(src)
    cut=cavity(src,coll,mat)
    impacts=source_tree.overlap(tree(cut.data))
    if impacts:
        at=np.array([src.loop_triangles[i].center[:] for i,j in impacts])*1000
        print('CAVITY BREAKTHROUGH',len(impacts),at.min(axis=0),at.max(axis=0),at[::max(1,len(at)//8)],flush=True)
    verts=[v.co.copy() for v in src.vertices]
    src.calc_loop_triangles()
    tris=list(src.loop_triangles)
    tris_by_face=defaultdict(list)
    for t in tris:tris_by_face[t.polygon_index].append(t.index)
    uv=src.uv_layers.active
    src_tri_norm=np.asarray([tuple(n.vector) for n in src.corner_normals],dtype='f')
    src_uv=np.asarray([tuple(v.uv) for v in uv.data],dtype='f')
    # Shared apex gives every mating return the same direction.
    apex=Vector((0,-.015,.034))
    proof={}
    for name,group in labels.items():
        tri_ids=[j for i in sorted(group) for j in tris_by_face[i]]
        selected=[tris[j] for j in tri_ids]
        orig=[tuple(t.vertices) for t in selected]
        subset=sorted(set(v for face in orig for v in face)); remap={v:i for i,v in enumerate(subset)}
        coords=[verts[i] for i in subset]; n=len(coords)
        fs=[tuple(remap[i] for i in face) for face in orig]
        # Assemble the uncut outer patch and a small inner copy entirely inside
        # the cavity. Only the seam-return triangles survive its subtraction.
        border={}
        for face in fs:
            for a,b in zip(face,(face[1],face[2],face[0])):
                if (b,a) in border:del border[b,a]
                else:border[a,b]=True
        backing=[tuple(i+n for i in reversed(f)) for f in fs]
        for a,b in border:
            backing.extend([(b,a,a+n),(b,a+n,b+n)])
        m=bpy.data.meshes.new(name+' · approved skin')
        m.from_pydata(coords+[apex+(v-apex)*.09 for v in coords],[],fs+backing)
        for ma in src.materials:m.materials.append(ma)
        m.materials.append(mat); inn=len(m.materials)-1
        m.polygons.foreach_set('material_index',np.r_[[t.material_index for t in selected],np.full(len(backing),inn)].astype('i'))
        m.update()
        o=bpy.data.objects.new(name,m);coll.objects.link(o);o.parent=shell.parent
        mod=o.modifiers.new('Trim to inner casting','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT'
        mod.object=cut;mod.material_mode='TRANSFER'
        dg=bpy.context.evaluated_depsgraph_get()
        result=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
        o.modifiers.clear();o.data=result;bpy.data.meshes.remove(m)
        result.name=name+' · assembled wall'
        # Exact CSG discards collinear triangles introduced by the former
        # subdivision stitching. Restore their edge loops for closed topology.
        repair=bmesh.new();repair.from_mesh(result)
        boundary_points={tuple(v.co):v for e in repair.edges if e.is_boundary for v in e.verts}
        for t in selected:
            if t.area>1.e-13:continue
            vs=[boundary_points.get(tuple(verts[i])) for i in t.vertices]
            if all(v is not None for v in vs) and not repair.faces.get(vs):
                f=repair.faces.new(vs);f.material_index=t.material_index
        if boundary_points:repair.to_mesh(result)
        repair.free();result.update()
        # Match every outer triangle to its approved UVs and normals. An exterior
        # triangle altered by the cavity fails this exact correspondence check.
        outer={tuple(sorted(tuple(verts[v]) for v in tri)):t for tri,t in zip(orig,selected)}
        data_uv=result.uv_layers.new(name=uv.name)
        outuv=np.zeros((len(result.loops),2),dtype='f')
        ns=np.zeros((len(result.loops),3),dtype='f')
        seen=set();extra=0
        for f in result.polygons:
            if result.materials[f.material_index]==mat:
                f.use_smooth=True
                continue
            pos=[tuple(result.vertices[v].co) for v in f.vertices]
            t=outer.get(tuple(sorted(pos)))
            if t is None:
                extra+=1;continue
            seen.add(t.index);f.use_smooth=src.polygons[t.polygon_index].use_smooth
            mapping={tuple(verts[v]):k for v,k in zip(t.vertices,t.loops)}
            for k,p in zip(f.loop_indices,pos):
                ns[k]=src_tri_norm[mapping[p]];outuv[k]=src_uv[mapping[p]]
        print('SPLIT',name,len(tri_ids),len(seen),extra,len(result.polygons),flush=True)
        missing=set(tri_ids)-seen
        if missing:
            print('MISSING',[(i,tris[i].area*1e6) for i in sorted(missing)[:10]],flush=True)
        assert not extra and all(tris[i].area*1e6<1e-7 for i in missing),(name,len(seen),len(tri_ids),extra)
        data_uv.data.foreach_set('uv',outuv.ravel())
        result.set_sharp_from_angle(angle=.58)
        result.normals_split_custom_set(ns.tolist());result.update()
        bm=bmesh.new();bm.from_mesh(result)
        bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
        assert bad==0 and volume>0,(name,bad,volume)
        proof[name]={'outer_triangles_verified':len(seen),'degenerate_source_triangles':len(missing),'max_outer_displacement_mm':0.0,
                     'open_edges':bad,'wall_volume_mm3':round(volume*1e9,2)}
        o['Review source']='Approved exterior triangles, Review 5 casting split'
        o['Inner casting']='Provisional 0.78 mm nominal allowance with local reinforcement and seam returns'
    bpy.data.objects.remove(cut,do_unlink=True)
    bpy.data.objects.remove(shell,do_unlink=True)
    return proof

