"""Blender 5.2 background build. -- --check runs the geometry audit without publishing."""
import bpy
import math
import sys
from itertools import combinations
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
from pathlib import Path
from collections import defaultdict
import json

ROOT = Path(__file__).resolve().parents[1]
MM = .001
RAD = math.radians
V = Vector
LAST = 121
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, LAST
aircraft = bpy.data.collections.new("V01 | Aircraft")
studio = bpy.data.collections.new("Studio | Locked five views")
for collection in (aircraft, studio):
    scene.collection.children.link(collection)
mesh_objects = []
position = {}
component = {}
attachments = set()
drives = []


def clay(name, value):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (value, value, value, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = m.diffuse_color
    bs.inputs["Roughness"].default_value = .72
    return m


shell, arm_mat, mech, glass = [clay(n, v) for n, v in (
    ("Clay | Shell", .48), ("Clay | Structure", .38),
    ("Clay | Joints", .25), ("Clay | Camera face", .16))]
floor_mat = clay("Studio | Floor", .32)


def attach(o, p, location, group):
    aircraft.objects.link(o)
    position[o.name] = V(location)
    o.parent = p
    o.location = ((V(location) - position[p.name]) if p else V(location)) * MM
    component[o.name] = group
    return o


def pivot(name, point, parent=None, group="body"):
    o = attach(bpy.data.objects.new(name, None), parent, point, group)
    o.empty_display_type = 'PLAIN_AXES'
    o.empty_display_size = .006
    return o


def mesh(name, vertices, faces, origin, parent, material, group, bevel=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata([(V(v)-V(origin))*MM for v in vertices], [], faces)
    data.update()
    o = attach(bpy.data.objects.new(name, data), parent, origin, group)
    data.materials.append(material)
    mesh_objects.append(o)
    # All sections are closed. Recalculate consistent outward normals.
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    if bevel:
        mod = o.modifiers.new("Clay edge radius", 'BEVEL')
        mod.width, mod.segments, mod.limit_method = bevel*MM, 3, 'ANGLE'
        mod.harden_normals = True
    normals = o.modifiers.new("Face normals", 'WEIGHTED_NORMAL')
    normals.keep_sharp = True
    return o


def rings(name, sections, origin, parent, material, group, bevel=0):
    n, k = len(sections[0]), len(sections)
    faces = [tuple(reversed(range(n))), tuple(range((k-1)*n,k*n))]
    faces += [(i*n+j, i*n+(j+1)%n, (i+1)*n+(j+1)%n, (i+1)*n+j)
              for i in range(k-1) for j in range(n)]
    return mesh(name, sum(sections, []), faces, origin, parent, material, group, bevel)


def roundrect(w, h, r):
    r = min(r, w/2-.001, h/2-.001)
    pts = []
    for sx, sz, angle in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
        for j in range(5):
            a = RAD(angle + j*22.5)
            pts.append((sx*(w/2-r)+r*math.cos(a),sz*(h/2-r)+r*math.sin(a)))
    return pts


def box(name, center, dims, r, parent, material, group):
    x,y,z = center
    w,l,h = dims
    return rings(name, [[(x+u,y+v*l/2,z+t) for u,t in roundrect(w,h,r)]
                        for v in (-1,1)], center, parent, material, group, min(.6,r*.5))


def tube(name, start, end, r, parent, material, group, bevel=.4):
    a,b = V(start),V(end)
    d = (b-a).normalized()
    u = d.cross(V((1,0,0)) if abs(d.x)<.85 else V((0,1,0))).normalized()
    v = d.cross(u)
    return rings(name, [[p+r*(u*math.cos(i*math.tau/40)+v*math.sin(i*math.tau/40))
                         for i in range(40)] for p in (a,b)], a, parent, material, group, bevel)


def beam(name, points, parent, material, group, origin=None):
    centers=[V(row[:3]) for row in points]
    tangent = centers[-1]-centers[0]
    across = V((-tangent.y,tangent.x,0)).normalized()
    if across.length < .5:
        across=V((1,0,0))
    return rings(name, [[p+across*u+V((0,0,v)) for u,v in roundrect(w,h,min(h*.33,w*.25))]
                        for p,(*_,w,h) in zip(centers,points)], origin or centers[0],parent,material,group,.45)


def join(group_a, group_b):
    attachments.add(frozenset((group_a,group_b)))


def drive(o, axis, begin, end, angle, initial=0):
    drives.append((o,V(axis).normalized(),begin,end,angle,initial))


root = pivot("Drone.V01", (0,0,0))
shell_sections = [(-73.5,32,18,43),(-69,35,14,47),(-45,34,14,50),
                  (-19,35,17,52),(13,40,20,53),(39,46,27,56),
                  (52,43,33,53.5),(62,37,35,49),(64.5,30,36,46)]
body = rings("Body.shell", [[(u,y,(lo+hi)/2+v) for u,v in roundrect(w,hi-lo,5)]
                           for y,w,lo,hi in shell_sections], (0,0,32),root,shell,"body",.75)
# Cut an actual aft-opening socket. Its removable pack is a separate solid.
cut = box("Battery.socket_tool",(0,-51,30.5),(26.8,51,18.5),2.5,root,mech,"tool")
bpy.context.view_layer.objects.active=body
boolean=body.modifiers.new("Rear battery aperture",'BOOLEAN')
boolean.operation='DIFFERENCE'
boolean.object=cut
for mod in list(body.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
mesh_objects.remove(cut)
bpy.data.objects.remove(cut,do_unlink=True)
box("Battery.bay_insert",(0,-48.8,30.5),(25.4,46,17),2.2,root,arm_mat,"battery")
for sign,side in ((1,"R"),(-1,"L")):
    box("Leg.rear."+side,(sign*15,-55,8.3),(7,13,16.6),2.3,root,arm_mat,"body")

# Three nested mechanical axes, with a front-facing camera looking along +Y.
yaw = pivot("Gimbal.yaw",(0,45,32),root,"gimbal")
tube("Gimbal.yaw_boss",(0,45,29),(0,45,33),5,yaw,mech,"gimbal")
roll = pivot("Gimbal.roll",(0,43,23),yaw,"gimbal")
box("Gimbal.rear_carrier",(0,42,26),(16,5,12),2,roll,arm_mat,"gimbal")
pitch = pivot("Gimbal.pitch",(0,52,22),roll,"gimbal")
for s,side in ((1,"R"),(-1,"L")):
    beam("Gimbal.yoke."+side,[(s*9,42,25,3.6,7),(s*10,52,22,3,6)],roll,arm_mat,"gimbal")
    tube("Gimbal.trunnion."+side,(s*8,52,22),(s*11,52,22),2.7,pitch,mech,"gimbal")
box("Camera.block",(0,53,22),(17.7,13,15),3,pitch,shell,"gimbal")
tube("Camera.lens_proxy",(0,59.2,22),(0,62,22),5.5,pitch,glass,"gimbal")
join("body","gimbal")
# A separate hinge group lets the contact audit exempt the root bearing only.
for s, side in ((1,"R"),(-1,"L")):
    for front in (True,False):
        code=("F" if front else "R")+side
        hinge=(s*28.4,40,42) if front else (s*25.2,-32,16.22)
        hub=(s*94,78,47.07) if front else (s*78,78-math.sqrt(213**2-172**2),25.5)
        hx,hy,hz=hinge
        mx,my,mz=hub
        d=V((mx-hx,my-hy,0))
        folded_dir=V((s*(4.6 if front else 6.8),(-1 if front else 1)*math.sqrt(d.length**2-(4.6 if front else 6.8)**2),0))
        if front:
            axis=V((0,0,1))
            angle=math.atan2(d.x*folded_dir.y-d.y*folded_dir.x,d.dot(folded_dir))
        else:
            axis=(d.normalized()+folded_dir.normalized()).normalized()
            angle=math.pi*s  # outward arm first swings downward
        shoulder=code+".bearing"
        group=code+".arm"
        # Stationary, shaped mounting lug reaching the central hull.
        beam("Hinge.mount."+code,[(s*(18 if front else 16),hy,hz,10,8),
                                   (hx,hy,hz,9,8)],root,arm_mat,shoulder)
        join(shoulder,"body")
        rocker=pivot("Hinge.axis."+code,hinge,root,shoulder)
        tube("Hinge.pin."+code,V(hinge)-axis*4.5,V(hinge)+axis*4.5,4.5,rocker,mech,shoulder)
        join(group,shoulder)
        drive(rocker,axis,85 if front else 48,121 if front else 84,angle)
        ax,ay=(mx-hx),(my-hy)
        beam("Arm."+code,[(hx,hy,hz,9,8),(hx+ax*.19,hy+ay*.19,hz+1,9,7.5),
                          (hx+ax*.73,hy+ay*.73,mz-1.5,7,6.4),(mx,my,mz-1,9,7)],
             rocker,arm_mat,group,hinge)
        tube("Motor."+code,(mx,my,mz-4),(mx,my,mz+6.7),7.5,rocker,mech,group,.65)
        if front:
            box("Leg.front."+side,(mx,my+3.3,22),(5.6,7.2,44),2,rocker,arm_mat,group)
        z=mz+6.8
        rotor=pivot("Propeller.hub."+code,(mx,my,z),rocker,group)
        tube("Propeller.cap."+code,(mx,my,z-.5),(mx,my,z+1.8),4.2,rotor,mech,group,.25)
        # Independent clocking matches the reference drone's posed blade envelope.
        initial=RAD({"FR":14.3,"FL":90,"RR":90,"RL":0}[code])
        park=math.atan2(-d.y,-d.x)-math.pi/2
        travel=(park-initial+math.pi)%math.tau-math.pi
        drive(rotor,(0,0,1),1,22,travel,initial)
        for i,sign in enumerate((1,-1)):
            pin=(mx+sign*2.4,my,z+.15+i*1.55)
            blade=pivot(f"Blade.pin.{code}.{i+1}",pin,rotor,group)
            # Offset roots and slight axial stagger allow the pair to nest.
            blade_group=f"{code}.blade{i+1}"
            join(blade_group,group)
            length=59.69-2.4
            profiles=[(0,1.5,0),(.10,2.3,0),(.29,3.9,.5),(.56,4.2,1.2),
                      (.78,3.3,1.9),(.94,1.9,2.6),(1,.55,2.4)]
            sec=[]
            for t,w,sweep in profiles:
                x=pin[0]+sign*length*t
                y=pin[1]+sign*sweep
                sec.append([(x,y+w*u,pin[2]+v) for u,v in
                            [(-1,0),(-.4,.43),(.5,.30),(1,-.12),(.25,-.47),(-.6,-.38)]])
            rings(f"Propeller.blade.{code}.{i+1}",sec,pin,blade,arm_mat,blade_group)
            drive(blade,(0,0,1),22,47,sign*RAD(90))

# Bake quaternions to individual frame samples for identical GLB playback.
def set_motion():
    for o,axis,start,stop,angle,initial in drives:
        o.rotation_mode='QUATERNION'
        previous=None
        for frame in range(1,LAST+1):
            t=max(0,min(1,(frame-start)/(stop-start)))
            q=Quaternion(axis, initial+angle*t*t*(3-2*t))
            if previous is not None: q.make_compatible(previous)
            previous=q.copy()
            o.rotation_quaternion=q
            o.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Fold')
        o.animation_data.action.name="Fold."+o.name
        track=o.animation_data.nla_tracks.new()
        track.name="Fold"
        track.strips.new("Fold",1,o.animation_data.action)
        o.animation_data.action=None
    for name,f in [('Unfolded',1),('Blades parked',47),('Rear arms stowed',84),('Folded',121)]:
        scene.timeline_markers.new(name,frame=f)
    scene.frame_set(1)


def snapshot():
    dg=bpy.context.evaluated_depsgraph_get()
    entries={}
    for o in mesh_objects:
        ev=o.evaluated_get(dg)
        me=ev.to_mesh()
        verts=[ev.matrix_world @ v.co for v in me.vertices]
        faces=[tuple(p.vertices) for p in me.polygons]
        bmin=V(tuple(min(p[i] for p in verts) for i in range(3)))
        bmax=V(tuple(max(p[i] for p in verts) for i in range(3)))
        entries[o.name]=(verts,faces,bmin,bmax)
        ev.to_mesh_clear()
    return entries


def audit():
    hits=defaultdict(list)
    sizes={}
    # Local evaluated meshes remain rigid through the entire fold.
    original=snapshot()
    local={}
    for o in mesh_objects:
        inv=o.matrix_world.inverted()
        local[o.name]=([inv@v for v in original[o.name][0]],original[o.name][1])
    for f in range(1,LAST+1):
        scene.frame_set(f)
        geom={}
        for o in mesh_objects:
            vs,faces=local[o.name]
            verts=[o.matrix_world@v for v in vs]
            coords=list(zip(*verts))
            geom[o.name]=(verts,faces,tuple(map(min,coords)),tuple(map(max,coords)))
        if f in (1,LAST):
            for k,parts in [('airframe',[n for n in geom if not n.startswith('Propeller.')]),
                            ('all',list(geom))]:
                sizes[f'{f}-{k}']=[round(1000*(max(geom[n][3][i] for n in parts)-min(geom[n][2][i] for n in parts)),3) for i in (1,0,2)]
        if f == 1:
            centers = {key: bpy.data.objects["Propeller.hub."+key].matrix_world.translation
                       for key in ("FR","FL","RR","RL")}
            sizes["wheelbases"] = [round((centers[a]-centers[b]).xy.length*1000,3)
                                   for a,b in (("FR","RL"),("FL","RR"))]
            sizes["propeller_diameters"] = [
                round(2000*max((v-center).xy.length for i in (1,2)
                               for v in geom[f"Propeller.blade.{key}.{i}"][0]),3)
                for key,center in centers.items()]
        trees={}
        for n,m in combinations(geom,2):
            a,b=component[n],component[m]
            if a==b: continue
            if frozenset((a,b)) in attachments:
                # The rotor joint may contact its motor and cap. Check blades
                # against the arm and landing foot even inside that assembly.
                blade_pair = '.blade' in a or '.blade' in b
                if not blade_pair or any(nm.startswith(('Motor.', 'Propeller.cap.')) for nm in (n,m)):
                    continue
            va,fa,la,ha=geom[n]
            vb,fb,lb,hb=geom[m]
            if any(la[i]>=hb[i] or lb[i]>=ha[i] for i in range(3)): continue
            for key,vs,fs in ((n,va,fa),(m,vb,fb)):
                if key not in trees: trees[key]=BVHTree.FromPolygons(vs,fs)
            overlap = bool(trees[n].overlap(trees[m]))
            # For closed rigid pieces without crossing faces, test a vertex
            # when one bounding box fits completely inside the other.
            for inner,outer,ilo,ihi,olo,ohi in ((n,m,la,ha,lb,hb),(m,n,lb,hb,la,ha)):
                if not overlap and all(olo[i] <= ilo[i] and ihi[i] <= ohi[i] for i in range(3)):
                    point=geom[inner][0][0]
                    near,normal,_,_=trees[outer].find_nearest(point)
                    overlap=near is not None and (point-near).dot(normal) < -1e-7
            if overlap: hits[(n,m)].append(f)
    return sizes,{' / '.join(pair):[min(frames),max(frames),len(frames)] for pair,frames in hits.items()}


def studio_setup():
    from mathutils import Euler
    target=V((0,0,.026))
    def studio_object(name,data,location):
        obj=bpy.data.objects.new(name,data)
        studio.objects.link(obj)
        obj.location=location
        return obj
    def aim(o):
        o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    for label,where in {'front':(0,.6,.026),'side':(.6,0,.026),'top':(0,0,.65),
                        'back':(0,-.6,.026),'three-quarter':(.34,.49,.275)}.items():
        data=bpy.data.cameras.new(label)
        c=studio_object('Studio.camera.'+label,data,where)
        data.type='ORTHO'
        data.ortho_scale=.50 if label=='top' else .352
        data.clip_start=.001
        aim(c)
        if label=='top': c.rotation_euler=Euler((0,0,math.pi))
    scene.camera=bpy.data.objects['Studio.camera.three-quarter']
    for name,loc,power,size in [('Key',(.21,.26,.40),6.2,.30),('Fill',(-.22,.12,.21),2.8,.28),
                                ('Rim',(-.10,-.29,.30),6.5,.23)]:
        light=bpy.data.lights.new(name,'AREA')
        light.energy=power
        light.shape='DISK'
        light.size=size
        aim(studio_object('Studio.'+name,light,loc))
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.006))
    plane=bpy.context.object
    plane.name='Studio.floor'
    for c in list(plane.users_collection): c.objects.unlink(plane)
    studio.objects.link(plane)
    plane.data.materials.append(floor_mat)
    for f,z in ((1,0),(121,-.00199)):
        plane.location.z=z-.00002
        plane.keyframe_insert(data_path='location',frame=f)
    scene.world=bpy.data.worlds.new('Neutral studio')
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
    scene.render.engine='CYCLES'
    scene.cycles.samples=10
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1920
    scene.render.resolution_y=1080
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    scene.render.image_settings.file_format='PNG'
    # Keep the inspection viewport clear of the studio's camera and light widgets.
    for obj in studio.objects: obj.hide_set(True)
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            view=area.spaces.active
            view.clip_start=.001
            view.overlay.show_overlays=False
            view.region_3d.view_distance=.38
            view.region_3d.view_location=target
            view.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()


set_motion()
sizes,hits=audit()
print('AUDIT',json.dumps({'sizes':sizes,'intersections':hits}),flush=True)
if '--check' in sys.argv:
    sys.exit(0)
if hits:
    raise RuntimeError("Unresolved moving contacts. Run --check.")
blend=ROOT/'blender/drone-v01.blend'
glb=ROOT/'exports/drone-v01.glb'
if blend.exists() or glb.exists(): raise FileExistsError('V01 exists. Build in a fresh project copy.')
scene.frame_set(1)
studio_setup()
scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT')
for o in aircraft.objects: o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(glb),use_selection=True,export_apply=True,
                          export_animation_mode='NLA_TRACKS',export_animations=True,
                          export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version=0
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
(ROOT/'measurements/v01-audit.json').write_text(json.dumps({'dimensions_mm':sizes,'intersections':hits,'sampled_frames':LAST},indent=2)+'\n')
