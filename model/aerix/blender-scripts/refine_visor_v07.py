"""Front fascia reference pass: continuous twin borders and layered stereo optics."""
import bpy,math,ast,bmesh,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v06.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for node in ast.parse((ROOT/'scripts/blender/polish_exterior_v05.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['material','finish','ring','cyl','box','curve']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
for o in list(bpy.data.objects):
 if o.name=='FRONT_VISOR' or o.name.startswith('STEREO_'):bpy.data.objects.remove(o,do_unlink=True)
FRAME=material('Visor satin graphite frame',(.032,.035,.038),.65,.28)
EDGE=material('Visor edge highlight',(.12,.13,.14),.8,.23)
PANEL=material('Continuous smoked visor',(.004,.005,.007),.32,.21)
BLACK=material('Optical anodized rings',(.007,.009,.011),.48,.24)
DARK=material('Deep optical aperture',(.001,.002,.003),0,.24)
COAT=material('Stereo blue green multilayer coating',(.013,.032,.038),.62,.11)
GLASS=material('Stereo central convex element',(.009,.023,.03),.42,.075)
# Rounded rectangle, with subdivided straight spans to support the gentle front bow.
def outline(w,h,r):
 pts=[]
 centers=[(w/2-r,h/2-r),(-w/2+r,h/2-r),(-w/2+r,-h/2+r),(w/2-r,-h/2+r)]
 for k,(x,z) in enumerate(centers):
  for j in range(13):
   a=(k*90+j*90/12)*math.pi/180;pts.append((x+r*math.cos(a),z+r*math.sin(a)))
  nx,nz=centers[(k+1)%4];a=(k+1)*math.pi/2;end=(nx+r*math.cos(a),nz+r*math.sin(a));start=pts[-1]
  for j in range(1,13):pts.append((start[0]+(end[0]-start[0])*j/13,start[1]+(end[1]-start[1])*j/13))
 return pts

def pos(x,z,y):return (x,y+.0025*(abs(x)/.061)**6,.0815+z+.0009*(abs(x)/.061)**2)
def meshob(name,vs,fs,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);finish(o,name,mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();return o
outer=outline(.123,.027,.009);inner=outline(.115,.0205,.007)
n=len(outer);vs=[pos(x,z,-.146) for x,z in outer]+[pos(x,z,-.1465) for x,z in inner]+[pos(x,z,-.138) for x,z in outer]+[pos(x,z,-.138) for x,z in inner];fs=[]
for i in range(n):
 j=(i+1)%n;fs.extend([(i,j,n+j,n+i),(i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i),(2*n+j,2*n+i,3*n+i,3*n+j)])
frame=meshob('FRONT_VISOR_FRAME',vs,fs,FRAME);m=frame.modifiers.new('Fine frame edge radius','BEVEL');m.width=.00035;m.segments=3
# Narrow continuous perimeter lines frame the inset, including rounded end returns.
curve('VISOR_OUTER_BORDER',[pos(x,z,-.14625) for x,z in outer],.00020,EDGE,root,True)
curve('VISOR_INNER_BORDER',[pos(x,z,-.14665) for x,z in inner],.00017,BLACK,root,True)
# Closed backplate with two real lens cavities.
vs=[pos(x,z,-.144) for x,z in inner]+[pos(x,z,-.136) for x,z in inner]
fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
plate=meshob('FRONT_VISOR',vs,fs,PANEL)
for sign in [-1,1]:
 x=sign*.044;z=.0805
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.0075,depth=.025,location=(x,-.143,z),rotation=(math.pi/2,0,0));cut=bpy.context.object;bpy.context.view_layer.objects.active=plate
 m=plate.modifiers.new('Lens pocket','BOOLEAN');m.operation='DIFFERENCE';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)
 ring('STEREO_SOCKET_'+str(sign),(x,-.140,z),.00745,.0063,.008,BLACK,axis='Y')
 for i,(r,ri,y) in enumerate([(.0072,.00635,-.1446),(.0059,.00505,-.1441),(.00465,.0039,-.1438)]):ring('STEREO_RETAINER_'+str(sign)+'_'+str(i),(x,y,z),r,ri,.00045,BLACK,axis='Y')
 cyl('STEREO_BACKING_'+str(sign),(x,-.138,z),.0062,.0005,DARK,axis='Y')
 # Nested convex optical surfaces avoid the old flat disc/button appearance.
 for k,(r,dep,y,mat) in enumerate([(.00505,.00075,-.1429,COAT),(.0037,.0012,-.1433,GLASS)]):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(x,y,z));o=bpy.context.object;o.scale=(r,dep,r);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'STEREO_GLASS_'+str(sign)+'_'+str(k),mat)
# Dark central optical aperture with a curved reflective surface.
PUPIL=material('Stereo central pupil',(.0015,.004,.006),.3,.075)
for sign in [-1,1]:
 x=sign*.044;z=.0805
 ring('STEREO_INNER_OPTICAL_RING_'+str(sign),(x,-.14413,z),.00275,.00248,.00010,BLACK,axis='Y')
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(x,-.14442,z));o=bpy.context.object;o.scale=(.00185,.00020,.00185);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'STEREO_PUPIL_'+str(sign),PUPIL)
# LED tucked beneath the upper lip.
led=bpy.data.objects['STATUS_LIGHT'];led.location=(0,-.1468,.0907);led.scale.x=.88
p=led.data.materials[0].node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(.55,.8,1,1);p.inputs['Emission Strength'].default_value=2
# Small frontal softbox produces physically rendered catchlights in the tiny optics.
d=bpy.data.lights.new('OPTICAL_CATCHLIGHT','AREA');d.energy=.035;d.shape='RECTANGLE';d.size=.022;d.size_y=.045
o=bpy.data.objects.new('OPTICAL_CATCHLIGHT',d);s.collection.objects.link(o);o.location=(-.11,-.31,.23);o.rotation_euler=(Vector((0,-.144,.08))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('CAM_visor');d.type='ORTHO';d.ortho_scale=.151;o=bpy.data.objects.new('CAM_visor',d);s.collection.objects.link(o);o.location=(.055,-.38,.165);o.rotation_euler=(Vector((0,-.137,.089))-o.location).to_track_quat('-Z','Y').to_euler()
word=bpy.data.objects['AERIX_WORDMARK'];m=word.modifiers.new('Flush printed wordmark','SHRINKWRAP');m.target=bpy.data.objects['BODY_SHELL_TOP'];m.wrap_method='NEAREST_SURFACEPOINT';m.offset=.000045
s.camera=bpy.data.objects['CAM_hero'];bpy.data.objects['STUDIO_GROUND'].hide_render=False;s.cycles.samples=32;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v07.blend'))
preview='--preview' in sys.argv
if preview:s.render.resolution_percentage=70;s.cycles.samples=16
for name in (['visor'] if preview else ['visor','hero']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v07'/('preview.png' if preview else name+'.png'));bpy.ops.render.render(write_still=True)
print('V07_COMPLETE')
