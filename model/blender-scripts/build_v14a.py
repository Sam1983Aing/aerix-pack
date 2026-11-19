"""Refine the belly return and camera perimeter on the V14 studio master."""
from pathlib import Path
from math import cos, sin, pi, tau, radians, sqrt
import json
import sys
import bpy
import bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from rill_shell import skin,stations,U,T
from v14a_views import render_details

scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v14.blend'
scene.frame_set(1)
group=bpy.data.collections['V14 | Aircraft']
report={}
changed=('Shell.moulded_fuselage','Camera.face_trim','Camera.lens_barrel','Camera.block')
original={name:group.objects[name].data for name in changed}

def set_mesh(obj,verts,faces,slots,materials,uvs,smooth,sharp=()):
    me=bpy.data.meshes.new(obj.name+' · rolled edges')
    me.from_pydata(verts,[],faces)
    for m in materials: me.materials.append(m)
    texture=me.uv_layers.new(name='Finish UV') if uvs else None
    for f,slot,uv,shading in zip(me.polygons,slots,uvs or [()]*len(faces),smooth):
        f.material_index=slot
        f.use_smooth=shading
        for loop,coord in zip(f.loop_indices,uv):
            texture.data[loop].uv=coord
    for e in me.edges:
        if tuple(sorted(e.vertices)) in sharp: e.use_edge_sharp=True
    assert not me.validate(),obj.name
    me.update()
    bm=bmesh.new()
    bm.from_mesh(me)
    assert all(e.is_manifold and e.is_contiguous for e in bm.edges),obj.name
    bm.free()
    obj.data=me
    bpy.context.view_layer.update()

def curve(points,i,t,reach):
    a,b=points[i:i+2]
    delta=b-a
    length=delta.length
    p=a+t*delta
    k=i if t<=.5 else i+1
    if not 0<k<len(points)-1 or length<1e-8: return p
    before,corner,after=points[k-1:k+2]
    incoming=corner-before
    outgoing=after-corner
    cut=min(reach,.45*incoming.length,.45*outgoing.length)
    relative=(t if k==i else t-1)*length
    if abs(relative)>=cut or cut<=1e-8: return p
    u=(1+relative/cut)*.5
    # A quadratic fillet meets the straight runs tangentially on both ends.
    return corner-(1-u)**2*cut*incoming.normalized()+u*u*cut*outgoing.normalized()

def belly():
    obj=group.objects['Shell.moulded_fuselage']
    me=obj.data
    verts=[v.co.copy() for v in me.vertices]
    # V13 adjusted some sidewall X positions. V12 has the same vertex IDs
    # and the original station coordinates, so it supplies only the lookup.
    with bpy.data.libraries.load(str(root/'blender/drone-v12.blend')) as (src,dst):
        dst.meshes=['RILL shell · grilles and hatch']
    cage=dst.meshes[0]
    assert len(cage.vertices)==len(verts)
    lookup=KDTree(len(verts))
    for v in cage.vertices: lookup.insert(v.co*1000,v.index)
    lookup.balance()
    rim=[(-1,t) for t in reversed(T) if t<=.74]+[(u,0) for u in U[1:]]+[(1,t) for t in T if 0<t<=.74]
    rows=[r for r in stations if -58.7<=r[0]<=64.1]
    ids=[]
    for row in rows:
        indices=[]
        for u,v in rim:
            _,idx,gap=lookup.find(skin(row,u,v))
            assert gap<.001,(u,v,gap)
            indices.append(idx)
        ids.append(indices)
    bpy.data.meshes.remove(cage)
    nr,nc=len(ids),len(rim)
    fs={frozenset(p.vertices):p for p in me.polygons}
    source={}
    for i in range(nr-1):
        for j in range(nc-1):
            corners=(ids[i][j],ids[i+1][j],ids[i+1][j+1],ids[i][j+1])
            poly=fs[frozenset(corners)]
            source[i,j]=(poly.material_index,poly.index)
    removed={f for _,f in source.values()}
    # More samples near the old knuckles retain the flats between small fillets.
    fy=(0,.055,.15,.31,.5,.69,.85,.945)
    fx=(0,.12,.32,.5,.68,.88)
    row_params=[(i,t) for i in range(nr-1) for t in fy]+[(nr-2,1.)]
    col_params=[(j,t) for j in range(nc-1) for t in fx]+[(nc-2,1.)]
    grid=[]
    uvrows=[]
    lines=[[verts[rr[j]] for rr in ids] for j in range(nc)]
    for i,t in row_params:
        ends=i==0 and t==0 or i==nr-2 and t==1
        stripe=[line[i].lerp(line[i+1],t) if j in (0,nc-1) else curve(line,i,t,.0038)
                for j,line in enumerate(lines)]
        gridrow=[]
        coords=[]
        for j,u in col_params:
            pt=stripe[j].lerp(stripe[j+1],u) if ends else curve(stripe,j,u,.00058)
            existing=ids[i+int(t)][j+int(u)] if t in (0.,1.) and u in (0.,1.) else None
            if existing is None:
                existing=len(verts)
                verts.append(pt)
            gridrow.append(existing)
            coords.append(pt)
        grid.append(gridrow)
        # Texture follows the mold around its side and underside at metric scale.
        across=0.
        uvrow=[]
        for j,pt in enumerate(coords):
            if j: across+=(pt-coords[j-1]).length
            uvrow.append((pt.y/.0128,across/.0128))
        uvrows.append(uvrow)
    # The cage points in the interiors may now sit on the fillet instead
    # of the old corner. Commit after the complete tensor patch has been sampled.
    for ii,(i,t) in enumerate(row_params):
        if t not in (0.,1.): continue
        stripe=[line[i].lerp(line[i+1],t) if j in (0,nc-1) else curve(line,i,t,.0038)
                for j,line in enumerate(lines)]
        ends=ii in (0,len(grid)-1)
        for jj,(j,u) in enumerate(col_params):
            if u not in (0.,1.): continue
            verts[grid[ii][jj]]=stripe[j].lerp(stripe[j+1],u) if ends else curve(stripe,j,u,.00058)
    # Stitch the four straight patch boundaries to the original shell. Outer
    # faces retain their materials, UV corners, normals and authored crease flags.
    boundary={}
    def register(chain,n):
        for k in range(0,len(chain)-1,n):
            segment=chain[k:k+n+1]
            boundary[segment[0],segment[-1]]=segment[1:-1]
            boundary[segment[-1],segment[0]]=segment[-2:0:-1]
    register(grid[0],len(fx))
    register(grid[-1],len(fx))
    register([row[0] for row in grid],len(fy))
    register([row[-1] for row in grid],len(fy))
    faces=[]; slots=[]; uv=[]; smooth=[]
    olduv=me.uv_layers.active.data
    for f in me.polygons:
        if f.index in removed: continue
        face=[]; tex=[]
        seq=list(f.vertices)
        for k,a in enumerate(seq):
            b=seq[(k+1)%len(seq)]
            ua=olduv[f.loop_indices[k]].uv
            ub=olduv[f.loop_indices[(k+1)%len(seq)]].uv
            face.append(a); tex.append(tuple(ua))
            for v in boundary.get((a,b),()):
                factor=(verts[v]-verts[a]).length/(verts[b]-verts[a]).length
                face.append(v); tex.append(tuple(ua.lerp(ub,factor)))
        faces.append(face); uv.append(tex); slots.append(f.material_index); smooth.append(f.use_smooth)
    outward=(verts[ids[1][0]]-verts[ids[0][0]]).cross(verts[ids[0][1]]-verts[ids[0][0]])
    reverse=outward.dot(me.polygons[source[0,0][1]].normal)<0
    for i in range(len(grid)-1):
        for j in range(len(col_params)-1):
            sq=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            if reverse: sq.reverse()
            faces.append([grid[r][c] for r,c in sq])
            uv.append([uvrows[r][c] for r,c in sq])
            slots.append(source[row_params[i][0],col_params[j][0]][0])
            smooth.append(True)
    inside={v for row in ids[1:-1] for v in row[1:-1]}
    sharp={tuple(sorted(e.vertices)) for e in me.edges if e.use_edge_sharp and not inside.intersection(e.vertices)}
    set_mesh(obj,verts,faces,slots,list(me.materials),uv,smooth,sharp)

    # Use the smooth casting as a guide for highlights. Fit its geometry to the
    # approved skin with an explicit V14 triangle correspondence. Subdividing
    # both sides of the same diagonal bounds every point of the surface.
    guide=obj.data
    guide_normals=[v.normal.copy() for v in guide.vertices]
    limited=verts[:]
    src_pts=[v.co.copy() for v in me.vertices]
    me.calc_loop_triangles()
    triangulation={}
    for tri in me.loop_triangles:
        triangulation.setdefault(tri.polygon_index,[]).append(tuple(tri.vertices))
    def limit(base,desired):
        delta=desired-base
        return base+delta.normalized()*min(delta.length,.000045)
    out_faces=[]; out_uv=[]; out_slots=[]; out_smooth=[]; custom=[]
    def emit(f,tex,slot,shading,custom_normals):
        out_faces.append(f); out_uv.append(tex); out_slots.append(slot)
        out_smooth.append(shading); custom.extend(custom_normals)
    for f in me.polygons:
        if f.index in removed: continue
        tex_by_index={v:olduv[l].uv.copy() for v,l in zip(f.vertices,f.loop_indices)}
        border=any((a,b) in boundary for a,b in f.edge_keys)
        for seq in triangulation[f.index] if border else [tuple(f.vertices)]:
            final=[]; tex=[]
            for k,a in enumerate(seq):
                b=seq[(k+1)%len(seq)]
                final.append(a); tex.append(tex_by_index[a])
                for v in boundary.get((a,b),()):
                    fpos=(limited[v]-src_pts[a]).length/(src_pts[b]-src_pts[a]).length
                    final.append(v); tex.append(tex_by_index[a].lerp(tex_by_index[b],fpos))
            emit(final,tex,f.material_index,f.use_smooth,[(0,0,0)]*len(final))
    intersections={}
    for ri,(i,t0) in enumerate(row_params[:-1]):
        t1=row_params[ri+1][1] if row_params[ri+1][0]==i else 1.
        for ci,(j,u0) in enumerate(col_params[:-1]):
            u1=col_params[ci+1][1] if col_params[ci+1][0]==j else 1.
            slot,old=source[i,j]
            a,b,c,d=(ids[i][j],ids[i+1][j],ids[i+1][j+1],ids[i][j+1])
            diag_ac=all(a in tri and c in tri for tri in triangulation[old])
            def side(t,u): return t-u if diag_ac else t+u-1
            def original_point(t,u):
                if diag_ac:
                    coeff=(1-max(t,u),max(0,t-u),min(t,u),max(0,u-t))
                else:
                    w=max(0,t+u-1)
                    coeff=(1-t-u+w,t-w,w,u-w)
                return sum((src_pts[k]*weight for k,weight in zip((a,b,c,d),coeff)),Vector())
            corners=[(ri,ci,t0,u0),(ri+1,ci,t1,u0),(ri+1,ci+1,t1,u1),(ri,ci+1,t0,u1)]
            quad=[]
            for r,q,t,u in corners:
                index=grid[r][q]
                limited[index]=limit(original_point(t,u),verts[index])
                quad.append((index,t,u,Vector(uvrows[r][q])))
            signs=[side(t,u) for _,t,u,_ in quad]
            parts=[quad]
            if min(signs)<-1e-8 and max(signs)>1e-8:
                parts=[[],[]]
                for k,(a0,t,u,tex) in enumerate(quad):
                    a1,tb,ub,txb=quad[(k+1)%4]
                    val,nxt=signs[k],signs[(k+1)%4]
                    if val<1e-8: parts[0].append(quad[k])
                    if val>-1e-8: parts[1].append(quad[k])
                    if val*nxt < -1e-14:
                        f=val/(val-nxt); tt=t+f*(tb-t); uu=u+f*(ub-u)
                        key=(old,round(tt,9),round(uu,9))
                        if key not in intersections:
                            intersections[key]=len(limited)
                            limited.append(limit(original_point(tt,uu),verts[a0].lerp(verts[a1],f)))
                            guide_normals.append(guide_normals[a0].lerp(guide_normals[a1],f).normalized())
                        entry=(intersections[key],tt,uu,tex.lerp(txb,f))
                        parts[0].append(entry); parts[1].append(entry)
            for poly in parts:
                if reverse: poly=poly[::-1]
                vertices=[p[0] for p in poly]
                emit(vertices,[p[3] for p in poly],slot,True,[guide_normals[k] for k in vertices])
    set_mesh(obj,limited,out_faces,out_slots,list(me.materials),out_uv,out_smooth,sharp)
    obj.data.normals_split_custom_set(custom)
    bpy.data.meshes.remove(guide)

def trim():
    obj=group.objects['Camera.face_trim']
    me=obj.data
    # V08 used five chords per quarter. Use exact rounded rectangles between
    # the same straight tangents and carry a small shoulder around the lip.
    shapes=[(59.04,20.90,12.40,2.45),(59.16,20.84,12.34,2.445),
            (59.195,20.80,12.30,2.442),(59.211,20.76,12.26,2.43),
            (59.245,20.19,11.74,2.205),(59.249,20.15,11.70,2.19),
            (59.244,20.12,11.67,2.176),(59.227,20.10,11.64,2.17),
            (59.04,20.06,11.59,2.16)]
    # Recover the authored coordinate mapping from corresponding tangent points.
    base=Vector(me.vertices[0].co)
    xmax=20.90/2; z0=12.4/2-2.45
    unitx=(me.vertices[5].co.x-me.vertices[6].co.x)/(20.9-2*2.45)
    unitz=(me.vertices[0].co.z-me.vertices[23].co.z)/(2*z0)
    unity=(me.vertices[24].co.y-base.y)/(.17)
    verts=[]; faces=[]; slots=[]; uvs=[]
    n=25
    for y,w,h,r in shapes:
        for sx,sz,start in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
            for j in range(n):
                a=radians(start+90*j/(n-1))
                x=sx*(w/2-r)+r*cos(a)
                z=sz*(h/2-r)+r*sin(a)
                verts.append(base+Vector(((x-xmax)*unitx,(y-59.04)*unity,(z-z0)*unitz)))
    count=4*n
    for i in range(len(shapes)):
        for j in range(count):
            k=(j+1)%count
            b=(i+1)%len(shapes)
            f=[i*count+j,i*count+k,b*count+k,b*count+j]
            # The parameter loops run counterclockwise in X,Z.
            norm=(verts[f[1]]-verts[f[0]]).cross(verts[f[2]]-verts[f[0]])
            if i==0 and j==0: flip=norm.x<0
            if flip: f.reverse()
            faces.append(f); slots.append(1 if 2<=i<=5 else 0)
            uvs.append([(verts[p].x/.0128,verts[p].z/.0128) for p in f])
    # Interpolate each original five-chord quarter for a limiting reference.
    for i,shape in enumerate(shapes):
        blend=(0,.70,.91,1,.90,1,.12,.23,1)[i]
        for j in range(count):
            corner,h=divmod(j,n)
            at=h*5/(n-1); idx=min(4,int(at)); frac=at-idx
            def prior(r):
                a=me.vertices[r*24+corner*6+idx].co
                b=me.vertices[r*24+corner*6+idx+1].co
                return a.lerp(b,frac)
            lo=(0,0,0,0,1,1,2,2,2)[i]
            basepoint=prior(lo).lerp(prior(min(3,lo+1)),blend)
            delta=verts[i*count+j]-basepoint
            verts[i*count+j]=basepoint+delta.normalized()*min(delta.length,.000029)
    set_mesh(obj,verts,faces,slots,list(me.materials),uvs,[True]*len(faces))

def refine_camera_ring(name,steps,closed):
    obj=group.objects[name]
    me=obj.data
    n=96
    count=len(me.vertices)//n
    assert len(me.vertices)==count*n
    c=n*steps
    source=[list(me.vertices)[i*n:(i+1)*n] for i in range(count)]
    sections=[(14.95,12.40,2.18),(16.25,13.78,2.38),(17.10,14.48,2.48),
              (17.34,14.58,2.36),(17.34,14.58,2.32),(17.12,14.40,2.29),
              (16.70,13.99,2.16),(16.41,13.71,2.04)]
    pts=[]; faces=[]; slots=[]; uvs=[]; smooth=[]; sharp=set()
    for i,row in enumerate(source):
        center=(row[0].co+row[n//2].co)*.5
        xrad=row[0].co.x-center.x
        zrad=row[n//4].co.z-center.z
        for j in range(c):
            x,z=cos(tau*j/c),sin(tau*j/c)
            if not closed and i<len(sections):
                w,h,r=sections[i]
                a,b=abs(x),abs(z)
                radius=min(w*.5/max(a,1e-10),h*.5/max(b,1e-10))
                cx,cz=w*.5-r,h*.5-r
                if a*radius>cx and b*radius>cz:
                    dot=a*cx+b*cz
                    radius=dot+sqrt(max(0,dot*dot-cx*cx-cz*cz+r*r))
                x*=2*radius/w
                z*=2*radius/h
            pt=center+Vector((x*xrad,0,z*zrad))
            if j%steps==0: assert (pt-row[j//steps].co).length<1e-7,(name,i,j)
            lo,frac=divmod(j,steps)
            basepoint=row[lo].co.lerp(row[(lo+1)%n].co,frac/steps)
            delta=pt-basepoint
            pts.append(basepoint+delta.normalized()*min(delta.length,.000029))
    me.calc_loop_triangles()
    corner_normals=[]
    original_tris={}
    for tri in me.loop_triangles:
        original_tris.setdefault(tri.polygon_index,[]).append(set(tri.vertices))
    for f in me.polygons:
        old=list(f.vertices)
        normals={v:me.corner_normals[l].vector.copy() for v,l in zip(old,f.loop_indices)}
        olduv={v:me.uv_layers.active.data[l].uv.copy() for v,l in zip(old,f.loop_indices)} if me.uv_layers.active else {}
        if len(old)>4:
            base=min(old)//n*c
            face=[base+j for j in range(c)]
            if (old[1]-old[0])%n!=1: face.reverse()
            faces.append(face); smooth.append(f.use_smooth); slots.append(f.material_index)
            for at in face:
                j,sub=divmod(at-base,steps)
                corner_normals.append(normals[base//steps+j].lerp(normals[base//steps+(j+1)%n],sub/steps).normalized())
            if olduv:
                uv=[]
                for at in face:
                    j,sub=divmod(at-base,steps)
                    uv.append(olduv[base//steps+j].lerp(olduv[base//steps+(j+1)%n],sub/steps))
                uvs.append(uv)
            continue
        # Start at one of the two azimuthal edges, following the old winding.
        which=next(k for k in range(4) if old[k]//n==old[(k+1)%4]//n)
        a,b,d,e=(old[(which+k)%4] for k in range(4))
        direction=1 if (b-a)%n==1 else -1
        forward=all(a in tri and d in tri for tri in original_tris[f.index])
        spine=[]; spine_uv=[]
        for sub in range(steps+1):
            t=sub/steps
            j=((a%n)*steps+direction*sub)%c
            top=a//n*c+j; bottom=e//n*c+j
            fraction=t if forward else 1-t
            if sub in (0,steps):
                index=top if fraction==0 else bottom
            else:
                idx1,idx2=(a,d) if forward else (e,b)
                base=me.vertices[idx1].co.lerp(me.vertices[idx2].co,t)
                delta=pts[top].lerp(pts[bottom],fraction)-base
                index=len(pts)
                pts.append(base+delta.normalized()*min(delta.length,.000029))
            spine.append(index)
            if olduv: spine_uv.append(olduv[a if forward else e].lerp(olduv[d if forward else b],t))
        for sub in range(steps):
            lo,hi=sub/steps,(sub+1)/steps
            jl=((a%n)*steps+direction*sub)%c
            jr=(jl+direction)%c
            top_l,top_r=a//n*c+jl,a//n*c+jr
            bot_l,bot_r=e//n*c+jl,e//n*c+jr
            mid_l,mid_r=spine[sub:sub+2]
            n1,n2=(normals[a],normals[d]) if forward else (normals[e],normals[b])
            n_for={top_l:normals[a].lerp(normals[b],lo),top_r:normals[a].lerp(normals[b],hi),
                   bot_l:normals[e].lerp(normals[d],lo),bot_r:normals[e].lerp(normals[d],hi),
                   mid_l:n1.lerp(n2,lo),mid_r:n1.lerp(n2,hi)}
            uv_for={}
            if olduv:
                uv_for={top_l:olduv[a].lerp(olduv[b],lo),top_r:olduv[a].lerp(olduv[b],hi),
                        bot_l:olduv[e].lerp(olduv[d],lo),bot_r:olduv[e].lerp(olduv[d],hi),
                        mid_l:spine_uv[sub],mid_r:spine_uv[sub+1]}
            for seq in ((top_l,top_r,mid_r,mid_l),(mid_l,mid_r,bot_r,bot_l)):
                face=list(dict.fromkeys(seq))
                faces.append(face); smooth.append(f.use_smooth); slots.append(f.material_index)
                corner_normals.extend(n_for[v].normalized() for v in face)
                if olduv: uvs.append([uv_for[v] for v in face])
    for edge in me.edges:
        if not edge.use_edge_sharp: continue
        a,b=edge.vertices
        ai,aj=divmod(a,n); bi,bj=divmod(b,n)
        if ai==bi:
            start=aj if (aj+1)%n==bj else bj
            for k in range(steps):
                sharp.add(tuple(sorted((ai*c+(start*steps+k)%c,ai*c+(start*steps+k+1)%c))))
        else:
            sharp.add(tuple(sorted((steps*a,steps*b))))
    set_mesh(obj,pts,faces,slots,list(me.materials),uvs,smooth,sharp)
    obj.data.normals_split_custom_set(corner_normals)

belly()
trim()
refine_camera_ring('Camera.lens_barrel',2,True)
refine_camera_ring('Camera.block',4,False)
def sample_surface(me,matrix):
    me.calc_loop_triangles()
    vertices=[matrix@v.co for v in me.vertices]
    triangles=[tuple(t.vertices) for t in me.loop_triangles]
    return vertices,triangles,BVHTree.FromPolygons(vertices,triangles,all_triangles=True)

def deviation(source,target):
    vs,triangles,_=source
    tree=target[2]
    highest=0.
    where=None
    for tri in triangles:
        a,b,c=(vs[j] for j in tri)
        for p in (a,(a+b)*.5,(b+c)*.5,(a+c)*.5,(a+b+c)/3):
            distance=tree.find_nearest(p)[3]
            if distance>highest:
                highest=distance
                where=p
    return {'max_sample_mm':round(highest*1000,4),'at_mm':[round(v*1000,2) for v in where]}

if '--distance' in sys.argv or '--publish' in sys.argv:
    distances={}
    for name in changed:
        o=group.objects[name]
        a,b=[sample_surface(m,o.matrix_world) for m in (original[name],o.data)]
        distances[name]=[deviation(a,b),deviation(b,a)]
    assert max(row['max_sample_mm'] for pair in distances.values() for row in pair)<.05,distances
    report['surface_samples_v14_to_revision_and_reverse']=distances
    print('Exterior distance samples',json.dumps(distances),flush=True)
if '--preview' in sys.argv:
    render_details(root/'measurements','v14a-proof',True)
elif '--publish' in sys.argv or '--check' in sys.argv:
    from check_v13_joints import check_joints
    from check_v09_gear import inspect_gear
    from v10_alignment import alignment
    report.update(check_joints(group))
    report['fold']=inspect_gear(group)
    report['optical_center_xz_mm']=alignment(group.objects)
    assert all(max(map(abs,v))<.001 for v in report['optical_center_xz_mm'].values())
    print('Native fold and optical audit',json.dumps(report),flush=True)
    if '--check' in sys.argv: sys.exit(0)
    blend=root/'blender/drone-v14a.blend'
    glb=root/'exports/drone-v14a.glb'
    assert not blend.exists() and not glb.exists()
    group.name='V14a | Aircraft'
    group.objects['Drone.V14'].name='Drone.V14a'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects: obj.select_set(True)
    tmp=root/'exports/pending-v14a.glb'
    bpy.ops.export_scene.gltf(filepath=str(tmp),use_selection=True,export_apply=True,export_texcoords=True,
        export_tangents=True,export_image_format='AUTO',export_animation_mode='NLA_TRACKS',export_animations=True,
        export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    tmp.rename(glb)
    (root/'measurements/v14a-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
