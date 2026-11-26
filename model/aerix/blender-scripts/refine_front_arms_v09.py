"""Matched front arm assemblies from the approved right/left motor close-ups."""
import bpy,math,ast,bmesh,re,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v08.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for node in ast.parse((ROOT/'scripts/blender/polish_exterior_v05.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['material','finish','ring','curve','box','cyl','grain']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
CARBON=material('V09 fine matte blade composite',(.006,.007,.009),.05,.43)
grain(CARBON,320,.12,.000022,(.40,.47));CARBON.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.3
POD=material('V09 satin molded graphite',(.009,.011,.013),.22,.32);grain(POD,460,.12,.000028,(.29,.37))
ALLOY=material('V09 satin turned motor alloy',(.30,.32,.34),.88,.3);grain(ALLOY,650,.10,.000018,(.25,.32));p=ALLOY.node_tree.nodes.get('Principled BSDF');a=p.inputs.get('Anisotropic');
if a:a.default_value=.5
EDGE=material('V09 machined edge',(.45,.47,.49),.9,.23)
CAP=material('V09 titanium arm cap',(.29,.275,.248),.73,.4);grain(CAP,400,.12,.00003,(.35,.43))
COPPER=material('V09 recessed copper windings',(.37,.13,.034),.78,.27)
GOLD=material('V09 champagne blade tip',(.52,.385,.22),.65,.33)
DARK=material('V09 deep recess',(.0025,.003,.004),.05,.43)
BOLT=material('V09 fastener gunmetal',(.042,.049,.055),.8,.25)
RUBBER=material('V09 foot grip',(.004,.005,.006),0,.65)

def mesh(name,vs,fs,mat,parent=root,bevel=0,sub=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);s.collection.objects.link(ob);ob.parent=parent;me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 if sub:m=ob.modifiers.new('Continuous molded surface','SUBSURF');m.levels=sub
 if bevel:m=ob.modifiers.new('Small machined radius','BEVEL');m.width=bevel;m.segments=3
 if not sub:ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return ob

def lathe(name,profile,loc,mat,parent,closed=True):
 n=96;vs=[(loc[0]+r*math.cos(j*math.tau/n),loc[1]+r*math.sin(j*math.tau/n),z) for r,z in profile for j in range(n)];fs=[]
 for k in range(len(profile) if closed else len(profile)-1):
  kk=(k+1)%len(profile)
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,kk*n+q,kk*n+j))
 return mesh(name,vs,fs,mat,parent,.00015)

def capsule(name,length,width,z0,z1,mat,parent):
 r=width/2;c=length/2-r;pts=[]
 for sign,start in [(1,-math.pi/2),(-1,math.pi/2)]:
  for j in range(17):a=start+j*math.pi/16;pts.append((sign*c+r*math.cos(a),r*math.sin(a)))
 n=len(pts);vs=[(x,y,z) for z in [z0,z1] for x,y in pts];fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 return mesh(name,vs,fs,mat,parent,.00028)

for tag,sign in [('FL',-1),('FR',1)]:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];prop=bpy.data.objects['PROPELLER_'+tag];hinge=arm.location.copy();motor=Vector((sign*.165,-.140,0));out=Vector((sign,0,0));tan=Vector((-out.y,out.x,0))
 # Only the two front arms are replaced. Retain the named hinge and rotor roots.
 for ob in list(bpy.data.objects):
  if ob.parent==prop or (re.search('_'+tag+r'(?:_|$)',ob.name) and ob.name.startswith(('MOTOR_','COLLAR_','WINDING_','LANDING_FOOT_','FOOT_PAD_'))) or ob.name in ['ARM_'+tag,'ARM_INLAY_'+tag]:bpy.data.objects.remove(ob,do_unlink=True)
 prop.location.z=.117-hinge.z
 def attach(ob):ob.parent=arm;ob.matrix_parent_inverse=Matrix.Translation(-hinge);return ob
 # Tapered dark structural arm and a chamfered satin cap.
 direction=(motor-Vector((hinge.x,hinge.y,0))).normalized();across=Vector((-direction.y,direction.x,0));start=Vector((hinge.x,hinge.y,0))+direction*.008;end=motor-direction*.017
 for iscap in [False,True]:
  vs=[];rows=[(0,.027),(.08,.026),(.88,.022),(1,.023)]
  for t,w in rows:
   center=start.lerp(end,t)
   if iscap:profile=[(-w*.40,.0905), (w*.40,.0905),(w*.48,.0888),(w*.48,.0875),(-w*.48,.0875),(-w*.48,.0888)]
   else:profile=[(-w*.48,.088),(w*.48,.088),(w*.50,.084),(w*.47,.063),(-w*.47,.063),(-w*.50,.084)]
   for xx,z in profile:v=center+across*xx;vs.append((v.x,v.y,z))
  n=6;fs=[tuple(range(n-1,-1,-1)),tuple((len(rows)-1)*n+j for j in range(n))]
  for k in range(len(rows)-1):
   for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
  attach(mesh(('ARM_INLAY_' if iscap else 'ARM_')+tag,vs,fs,CAP if iscap else POD,bevel=.0007))
 # One continuous housing flows into an outboard landing leg with a scooped underside.
 levels=[(.086,0,.0176,.0176),(.084,0,.0180,.0180),(.075,0,.0186,.0182),(.066,0,.018,.018),(.063,0,.0175,.0175),(.061,.003,.015,.014),(.060,.007,.011,.011),(.058,.010,.008,.008),(.055,.012,.006,.0065),(.050,.012,.0055,.0055),(.019,.012,.0045,.0038),(.0135,.012,.0044,.0037),(.0128,.012,.0041,.0035)]
 n=40;vs=[]
 for z,offset,ru,rv in levels:
  for j in range(n):
   a=j*math.tau/n;power=1 if z>=.061 else .45 if z<=.05 else .45+.55*(z-.05)/.011
   cu=math.copysign(abs(math.cos(a))**power,math.cos(a));sv=math.copysign(abs(math.sin(a))**power,math.sin(a))
   v=motor+out*(offset+ru*cu)+tan*(rv*sv);vs.append((v.x,v.y,z))
 fs=[tuple(range(n-1,-1,-1)),tuple((len(levels)-1)*n+j for j in range(n))]
 for k in range(len(levels)-1):
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
 attach(mesh('MOTOR_BASE_'+tag,vs,fs,POD,sub=2))
 foot=motor+out*.012;pad=box('FOOT_PAD_'+tag,(foot.x,foot.y,.0127),(.0082,.0068,.0012),RUBBER,bevel=.0008);attach(pad)
 # Hollow motor bell. The windings are recessed below the ventilated crown.
 profile=[(.0165,.086),(.0175,.0865),(.0181,.088),(.0182,.091),(.0182,.103),(.0180,.1065),(.0177,.108),(.0156,.108),(.0155,.1055),(.0155,.088)]
 attach(lathe('MOTOR_'+tag,profile,motor,ALLOY,root))
 for name,z,ro,ri,d,mat in [('SEAL',.0855,.0179,.0167,.0009,DARK),('LOWER_RIM',.0878,.01825,.0175,.00055,EDGE),('TURN_LINE',.090,.0183,.01805,.00022,DARK),('TOP_LINE',.1057,.0182,.0178,.00035,EDGE),('CROWN',.1085,.0184,.0158,.0012,EDGE)]:attach(ring('MOTOR_'+name+'_'+tag,(motor.x,motor.y,z),ro,ri,d,mat))
 attach(cyl('MOTOR_STATOR_BASE_'+tag,(motor.x,motor.y,.098),.0148,.002,DARK))
 for j in range(12):
  a=j*math.tau/12;rad=Vector((math.cos(a),math.sin(a),0));tg=Vector((-math.sin(a),math.cos(a),0));center=motor+rad*.012;center.z=.1023
  ob=box('MOTOR_POLE_'+tag+'_'+str(j),center,(.003,.004,.005),DARK,bevel=.00035);ob.rotation_euler.z=a;attach(ob)
  for k in range(4):
   pts=[]
   for q in range(24):
    t=q*math.tau/24;v=center+rad*((k-1.5)*.0006)+tg*(.0018*math.cos(t))+Vector((0,0,.0025*math.sin(t)));pts.append(tuple(v))
   attach(curve('WINDING_'+tag+'_'+str(j)+'_'+str(k),pts,.00026,COPPER,root,True))
 # Six swept crown spokes surround six broad open vents.
 for j in range(6):
  a=j*math.tau/6;outline=[(.0065,a-.24),(.0172,a-.13),(.0172,a+.16),(.0065,a+.30)];vs=[]
  for z in [.1074,.109]:
   for r,t in outline:vs.append((motor.x+r*math.cos(t),motor.y+r*math.sin(t),z))
  fs=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)];attach(mesh('MOTOR_CROWN_SPOKE_'+tag+'_'+str(j),vs,fs,ALLOY,bevel=.0004))
 attach(cyl('MOTOR_HUB_'+tag,(motor.x,motor.y,.110),.0076,.005,BOLT))
 attach(ring('MOTOR_BEARING_SEAL_'+tag,(motor.x,motor.y,.113),.0062,.0038,.0008,DARK))
 attach(cyl('MOTOR_SHAFT_'+tag,(motor.x,motor.y,.1145),.0034,.006,EDGE))
 # Two folding blade roots and a low capsule-shaped clamp.
 for x in [-.010,.010]:cyl('PROP_FOLD_ROOT_'+tag,(x,0,0),.0052,.0028,POD,prop)
 capsule('PROP_BRIDGE_'+tag,.033,.0098,.0013,.0041,BOLT,prop)
 capsule('PROP_BRIDGE_INSET_'+tag,.028,.0068,.0040,.0043,DARK,prop)
 for i,x in enumerate([-.010,0,.010]):
  ring('PROP_COUNTERSINK_'+tag+'_'+str(i),(x,0,.0045),.00255,.0017,.00055,EDGE if i!=1 else BOLT,prop)
  cyl('PROP_BOLT_'+tag+'_'+str(i),(x,0,.0045),.00175,.0007,BOLT,prop)
  cyl('PROP_HEX_SOCKET_'+tag+'_'+str(i),(x,0,.00491),.00085,.00012,DARK,prop,vertices=6)
 # Swept, nearly straight leading edge and a broader root flare, with a thin airfoil.
 stations=[(.006,.0035,-.0035),(.011,.0045,-.0045),(.018,.0042,-.006),(.024,.005,-.014),(.033,.0058,-.022),(.046,.006,-.0225),(.064,.0055,-.020),(.081,.0048,-.016),(.091,.004,-.0108),(.0936,.0037,-.0095),(.0943,.0036,-.0092),(.0951,.0034,-.0089),(.0958,.0031,-.0083),(.0975,.002,-.007),(.0995,-.001,-.004),(.1,-.0024,-.0026)]
 hand=1 if tag=='FL' else -1;n=24
 for k in range(2):
  flip=1 if k==0 else -1;vs=[]
  for r,lead,trail in stations:
   chord=(lead-trail)/2;center=(lead+trail)/2;pitch=hand*math.radians(10-6*r/.1)
   for j in range(n):
    a=j*math.tau/n;yy=center+chord*math.cos(a);zz=.00055*math.sin(a)+.00048*(1-math.cos(a)**2)
    y=yy*math.cos(pitch)-zz*math.sin(pitch);z=yy*math.sin(pitch)+zz*math.cos(pitch);vs.append((flip*r,flip*hand*y,z))
  fs=[];mats=[]
  for st in range(len(stations)-1):
   for j in range(n):
    q=(j+1)%n;fs.append((st*n+j,st*n+q,(st+1)*n+q,(st+1)*n+j))
    r=stations[st][0];inlay=r>=.0936 and not (.0951<=r<.0958) and j not in [0,11,12,23];mats.append(1 if inlay else 0)
  fs.extend([tuple(range(n-1,-1,-1)),tuple((len(stations)-1)*n+j for j in range(n))]);mats.extend([0,0])
  ob=mesh('BLADE_'+tag+'_'+str(k),vs,fs,CARBON,prop,sub=2);ob.data.materials.append(GOLD)
  for p,mi in zip(ob.data.polygons,mats):p.material_index=mi

# Review cameras include the complete front rotor and leg at both sides.
for name,loc,target,scale in [('front_right',(.34,-.35,.30),(.155,-.14,.076),.285),('front_left',(-.34,-.35,.30),(-.155,-.14,.076),.285),('motor_detail',(.26,-.30,.26),(.165,-.14,.103),.10)]:
 d=bpy.data.cameras.new('CAM_'+name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;bpy.data.objects['STUDIO_GROUND'].hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v09.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=20;s.render.resolution_percentage=70
for name in (['front_right','motor_detail'] if preview else ['hero','front_right','front_left','motor_detail']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v09'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V09_COMPLETE')
