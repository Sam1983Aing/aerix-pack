"""Open V02, shape its arm sleeves and bearings, and verify against the original V01."""
import bpy
import bmesh
import math
import json
import sys
from pathlib import Path
from itertools import combinations
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
V02=ROOT/'blender/drone-v02.blend'
assert Path(bpy.data.filepath).resolve()==V02
CODES=('FR','FL','RR','RL')
PARTS=[f'{kind}.{code}' for code in CODES for kind in ('Arm','Hinge.pin','Hinge.mount')]
PIVOTS=[f'Hinge.axis.{code}' for code in CODES]
MM=.001


def geometry(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    me.calc_loop_triangles()
    verts=[v.co.copy() for v in me.vertices]
    tris=[tuple(t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return verts,tris


def poses(names):
    samples=[]
    for frame in range(1,122):
        bpy.context.scene.frame_set(frame)
        samples.append([bpy.data.objects[n].matrix_world.copy() for n in names])
    bpy.context.scene.frame_set(1)
    return samples


# Preserve the actual approved control solids and transforms before constructing V03.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/drone-v01.blend'))
bpy.context.scene.frame_set(1)
old={name:geometry(bpy.data.objects[name]) for name in PARTS}
v01_matrices=poses(PIVOTS+PARTS)
bpy.ops.wm.open_mainfile(filepath=str(V02))
scene=bpy.context.scene
scene.frame_set(1)
aircraft=bpy.data.collections['V02 | Aircraft']


def finish(name,rgb,metal,rough):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    shader=m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value=m.diffuse_color
    shader.inputs['Metallic'].default_value=metal
    shader.inputs['Roughness'].default_value=rough
    return m


graphite=finish('Basalt | graphite arm sleeve',(.018,.019,.021),.35,.45)
under=finish('Basalt | lower arm facet',(.013,.014,.015),.31,.49)
bearing=finish('Basalt | bearing barrel',(.057,.060,.063),.71,.36)
cap=finish('Basalt | recessed pin face',(.032,.034,.035),.64,.43)
copper=finish('Basalt | copper collar',(.32,.145,.071),.76,.34)
joint=finish('Basalt | hinge reveal',(.006,.0065,.007),.13,.48)
mats=[graphite,under,bearing,cap,copper,joint]
GRAPHITE,UNDER,BEARING,CAP,COPPER,JOINT=range(6)


def replace_loft(obj,rings,side_materials,cap_material=GRAPHITE):
    """Replace only mesh data: object origin, parent transform and animation survive."""
    n=len(rings[0])
    faces=[tuple(range(n-1,-1,-1)),tuple(range((len(rings)-1)*n,len(rings)*n))]
    ids=[cap_material,cap_material]
    for k,row in enumerate(side_materials):
        for j,material in enumerate(row):
            faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
            ids.append(material)
    me=bpy.data.meshes.new(obj.name+' | Basalt')
    me.from_pydata([p for ring in rings for p in ring],[],faces)
    for m in mats: me.materials.append(m)
    for i,(poly,idx) in enumerate(zip(me.polygons,ids)):
        poly.material_index=idx
        poly.use_smooth=i>=2
    bm=bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    assert not me.validate(),obj.name
    me.set_sharp_from_angle(angle=math.radians(28))
    obj.modifiers.clear()
    obj.data=me


def raw_centers(obj,n):
    data=[v.co.copy() for v in obj.data.vertices]
    return [sum(data[k:k+n],Vector())/n for k in range(0,len(data),n)]


def beam_shape(obj, moving):
    # The V01 sleeves use 20 points per cross section. Inherit the interpolated
    # centerline and section limits including the different rear-arm rise.
    points=[v.co.copy() for v in obj.data.vertices]
    centers=raw_centers(obj,20)
    forward=centers[-1]-centers[0]
    forward.z=0
    length=forward.length
    forward.normalize()
    cross=Vector((-forward.y,forward.x,0))
    axis_z=Vector((0,0,1))
    distances=[(p-centers[0]).dot(forward) for p in centers]
    sections=[]
    for i,c in enumerate(centers):
        offsets=[p-c for p in points[i*20:(i+1)*20]]
        sections.append((max(abs(v.dot(cross)) for v in offsets),max(abs(v.z) for v in offsets)))
    def station(t):
        d=t*length
        i=next((k for k in range(len(centers)-1) if d<=distances[k+1]),len(centers)-2)
        w=(d-distances[i])/(distances[i+1]-distances[i])
        return (centers[i].lerp(centers[i+1],w),
                *[(1-w)*sections[i][j]+w*sections[i+1][j] for j in (0,1)])
    # Each station gives axial position, relative width and height, blend from
    # a round root to a shouldered extrusion, and finish on the following strip.
    if moving:
        def at(mm): return mm*MM/length
        layout=[
            (at(.52),.79,.78,0,BEARING),(at(.88),.92,.93,0,BEARING),
            (at(3.59),.94,.95,.13,BEARING),(at(3.75),.88,.88,.13,JOINT),
            (at(3.96),.89,.90,.13,COPPER),(at(4.13),.97,.97,.14,COPPER),
            (at(5.08),.97,.97,.14,COPPER),(at(5.23),.89,.90,.14,JOINT),
            (at(5.49),.88,.89,.15,BEARING),(at(5.69),.94,.94,.20,BEARING),
            (at(7.12),.94,.94,.34,JOINT),(at(7.36),.88,.88,.39,GRAPHITE),
            (.19,.94,.94,.97,GRAPHITE),(.40,.96,.95,1,GRAPHITE),
            (.73,.94,.93,1,GRAPHITE),(.88,.91,.93,.99,GRAPHITE),
            (.95,.91,.90,.72,GRAPHITE),(.985,.86,.85,.5,GRAPHITE)]
    else:
        layout=[(.055,.76,.82,.75,UNDER),(.12,.91,.93,.78,GRAPHITE),
                (.43,.94,.94,.62,GRAPHITE),(.68,.92,.91,.35,BEARING),
                (.87,.89,.88,.13,BEARING),(.95,.75,.77,0,BEARING)]
    rings=[]
    materials=[]
    n=64
    for t,width,height,faceted,metal in layout:
        center,half_w,half_h=station(t)
        ring=[]
        strip=[]
        for i in range(n):
            a=math.tau*i/n
            u,v=math.cos(a),math.sin(a)
            # Intersect each ray with an octagonal cross section. The two
            # shoulder planes read as one long highlight beside the upper flat.
            r=min(1/max(abs(u),1e-9),1/max(abs(v),1e-9),1.47/max(abs(u)+abs(v),1e-9))
            scale=1+faceted*(r-1)
            ring.append(center+cross*(u*half_w*width*scale)+axis_z*(v*half_h*height*scale))
            strip.append(UNDER if metal==GRAPHITE and math.sin(a+math.pi/n)<-.54 else metal)
        rings.append(ring)
        materials.append(strip)
    replace_loft(obj,rings,materials[:-1])


def pin_shape(obj):
    # This basis comes from the original pin mesh. The rear pair has oblique axes.
    a,b=raw_centers(obj,40)
    along=(b-a).normalized()
    u=(obj.data.vertices[0].co-a).normalized()
    v=along.cross(u).normalized()
    span=(b-a).length/MM
    # Recessed concentric end face, outer cap lip and turned barrel. All
    # positions below are relative to the inherited bearing endpoints.
    profile=[(.37,2.45,CAP),(.36,2.56,JOINT),(.23,2.66,JOINT),(.21,2.82,CAP),
             (.21,3.61,BEARING),(.31,3.85,BEARING),(.53,4.10,BEARING),
             (.91,4.12,JOINT),(1.09,3.99,BEARING),(span-1.09,3.99,JOINT),
             (span-.91,4.12,BEARING),(span-.53,4.10,BEARING),(span-.31,3.85,BEARING),
             (span-.21,3.61,CAP),(span-.21,2.82,JOINT),(span-.23,2.66,JOINT),
             (span-.36,2.56,CAP),(span-.37,2.45,CAP)]
    n=64
    rings=[[a+along*(d*MM)+(u*math.cos(math.tau*i/n)+v*math.sin(math.tau*i/n))*(r*MM)
            for i in range(n)] for d,r,_ in profile]
    replace_loft(obj,rings,[[m]*n for _,_,m in profile[:-1]],CAP)


for code in CODES:
    beam_shape(bpy.data.objects['Arm.'+code],True)
    beam_shape(bpy.data.objects['Hinge.mount.'+code],False)
    pin_shape(bpy.data.objects['Hinge.pin.'+code])
scene.frame_set(1)


def surface_check():
    report={}
    for name in PARTS:
        vs,fs=old[name]
        outer=BVHTree.FromPolygons(vs,fs,all_triangles=True)
        new,faces=geometry(bpy.data.objects[name])
        inner=BVHTree.FromPolygons(new,faces,all_triangles=True)
        crossings=outer.overlap(inner)
        if crossings: raise RuntimeError(f'{name}: {len(crossings)} crossings of V01 clearance envelope')
        probes=[*new,*[sum((new[k] for k in f),Vector())/3 for f in faces]]
        inset=float('inf')
        for p in probes:
            q,n,_,dist=outer.find_nearest(p)
            if (p-q).dot(n)>1e-7: raise RuntimeError(name+' extends outside V01')
            inset=min(inset,dist)
        report[name]=round(inset/MM,4)
    return report


def pose_check():
    current=poses(PIVOTS+PARTS)
    error=max(abs(old_mat[r][c]-new_mat[r][c])
              for a,b in zip(v01_matrices,current) for old_mat,new_mat in zip(a,b)
              for r in range(4) for c in range(4))
    assert error<1e-7,error
    return error


def bounds(vs):
    cols=list(zip(*vs))
    return tuple(map(min,cols)),tuple(map(max,cols))


def disjoint(a,b):
    return any(a[1][i]<b[0][i] or b[1][i]<a[0][i] for i in range(3))


def mated(a,b):
    if a.rsplit('.',1)[-1]!=b.rsplit('.',1)[-1]: return False
    return a.startswith(('Arm.','Hinge.')) and b.startswith(('Arm.','Hinge.','Motor.')) or (
        a.startswith('Arm.') and b.startswith('Leg.front.'))


def audit():
    inset=surface_check()
    matrix_error=pose_check()
    meshes={o.name:geometry(o) for o in aircraft.objects if o.type=='MESH'}
    pairs=set()
    for a in PARTS:
        for b in meshes:
            if a==b or mated(a,b): continue
            if a.startswith('Hinge.mount.') and b.startswith('Shell.'): continue
            if a.startswith('Arm.F') and b=='Leg.front.'+a[-1]: continue
            pairs.add(tuple(sorted((a,b))))
    sizes={}
    for frame in range(1,122):
        scene.frame_set(frame)
        verts={}
        boxes={}
        trees={}
        for n,(vs,_) in meshes.items():
            mat=bpy.data.objects[n].matrix_world
            verts[n]=[mat@p for p in vs]
            boxes[n]=bounds(verts[n])
        if frame in (1,121):
            for k,group in [('all',list(meshes)),('airframe',[n for n in meshes if not n.startswith('Propeller.')])]:
                sizes[f'{frame}-{k}']=[round((max(boxes[n][1][i] for n in group)-
                                              min(boxes[n][0][i] for n in group))/MM,3) for i in (1,0,2)]
        for a,b in pairs:
            if disjoint(boxes[a],boxes[b]): continue
            for n in (a,b):
                if n not in trees: trees[n]=BVHTree.FromPolygons(verts[n],meshes[n][1],all_triangles=True)
            if trees[a].overlap(trees[b]): raise RuntimeError(f'Contact: {a} / {b} frame {frame}')
    baseline=json.loads((ROOT/'measurements/v01-audit.json').read_text())['dimensions_mm']
    assert all(vals==baseline[key] for key,vals in sizes.items()),sizes
    scene.frame_set(1)
    return {'sampled_frames':121,'dimensions_mm':sizes,'pivot_and_part_matrix_error':matrix_error,
            'max_v01_envelope_crossings':0,'sampled_surface_inset_mm':inset,
            'non_mating_pairs_per_frame':len(pairs),'unexpected_surface_crossings':0}


report=audit()
print('V03 audit:',json.dumps(report),flush=True)
if '--preview' in sys.argv:
    scene.camera=bpy.data.objects['Studio.camera.three-quarter']
    scene.render.resolution_percentage=60
    scene.render.filepath=str(ROOT/'measurements/v03-arm-preview.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)
if '--check' in sys.argv: sys.exit(0)
blend=ROOT/'blender/drone-v03.blend'
glb=ROOT/'exports/drone-v03.glb'
if blend.exists() or glb.exists(): raise FileExistsError('V03 already published')
bpy.data.objects['Drone.V02'].name='Drone.V03'
aircraft.name='V03 | Aircraft'
bpy.ops.object.select_all(action='DESELECT')
for obj in aircraft.objects: obj.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['Arm.FR']
pending=ROOT/'exports/pending-v03.glb'
bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
    export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
pending.rename(glb)
(ROOT/'measurements/v03-audit.json').write_text(json.dumps(report,indent=2)+'\n')
