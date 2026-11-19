"""Mold the battery hatch reveal and two recessed grilles into the approved housing."""
from collections import defaultdict
from functools import lru_cache
from mathutils.kdtree import KDTree
from math import cos, sin, pi, radians
from mathutils.bvhtree import BVHTree
from pathlib import Path
import sys
import bpy
import bmesh
from mathutils import Vector, geometry

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from rill_shell import stations, U, T, skin
from v12_shell_view import shell_detail_camera

scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v11.blend'
scene.frame_set(1)
group=bpy.data.collections['V11 | Aircraft']
shell=group.objects['Shell.moulded_fuselage']
source=shell.data
points=[v.co*1000 for v in source.vertices]
faces=[tuple(p.vertices) for p in source.polygons]
mats=[p.material_index for p in source.polygons]
materials=list(source.materials)
grille_material=len(materials)
materials.append(bpy.data.materials['Basalt | gimbal carbon casting'])
grille_rays=[]
lookup=KDTree(len(points))
for i,xyz in enumerate(points): lookup.insert(xyz,i)
lookup.balance()
source_faces={frozenset(f):i for i,f in enumerate(faces)}
rows={r[0]:r for r in stations}


@lru_cache(maxsize=None)
def idx(y,u,v):
    _,i,distance=lookup.find(skin(rows[y],u,v))
    assert distance<.001,(y,u,v,distance)
    return i


def vertex(p):
    points.append(Vector(p))
    return len(points)-1


def face(indices,mat):
    faces.append(tuple(indices))
    mats.append(mat)


def bridge(a,b,mat):
    assert len(a)==len(b)
    for j in range(len(a)):
        k=(j+1)%len(a)
        face((a[j],a[k],b[k],b[j]),mat)


def edge(a,b):
    return tuple(sorted((a,b)))


def hatch():
    # Trace one closed boundary in the existing grid, over the crown and back
    # down both sides, then across the lower edge of the rear battery door.
    y0=-59.2
    aft=[r[0] for r in stations if r[0]<=y0]
    t=[v for v in T if v>=.50]
    ring=([idx(y0,u,1) for u in U]+[idx(y0,1,v) for v in t[-2::-1]]
          +[idx(y,1,.50) for y in aft[-2::-1]]+[idx(aft[0],u,.50) for u in U[-2::-1]]
          +[idx(y,-1,.50) for y in aft[1:]]+[idx(y0,-1,v) for v in t[1:-1]])
    edges=defaultdict(list)
    for i,f in enumerate(faces):
        for j,a in enumerate(f): edges[edge(a,f[j-1])].append(i)
    border={edge(a,ring[j-1]) for j,a in enumerate(ring)}
    seed=source_faces[frozenset(idx(y,u,1) for y in aft[-2:] for u in (0,.12))]
    todo=[seed]
    inside={seed}
    while todo:
        f=faces[todo.pop()]
        for j,a in enumerate(f):
            e=edge(a,f[j-1])
            if e in border: continue
            for other in edges[e]:
                if other not in inside:
                    inside.add(other)
                    todo.append(other)
    assert 200<len(inside)<1400,len(inside)
    vectors=[]
    normals=[]
    for j,a in enumerate(ring):
        b=ring[(j+1)%len(ring)]
        k,=set(edges[edge(a,b)])&inside
        along=(points[b]-points[a]).normalized()
        across=source.polygons[k].center*1000-(points[a]+points[b])/2
        vectors.append((across-along*along.dot(across)).normalized())
        normals.append(source.polygons[k].normal.copy())
    last=ring
    # Rounded shoulders flank a recessed shadow line; the rear return widens
    # locally at its midpoint to form a shallow thumb purchase.
    for span,depth,material in ((.075,.018,0),(.15,.105,0),(.205,.30,2),
                                (.31,.33,2),(.39,.12,1),(.47,.025,0),(.56,0,0)):
        new=[]
        for j,a in enumerate(ring):
            miter=(vectors[j-1]+vectors[j])/max(.6,1+vectors[j-1].dot(vectors[j]))
            normal=(normals[j-1]+normals[j]).normalized()
            x,y,z=points[a]
            grip=max(0,1-(abs(x)/9)**2)**2 if y < -69 and z<36 else 0
            p=points[a]+span*(1+2.6*grip)*miter-depth*(1+.65*grip)*normal
            new.append(vertex(p))
        bridge(last,new,material)
        last=new
    remap=dict(zip(ring,last))
    for i in inside:
        faces[i]=tuple(remap.get(a,a) for a in faces[i])
        # The rear cap is a single molded part. Continue its pigment across
        # the former joint and down to the new lower edge of the door.
        if mats[i]!=4: mats[i]=0
    # Remove the painted precursor of the front boundary. Keep the long side
    # joint ahead of the hatch, up to its real intersection with the new cut.
    perimeter=[(u,0) for u in U]+[(1,t) for t in T[1:]]+[(u,1) for u in U[-2::-1]]+[(-1,t) for t in T[-2:0:-1]]
    for i,(u,v) in enumerate(perimeter):
        p,q=perimeter[(i+1)%len(perimeter)]
        if min(v,q)<=.40: continue
        old=source_faces[frozenset((idx(y0,u,v),idx(y0,p,q),idx(-58.7,p,q),idx(-58.7,u,v)))]
        side=abs(p)==abs(u)==1 and p==u
        mats[old]=1 if side and (q+v)/2<.77 else 0
        if side and min(v,q)==.77: mats[old]=2
        if v==q==1 and min(abs(u),abs(p))>=.67: mats[old]=4
    return inside


def rounded_rectangle(width,height,r):
    outline=[]
    for sx,sy,start in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        for j in range(7):
            ang=radians(start+90*j/6)
            outline.append((sx*(width/2-r)+r*cos(ang),sy*(height/2-r)+r*sin(ang)))
    sampled=[]
    for i,a in enumerate(outline):
        b=outline[(i+1)%len(outline)]
        steps=(24 if abs(b[0]-a[0])>3 else 4) if i%7==6 else 1
        sampled.extend((a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps) for j in range(steps))
    return sampled


def triangulate(outline,holes=(),interior=()):
    # Return indexed planar triangles in the outer loop, excluding each bore.
    rings=[outline,*holes]
    xy=[]
    constraints=[]
    for boundary in rings:
        first=len(xy)
        xy.extend(Vector(p) for p in boundary)
        constraints.extend((first+j,first+(j+1)%len(boundary)) for j in range(len(boundary)))
    xy.extend(Vector(p) for p in interior)
    def within(p,ring):
        parity=False
        for j,(x,y) in enumerate(ring):
            a,b=ring[j-1]
            if (y>p.y)!=(b>p.y) and p.x<(a-x)*(p.y-y)/(b-y)+x:
                parity=not parity
        return parity
    vertices,_,triangles,origin,_,_=geometry.delaunay_2d_cdt(xy,constraints,[],0,1e-6)
    assert all(len(o)==1 for o in origin),'Intersecting contours in side grille'
    kept=[]
    for tri in triangles:
        c=sum((vertices[j] for j in tri),Vector((0,0)))/3
        if within(c,outline) and not any(within(c,h) for h in holes):
            kept.append([origin[j][0] for j in tri])
    return kept


def vent(side):
    # An isoparametric patch follows the V11 sidewall and its rear stow relief.
    # Coordinates in the detail chart are millimeters, with V scaled by 36.
    ys=[-55,-49,-43,-37,-29]
    vs=[v for v in T if v>=.785]
    mid_y,mid_t=-43.6,.903
    def to_chart(y,v): return (y-mid_y,36*(v-mid_t))
    def coord(p,depth):
        y=mid_y+p[0]
        v=mid_t+p[1]/36
        i=next((i for i in range(len(ys)-1) if y<=ys[i+1]+1e-6),len(ys)-2)
        j=next((j for j in range(len(vs)-1) if v<=vs[j+1]+1e-6),len(vs)-2)
        a,b=ys[i:i+2]; lo,hi=vs[j:j+2]
        factor=(v-lo)/(hi-lo)
        left=points[idx(a,side,lo)].lerp(points[idx(a,side,hi)],factor)
        right=points[idx(b,side,lo)].lerp(points[idx(b,side,hi)],factor)
        pos=left.lerp(right,(y-a)/(b-a))
        pos.x-=side*depth
        return pos
    grid=([(y,vs[0]) for y in ys]+[(ys[-1],v) for v in vs[1:]]+
          [(y,vs[-1]) for y in ys[-2::-1]]+[(ys[0],v) for v in vs[-2:0:-1]])
    boundary=[to_chart(y,v) for y,v in grid]
    outer=[idx(y,side,v) for y,v in grid]
    for a,b in zip(ys,ys[1:]):
        for low,high in zip(vs,vs[1:]):
            fi=source_faces[frozenset(idx(y,side,v) for y in (a,b) for v in (low,high))]
            faces[fi]=()
    shape=rounded_rectangle(16.8,3.95,1.18)
    mouth=[vertex(coord(p,0)) for p in shape]
    shell_samples=[]
    for offset in range(1,43):
        y=ys[0]+offset*(ys[-1]-ys[0])/43
        for j in range(1,12):
            v=vs[0]+j*(vs[-1]-vs[0])/12
            p=to_chart(y,v)
            if abs(p[0])>8.5 or abs(p[1])>2.08: shell_samples.append(p)
    ids=outer+mouth+[vertex(coord(p,0)) for p in shell_samples]
    for tri in triangulate(boundary,[shape],shell_samples):
        face([ids[i] for i in tri],0)
    last=mouth
    for w,h,r,depth,mat in ((16.58,3.73,1.10,.05,0),(16.32,3.47,.99,.21,1),
                            (16.18,3.33,.93,.56,3)):
        shape=rounded_rectangle(w,h,r)
        new=[vertex(coord(p,depth)) for p in shape]
        bridge(last,new,mat)
        last=new
    # Each individual opening passes through the recessed plate into a common
    # plenum. The closed dark rear wall is visible between the perforations.
    cells=[]
    for row in (-1,0,1):
        for col in range(-7,8):
            cx,cy=(col+.5*(row!=0))*1.20,row*.94
            hole=[(cx+.47*cos(pi/3*j+pi/6),cy+.47*sin(pi/3*j+pi/6)) for j in range(6)]
            if abs(cx)+.48<7.53-(.30 if row!=0 else 0): cells.append(hole)
    front_holes=[[vertex(coord(p,.56)) for p in hole] for hole in cells]
    back_holes=[[vertex(coord(p,.78)) for p in hole] for hole in cells]
    back_rim=[vertex(coord(p,.78)) for p in shape]
    front=last+sum(front_holes,[])
    back=back_rim+sum(back_holes,[])
    for tri in triangulate(shape,cells):
        face([front[i] for i in tri],grille_material)
        face([back[i] for i in tri],3)
    for a,b in zip(front_holes,back_holes): bridge(a,b,3)
    floor=[vertex(coord(p,1.4)) for p in shape]
    bridge(back_rim,floor,3)
    support=[(i*.51,j*.44) for i in range(-14,15) for j in range(-3,4)]
    floor+= [vertex(coord(p,1.4)) for p in support]
    for tri in triangulate(shape,interior=support): face([floor[i] for i in tri],3)
    for hole in cells:
        center=tuple(sum(v[i] for v in hole)/len(hole) for i in (0,1))
        grille_rays.append((side,coord(center,0)*.001))
    print('Open grille perforations',side,len(cells),flush=True)


hatch_faces=hatch()
for s in (-1,1): vent(s)
me=bpy.data.meshes.new('RILL shell · grilles and hatch')
actual=[i for i,f in enumerate(faces) if f]
me.from_pydata([p*.001 for p in points],[],[faces[i] for i in actual])
for m in materials: me.materials.append(m)
for polygon,i in zip(me.polygons,actual):
    polygon.material_index=mats[i]
    polygon.use_smooth=True
bm=bmesh.new()
bm.from_mesh(me)
# Soft transitions across the hatch casting retain the crisp return of the
# narrow channel. Do this only where both faces belong to the molded lid.
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for e in bm.edges:
    if len(e.link_faces)==2:
        e.smooth=e.calc_face_angle(0)<radians(33)
    if len(e.link_faces)==2 and all(actual[f.index] in hatch_faces for f in e.link_faces):
        if e.calc_face_angle(0)<radians(65):
            e.smooth=True
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
errors=[e for e in bm.edges if not e.is_manifold]
assert not errors,('open edges',len(errors),[tuple(v.co[:] for v in e.verts) for e in errors[:3]])
bm.to_mesh(me)
bm.free()
assert not me.validate()
shell.data=me
# The same physical projection and origin as V11 keep the molding grain stable.
uv=me.uv_layers.new(name='Finish UV')
for p in me.polygons:
    axis=max(range(3),key=lambda k:abs(p.normal[k]))
    h,v=((1,2),(2,0),(0,1))[axis]
    sign=1 if p.normal[axis]>=0 else -1
    for loop in p.loop_indices:
        xyz=me.vertices[me.loops[loop].vertex_index].co
        uv.data[loop].uv=(sign*xyz[h]/.0128,xyz[v]/.0128)
me.update()
bpy.context.view_layer.update()
tree=BVHTree.FromObject(shell,bpy.context.evaluated_depsgraph_get())
depths=[]
for side,surface in grille_rays:
    axis=Vector((side,0,0))
    hit,_,_,_=tree.ray_cast(surface+.012*axis,-axis,.02)
    assert hit is not None
    depth=(surface-hit).dot(axis)*1000
    depths.append(depth)
assert min(depths)>1.20 and max(depths)<1.60,(min(depths),max(depths))
print('Baffle depths at all grille centers in mm:',min(depths),max(depths),flush=True)

if '--preview' in sys.argv:
    for label,folded in [('open',False),('folded',True)]:
        shell_detail_camera(scene,folded)
        scene.render.resolution_percentage=64
        scene.cycles.samples=20
        scene.render.filepath=str(root/f'measurements/v12-preview-{label}.png')
        bpy.ops.render.render(write_still=True)
else:
    from check_v09_gear import inspect_gear
    from v10_alignment import alignment
    import json
    report=inspect_gear(group)
    report['after_xz_mm']=alignment(group.objects)
    assert report==json.loads((root/'measurements/v11-export-audit.json').read_text())
    (root/'measurements/v12-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    blend=root/'blender/drone-v12.blend'
    glb=root/'exports/drone-v12.glb'
    assert not blend.exists() and not glb.exists()
    scene.frame_set(1)
    group.name='V12 | Aircraft'
    group.objects['Drone.V11'].name='Drone.V12'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects: obj.select_set(True)
    pending=root/'exports/pending-v12.glb'
    bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
        export_texcoords=True,export_tangents=True,export_image_format='AUTO',
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
