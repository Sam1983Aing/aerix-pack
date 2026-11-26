"""AERIX V17: rounded camera pod, smooth gimbal drums, and recessed layered optics."""
import bpy,bmesh,math,ast,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT'];gimbal=bpy.data.objects['CAMERA_GIMBAL_ROOT']
for node in ast.parse((ROOT/'scripts/blender/polish_exterior_v05.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['material','finish','grain','box','cyl','curve']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
for node in ast.parse((ROOT/'scripts/blender/refine_body_v16.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['interpolator','smooth']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shape>','exec'))
# Preserve the top-level gimbal transform; replace the old box camera, grip teeth and optics.
for ob in list(gimbal.children_recursive):bpy.data.objects.remove(ob,do_unlink=True)
Z=.038;Y=-.142
pitch=bpy.data.objects.new('CAMERA_PITCH_ROOT',None);s.collection.objects.link(pitch);pitch.parent=gimbal;pitch.location=(0,Y,Z);pitch.empty_display_size=.007
optics=bpy.data.objects.new('LENS_OPTICS_ROOT',None);s.collection.objects.link(optics);optics.parent=pitch;optics.location=(0,-.036,0);optics.empty_display_size=.005
bpy.context.view_layer.update()
def parent_keep(ob,parent):ob.parent=parent;ob.matrix_parent_inverse=parent.matrix_world.inverted();return ob
def mesh(name,vs,fs,mat,parent=pitch,bevel=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);me.materials.append(mat);parent_keep(ob,parent)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 if bevel:m=ob.modifiers.new('Small finished edge','BEVEL');m.width=bevel;m.segments=3
 return ob
POD=material('V17 satin anodized camera housing',(.021,.024,.027),.62,.30);grain(POD,750,.06,.000012,(.275,.315))
EDGE=material('V17 dark machined lens edge',(.035,.040,.044),.82,.24)
BARREL=material('V17 satin black lens barrel',(.009,.012,.014),.55,.26)
BAFFLE=material('V17 optical light trap',(.0025,.0032,.0038),.12,.42)
RUBBER=material('V17 fine gimbal seal',(.004,.005,.006),.05,.48)
SCREW=material('V17 recessed graphite fastener',(.033,.037,.040),.78,.27)
GLASS=material('V17 clear coated front optical glass',(.98,.995,.99),0,.012)
p=GLASS.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1.0;p.inputs['Specular IOR Level'].default_value=.18;p.inputs['IOR'].default_value=1.48;p.inputs['Thin Film Thickness'].default_value=0;p.inputs['Thin Film IOR'].default_value=1.34
INNER=material('V17 blue green inner optical coating',(.018,.120,.135),1.0,.055)
p=INNER.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.0;p.inputs['Coat Roughness'].default_value=.04;p.inputs['IOR'].default_value=1.48
MID=GLASS.copy();MID.name='V17 faint violet middle optical glass';p=MID.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.94,.945,.985,1);p.inputs['Thin Film Thickness'].default_value=0

def radial(name,profile,mat,parent=pitch,axis='Y',closed=True,n=160,bevel=0):
 refined=[]
 for i,a in enumerate(profile):
  refined.append(a)
  if not closed and i==len(profile)-1:continue
  b=profile[(i+1)%len(profile)];steps=max(1,math.ceil(math.hypot(b[0]-a[0],b[1]-a[1])/.00055))
  refined.extend((a[0]+(b[0]-a[0])*t/steps,a[1]+(b[1]-a[1])*t/steps) for t in range(1,steps))
 profile=refined;vs=[]
 for a,r in profile:
  for j in range(n):
   t=j*math.tau/n
   vs.append((r*math.cos(t),a,Z+r*math.sin(t)) if axis=='Y' else (a,Y+r*math.cos(t),Z+r*math.sin(t)))
 fs=[]
 for k in range(len(profile) if closed else len(profile)-1):
  q=(k+1)%len(profile)
  for j in range(n):jj=(j+1)%n;fs.append((k*n+j,k*n+jj,q*n+jj,q*n+j))
 if not closed:fs.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+j for j in range(n))])
 ob=mesh(name,vs,fs,mat,parent,bevel)
 if not closed:
  for p in list(ob.data.polygons)[-2:]:p.use_smooth=False
 return ob

# One smooth pod loft changes from a circular front throat into a subtly squared rear chamber.
sections=[(-.176,.0205,.0205,1),(-.173,.0218,.0218,1),(-.168,.0238,.0228,.97),(-.157,.0272,.0234,.88),(-.146,.0282,.0238,.85),(-.135,.0275,.0231,.86),(-.125,.0240,.0208,.93),(-.120,.0178,.0158,1),(-.118,.007,.0065,1)]
fx=interpolator([(a,x) for a,x,z,p in sections]);fz=interpolator([(a,z) for a,x,z,p in sections]);fp=interpolator([(a,p) for a,x,z,p in sections]);n=160;rows=77;vs=[]
for k in range(rows):
 y=sections[0][0]+(sections[-1][0]-sections[0][0])*k/(rows-1);rx=fx(y);rz=fz(y);pw=fp(y)
 for j in range(n):a=j*math.tau/n;c=math.cos(a);d=math.sin(a);vs.append((rx*math.copysign(abs(c)**pw,c),y,Z+rz*math.copysign(abs(d)**pw,d)))
fs=[tuple((rows-1)*n+j for j in range(n))]
for k in range(rows-1):
 for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
# Front opening, long dark lens well, and an opaque rear bulkhead.
for y,r in [(-.176,.0180),(-.153,.0180),(-.148,.0100)]:
 for j in range(n):a=j*math.tau/n;vs.append((r*math.cos(a),y,Z+r*math.sin(a)))
for ka,kb in [(0,rows),(rows,rows+1),(rows+1,rows+2)]:
 for j in range(n):q=(j+1)%n;fs.append((ka*n+j,ka*n+q,kb*n+q,kb*n+j))
fs.append(tuple((rows+2)*n+j for j in range(n-1,-1,-1)))
pod=mesh('CAMERA_HOUSING',vs,fs,POD)
for p in pod.data.polygons:
 if len(p.vertices)>4:p.use_smooth=False
# Smooth retaining bezel and restrained machined annuli; no oversized grip ribs.
radial('LENS_BARREL',[(-.1755,.0204),(-.178,.0214),(-.1828,.0218),(-.1843,.0215),(-.1847,.0209),(-.1847,.0188),(-.1840,.0174),(-.1823,.0163),(-.1760,.0163)],BARREL)
radial('LENS_OUTER_EDGE',[(-.1837,.02163),(-.1841,.02159),(-.18445,.02130),(-.18455,.0210),(-.18430,.02091),(-.18380,.02125)],EDGE)
radial('LENS_FRONT_SEAL',[(-.18472,.0203),(-.18475,.0201),(-.18475,.01992),(-.1845,.01992),(-.18448,.0203)],RUBBER)
radial('LENS_INNER_RETAINING_RING',[(-.1818,.01635),(-.1824,.0163),(-.1827,.0156),(-.1824,.01465),(-.1816,.01445),(-.1811,.01465),(-.1811,.01635)],BAFFLE,optics)
# Deep black steps and narrow highlights produce visible depth at oblique angles.
for i,(y,ro,ri) in enumerate([(-.1788,.01450,.0127),(-.1770,.01270,.0109),(-.1751,.01090,.0088),(-.1731,.00880,.0066)]):
 radial('LENS_INTERNAL_BAFFLE_'+str(i),[(y-.00045,ro),(y-.00045,ri),(y+.0012,ri),(y+.0012,ro)],BAFFLE,optics)
 radial('LENS_INTERNAL_EDGE_'+str(i),[(y-.00047,ri+.00020),(y-.0005,ri+.00009),(y-.00039,ri),(y-.00025,ri+.00018)],BARREL,optics)
# Cut fine concentric anti-reflection ribs into the wall, away from the optical aperture.
for i in range(6):
 y=-.1806+i*.00028;r=.01455
 radial('LENS_MICRO_RIB_'+str(i),[(y-.000035,r+.00010),(y,r),(y+.000035,r+.00010),(y+.000035,r+.00018),(y-.000035,r+.00018)],BAFFLE,optics,n=128)

def optical_element(name,r,y,sag,thickness,mat):
 # A spherical front cap and a flatter rear cap form a closed, finite-thickness lens.
 rings=32;n=160;vs=[];fs=[];radius=(r*r+sag*sag)/(2*sag)
 for back in [False,True]:
  vs.append((0,y+thickness if back else y,Z))
  for k in range(1,rings+1):
   rr=r*k/rings;rise=radius-math.sqrt(max(0,radius*radius-rr*rr))
   yy=y+thickness+rise*.45 if back else y+rise
   for j in range(n):a=j*math.tau/n;vs.append((rr*math.cos(a),yy,Z+rr*math.sin(a)))
 count=1+rings*n
 for j in range(n):fs.append((0,1+j,1+(j+1)%n))
 for k in range(rings-1):
  for j in range(n):q=(j+1)%n;a=1+k*n+j;b=1+k*n+q;fs.append((a,b,b+n,a+n))
 fs+=[tuple(count+i for i in reversed(f)) for f in fs.copy()]
 for j in range(n):a=1+(rings-1)*n+j;b=1+(rings-1)*n+(j+1)%n;fs.append((a,b,b+count,a+count))
 return mesh(name,vs,fs,mat,optics)
optical_element('LENS_FRONT_ELEMENT',.01440,-.18140,.00080,.00085,GLASS)
optical_element('LENS_MIDDLE_ELEMENT',.01065,-.1765,.00080,.00085,MID)
optical_element('LENS_REAR_COATED_ELEMENT',.00642,-.17240,.00220,.00165,INNER)
# Dark iris surrounds a small pupil deep inside the optical stack.
radial('LENS_APERTURE',[(-.1685,.00645),(-.1685,.00345),(-.1680,.00345),(-.1680,.00645)],BAFFLE,optics)
for j in range(9):
 a=j*math.tau/9;pts=[]
 for r,t in [(.0035,a),(.0059,a+.13),(.00615,a+.49),(.0035,a+.66)]:pts.append((r*math.cos(t),-.16858,Z+r*math.sin(t)))
 vs=pts+[(x,y+.000035,z) for x,y,z in pts];fs=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)];mesh('LENS_IRIS_LEAF_'+str(j),vs,fs,BARREL,optics)
# A small curved dark optical core carries reflections without painting a glow onto the lens.
CORE=INNER.copy();CORE.name='V17 deep optical core';p=CORE.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.0025,.008,.010,1);p.inputs['Roughness'].default_value=.055
optical_element('LENS_DEEP_OPTICAL_CORE',.00335,-.1678,.00075,.0008,CORE)
# Thin side cover seam follows the rounded chamber just behind its widest section.
pts=[];yy=-.1325;rx=fx(yy)+.000035;rz=fz(yy)+.000035;pw=fp(yy)
for j in range(160):a=j*math.tau/160;pts.append((rx*math.copysign(abs(math.cos(a))**pw,math.cos(a)),yy,Z+rz*math.copysign(abs(math.sin(a))**pw,math.sin(a))))
parent_keep(curve('CAMERA_REAR_COVER_SEAM',pts,.00012,RUBBER,root,True),pitch)
# Fixed U-shaped suspension and circular pitch motor drums.
parent_keep(box('GIMBAL_MOUNT',(0,-.111,.057),(.045,.022,.008),BARREL,root,.002),gimbal)
for sign in [-1,1]:
 side='L' if sign<0 else 'R'
 parent_keep(box('GIMBAL_YOKE_'+side,(sign*.0315,-.124,.049),(.006,.031,.025),BARREL,root,.0025),gimbal)
 radial('GIMBAL_STATOR_'+side,[(sign*x,r) for x,r in [(.0280,.010),(.0280,.0142),(.0293,.0156),(.0336,.0157),(.0352,.0152),(.0358,.0145),(.0358,.0095)]],POD,gimbal,'X')
 radial('GIMBAL_OUTER_COVER_'+side,[(sign*x,r) for x,r in [(.0357,.0144),(.0365,.0147),(.0381,.0140),(.0384,.0134),(.03845,.0131)]],BARREL,gimbal,'X',False)
 radial('GIMBAL_COVER_EDGE_'+side,[(sign*x,r) for x,r in [(.0361,.0146),(.03635,.01464),(.0365,.01448),(.03625,.01443)]],EDGE,gimbal,'X')
 radial('GIMBAL_INNER_SEAL_'+side,[(sign*x,r) for x,r in [(.0276,.0143),(.0283,.0143),(.0283,.0121),(.0276,.0121)]],RUBBER,pitch,'X')
 # Fasteners are placed on the rear of the yoke, keeping the visible camera face clean.
 ob=cyl('GIMBAL_REAR_FASTENER_'+side,(sign*.0315,-.1088,.049),.0014,.00065,SCREW,root,'Y');parent_keep(ob,gimbal)
 # Fine circular socket in the fastener head.
 radial('GIMBAL_AXLE_SEAL_'+side,[(sign*x,r) for x,r in [(.0265,.010),(.0274,.010),(.0274,.0075),(.0265,.0075)]],RUBBER,pitch,'X')
# Small real studio reflectors reveal the curvature of the coated elements.
for name,loc,energy,size,sizey,color in [('LENS_KEY_GLINT',(.010,-.30,.066),.050,.006,.008,(.82,.98,1)),('LENS_EDGE_GLINT',(.095,-.27,.064),.004,.007,.033,(1,.91,.80))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='RECTANGLE';d.size=size;d.size_y=sizey;d.color=color;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,-.177,Z))-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,target,scale in [('main_camera',(.097,-.36,.145),(0,-.146,.044),.125),('main_lens',(0,-.36,.052),(0,-.178,Z),.056),('gimbal_side',(.24,-.28,.10),(0,-.144,.042),.116),('front_camera',(0,-.43,.13),(0,-.132,.068),.190)]:
 d=bpy.data.cameras.new('CAM_'+name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];bpy.data.objects['STUDIO_GROUND'].hide_render=False;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=True
s.cycles.samples=48;s.cycles.transmission_bounces=12;s.render.resolution_percentage=100;s.render.resolution_x=1536;s.render.resolution_y=1024
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v17.blend'))
if '--preview' in sys.argv:
 s.cycles.samples=40;s.render.resolution_percentage=70
 for name in ['main_camera','main_lens','gimbal_side','front_camera']:
  s.render.resolution_x=1200 if name=='main_lens' else 1536;s.render.resolution_y=1200 if name=='main_lens' else 1024
  s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v17'/(name+'-preview.png'));bpy.ops.render.render(write_still=True)
print('V17_CAMERA_BUILD_COMPLETE',flush=True)
