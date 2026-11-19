"""Seat the two matched camera covers and form a one-piece seat under each front pivot."""
from math import atan2, cos, exp, pi, radians, sin, tau
from pathlib import Path
import json
import sys
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from rill_shell import stations,T,skin
from v13_detail_views import detail_view,DETAILS

scene=bpy.context.scene
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v12.blend'
scene.frame_set(1)
group=bpy.data.collections['V12 | Aircraft']
parts=group.objects
shell=parts['Shell.moulded_fuselage']
case=bpy.data.materials['Basalt | camera graphite']
lower=bpy.data.materials['RILL | lower casing']


def project_uvs(obj,polygons,side=1):
    mesh=obj.data
    layer=mesh.uv_layers.active or mesh.uv_layers.new(name='Finish UV')
    coords=[obj.matrix_world@v.co for v in mesh.vertices]
    # Put the same point on each handed part at the same point in the grain.
    basis=obj.matrix_world.to_3x3().inverted().transposed()
    for p in polygons:
        n=basis@p.normal
        n.x*=side
        axis=max(range(3),key=lambda k:abs(n[k]))
        h,v=((1,2),(2,0),(0,1))[axis]
        orientation=1 if n[axis]>=0 else -1
        for loop in p.loop_indices:
            xyz=coords[mesh.loops[loop].vertex_index].copy()
            xyz.x*=side
            layer.data[loop].uv=(orientation*xyz[h]/.0128,xyz[v]/.0128)


def replace_loft(obj,rings,material,side,crease=36):
    count=len(rings[0])
    assert all(len(r)==count for r in rings)
    grid=[(a*count+j,a*count+(j+1)%count,(a+1)*count+(j+1)%count,(a+1)*count+j)
          for a in range(len(rings)-1) for j in range(count)]
    grid.extend((tuple(reversed(range(count))),tuple(range((len(rings)-1)*count,len(rings)*count))))
    inv=obj.matrix_world.inverted()
    mesh=bpy.data.meshes.new(obj.name+' · V13')
    mesh.from_pydata([inv@(p*.001) for r in rings for p in r],[],grid)
    mesh.materials.append(material)
    for p in mesh.polygons: p.use_smooth=len(p.vertices)==4
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),obj.name
    bm.to_mesh(mesh)
    bm.free()
    assert not mesh.validate(),obj.name
    mesh.set_sharp_from_angle(angle=radians(crease))
    obj.data=mesh
    mesh.update()
    project_uvs(obj,mesh.polygons,side)


def camera_cover(side,label):
    # Front and rear of the two covers are clear of the face and the yoke.
    # A shallow blind counterbore seats the cap on the end of its trunnion.
    profile=[(15.30,2.12),(15.33,2.40),(15.27,3.14),(15.02,3.47),
             (15.02,4.77),(15.08,5.13),(15.22,5.43),(15.42,5.60),
             (15.68,5.63),(15.89,5.52),(16.06,5.24),(16.17,4.75),
             (16.24,4.00),(16.30,3.00),(16.34,1.80),(16.36,.70)]
    pitch=parts['Gimbal.pitch'].matrix_world.translation*1000
    rings=[[Vector((side*x,pitch.y+r*cos(i*tau/96),pitch.z+r*sin(i*tau/96)))
            for i in range(96)] for x,r in profile]
    replace_loft(parts['Gimbal.pitch_cover.'+label],rings,case,side)


def soften_socket_wall():
    # Remove the V-shaped ridge at the two old bracket seats. The wall only
    # moves inward. Keep faces and UVs on the rest of the V12 housing intact.
    me=shell.data
    search=KDTree(len(me.vertices))
    for vertex in me.vertices: search.insert(vertex.co*1000,vertex.index)
    search.balance()
    changes={}
    for row in stations:
        y=row[0]
        if not -6<y<34: continue
        weight=min(1,(y+6)/13,(34-y)/11)
        weight=weight**2*(3-2*weight)
        for side in (-1,1):
            sample=[skin(row,side,v) for v in T]
            for p in sample:
                if not 23.2<p.z<36.5: continue
                blend=min(1,(p.z-23.2)/3.1,(36.5-p.z)/2.4)
                blend=blend**2*(3-2*blend)
                weights=[exp(-.5*((q.z-p.z)/4.1)**2) for q in sample]
                mean=sum(abs(q.x)*w for q,w in zip(sample,weights))/sum(weights)
                target=min(abs(p.x),mean)
                _,idx,dist=search.find(p)
                assert dist<.001
                changes[idx]=side*(abs(p.x)+(target-abs(p.x))*weight*blend)*.001
    for idx,x in changes.items(): me.vertices[idx].co.x=x
    me.update()
    local=[p for p in me.polygons if any(i in changes for i in p.vertices)]
    # On these continuous molded walls the old sharp marks emphasize individual
    # tessellation faces, especially when the camera is below the bearing.
    local_edges={tuple(sorted(k)) for p in local for k in p.edge_keys}
    for e in me.edges:
        if tuple(sorted(e.vertices)) in local_edges: e.use_edge_sharp=False
    project_uvs(shell,local)
    bpy.context.view_layer.update()


def arm_root(side,label):
    # Continue the first full-width sleeve section around the back of its
    # journal. Keep every subsequent V12 span and the motor interface exactly.
    obj=parts['Arm.F'+label]
    coords=[obj.matrix_world@v.co*1000 for v in obj.data.vertices]
    assert len(coords)==9*24
    rows=[coords[i:i+24] for i in range(0,len(coords),24)]
    pivot=parts['Hinge.axis.F'+label].matrix_world.translation*1000
    along=Vector((side*57.2,24.7,0)).normalized()
    transverse=Vector((-along.y,along.x,0))
    # The rear half of the sleeve wraps the vertical journal. Each horizontal
    # section has a circular end, so the bearing enters a flat, rolled underside.
    base=[]
    for su,sz,start in ((1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)):
        radius=1.75 if sz>0 else .82
        for j in range(6):
            a=radians(start+18*j)
            u=su*(5.35-radius)+radius*cos(a)
            z=sz*(4.40-radius)+radius*sin(a)
            base.append((u,z))
    rows[0]=[pivot+transverse*u+Vector((0,0,z)) for u,z in base]
    prefix=[]
    for theta in (.018,.12,.26,.43,.63,.85,1.07,1.27,1.44):
        prefix.append([pivot+transverse*(u*sin(theta))-along*(abs(u)*cos(theta))+
                       Vector((0,0,z)) for u,z in base])
    replace_loft(obj,prefix+rows,obj.data.materials[0],side)
    # Keep the visible journal a single smooth land between the two castings.
    # The assembly shoulders and retaining cap remain buried or above the sleeve.
    pin=parts['Hinge.pin.F'+label]
    inv=pin.matrix_world.inverted()
    for v in pin.data.vertices:
        xyz=pin.matrix_world@v.co*1000
        if 35.7<xyz.z<44.1:
            delta=Vector((xyz.x-pivot.x,xyz.y-pivot.y,0))
            delta.normalize()
            xyz.x=pivot.x+3.84*delta.x
            xyz.y=pivot.y+3.84*delta.y
            v.co=inv@(xyz*.001)
    pin.data.update()


def support(side,label,wall):
    # Each closed seat has a D-shaped footprint, a filleted nose and a blind
    # cylindrical journal pocket. Its inboard edge follows the housing wall.
    pivot=parts['Hinge.axis.F'+label].matrix_world.translation*1000
    x0=abs(pivot.x)
    y0=pivot.y
    def casting_outline(r,top_z,slope):
        row=[Vector((side*(x0+r*cos(a)),y0+r*sin(a),top_z+slope*r*cos(a)))
             for a in [-pi/2+pi*i/48 for i in range(49)]]
        def cheek(t,span):
            flare=.60*t*t
            y=y0+span*(r+flare)
            x=x0
            for _ in range(4):
                z=top_z+slope*(x-x0)
                cross=wall.ray_cast(Vector((side*.08,y*.001,z*.001)),Vector((-side,0,0)),.08)[0]
                assert cross is not None,(y,z)
                x=x0*(1-t)+(side*cross.x*1000-.55)*t
            return Vector((side*x,y,top_z+slope*(x-x0)))

        row += [cheek(i/16,1) for i in range(1,17)]
        row += [cheek(1,1-2*i/32) for i in range(1,33)]
        row += [cheek(i/16,-1) for i in range(15,0,-1)]
        return row
    rows=[casting_outline(r,z,d) for r,z,d in [
        (4.22,30.94,.115),(4.51,31.00,.115),(4.78,31.17,.115),
        (4.96,31.46,.11),(5.04,31.83,.10),(5.04,33.35,.012),
        (5.00,33.65,0),(4.88,33.87,0),(4.64,34.02,0),(4.38,34.07,0)]]
    angles=[atan2(p.y-y0,side*p.x-x0) for p in rows[-1]]
    for radius,z in [(4.07,34.07),(3.99,34.02),(3.94,33.92),
                     (3.94,32.58),(3.85,32.43),(3.47,32.38),(3.18,32.37)]:
        rows.append([Vector((side*(x0+radius*cos(a)),y0+radius*sin(a),z)) for a in angles])
    obj=parts['Hinge.socket.F'+label]
    replace_loft(obj,rows,lower,side)
    bpy.data.objects.remove(parts['Hinge.bracket.F'+label],do_unlink=True)


soften_socket_wall()
wall=BVHTree.FromObject(shell,bpy.context.evaluated_depsgraph_get())
for side,label in ((1,'R'),(-1,'L')):
    camera_cover(side,label)
    support(side,label,wall)
    arm_root(side,label)
bpy.context.view_layer.update()

from check_v13_joints import check_joints
report=check_joints(group)
print('Joint review',json.dumps(report),flush=True)
if '--preview' in sys.argv:
    for name in DETAILS:
        detail_view(scene,name)
        scene.render.resolution_percentage=65
        scene.cycles.samples=20
        scene.render.filepath=str(root/f'measurements/v13-preview-{name}.png')
        bpy.ops.render.render(write_still=True)
else:
    from check_v09_gear import inspect_gear
    from v10_alignment import alignment
    report['fold']=inspect_gear(group)
    report['optical_center_xz_mm']=alignment(parts)
    reference=json.loads((root/'measurements/v12-native-audit.json').read_text())
    for k,value in report['fold'].items():
        if k!='meshes': assert value==reference[k],(k,value,reference[k])
    assert report['fold']['meshes']==reference['meshes']-2
    assert all(max(map(abs,v))<.001 for v in report['optical_center_xz_mm'].values())
    blend=root/'blender/drone-v13.blend'
    glb=root/'exports/drone-v13.glb'
    assert not blend.exists() and not glb.exists()
    scene.frame_set(1)
    group.name='V13 | Aircraft'
    parts['Drone.V12'].name='Drone.V13'
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    pending=root/'exports/pending-v13.glb'
    bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
        export_texcoords=True,export_tangents=True,export_image_format='AUTO',
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
    (root/'measurements/v13-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
