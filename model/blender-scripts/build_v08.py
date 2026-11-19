"""Rebuild the reference drone study from the local orthographic and folded photographs.
Run against the unmodified V07 file. Coordinates below are millimetres in the open pose.
"""
from pathlib import Path
from math import sin, cos, pi, tau, sqrt, atan2, radians, exp
import sys, json
import bpy, bmesh
from mathutils import Vector, Quaternion, geometry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_v04_assembly import audit
from rill_shell import stations, U, T, skin

assert Path(bpy.data.filepath) == ROOT / 'blender/drone-v07.blend'
scene = bpy.context.scene
scene.frame_set(1)
group = bpy.data.collections['V07 | Aircraft']
body = bpy.data.objects['Drone.V07']
for obj in list(group.objects):
    if obj != body and not obj.name.startswith(('Gimbal.', 'Camera.')):
        bpy.data.objects.remove(obj, do_unlink=True)
body.name = 'Drone.V08'
group.name = 'V08 | Aircraft'
yaw = bpy.data.objects['Gimbal.yaw']
yaw.location = (0, .042, .033)
yaw.scale = (1.36,)*3
origins = {body.name:Vector((0,0,0))}
drives = []
Z = Vector((0,0,1))


def mat(name, rgb, roughness, metallic=0):
    m = bpy.data.materials.new('RILL | '+name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    for key, val in [('Base Color',m.diffuse_color),('Roughness',roughness),('Metallic',metallic)]:
        bs.inputs[key].default_value = val
    return m


stone = mat('warm ceramic grey',(.425,.435,.424),.44,.035)
lower = mat('lower casing',(.37,.382,.373),.48,.025)
flank = mat('sloping upper shoulder',(.374,.383,.374),.45,.035)
seam = mat('joint shadow',(.075,.082,.080),.54)
rubber = mat('graphite elastomer',(.024,.027,.027),.56)
vent = mat('intake depth',(.009,.012,.013),.72)
steel = mat('satin aluminium',(.40,.424,.43),.31,.85)
copper = mat('stator winding',(.39,.167,.053),.35,.67)
carbon = mat('carbon blade',(.010,.011,.012),.47,.04)
carbon.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.16
orange = mat('signal orange',(.93,.205,.031),.4,.03)
mark = mat('wordmark',(.21,.224,.22),.45)


def node(name, parent, origin, data=None):
    o = bpy.data.objects.new(name,data)
    group.objects.link(o)
    o.parent = parent
    origins[o.name] = Vector(origin)
    o.location = (origins[o.name]-origins[parent.name])*.001
    if data is None: o.empty_display_size = .004
    return o


def mesh(name, parent, origin, points, faces, materials, ids=None, smooth=True, angle=36):
    me = bpy.data.meshes.new(name)
    o = node(name,parent,origin,me)
    me.from_pydata([(Vector(p)-Vector(origin))*.001 for p in points],[],faces)
    for m in materials: me.materials.append(m)
    for i,p in enumerate(me.polygons):
        p.material_index = ids[i] if ids else 0
        p.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), name
    bm.to_mesh(me)
    bm.free()
    assert not me.validate(), name
    me.set_sharp_from_angle(angle=radians(angle))
    return o


def loft(name, parent, sections, materials, bands=None, closed=False, angle=36):
    n = len(sections[0])
    count = len(sections)
    faces, ids = [], []
    for i in range(count if closed else count-1):
        k = (i+1)%count
        for j in range(n):
            h = (j+1)%n
            faces.append((i*n+j,i*n+h,k*n+h,k*n+j))
            ids.append(bands[i] if bands else 0)
    if not closed:
        faces.extend([list(reversed(range(n))),list(range((count-1)*n,count*n))])
        ids.extend([0,bands[-1] if bands else 0])
    return mesh(name,parent,origins[parent.name],sum(sections,[]),faces,materials,ids,angle=angle)


def rounded(w,h,r):
    r = min(r,w*.495,h*.495)
    out = []
    for sx,sz,a in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        for j in range(6):
            b = radians(a+18*j)
            out.append((sx*(w/2-r)+r*cos(b),sz*(h/2-r)+r*sin(b)))
    return out


def turn(name,parent,point,axis,profile,mats,closed=False,n=48):
    a = Vector(axis).normalized()
    u = a.cross(Vector((0,1,0)) if abs(a.y)<.9 else Z).normalized()
    v = a.cross(u)
    rings = [[Vector(point)+a*d+r*(u*cos(tau*j/n)+v*sin(tau*j/n)) for j in range(n)] for d,r,idx in profile]
    return loft(name,parent,rings,mats,[idx for d,r,idx in profile],closed)


def beam(name,parent,rows,mats,across,bands=None):
    a = Vector(across).normalized()
    rings = [[Vector((x,y,z))+a*u+Z*v for u,v in rounded(w,h,r)] for x,y,z,w,h,r in rows]
    return loft(name,parent,rings,mats,bands)


def casing():
    vs,fs,ids = [],[],[]
    index={}
    def vert(p):
        key=tuple(round(n,6) for n in p)
        if key not in index:
            index[key]=len(vs)
            vs.append(p)
        return index[key]
    def face(ps, m=0):
        fs.append([vert(p) for p in ps])
        ids.append(m)
    perimeter = [(u,0) for u in U]+[(1,t) for t in T[1:]]+[(u,1) for u in U[-2::-1]]+[(-1,t) for t in T[-2:0:-1]]
    for i,(a,b) in enumerate(zip(stations,stations[1:])):
        for j,(u,v) in enumerate(perimeter):
            p,q=perimeter[(j+1)%len(perimeter)]
            side = abs(p)==abs(u)==1 and p==u
            m=1 if v==q==0 or (side and (q+v)/2<.77) else 0
            if side and v!=q and min(v,q)==.77: m=2
            if v==q==1 and min(abs(u),abs(p))>=.67: m=4
            if a[0]==-59.2 and min(v,q)>.40: m=2
            face([skin(a,u,v),skin(a,p,q),skin(b,p,q),skin(b,u,v)],m)
    # Tile the front around two formed corner intakes and the narrow nose indicator.
    for row, front in ((stations[0],False),(stations[-1],True)):
        gaps=[(-.86,-.50,.16,.74),(.50,.86,.16,.74),(-.24,.24,.40,.50)] if front else []
        for u,p in zip(U,U[1:]):
            for v,q in zip(T,T[1:]):
                if any(l<=u<p<=r and b<=v<q<=t for l,r,b,t in gaps): continue
                face([skin(row,u,v),skin(row,p,v),skin(row,p,q),skin(row,u,q)],0 if front else 1)
        for l,r,b,t in gaps:
            us=[u for u in U if l<=u<=r]
            ts=[v for v in T if b<=v<=t]
            uv=[(u,b) for u in us]+[(r,v) for v in ts[1:]]+[(u,t) for u in us[-2::-1]]+[(l,v) for v in ts[-2:0:-1]]
            prev=[skin(row,u,v) for u,v in uv]
            for scale,depth,material in ((.86,.10,0),(.76,1.1,1),(.70,2.2,3)):
                nxt=[]
                for u,v in uv:
                    a=(2*u-l-r)/(r-l)
                    h=(2*v-b-t)/(t-b)
                    k=(abs(a)**4+abs(h)**4)**(-.25)
                    pos=skin(row,(l+r)/2+a*k*scale*(r-l)/2,(b+t)/2+h*k*scale*(t-b)/2)
                    pos.y-=depth
                    nxt.append(pos)
                for j in range(len(uv)):
                    f=(j+1)%len(uv)
                    face([prev[j],prev[f],nxt[f],nxt[j]],material)
                prev=nxt
            center=sum(prev,Vector())/len(prev)
            for j,p in enumerate(prev): face([p,prev[(j+1)%len(prev)],center],3)
    return mesh('Shell.moulded_fuselage',body,(0,0,0),vs,fs,[stone,lower,seam,vent,flank],ids,angle=33)

hull = casing()

for s, side in ((1,'R'),(-1,'L')):
    # The rear feet are short pads integrated into the belly casting.
    rows=[(s*13,y,z,w,h,r) for y,z,w,h,r in [(-61,8.0,3.8,5,1.3),(-59,7.1,5.0,11.7,1.8),
          (-56,6.35,5.3,12.7,1.9),(-53,6.5,5.3,13,2),(-50,8.3,4.8,10,1.8)]]
    beam('Leg.rear.'+side,body,rows,[lower],(1,0,0))

# Positive seat for the retained articulated camera, under the nose canopy.
turn('Shell.gimbal_socket',body,(0,42,33),Z,[(-.2,5.2,0),(.3,5.9,0),(2.8,6.6,0),(4.6,7.4,0)],[rubber])
# Widen the camera face into the photographed landscape-format pod. Keep the two
# optical elements, iris, receiver and barrel coaxial as the lens moves off centre.
pitch=bpy.data.objects['Gimbal.pitch']
origins[pitch.name]=Vector((0,52,22))
yaw.scale=(1,1,1)
yaw.location=(0,.045,.032)
bpy.context.view_layer.update()
for obj in [o for o in group.objects if o.name.startswith('Camera.')]:
    matrix=obj.matrix_world.copy()
    inverse=matrix.inverted()
    for vtx in obj.data.vertices:
        v=(matrix@vtx.co)*1000
        if obj.name=='Camera.block' and vtx.index<8*96:
            t=min(1,max(0,(v.y-52)/5))
            v.x*=1+.32*t*t*(3-2*t)
        else:
            v.x-=2.7
        vtx.co=inverse@(v*.001)
for s,side in ((1,'R'),(-1,'L')):
    turn('Gimbal.pitch_cover.'+side,pitch,(s*8.18,52,22),(s,0,0),
         [(0,5.6,0),(.3,6.6,0),(1.1,7.15,0),(2.8,7.30,0),(3.55,7.05,0),
          (3.86,6.66,0),(4.0,5.85,0),(4.05,4.62,0)], [rubber])
rings=[]
for y,w,h,rad in [(59.04,20.90,12.4,2.45),(59.21,20.78,12.28,2.44),
                   (59.25,20.13,11.68,2.18),(59.04,20.06,11.59,2.16)]:
    rings.append([Vector((x,y,22+z)) for x,z in rounded(w,h,rad)])
loft('Camera.face_trim',pitch,rings,[seam,steel],[0,1,0,0],True)
yaw.location=(0,.042,.033)
yaw.scale=(1.36,)*3
# A modest, conforming wordmark on the rear crown.
def wordmark():
    font=bpy.data.curves.new('RILL lettering','FONT')
    font.body='RILL'
    font.size=.0055
    font.space_character=1.12
    font.align_x='CENTER'
    font.align_y='CENTER'
    font.extrude=.00007
    o=node('Shell.RILL',body,(0,0,0),font)
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    o.data.materials.append(mark)
    for vert in o.data.vertices:
        x,y,z=vert.co*1000
        y=-43+y
        for a,b in zip(stations,stations[1:]):
            if a[0]<=y<=b[0]:
                k=(y-a[0])/(b[0]-a[0])
                roof=skin(a,x/a[1],1).z*(1-k)+skin(b,x/b[1],1).z*k
                break
        vert.co=Vector((x,y,roof+.008+z))*.001
    o.select_set(False)
wordmark()

# Motor positions digitized in the the reference overhead photo. Set the opposing-axis
# distance to the published 213 mm after correcting for the image scale.
front_x, rear_x, front_y = 88.4,83.1,39.7
rear_y=front_y-sqrt(213**2-(front_x+rear_x)**2)


def motor(parent,hub,code,rotor):
    mx,my,mz=hub
    profile=[(-4.6,6.2,0),(-4.35,7.2,0),(-3.7,8.04,0),(-2.8,8.3,0),
             (1.0,8.3,0),(2.3,8.06,0),(2.55,7.90,1),(2.88,7.89,1),
             (3.0,7.98,2),(6.15,7.93,2),(6.58,7.64,2),(6.66,6.94,2),
             (6.28,6.65,1),(3.92,6.50,1),(3.82,5.96,1),(3.83,3.9,1),
             (5.75,3.25,1),(6.2,2.9,2),(6.28,1.65,2)]
    turn('Motor.'+code,parent,hub,Z,profile,[stone,rubber,steel])
    # Raised, fluted copper stator recessed inside the satin metal motor bell.
    n=100
    rings=[]
    for zz,rr in ((3.79,4.1),(3.85,6.1),(4.52,6.05),(5.46,5.54),(5.47,4.80),(4.5,4.15)):
        ring=[]
        for j in range(n):
            a=tau*j/n
            k=(j%10)/10
            radius=rr+(.07 if k<.8 else -.15)
            ring.append(Vector((mx+radius*cos(a),my+radius*sin(a),mz+zz-(.47 if k>=.8 else 0))))
        rings.append(ring)
    stator=loft('Motor.stator.'+code,parent,rings,[copper,vent],closed=True)
    for i,p in enumerate(stator.data.polygons): p.material_index=1 if i%n%10>=8 else 0
    caprows=[]
    for zz,w,h in ((5.9,11.4,3.4),(6.4,12.4,4.45),(7.0,12.4,4.45),(7.1,11.85,3.9)):
        caprows.append([Vector((mx+u,my+v,mz+zz)) for u,v in rounded(w,h,1.7)])
    loft('Propeller.bridge.'+code,rotor,caprows,[steel])


def blade_form(parent,pin,direction,hand,code,j):
    # A convex leading edge, a straighter trailing edge, spanwise twist and a clipped tip.
    # The painted stripe follows the final swept section on both faces.
    profile=[(-1.55,2.5,0),(-.55,4.25,0),(1.35,4.6,0),(3.8,4.75,.05),
             (6.0,6.2,.08),(9.5,8.5,.20),(14,10.8,.58),(20,12.0,1.10),
             (28,12.2,2.05),(35,11.5,2.8),(43,9.9,3.23),(49,8.0,3.40),
             (53,6.75,3.35),(54.0,6.42,3.30),(56.6,5.8,3.20),(57.0,5.0,3.15)]
    rings=[]
    for span,chord,curve in profile:
        twist=radians(7.5-8*max(0,span)/57)
        ring=[]
        for width,height in [(-.50,-.04),(-.46,.19),(-.30,.39),(0,.43),(.30,.26),(.48,.055),
                             (.50,-.045),(.34,-.13),(0,-.21),(-.31,-.24),(-.46,-.16)]:
            w=width*chord
            # Skew the tip cut slightly in plan and retain blade handedness per motor.
            sweep=hand*(curve+w)
            ring.append(pin+Vector((direction*(span+max(0,(span-47)/10)*width*1.6),
                                    direction*sweep, height+hand*w*sin(twist))))
        rings.append(ring)
    return loft(f'Propeller.blade.{code}.{j}',parent,rings,[carbon,orange],
                [int(i>=13) for i in range(len(profile))],angle=42)


for s,side in ((1,'R'),(-1,'L')):
    for front in (True,False):
        code=('F' if front else 'R')+side
        hinge=Vector((s*(31.2 if front else 26.5),15 if front else -48.2,40.2 if front else 15.2))
        hub=Vector((s*(front_x if front else rear_x),front_y if front else rear_y,46.7 if front else 23.0))
        planar=Vector((hub.x-hinge.x,hub.y-hinge.y,0))
        lateral=Vector((-planar.y,planar.x,0)).normalized()
        delta=s*(.9 if front else 5.6)
        folded=Vector((delta,(-1 if front else 1)*sqrt(planar.length_squared-delta**2),0))
        if front:
            axis=Z
            angle=atan2(planar.x*folded.y-planar.y*folded.x,planar.dot(folded))
        else:
            axis=(planar.normalized()+folded.normalized()).normalized()
            angle=pi*s
        hinge_node=node('Hinge.axis.'+code,body,hinge)
        drives.append((hinge_node,axis,85 if front else 48,121 if front else 84,angle,0))
        hx,hy,hz=hinge
        # The fixed seat supports the inboard end of the journal. It sits below
        # the front arm and on the inner side of the oblique rear hinge axis.
        seat = hinge-axis*(7.45 if front else 9.85)
        mount_rows=[(seat.x-s*d,seat.y,seat.z,w,h,r) for d,w,h,r in
                    [(8,8,4.4,1.5),(4,9,4.3,1.4),(1.5,9.7,4.1,1.2),(0,9.5,3.7,1.2)]]
        beam('Hinge.bracket.'+code,body,mount_rows,[lower],(0,1,0))
        turn('Hinge.socket.'+code,body,hinge,axis,[(-9.0,4.35,0),(-8.7,5.1,0),
             (-6.8,5.3,0),(-6.45,4.85,0),(-6.4,4.25,1)], [lower,seam])
        turn('Hinge.pin.'+code,hinge_node,hinge,axis,[(-7.85,3.35,0),(-7.7,3.85,0),
             (-4.35,3.85,0),(-4.15,4.22,0),(3.5,4.22,0),(4.60,4.18,0),
             (4.85,3.91,0),(4.88,3.05,1)],[rubber,steel])
        profiles = ([(0,10.7,8.8),(.08,11,9.7),(.16,11.0,10.5),(.24,10.1,10.2),
                     (.48,9.3,9.2),(.76,8.8,8.5),(.86,9.1,8.1),(.94,12,8.2),(1,12.9,8.7)]
             if front else [(0,13,11),(.08,14.2,12.1),(.16,14,12.4),(.25,12.0,11.5),(.32,10.2,10.6),
                            (.48,9.4,9.2),(.75,8.9,8.2),(.84,9.1,8.1),(.94,12.0,8.2),(1,12.8,8.6)])
        rows=[]
        for t,w,h in profiles:
            p=hinge.lerp(hub,t)
            if not front:
                p.y-=1.0*sin(pi*t)**2+2.0*sin(2*pi*t)**2
                p.y+=3.7*exp(-((t-.16)/.125)**2)*min(1,t/.08)
            p.z-=1.6*sin(pi*t)**2+1.1*t
            rows.append((*p,w,h,min(2.05,h*.26)))
        beam('Arm.'+code,hinge_node,rows,[stone],lateral)
        if front:
            # Landing struts are cast into the outboard side of each front motor cradle.
            rings=[]
            for zz,out,forward,w,depth,r in [(0,4.6,5.1,4.7,6,1.2),(.6,4.6,5.1,5.5,6.7,1.4),
                   (1.65,4.6,5.1,5.65,6.85,1.5),(4,4.6,5.1,5.8,7.1,1.65),(30,4.8,4.8,6.1,8.1,1.7),
                   (39,4.5,4.5,6.6,9.35,1.9),(42,4.25,4.1,7.5,10.4,2.1),
                   (44.9,3.75,3.7,8.1,10.3,2.2),(47.1,3.5,3.3,7.65,9.5,2.2)]:
                rings.append([Vector((hub.x+s*(out+5.1)+u,hub.y+forward+1.5+v,zz)) for u,v in rounded(w,depth,r)])
            loft('Leg.front.'+side,hinge_node,rings,[lower,stone,rubber],[2,1,1,1,1,1,1,1,1])
            # Recessed dark window in the outboard shoulder of the landing strut.
            lamp=[]
            for zz,w,h in [(47.03,4.65,2.48),(47.17,4.65,2.48),(47.29,4.20,2.10)]:
                lamp.append([Vector((hub.x+s*(9.1+.82*u-.57*v),hub.y+5.9+.57*u+.82*v,zz))
                             for u,v in rounded(w,h,.57)])
            loft('Leg.window.'+side,hinge_node,lamp,[seam,rubber],[0,1,1])
        rotor=node('Propeller.hub.'+code,hinge_node,hub+Z*6.9)
        motor(hinge_node,hub,code,rotor)
        initial=radians({'FR':-52.5,'FL':52.5,'RR':49.6,'RL':-49.6}[code])
        park=atan2(-planar.y,-planar.x)-pi/2
        if not front: park+=s*radians(7.0)
        travel=(park-initial+pi)%tau-pi
        drives.append((rotor,Z,1,22,travel,initial))
        for j,sgn in enumerate((1,-1),1):
            pin=hub+Vector((sgn*3.60,0,7.12+(j-1)*1.35))
            spindle=node(f'Blade.pin.{code}.{j}',rotor,pin)
            blade_form(spindle,pin,sgn,1 if code in ('FR','RL') else -1,code,j)
            turn(f'Propeller.screw.{code}.{j}',rotor,pin,Z,[(-2.60,1.2,0),(-2.4,1.65,0),
                 (.16,1.65,0),(.38,2.18,0),(.76,2.15,0),(.86,1.84,0),(.87,.92,1)],[rubber,seam],n=32)
            drives.append((spindle,Z,22,47,sgn*radians(90),0))

for obj,axis,start,end,angle,initial in drives:
    obj.rotation_mode='QUATERNION'
    last=None
    for f in range(1,122):
        t=min(1,max(0,(f-start)/(end-start)))
        q=Quaternion(axis,initial+angle*t*t*(3-2*t))
        if last is not None: q.make_compatible(last)
        obj.rotation_quaternion=q
        obj.keyframe_insert(data_path='rotation_quaternion',frame=f,group='Fold')
        last=q.copy()
    action=obj.animation_data.action
    action.name='V08.Fold.'+obj.name
    track=obj.animation_data.nla_tracks.new()
    track.name='Fold'
    track.strips.new('Fold',1,action)
    obj.animation_data.action=None
scene.frame_set(1)
floor=bpy.data.objects['Studio.floor']
for f,ground in ((1,0),(121,-1.95)):
    floor.location.z=ground*.001-.00002
    floor.keyframe_insert(data_path='location',frame=f)
scene.frame_set(1)
scene.camera=bpy.data.objects['Studio.camera.three-quarter']
draft='--publish' not in sys.argv
if draft:
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'measurements/v08-work.blend'))
else:
    blend=ROOT/'blender/drone-v08.blend'
    glb=ROOT/'exports/drone-v08.glb'
    assert not blend.exists() and not glb.exists()
    poses=audit(group,range(1,122))
    baseline=set(poses[0]['contacts'])
    assert all(len(row['groups'])==1 for row in poses), 'Disconnected component in fold'
    for row in poses:
        new=set(row['contacts'])-baseline
        assert not new,(row['frame'],new)
    assert not any('Shell.moulded_fuselage' in pair and any(n.startswith(('Motor.','Arm.','Propeller.','Leg.front.')) for n in pair) for pair in baseline)
    scene.frame_set(1)
    pending=ROOT/'exports/pending-v08.glb'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects: obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
