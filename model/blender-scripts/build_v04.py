"""Rebuild the aft belly, fit the six measured shell sections and detail the four rotors."""
from pathlib import Path
from math import cos,sin,pi,radians
from bisect import bisect_right
import bpy,bmesh,sys,json
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import audit,widths

source=ROOT/'blender/drone-v03.blend'
assert Path(bpy.data.filepath)==source
versions={}
for v in ('v01','v03'):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'blender/drone-{v}.blend'))
    group=bpy.data.collections[v.upper()+' | Aircraft']
    bpy.context.scene.frame_set(1)
    versions[v]=widths(group)
    animated=sorted(o.name for o in group.objects if o.type=='EMPTY' and o.animation_data)
    matrices=[]
    for frame in range(1,122):
        bpy.context.scene.frame_set(frame)
        matrices.append([tuple(x for row in bpy.data.objects[n].matrix_world for x in row) for n in animated])
    if v=='v01': reference_matrices=matrices
    else:
        motion_error=max(abs(a-b) for f,g in zip(matrices,reference_matrices) for old,new in zip(f,g) for a,b in zip(old,new))
        print('Articulated nodes',animated,'matrix deviation',motion_error,flush=True)
        assert len(animated)==16 and motion_error<1.e-6
    bpy.context.scene.frame_set(1)
scene=bpy.context.scene
root=bpy.data.objects['Drone.V03']
scene.frame_set(1)
M=.001
TAU=2*pi


def finish(name,rgb,metal,rough):
    mat=bpy.data.materials.new('Basalt | '+name)
    mat.diffuse_color=(*rgb,1)
    mat.use_nodes=True
    bs=mat.node_tree.nodes['Principled BSDF']
    for k,v in [('Base Color',mat.diffuse_color),('Metallic',metal),('Roughness',rough)]:
        bs.inputs[k].default_value=v
    return mat


bell=finish('motor graphite',(.018,.019,.020),.58,.36)
lip=finish('turned motor rim',(.10,.106,.114),.82,.31)
titanium=finish('brushed rotor button',(.36,.37,.38),.82,.33)
deep=bpy.data.materials['Basalt | hinge reveal']
blade_mat=finish('porcelain rotor blades',(.79,.78,.754),.14,.36)
casting=bpy.data.materials['Basalt | lower casting']


def loft(obj,rings,mats,strip_ids,angle=32):
    n=len(rings[0])
    faces=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
    indices=[0,strip_ids[-1][0]]
    for i,ids in enumerate(strip_ids):
        for j,m in enumerate(ids):
            k=i*n+j
            h=i*n+(j+1)%n
            faces.append((k,h,h+n,k+n));indices.append(m)
    mesh=bpy.data.meshes.new(obj.name+' V04')
    mesh.from_pydata([p for row in rings for p in row],[],faces)
    for mat in mats: mesh.materials.append(mat)
    for i,(poly,idx) in enumerate(zip(mesh.polygons,indices)):
        poly.material_index=idx
        poly.use_smooth=i>=2
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),obj.name
    bm.to_mesh(mesh);bm.free()
    assert not mesh.validate(),obj.name
    mesh.set_sharp_from_angle(angle=radians(angle))
    obj.modifiers.clear()
    obj.data=mesh


def linear(x,rows):
    i=max(0,min(len(rows)-2,bisect_right([r[0] for r in rows],x)-1))
    a,b=rows[i:i+2]
    t=max(0,min(1,(x-a[0])/(b[0]-a[0])))
    return [(1-t)*aa+t*bb for aa,bb in zip(a[1:],b[1:])]


# Use the two measured outlines as a transverse correction near the outer sidewalls.
# Preserve the battery and camera openings at their original sizes.
stations=[(-73.5,0)]+[(float(y),(w-versions['v03'][y])/2) for y,w in versions['v01'].items()]+[(64.5,0)]
for obj in group.objects:
    if not obj.name.startswith('Shell.') or obj.name in ('Shell.lower_chassis','Shell.nose_face'): continue
    for v in obj.data.vertices:
        x,y,z=v.co/M
        delta=linear(y,stations)[0]
        influence=max(0,min(1,(abs(x)-13.5)/2.8))
        v.co.x+=(1 if x>=0 else -1)*delta*influence*M

# The service pockets are shaped directly into a continuous cross-section.
# The inner roof lies under the removable pack, and the forward relief follows the yoke.
source_stations=[(-73.5,32,18,43),(-69,35,14,47),(-45,34,14,50),(-19,35,17,52),
                 (13,40,20,53),(39,46,27,56),(52,43,33,53.5),(62,37,35,49),(64.5,30,36,46)]
# Read the V02 upper casting's continuous curve from its own profile by interpolating
# the same Hermite stations; a narrow internal tongue bridges the visible panel seam.
def hull(y):
    i=max(0,min(len(source_stations)-2,bisect_right([r[0] for r in source_stations],y)-1))
    s=source_stations
    length=s[i+1][0]-s[i][0];t=(y-s[i][0])/length
    def slope(k,j):
        return (s[k+1][j]-s[k][j])/(s[k+1][0]-s[k][0])
    def tangent(k,j):
        if k==0:return slope(0,j)
        if k==len(s)-1:return slope(k-1,j)
        a,b=slope(k-1,j),slope(k,j)
        return 2*a*b/(a+b) if a*b>0 else 0.
    return [(2*t**3-3*t*t+1)*s[i][j]+(t**3-2*t*t+t)*length*tangent(i,j)
            +(-2*t**3+3*t*t)*s[i+1][j]+(t**3-t*t)*length*tangent(i+1,j) for j in (1,2,3)]


rows=[]
ys=sorted(set([-73.5,64.5,-71,-26,-25.7,-25.4,36,38,38.8,39,55,56.4,57,63]+list(range(-73,65))))
for y in ys:
    w,lo,hi=hull(y); half=w/2+linear(y,stations)[0]
    seam=lo+min(5.1,(hi-lo)*.16)
    # An indentation below the yoke takes effect only inside its transverse footprint.
    relief=linear(y,[(36,0),(38.8,1),(56.4,1),(57,0)])[0]
    inner_lo=lo+max(0,30.1-lo)*relief
    # Shelf for the battery with a fitted aft stop at the inner end of the socket.
    inner_hi=min(seam+.36,21.28) if y<=-25.7 else seam+.36
    if -28<=y<=-25.7:inner_hi=21.28
    carrier=linear(y,[(37.6,0),(39.0,1),(45.0,1),(46.2,0)])[0]
    inner_lo+=max(0,32.15-inner_lo)*carrier
    inner_hi=max(inner_hi,inner_lo+.45)
    # At the very nose, seat the underside of the nose insert on the lip.
    if y>62.9:inner_hi=min(inner_hi,37.38)
    inner_lo=min(inner_lo,inner_hi-.32)
    # Keep outer edge just below the seam; extend the hidden land into the gasket.
    side=[(0,inner_lo),(half*.46,inner_lo),(half*.58,inner_lo),
          (half*.68,lo+.20),(half-2.30,lo+.28),(half-1.27,lo+1.12),
          (half-.59,seam-1.0),(half-.53,seam-.20),(half-1.23,seam-.20),
          (half-1.38,seam+.36),(half-2.5,seam+.36),(min(13.0,half-3.2),inner_hi)]
    outline=side+[(0,inner_hi)]+[(-x,z) for x,z in reversed(side[1:])]
    rows.append([(x*M,y*M,z*M) for x,z in outline])
chassis=bpy.data.objects['Shell.lower_chassis']
loft(chassis,rows,[casting],[[0]*len(rows[0]) for _ in rows[:-1]],26)


def new_part(name,parent):
    obj=bpy.data.objects.new(name,bpy.data.meshes.new(name))
    group.objects.link(obj);obj.parent=parent
    return obj


def lug(name,segments):
    # Rounded rectangular mounting shoe with different widths at the two ends.
    rows=[]
    for z,x,y,w,d in segments:
        r=min(w,d)*.25
        row=[]
        for sx,sy,start in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
            for j in range(5):
                a=radians(start+j*22.5)
                row.append(((x+sx*(w/2-r)+r*cos(a))*M,(y+sy*(d/2-r)+r*sin(a))*M,z*M))
        rows.append(row)
    loft(new_part(name,root),rows,[casting],[[0]*20 for _ in rows[:-1]])


for sign,side in ((1,'R'),(-1,'L')):
    lug('Seat.rear_foot.'+side,[(14.4,sign*15,-55,6.4,12),(16.1,sign*14.7,-55,7.6,13.7),
                                (18,sign*13.4,-55,8.3,15.2)])
    lug('Seat.rear_hinge.'+side,[(14.5,sign*16.65,-32,3.3,6.6),(16.8,sign*15.20,-32,6.0,9.1),
                                (20.0,sign*13.8,-32,7.0,10.8)])
# Centered internal seats secure the service pack and fascia with a perimeter reveal.
lug('Seat.battery_stop',[(25,0,-25.7,12,2.0),(35,0,-25.7,12,2.0)])
lug('Seat.nose_insert',[(39,0,63.2,11,1.6),(43,0,63.2,11,1.6)])


def turned(obj,profile,materials,fluting=False):
    n=96
    rings=[]; strips=[]
    for z,r,mat in profile:
        ring=[]
        for j in range(n):
            a=TAU*j/n
            # Interrupted annular recess in the top of the rotor bell.
            recess=.47*(max(0,cos(8*a))**.48) if fluting and 5.02<r<6.04 and z>9 else 0
            ring.append((r*cos(a)*M,r*sin(a)*M,(z-recess)*M))
        rings.append(ring)
        strips.append([mat]*n)
    loft(obj,rings,materials,strips[:-1],27)


for code in ('FR','FL','RR','RL'):
    motor=bpy.data.objects['Motor.'+code]
    turned(motor,[(0,5.55,0),(.22,6.35,0),(.71,7.17,0),(1.14,7.42,0),
           (1.36,7.46,0),(1.54,7.29,1),(1.8,7.29,1),(2.00,7.45,0),
           (8.17,7.48,0),(8.52,7.46,0),(8.76,7.26,1),(9.03,7.25,1),
           (9.22,7.44,2),(9.62,7.44,2),(10.1,7.13,2),(10.31,6.72,0),
           (10.32,6.20,0),(10.17,5.92,1),(10.05,5.24,1),(10.34,4.91,0),
           (10.56,4.45,2),(10.69,3.64,2)], [bell,deep,lip],True)
    turned(bpy.data.objects['Propeller.cap.'+code],[(0,3.54,1),(.14,4.09,1),(.50,4.16,1),
           (.62,4.04,0),(.85,4.13,0),(1.78,4.12,0),(2.01,3.96,0),(2.17,3.68,0),
           (2.21,3.52,2),(2.15,3.36,2),(2.18,3.23,0),(2.23,2.94,0)],
           [titanium,deep,lip])
    for i,sign in ((1,1),(2,-1)):
        obj=bpy.data.objects[f'Propeller.blade.{code}.{i}']
        original=[v.co.copy()/M for v in obj.data.vertices]
        sections=[]
        for k in range(0,len(original),6):
            section=original[k:k+6]
            w=(section[3].y-section[0].y)/2
            sections.append((abs(section[0].x),(section[0].y+section[3].y)/2,w))
        rows=[]
        for j in range(37):
            dist=sections[-1][0]*j/36
            mid,w=linear(dist,sections)
            t=j/36
            scale=.93+.07*t
            # A closed cambered section, with a rounded leading edge and tapered trailing edge.
            ring=[]
            for q in range(28):
                theta=TAU*q/28
                u=cos(theta)
                thickness=(.34-.11*t)*sin(theta)*(1+.32*u)
                camber=.14*(1-u*u)-.06*u
                ring.append((sign*dist*M,(mid+w*u*scale)*M,(camber+thickness)*M))
            rows.append(ring)
        loft(obj,rows,[blade_mat],[[0]*28 for _ in rows[:-1]],36)

scene.frame_set(1)
versions['v04']=widths(group)
print('WIDTH',versions,flush=True)
# Check reference files for all frames, including intermediate blade parking angles.
report=audit(group,range(1,122))
all_contacts=set(tuple(pair) for row in report for pair in row['contacts'])
groups={str(row['frame']):row['groups'] for row in report if len(row['groups'])!=1}
print('DISCONNECTED',list(groups.items())[:1],flush=True)
print('ENVELOPES',report[0]['size_mm'],report[-1]['size_mm'],flush=True)
saved={n:tuple(bpy.data.objects[n].matrix_world.translation) for n in bpy.data.objects.keys() if n.startswith('Hinge.axis.')}
baseline=json.loads((ROOT/'measurements/v03-attachment-baseline.json').read_text())
known=set(tuple(p) for row in baseline for p in row['contacts'])
added=sorted(all_contacts-known)
print('NEW CONTACTS',added,flush=True)
if '--inspect' in sys.argv:
    from check_v04_assembly import world_solids,local_meshes
    ss=world_solids(local_meshes(group),{})
    a,b=ss['Gimbal.rear_carrier'],ss['Shell.lower_chassis']
    print('Carrier intersections on lower casting (mm):',sorted({tuple(round(k*1000,2) for k in b.vertices[i]) for _,j in a.tree.overlap(b.tree) for i in b.faces[j]}))
    if '--preview' in sys.argv:
        scene.render.resolution_percentage=55
        scene.camera=bpy.data.objects['Studio.camera.three-quarter']
        scene.render.filepath=str(ROOT/'measurements/v04-draft.png')
        bpy.ops.render.render(write_still=True)
    sys.exit(0)
assert not groups,'Disconnected surfaces'
required=set()
def require(a,b): required.add(tuple(sorted((a,b))))
for side in ('L','R'):
    for seat,attached in [('rear_foot','Leg.rear.'),('rear_hinge','Hinge.mount.R')]:
        name=f'Seat.{seat}.{side}'
        require(name,attached+side)
        require(name,'Shell.lower_chassis')
    for prefix in ('F','R'):
        code=prefix+side
        require('Arm.'+code,'Motor.'+code)
        require('Motor.'+code,'Propeller.cap.'+code)
        for i in (1,2): require('Propeller.cap.'+code,f'Propeller.blade.{code}.{i}')
for row in report:
    missing=required-set(map(tuple,row['contacts']))
    assert not missing,(row['frame'],missing)
for a,b in added:
    if a.startswith('Seat.') or b.startswith('Seat.'):
        other=b if a.startswith('Seat.') else a
        assert other.startswith(('Shell.','Battery.','Hinge.mount.R','Leg.rear.','Seat.')),(a,b)
    else:
        assert 'Shell.lower_chassis' in (a,b),(a,b)
        other=b if a=='Shell.lower_chassis' else a
        assert other.startswith(('Gimbal.yaw_boss','Shell.','Hinge.mount.','Leg.rear.','Battery.')),(a,b)
expected=json.loads((ROOT/'measurements/v01-audit.json').read_text())['dimensions_mm']
for row,k in [(report[0],'1-all'),(report[-1],'121-all')]:
    assert max(abs(a-b) for a,b in zip(row['size_mm'],expected[k]))<.65,(row['size_mm'],expected[k])
assert max(abs(w-versions['v01'][y]) for y,w in versions['v04'].items())<.25
blend=ROOT/'blender/drone-v04.blend'
glb=ROOT/'exports/drone-v04.glb'
assert not blend.exists() and not glb.exists()
root.name='Drone.V04';group.name='V04 | Aircraft'
bpy.ops.object.select_all(action='DESELECT')
for obj in group.objects:obj.select_set(True)
pending=ROOT/'exports/pending-v04.glb'
bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
pending.rename(glb)
(ROOT/'measurements/v04-audit.json').write_text(json.dumps({'top_widths_mm':versions,'open_mm':report[0]['size_mm'],'folded_mm':report[-1]['size_mm'],'checked_frames':len(report),'animated_controls_matching_v01':len(animated),'required_connections_per_frame':len(required),'mesh_count':len(report[0]['groups'][0]),'disconnected_frames':groups,'new_contacts':added,'hinge_axis_centers_m':saved},indent=2)+'\n')
