"""Run on blender/drone-v01.blend. -- --preview writes two draft PNGs only."""
from pathlib import Path
from math import sin, cos, radians
from bisect import bisect_right
import sys
import json
import hashlib
import struct
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve() == ROOT/'blender/drone-v01.blend'
scene = bpy.context.scene
scene.frame_set(1)
aircraft = bpy.data.collections['V01 | Aircraft']
root = bpy.data.objects['Drone.V01']
source_body = bpy.data.objects['Body.shell']
retained = [o for o in aircraft.objects if o != source_body]
panels = []
MM = .001


def motion_digest(objects):
    digest = hashlib.sha256()
    for frame in range(1,122):
        scene.frame_set(frame)
        for obj in objects:
            digest.update(struct.pack('<16f', *(v for row in obj.matrix_world for v in row)))
    scene.frame_set(1)
    return digest.hexdigest()


def material(name, rgb, metallic, rough):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1)
    mat.use_nodes=True
    bs=mat.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=mat.diffuse_color
    bs.inputs['Metallic'].default_value=metallic
    bs.inputs['Roughness'].default_value=rough
    return mat


base_motion = motion_digest(retained)
deck = material('Basalt | charcoal magnesium',(.023,.024,.026),.42,.52)
lower = material('Basalt | lower casting',(.018,.019,.020),.29,.46)
faceplate = material('Basalt | nose insert',(.016,.0165,.018),.20,.42)
seal = material('Basalt | recessed joint',(.004,.0045,.005),.06,.61)
hardware = material('Study | graphite',(.018,.019,.020),.28,.46)
silver = material('Study | titanium',(.35,.36,.37),.72,.34)
white = material('Study | satin white',(.74,.74,.73),.12,.43)
copper = material('Study | muted copper',(.21,.095,.05),.72,.40)

# Longitudinal dimensions in mm from the approved V01 hull stations.
# Monotone cubic tangents hold the extrema at the measured stations.
stations=[(-73.5,32,18,43),(-69,35,14,47),(-45,34,14,50),(-19,35,17,52),
          (13,40,20,53),(39,46,27,56),(52,43,33,53.5),(62,37,35,49),(64.5,30,36,46)]
ys=[r[0] for r in stations]


def interpolate(y,col):
    i=min(max(bisect_right(ys,y)-1,0),len(ys)-2)
    def secant(k):
        return (stations[k+1][col]-stations[k][col])/(ys[k+1]-ys[k])
    def tangent(k):
        if k==0: return secant(0)
        if k==len(ys)-1: return secant(k-1)
        a,b=secant(k-1),secant(k)
        return 2*a*b/(a+b) if a*b>0 else 0.
    h=ys[i+1]-ys[i]
    t=(y-ys[i])/h
    return ((2*t**3-3*t*t+1)*stations[i][col]+(t**3-2*t*t+t)*h*tangent(i)
            +(-2*t**3+3*t*t)*stations[i+1][col]+(t**3-t*t)*h*tangent(i+1))


def profile(y, kind):
    w,lo,hi=(interpolate(y,i) for i in (1,2,3))
    # The approved nose panel has a distinct plane break at the forward shoulder.
    if y>=35:
        hi=56-(y-35)*10/29.5
    elif y>13:
        hi=min(56,53+(y-13)*3/18)
    half=w/2
    seam_z=lo+min(5.1,(hi-lo)*.16)
    crest=hi-seam_z
    # Starting at the lower right, climb the wall, shoulder and broad crown.
    if kind=='upper':
        right=[(half-.45,seam_z+.24),(half-.18,seam_z+1.05),
               (half-.08,seam_z+crest*.64),(half-.28,seam_z+crest*.73),
               (half-2.7,hi-2.1),(half-3.6,hi-.94),(half-4.8,hi-.43),
               (half*.36,hi-.11)]
        return right+[(0,hi)]+[(-x,z) for x,z in reversed(right)]
    if kind=='lower':
        right=[(half-.58,seam_z-.24),(half-.67,seam_z-1.0),
               (half-1.35,lo+1.55),(half-3.2,lo+.32),(half-4.5,lo)]
        return right+[(0,lo)]+[(-x,z) for x,z in reversed(right)]
    return [(half-1.10,seam_z-.235),(half-1.10,seam_z+.235),
            (-half+1.10,seam_z+.235),(-half+1.10,seam_z-.235)]


def solid(name, rings, mat):
    count=len(rings[0])
    vertices=[tuple(v*MM for v in point) for ring in rings for point in ring]
    faces=[tuple(reversed(range(count))),tuple(range(len(vertices)-count,len(vertices)))]
    faces.extend((k*count+j,k*count+(j+1)%count,(k+1)*count+(j+1)%count,(k+1)*count+j)
                 for k in range(len(rings)-1) for j in range(count))
    me=bpy.data.meshes.new(name)
    me.from_pydata(vertices,[],faces)
    me.update()
    bm=bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    obj=bpy.data.objects.new(name,me)
    aircraft.objects.link(obj)
    obj.parent=root
    obj.data.materials.append(mat)
    return obj


def panel(name,kind,start,end,mat,recess=False):
    count=len(profile(0,kind))
    steps=max(2,int(max(end(j)-start(j) for j in range(count))/2.4)+1)
    rings=[]
    for i in range(steps+1):
        row=[]
        for j in range(count):
            y=start(j)+(end(j)-start(j))*i/steps
            x,z=profile(y,kind)[j]
            if recess:
                # Pull the gasket face below the lip while keeping its lower face seated.
                x*=.967
                z-=.45*min(1,min(j,count-1-j)/3)
            row.append((x,y,z))
        rings.append(row)
    obj=solid(name,rings,mat)
    panels.append(obj)
    return obj


def constant(y): return lambda j:y


def hood_edge(j):
    # Inclined line at the side. Across the broad roof it becomes transverse.
    wall_to_deck=[18.4,18.6,27.0,28.4,31.6,33.0,34.0,34.0,34.0]
    return wall_to_deck[min(j,16-j)]


panel('Shell.waist_gasket','waist',constant(-73.49),constant(64.45),seal)
chassis=panel('Shell.lower_chassis','lower',constant(-73.5),constant(64.5),lower)
tail=panel('Shell.tail_return','upper',constant(-73.5),constant(-69.65),deck)
panel('Shell.tail_gasket','upper',constant(-69.63),constant(-69.23),seal,True)
main=panel('Shell.upper_deck','upper',constant(-69.21),lambda j:hood_edge(j)-.26,deck)
panel('Shell.nose_gasket','upper',lambda j:hood_edge(j)-.245,lambda j:hood_edge(j)+.245,seal,True)
hood=panel('Shell.nose_hood','upper',lambda j:hood_edge(j)+.26,constant(64.5),deck)


def rounded_plug(name,y0,y1,w,h,z,r,mat):
    outline=[]
    for sx,sz,a in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        for i in range(9):
            angle=radians(a+i*90/8)
            outline.append((sx*(w/2-r)+r*cos(angle),z+sz*(h/2-r)+r*sin(angle)))
    return solid(name,[[(x,y,hz) for x,hz in outline] for y in (y0,y1)],mat)


def apply(obj,modifier):
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def cut(obj,cutter):
    mod=obj.modifiers.new('Service opening','BOOLEAN')
    mod.operation='DIFFERENCE'
    mod.solver='EXACT'
    mod.object=cutter
    apply(obj,mod)


socket=rounded_plug('Tool.aft_socket',-78,-25.5,26.8,18.5,30.5,2.5,seal)
for obj in [p for p in panels if min(v.co.y for v in p.data.vertices)<-.0255]:
    cut(obj,socket)
bpy.data.objects.remove(socket,do_unlink=True)
# A shallow pocket clears the lateral yoke ears below the yaw mounting land.
pocket=rounded_plug('Tool.yoke_clearance',38.8,56.4,25.8,15.0,22.3,1.8,seal)
cut(chassis,pocket)
bpy.data.objects.remove(pocket,do_unlink=True)
nose_tool=rounded_plug('Tool.nose_pocket',63,68,25.9,8.2,41.1,2.95,seal)
for obj in (hood,chassis,panels[0]): cut(obj,nose_tool)
bpy.data.objects.remove(nose_tool,do_unlink=True)
insert=rounded_plug('Shell.nose_face',63.06,64.28,25.35,7.65,41.1,2.65,faceplate)
panels.append(insert)
for obj in panels:
    # Smooth the continuous loft surfaces; split the intentional shoulder breaks.
    me=obj.data
    me.validate()  # Normalize boolean mesh layers before auditing or exporting.
    for face in me.polygons: face.use_smooth=True
    me.set_sharp_from_angle(angle=radians(24))
    if 'gasket' not in obj.name:
        mod=obj.modifiers.new('Machined edge radii','BEVEL')
        mod.width=.00024
        mod.segments=3
        mod.angle_limit=radians(22)
        mod.harden_normals=True
    n=obj.modifiers.new('Panel normals','WEIGHTED_NORMAL')
    n.keep_sharp=True
    n.weight=45

bpy.data.objects.remove(source_body,do_unlink=True)
for obj in retained:
    if obj.type!='MESH': continue
    mat=hardware
    if obj.name.startswith('Propeller.blade.'): mat=white
    elif obj.name.startswith('Propeller.cap.'): mat=silver
    elif obj.name.startswith('Hinge.pin.'): mat=copper
    elif obj.name.startswith('Battery.'): mat=lower
    obj.data.materials[0]=mat
root.name='Drone.V02'
aircraft.name='V02 | Aircraft'
scene.cycles.samples=18


def inspect_view(label,output,scale=100):
    scene.camera=bpy.data.objects['Studio.camera.'+label]
    scene.render.resolution_percentage=scale
    scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)


if '--preview' in sys.argv:
    for label in ('three-quarter','side'):
        inspect_view(label,ROOT/f'measurements/v02-preview-{label}.png',65)
    sys.exit(0)


def triangles(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    me.calc_loop_triangles()
    data=([v.co.copy() for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles])
    ev.to_mesh_clear()
    return data


def bounds(vertices):
    cols=list(zip(*vertices))
    return tuple(map(min,cols)),tuple(map(max,cols))


def disjoint(a,b):
    return any(a[1][i]<b[0][i] or b[1][i]<a[0][i] for i in range(3))


def overlaps(va,ta,ba,vb,tb,bb):
    if disjoint(ba,bb): return False
    if ta.overlap(tb): return True
    for verts,other,inside,outside in ((va,tb,ba,bb),(vb,ta,bb,ba)):
        if all(outside[0][i]<=inside[0][i] and inside[1][i]<=outside[1][i] for i in range(3)):
            point=verts[0]
            close,normal,_,_=other.find_nearest(point)
            if close is not None and (point-close).dot(normal)<-1e-7: return True
    return False


def geometry_audit():
    assert motion_digest(retained)==base_motion, 'Retained object motion changed'
    meshes={obj:triangles(obj) for obj in aircraft.objects if obj.type=='MESH'}
    static={}
    for obj in panels:
        vs,fs=meshes[obj]
        vertices=[obj.matrix_world@v for v in vs]
        static[obj]=(vertices,BVHTree.FromPolygons(vertices,fs,all_triangles=True),bounds(vertices))
    # Stationary mounting lugs, rear feet, and the gimbal suspension are joined to the shell.
    # Check moving parts, battery insert, and the camera/yoke against each new panel.
    tested=[o for o in retained if o.type=='MESH' and o.name.startswith(
        ('Arm.','Motor.','Propeller.','Leg.front.','Battery.','Camera.','Gimbal.yoke','Gimbal.trunnion'))]
    hits={}
    sizes={}
    for frame in range(1,122):
        scene.frame_set(frame)
        for obj in tested:
            vs,fs=meshes[obj]
            vertices=[obj.matrix_world@v for v in vs]
            bb=bounds(vertices)
            nearby=[p for p,data in static.items() if not disjoint(bb,data[2])]
            if not nearby: continue
            tree=BVHTree.FromPolygons(vertices,fs,all_triangles=True)
            for p in nearby:
                if overlaps(vertices,tree,bb,*static[p]):
                    hits.setdefault(f'{obj.name} / {p.name}',[]).append(frame)
        if frame in (1,121):
            boxes={o:bounds([o.matrix_world@v for v in vs]) for o,(vs,_) in meshes.items()}
            for key,group in [('all',boxes),('airframe',[o for o in boxes if not o.name.startswith('Propeller.')])]:
                sizes[f'{frame}-{key}']=[round(1000*(max(boxes[o][1][i] for o in group)-
                                                 min(boxes[o][0][i] for o in group)),3) for i in (1,0,2)]
    baseline=json.loads((ROOT/'measurements/v01-audit.json').read_text())['dimensions_mm']
    delta={k:[round(v-r,3) for v,r in zip(values,baseline[k])] for k,values in sizes.items()}
    result={'frames':121,'retained_transform_count':len(retained),'motion_sha256':base_motion,
            'dimensions_mm':sizes,'change_from_v01_mm':delta,'parts_checked_against_shell':len(tested),
            'new_shell_parts':len(panels),'unexpected_contacts':hits}
    print('AUDIT '+json.dumps(result),flush=True)
    if hits or max(abs(v) for row in delta.values() for v in row)>.025:
        raise RuntimeError('V02 failed its geometry check')
    scene.frame_set(1)
    return result


report=geometry_audit()
if '--check' in sys.argv: sys.exit(0)
blend=ROOT/'blender/drone-v02.blend'
glb=ROOT/'exports/drone-v02.glb'
if blend.exists() or glb.exists(): raise FileExistsError('V02 already published.')
scene.camera=bpy.data.objects['Studio.camera.three-quarter']
bpy.ops.object.select_all(action='DESELECT')
for obj in aircraft.objects: obj.select_set(True)
bpy.context.view_layer.objects.active=main
# Write the viewer asset out of its discovery pattern until it is complete.
pending=ROOT/'exports/pending-v02.glb'
bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
    export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
pending.rename(glb)
(ROOT/'measurements/v02-audit.json').write_text(json.dumps(report,indent=2)+'\n')
