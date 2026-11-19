"""Refine the landing castings in V08. All design coordinates are in open-pose mm."""
from math import cos, sin, radians
from pathlib import Path
import bpy
import bmesh
import json
import sys
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from check_v09_gear import inspect_gear

assert Path(bpy.data.filepath) == ROOT/'blender/drone-v08.blend'
scene = bpy.context.scene
scene.frame_set(1)
group = bpy.data.collections['V08 | Aircraft']
mats = bpy.data.materials
stone = mats['RILL | warm ceramic grey']
lower = mats['RILL | lower casing']
rubber = mats['RILL | graphite elastomer']
flank = mats['RILL | sloping upper shoulder']


def rounded_section(depth, width, radius):
    # Traverse the cross-section from the outside face towards the leading corner.
    pts = []
    for u,v,a in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
        for j in range(8):
            theta = radians(a+90*j/7)
            pts.append((u*(depth/2-radius)+radius*cos(theta),
                        v*(width/2-radius)+radius*sin(theta)))
    return pts


def replace_skin(obj, rings, face_material, materials):
    count = len(rings[0])
    row_count = len(rings)
    faces = []
    assignments = []
    for i in range(row_count-1):
        for j in range(count):
            k = (j+1)%count
            faces.append((i*count+j,i*count+k,(i+1)*count+k,(i+1)*count+j))
            assignments.append(face_material(i,j))
    faces.extend([tuple(reversed(range(count))),tuple(range((row_count-1)*count,row_count*count))])
    assignments.extend([0,1])
    inv = obj.matrix_world.inverted()
    data = bpy.data.meshes.new(obj.name+' · V09')
    data.from_pydata([inv @ (p*.001) for row in rings for p in row], [], faces)
    for material in materials:
        data.materials.append(material)
    for poly, idx in zip(data.polygons,assignments):
        poly.material_index = idx
        poly.use_smooth = len(poly.vertices)==4
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),obj.name
    bm.to_mesh(data)
    bm.free()
    assert not data.validate(),obj.name
    data.set_sharp_from_angle(angle=radians(34))
    obj.data = data


def front_strut(sign, side):
    motor = bpy.data.objects['Propeller.hub.F'+side].matrix_world.translation*1000
    # Along and across the outboard corner of the motor cup. A narrow flat
    # arris survives around the moulded antenna cover on its broad outside face.
    radial = Vector((sign*.8,.6,0))
    transverse = Vector((-sign*.6,.8,0))
    specs = [
        # z, inner radius, outer radius, breadth, corner, tangential offset
        (0,9.20,12.80,6.05,.95,-1.05),
        (.23,8.85,13.03,6.62,1.02,-1.05),
        (.63,8.55,13.18,7.10,1.18,-1.03),
        (.79,8.54,13.18,7.12,1.20,-1.02),
        (1.04,8.11,13.39,7.52,1.35,-1.00),
        (1.58,7.81,13.48,7.84,1.45,-.98),
        (1.81,7.73,13.50,7.90,1.48,-.96),
        (2.04,7.70,13.53,7.96,1.49,-.94),
        (4.4,7.53,13.60,8.14,1.49,-.83),
        (8.8,7.55,13.69,8.24,1.51,-.54),
        (15,7.77,13.77,8.12,1.51,-.34),
        (27,7.80,13.87,8.48,1.57,-.07),
        (34.7,7.74,13.89,8.81,1.62,.13),
        (37.6,7.60,13.89,9.04,1.67,.20),
        (37.85,7.58,13.89,9.07,1.67,.20),
        (38.09,7.53,13.88,9.10,1.68,.20),
        (39.0,7.30,13.86,9.22,1.71,.19),
        (40.1,6.90,13.83,9.46,1.76,.18),
        (41.2,6.15,13.75,9.88,1.80,.15),
        (42.3,4.69,13.69,10.53,1.93,.11),
        (43.1,2.55,13.58,11.15,2.05,.06),
        (44.2,1.10,13.48,11.40,2.05,0),
        (45.6,.65,13.40,11.12,2.05,-.05),
        (46.68,1.05,13.15,10.62,2.04,-.10),
        (47.10,2.05,12.69,9.88,2.10,-.12)]
    rings = []
    for i,(z,inner,outer,w,r,offset) in enumerate(specs):
        section = rounded_section(outer-inner,w,r)
        # Extra vertices define the two very shallow longitudinal moulding lines.
        half_flat = w/2-r
        for fraction in (-.92,-.86,-.76,0,.76,.86,.92):
            notch = .12 if i in range(6,15) and abs(fraction)==.86 else 0
            if i in (6,14) and abs(fraction)<.86: notch=.10
            section.append(((outer-inner)/2-notch,half_flat*fraction))
        rings.append([Vector((motor.x,motor.y,z))+radial*((inner+outer)/2+u)+transverse*(offset+v)
                      for u,v in section])
    # Fit the outboard mould wall to the approved airframe span. The tuck
    # remains local to the foot and all sections remain mirror symmetric.
    shift=max(p.x*sign for ring in rings for p in ring)-101.50
    for ring in rings:
        for p in ring:
            p.x-=sign*shift
            p.y-=.55+.75*max(0,1-p.z/41.0)
    def finish(i,j):
        if i<=2: return 0
        if 5<=i<=14 and j>=32:
            if j in (32,33,36,37) or i in (5,14): return 2
        return 1
    replace_skin(bpy.data.objects['Leg.front.'+side],rings,finish,[rubber,stone,flank])
    # The small optical window sits on the outer shelf, tangent to the
    # motor rim. Its entire bottom rim is seated in the shoulder casting.
    window=[]
    for z,d,w,r in ((47.01,1.80,3.96,.58),(47.11,1.80,3.96,.58),(47.17,1.57,3.68,.54)):
        center=Vector((motor.x-sign*shift,motor.y-.55,z))+radial*10.75+transverse*(-.22)
        window.append([center+radial*u+transverse*v for u,v in rounded_section(d,w,r)])
    replace_skin(bpy.data.objects['Leg.window.'+side],window,lambda i,j:i,
                 [mats['RILL | joint shadow'],rubber])



def rear_foot(sign,side):
    # A flared heel grows into the belly. The smaller elastomer sole rolls up
    # its edges and has a whole planar face on the same datum as the front toes.
    sections = [
        # height, x, y, width, fore/aft length, corner
        (0,13,-55.1,3.65,5.10,1.17),
        (.23,13,-55.1,4.00,5.60,1.32),
        (.68,13,-55.05,4.18,5.78,1.39),
        (.89,13,-55.05,4.21,5.81,1.39),
        (1.10,13,-55.07,4.65,6.35,1.47),
        (1.65,13,-55.10,4.85,6.63,1.56),
        (3.6,13,-55.25,5.13,7.02,1.58),
        (6.3,13,-55.42,5.60,7.77,1.72),
        (8.7,13,-55.5,6.19,8.64,1.94),
        (10.1,13,-55.6,7.01,9.64,2.17),
        (11.30,13,-55.7,8.16,11.00,2.63),
        (12.35,13,-55.7,8.58,11.45,2.78)]
    rings = []
    for z,x,y,w,length,r in sections:
        rings.append([Vector((sign*(x+u),y+v,z)) for u,v in rounded_section(w,length,r)])
    replace_skin(bpy.data.objects['Leg.rear.'+side],rings,
                 lambda i,j:0 if i<=2 else 1,[rubber,lower])


for sign,side in ((1,'R'),(-1,'L')):
    front_strut(sign,side)
    rear_foot(sign,side)
bpy.context.view_layer.update()
report = inspect_gear(group)
print(json.dumps(report,indent=2),flush=True)
if '--publish' in sys.argv:
    blend=ROOT/'blender/drone-v09.blend'
    glb=ROOT/'exports/drone-v09.glb'
    assert not blend.exists() and not glb.exists()
    group.name='V09 | Aircraft'
    bpy.data.objects['Drone.V08'].name='Drone.V09'
    scene.frame_set(1)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects: obj.select_set(True)
    staged=ROOT/'exports/pending-v09.glb'
    bpy.ops.export_scene.gltf(filepath=str(staged),use_selection=True,export_apply=True,
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    staged.rename(glb)
    (ROOT/'measurements/v09-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
else:
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'measurements/v09-preview.blend'))
