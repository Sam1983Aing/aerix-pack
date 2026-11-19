"""Model the Basalt gimbal and a hollow lens barrel on the approved V04 axes."""
from pathlib import Path
import json
import math
import sys
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_v04_assembly import audit
from check_v05_gimbal import check_contacts

assert Path(bpy.data.filepath).resolve() == ROOT/'blender/drone-v04.blend'
scene = bpy.context.scene
scene.frame_set(1)
group = bpy.data.collections['V04 | Aircraft']
get = bpy.data.objects.__getitem__
pitch, roll, yaw = (get('Gimbal.'+axis) for axis in ('pitch','roll','yaw'))
turn = math.tau
segments = 96


def finish(name,color,metal,rough,ior=1.5,transmission=0,coat=0):
    mat=bpy.data.materials.new('Basalt | '+name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    shader=mat.node_tree.nodes['Principled BSDF']
    for key,value in [('Base Color',mat.diffuse_color),('Metallic',metal),('Roughness',rough),
                      ('IOR',ior),('Transmission Weight',transmission),('Coat Weight',coat),
                      ('Coat Roughness',.05)]:
        shader.inputs[key].default_value=value
    return mat


case=finish('camera graphite',(.020,.021,.023),.34,.38)
trim=finish('turned black barrel',(.016,.017,.019),.70,.28)
rim=finish('machined graphite edge',(.065,.067,.070),.78,.27)
black=finish('matte interior baffles',(.005,.006,.008),.12,.52)
fork=finish('gimbal carbon casting',(.021,.022,.024),.39,.40)
hub=finish('satin pitch bearing',(.22,.225,.23),.8,.32)
front_glass=finish('front optical crown',(.90,.94,.995),0,.037,1.52,1,.18)
rear_glass=finish('inner optical crown',(.57,.89,.71),0,.032,1.61,.96,.15)
iris=finish('diaphragm leaves',(.022,.027,.03),.50,.33)
sensor=finish('receiver surface',(.012,.046,.037),.61,.21)
# A light coating gives the outer and inner reflections different colors.
front_glass.node_tree.nodes['Principled BSDF'].inputs['Coat Tint'].default_value=(.82,.71,.99,1)


def piece(name,parent):
    if name in bpy.data.objects: return get(name)
    obj=bpy.data.objects.new(name,bpy.data.meshes.new(name))
    group.objects.link(obj)
    obj.parent=parent
    bpy.context.view_layer.update()
    return obj


def loft(name,parent,rings,materials,ids=None,loop=False):
    """Rows are whole closed sections in design-space mm; keep original joint origins."""
    obj=piece(name,parent)
    inv=obj.matrix_world.inverted()
    count=len(rings[0])
    coords=[inv@(Vector(point)*.001) for ring in rings for point in ring]
    faces=[];indices=[]
    for j in range(len(rings) if loop else len(rings)-1):
        k=(j+1)%len(rings)
        for i in range(count):
            f=(i+1)%count
            faces.append((j*count+i,j*count+f,k*count+f,k*count+i))
            idx=ids[j] if ids else 0
            indices.append(idx[i] if isinstance(idx,list) else idx)
    if not loop:
        faces.extend((tuple(range(count-1,-1,-1)),tuple(range((len(rings)-1)*count,len(rings)*count))))
        indices.extend((0,ids[-1] if ids and isinstance(ids[-1],int) else 0))
    mesh=bpy.data.meshes.new(name+' · Basalt')
    mesh.from_pydata(coords,[],faces)
    for mat in materials:mesh.materials.append(mat)
    for poly,idx in zip(mesh.polygons,indices):
        poly.material_index=idx
        poly.use_smooth=len(poly.vertices)==4
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),name
    bm.to_mesh(mesh);bm.free()
    assert not mesh.validate(),name
    mesh.set_sharp_from_angle(angle=math.radians(25))
    obj.modifiers.clear()
    obj.data=mesh
    return obj


def circle(axis,center,depth,radius,n=segments):
    pts=[]
    for i in range(n):
        a=turn*i/n
        u,v=radius*math.cos(a),radius*math.sin(a)
        x,y,z=center
        pts.append({'Y':(x+u,depth,z+v),'X':(depth,y+u,z+v),'Z':(x+u,y+v,depth)}[axis])
    return pts


def turned(name,parent,axis,center,profile,mats,loop=False):
    return loft(name,parent,[circle(axis,center,d,r) for d,r,_ in profile],
                mats,[idx for _,_,idx in profile],loop)


def section(y,x,z,w,h,r):
    # Ray intersection with a rounded rectangle; equal angular sampling makes
    # the front face transition cleanly into the circular bore.
    row=[]
    for i in range(segments):
        u,v=math.cos(turn*i/segments),math.sin(turn*i/segments)
        a,b=abs(u),abs(v)
        t=min(w/2/max(1e-10,a),h/2/max(1e-10,b))
        cx,cz=w/2-r,h/2-r
        if a*t>cx and b*t>cz:
            dot=a*cx+b*cz
            t=dot+math.sqrt(max(0,dot*dot-cx*cx-cz*cz+r*r))
        row.append((x+t*u,y,z+t*v))
    return row


# Three nested pivots remain at their V01 positions. The hanger carries the
# roll spindle; the fork pivots on the spindle and the camera pivots in the fork.
turned('Gimbal.yaw_boss',yaw,'Z',(0,45,0),
       [(29.62,2.55,0),(29.70,2.94,0),(29.90,2.94,1),(30.02,3.62,1),
        (30.15,4.00,0),(30.80,4.00,0),(31.02,4.25,1),(32.82,4.25,1),
        (33.05,3.98,1)],[trim,rim])
loft('Gimbal.yaw_hanger',yaw,[section(y,0,z,w,h,r) for y,z,w,h,r in
     [(40.02,25.37,6.00,6.20,1.40),(40.55,25.40,6.60,7.12,1.65),
      (42.40,26.08,6.88,8.58,1.70),(43.34,26.92,6.45,7.30,1.45)]],[fork])
turned('Gimbal.roll_spindle',yaw,'Y',(0,0,23),
       [(41.75,2.4,0),(42.10,2.68,1),(43.06,2.68,0),(43.22,2.45,0),
        (44.55,2.45,0),(44.80,2.22,0)],[trim,rim])
loft('Gimbal.rear_carrier',roll,[section(y,0,z,w,h,r) for y,z,w,h,r in
     [(43.55,23.1,16.4,4.6,1.5),(43.80,23.1,17.6,5.45,1.7),
      (44.89,23.1,17.6,5.45,1.7),(45.12,23.1,16.9,4.95,1.6)]],[fork])
for sign,side in ((-1,'L'),(1,'R')):
    loft('Gimbal.yoke.'+side,roll,[section(y,sign*x,z,w,h,r) for y,x,z,w,h,r in
         [(43.60,8.14,23.4,2.25,4.15,.78),(44.11,8.53,23.45,2.49,5.04,.95),
          (46.10,9.35,23.1,2.12,5.45,.94),(49.10,9.96,22.38,1.91,5.92,.9),
          (51.90,10.00,22,1.98,6.13,.9),(53.10,10.00,22,1.94,5.63,.92),
          (54.25,10.00,22,1.82,4.10,.88),(54.77,10,22,1.53,2.32,.65)]],[fork])
    turned('Gimbal.trunnion.'+side,pitch,'X',(0,52,22),
           [(sign*d,r,m) for d,r,m in [(7.75,2.15,0),(8.06,2.53,0),(10.32,2.53,0),
            (10.65,2.82,0),(11.04,2.85,0),(11.15,2.74,1),(11.28,2.61,1),
            (11.31,2.39,2),(11.28,2.30,2),(11.32,2.20,2)]],[trim,rim,hub])

center=(0,0,22)
housing=[section(y,0,22,w,h,r) for y,w,h,r in
         [(46.60,14.95,12.40,2.18),(47.02,16.25,13.78,2.38),(48.04,17.10,14.48,2.48),
          (55.86,17.34,14.58,2.36),(58.49,17.34,14.58,2.32),
          (58.83,17.12,14.40,2.29),(59.09,16.70,13.99,2.16),(59.17,16.41,13.71,2.04)]]
housing.extend(circle('Y',center,y,r) for y,r in [(59.17,5.37),(58.98,5.16),(54.06,5.12),(53.86,4.91)])
loft('Camera.block',pitch,housing,[case,black],[0]*8+[1]*3)
get('Camera.lens_proxy').name='Camera.lens_barrel'
# Cross section walks out along the outside and back along the inner wall.
turned('Camera.lens_barrel',pitch,'Y',center,
       [(54.20,5.13,0),(58.64,5.21,0),(59.08,5.41,1),(59.22,5.58,0),
        (59.59,5.58,0),(59.72,5.42,0),(60.12,5.42,0),(60.26,5.54,0),
        (61.17,5.54,1),(61.41,5.36,1),(61.44,4.96,0),(61.26,4.75,2),
        (60.80,4.57,2),(60.24,4.47,0),(59.92,4.38,2),(59.68,4.37,2),
        (59.57,4.21,2),(59.20,4.21,2),(59.09,4.13,2),(58.56,4.04,2),
        (58.34,3.87,0),(58.23,3.66,0),(58.27,3.39,1),(58.32,3.22,0),
        (58.16,3.10,2),(58.09,2.81,0),(58.13,2.61,1),(58.12,2.49,0),
        (57.95,2.41,2),(57.70,2.38,2),(57.54,2.31,2),(57.19,2.30,2),
        (56.97,2.27,2),(56.84,3.70,2),
        (56.57,3.72,2),(56.46,3.59,2),(54.20,3.56,2)],[trim,rim,black],True)


def optic(name,edge,radius,front_sag,edge_thickness,rear_sag,material):
    # Two independently sampled curved surfaces joined by a ground cylindrical edge.
    profile=[]
    for j in range(23):
        t=.016+.984*j/22
        profile.append((edge+front_sag*(1-t*t),radius*t,0))
    for j in range(22,-1,-1):
        t=.016+.984*j/22
        profile.append((edge-edge_thickness-rear_sag*(1-t*t),radius*t,0))
    turned(name,pitch,'Y',center,profile,[material])


optic('Camera.front_glass',59.98,4.40,.70,.37,.16,front_glass)
optic('Camera.inner_glass',57.72,2.43,.75,.38,.16,rear_glass)
# Seven-sided iris opening with a real hole and individually shaped overlapping-leaf edges.
iris_rows=[circle('Y',center,y,r) for y,r in [(55.96,3.69),(56.44,3.76)]]
for depth,rad in [(56.43,3.28),(56.32,2.15),(56.22,1.47),(55.96,1.47)]:
    ring=[]
    for i in range(segments):
        a=turn*i/segments
        sector=(a+math.pi/7)%(turn/7)-math.pi/7
        fr=rad*math.cos(math.pi/7)/math.cos(sector) if rad<2.2 else rad
        offset=(sector+math.pi/7)/(turn/7)*.035 if depth>56 else 0
        ring.append((fr*math.cos(a),depth+offset,22+fr*math.sin(a)))
    iris_rows.append(ring)
loft('Camera.iris',pitch,iris_rows,[black,iris],[0,0,1,1,0,0],True)
turned('Camera.receiver',pitch,'Y',center,[(53.79,3.79,0),(54.04,3.79,0),
       (54.30,3.62,0),(54.55,2.85,0),(54.55,2.02,1),(54.51,1.89,1)],[black,sensor])

scene.frame_set(1)
report=check_contacts(audit(group,range(1,122)))
print('V05 geometry check',report,flush=True)
if '--preview' in sys.argv:
    from v05_detail import set_detail_camera
    set_detail_camera(scene)
    scene.render.resolution_percentage=60
    scene.cycles.samples=40
    scene.render.filepath=str(ROOT/'measurements/v05-optics-preview.png')
    bpy.ops.render.render(write_still=True)
    sys.exit(0)

blend=ROOT/'blender/drone-v05.blend'
glb=ROOT/'exports/drone-v05.glb'
assert not blend.exists() and not glb.exists()
get('Drone.V04').name='Drone.V05'
group.name='V05 | Aircraft'
bpy.ops.object.select_all(action='DESELECT')
for obj in group.objects:obj.select_set(True)
pending=ROOT/'exports/pending-v05.glb'
bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
    export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
pending.rename(glb)
(ROOT/'measurements/v05-audit.json').write_text(json.dumps(report,indent=2)+'\n')
