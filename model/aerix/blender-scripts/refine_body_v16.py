"""V16: longitudinal fairing, restrained shoulders, and fitted fascia."""
import bpy,math,ast,bmesh,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for filename,names in [('polish_exterior_v05.py',['material','finish','ring','curve','box','cyl']),('refine_front_arms_v09.py',['mesh']),('refine_visor_v07.py',['outline'])]:
 for node in ast.parse((ROOT/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
TI=bpy.data.materials['Titanium — provisional'];BLACK=bpy.data.materials['Graphite'];FRAME=bpy.data.materials['Visor satin graphite frame'];PANEL=bpy.data.materials['Continuous smoked visor'];DARK=bpy.data.materials['Deep optical aperture']

def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def interpolator(points):
 xs,ys=zip(*points);n=len(xs);h=[xs[i+1]-xs[i] for i in range(n-1)];d=[(ys[i+1]-ys[i])/h[i] for i in range(n-1)];m=[d[0]]+[0]*(n-2)+[d[-1]]
 for i in range(1,n-1):
  if d[i-1]*d[i]>0:
   w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1];m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
 def sample(x):
  if x<=xs[0]:return ys[0]
  if x>=xs[-1]:return ys[-1]
  i=next(i for i in range(n-1) if xs[i]<=x<xs[i+1]);t=(x-xs[i])/h[i]
  return (2*t**3-3*t*t+1)*ys[i]+(t**3-2*t*t+t)*h[i]*m[i]+(-2*t**3+3*t*t)*ys[i+1]+(t**3-t*t)*h[i]*m[i+1]
 return sample
width=interpolator([(-.1355,.0672),(-.123,.0690),(-.094,.0727),(-.058,.0720),(-.008,.0657),(.036,.0631),(.060,.0625),(.087,.0545),(.112,.0490),(.128,.0488)])
seam=interpolator([(-.1355,.0940),(-.105,.0922),(-.060,.0920),(.028,.0920),(.077,.0911),(.128,.0900)])
def crown(y):
 t=(y+.1355)/.2635
 return .0954+.0295*math.sin(math.pi*t)
# The narrow end profiles still mate with the existing nose and tail fascia.
end_profile=interpolator([(0,1),(.3,.990),(.55,.955),(.66,.915),(.70,.888),(.72,.867),(.745,.816),(.91,.255),(.97,.071),(1,0)])
def cross_profile(x,y,w):
 t=(y+.1355)/.2635
 shoulder=.0475-.012*t+.006*math.sin(math.pi*t)
 a=1-.10*(abs(x)/shoulder)**2
 b=.90*(w-abs(x))/(w-shoulder)
 k=.045;h=max(k-abs(a-b),0)/k
 shaped=min(a,b)-h*h*k*.25
 # Fade the small end cross-sections into the established optical/rear seating edges.
 blend=smooth(0,.08,t)*(1-smooth(.92,1,t))
 return end_profile(abs(x)/w)*(1-blend)+shaped*blend

def plan_y(y,u):
 return y-.016*math.sqrt(max(0,1-u*u))*math.exp(-((y+.1355)/.027)**2)+.015*(1-smooth(.70,1,abs(u)))*math.exp(-((y-.128)/.027)**2)
def nose_y(x):return -.1355-.016*math.sqrt(max(.000001,1-(x/.0672)**2))

# Clean dense quad surface: one symmetric width curve and one continuous shoulder profile.
rows=181;cols=201;vs=[]
for k in range(rows):
 y=-.1355+(.128+.1355)*k/(rows-1);w=width(y);z=seam(y);h=crown(y)-z
 for j in range(cols):
  # Evaluate the width at the warped physical Y. This keeps end-cap rows injective
  # even where the width grows behind the strongly rounded nose boundary.
  # Mixed linear/cosine spacing avoids needle-thin corner quads.
  linear=-1+2*j/(cols-1);u=.5*linear+.5*math.sin(linear*math.pi/2);py=plan_y(y,u);pw=width(py)
  vs.append((u*pw,py,z+h*cross_profile(u*pw,y,pw)))
fs=[]
for k in range(rows-1):
 for j in range(cols-1):a=k*cols+j;fs.append((a,a+1,a+1+cols,a+cols))
shell=bpy.data.objects['BODY_SHELL_TOP'];me=bpy.data.meshes.new('V16 controlled crown quads');me.from_pydata(vs,[],fs);me.update();shell.data=me;me.materials.append(TI)
for p in me.polygons:p.use_smooth=True
for mod in list(shell.modifiers):shell.modifiers.remove(mod)
mod=shell.modifiers.new('Continuous formed shell wall','SOLIDIFY');mod.thickness=.0016;mod.offset=-1
# A tiny physical return catches light around the shaped nose edge, without a flat end cap.
for ob in list(bpy.data.objects):
 if ob.name.startswith(('SHELL_SEAM_','VISOR_')) or ob.name in ['FRONT_VISOR_FRAME','FRONT_VISOR']:bpy.data.objects.remove(ob,do_unlink=True)
for sign in [-1,1]:
 pts=[]
 for k in range(180):
  y=-.1355+(.128+.1355)*k/179;pts.append((sign*(width(y)-.0003),plan_y(y,sign),seam(y)-.0014))
 curve('SHELL_SEAM_'+str(sign),pts,.00018,BLACK,root)

# Rebuild the upper chassis wall from the new shell boundary, joining the preserved underside.
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
for node in ast.parse((ROOT/'scripts/blender/polish_underside_normals_v14.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='capture_normals':exec(compile(ast.Module(body=[node],type_ignores=[]),'<normal helpers>','exec'))
cradle=bpy.data.objects['BODY_CRADLE'];oldcache=capture_normals(cradle);tree=oldcache[0]
# Counterclockwise perimeter of the finished roof, sampled with its actual seam heights.
perimeter=[Vector(vs[j]) for j in range(cols)]+[Vector(vs[k*cols+cols-1]) for k in range(1,rows)]+[Vector(vs[(rows-1)*cols+j]) for j in range(cols-2,-1,-1)]+[Vector(vs[k*cols]) for k in range(rows-2,0,-1)]
def cross(a,b):return a.x*b.y-a.y*b.x
def edge_at(direction):
 hits=[]
 for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
  e=b-a;den=cross(direction,e)
  if abs(den)<1e-10:continue
  radius=cross(a,e)/den;t=cross(a,direction)/den
  if radius>0 and -.000001<=t<=1.000001:hits.append((radius,a.z+(b.z-a.z)*t))
 assert hits
 return max(hits)
levels=10;raw=sorted(set([round(math.tau*i/384,12) for i in range(384)]+[round(math.atan2(p.y,p.x)%math.tau,12) for p in perimeter]));angles=[]
for angle in raw:
 if not angles or angle-angles[-1]>.00001:angles.append(angle)
if math.tau-angles[-1]+angles[0]<.00001:angles.pop()
N=len(angles);lower=[];upper=[]
for a in angles:
 d=Vector((math.cos(a),math.sin(a),0));radii=[]
 for z in [.0615,.0625,.0642]:
  hit,n,idx,dist=tree.ray_cast(d*.40+Vector((0,0,z)),-d,1)
  if hit is None:raise ValueError(('Missed lower chassis',a,z))
  radii.append(math.hypot(hit.x,hit.y)-.00030)
 lower.append(radii);upper.append(edge_at(d))
verts=[]
for inner in [False,True]:
 for k in range(levels):
  for i,a in enumerate(angles):
   r1,z1=upper[i]
   if k<3:r=lower[i][k];z=[.0615,.0625,.0642][k]
   else:
    t=(k-2)/(levels-3);r=lower[i][2]+(r1-lower[i][2])*smooth(0,1,t);z=.0642+(z1-.0007-.0642)*t
   r-=.00165 if inner else 0;verts.append((r*math.cos(a),r*math.sin(a),z))
faces=[];count=levels*N
for k in range(levels-1):
 for j in range(N):
  q=(j+1)%N;a=k*N+j;b=k*N+q;faces.extend([(a,b,b+N,a+N),(count+a+N,count+b+N,count+b,count+a)])
for j in range(N):
 q=(j+1)%N;a=(levels-1)*N+j;b=(levels-1)*N+q;faces.extend([(q,j,count+j,count+q),(a,b,count+b,count+a)])
skirt=mesh('V16_UPPER_CHASSIS_WALL',verts,faces,BLACK)
for mod in list(skirt.modifiers):skirt.modifiers.remove(mod)
bm=bmesh.new();bm.from_mesh(skirt.data);print('SKIRT_VOLUME',len(bm.verts),bm.calc_volume(signed=True),flush=True);bm.free()
newcache=capture_normals(skirt)
def boolean(ob,cut,operation):
 bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Fitted upper chassis','BOOLEAN');mod.operation=operation;mod.solver='MANIFOLD';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name)
 bm=bmesh.new();bm.from_mesh(ob.data);print('BOOLEAN_AUDIT',operation,cut.name,len(bm.verts),bm.calc_volume(signed=True),sum(not e.is_manifold for e in bm.edges),flush=True);bm.free()
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,.20));cut=bpy.context.object;cut.dimensions=(.4,.5,.272);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
boolean(cradle,cut,'DIFFERENCE');bpy.data.objects.remove(cut,do_unlink=True)
boolean(cradle,skirt,'UNION');bpy.data.objects.remove(skirt,do_unlink=True)
# Keep the same real clearance around the four deployed folding collars.
for x,y in [(-.085,-.089),(.085,-.089),(-.070,.086),(.070,.086)]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=.01505,depth=.0386,location=(x,y,.081));cut=bpy.context.object;boolean(cradle,cut,'DIFFERENCE');bpy.data.objects.remove(cut,do_unlink=True)

def restore_chassis_normals():
 normals=[None]*len(cradle.data.loops)
 for face in cradle.data.polygons:
  choices=[(cache[0].find_nearest(face.center)[3],cache) for cache in [oldcache,newcache]];distance,cache=min(choices,key=lambda c:c[0]);tr,vs0,ts,ns=cache
  for li in face.loop_indices:
   p=cradle.data.vertices[cradle.data.loops[li].vertex_index].co
   if distance>.000015:n=face.normal.copy()
   else:
    q,_,idx,_=tr.find_nearest(p);a,b,c=ts[idx];n=barycentric_transform(q,vs0[a],vs0[b],vs0[c],*ns[idx]).normalized()
   normals[li]=n
 cradle.data.normals_split_custom_set(normals)

# A continuous curved fascia nested behind the titanium perimeter. The outer return flows into the cradle.
def facepos(x,z,depth):return (x,nose_y(x)+depth,.0800+z+.00065*(x/.0672)**2)
def ring_surface(name,outer,inner,mat):
 n=len(outer);vs=[]
 # Rounded outer lip -> inset return -> panel seating line.
 for t,depth in [(0,.00055),(.14,.00040),(.34,.00090),(.70,.0021),(1,.0030)]:
  for (xo,zo),(xi,zi) in zip(outer,inner):vs.append(facepos(xo+(xi-xo)*t,zo+(zi-zo)*t,depth))
 # Inner and outer back edges form a closed housing, extending into the main body.
 vs.extend(facepos(x,z,.0110) for x,z in inner);vs.extend(facepos(x,z,.0110) for x,z in outer)
 fs=[]
 for k in range(6):
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,(k+1)*n+q,(k+1)*n+j))
 for j in range(n):q=(j+1)%n;fs.append((6*n+j,6*n+q,q,j))
 ob=mesh(name,vs,fs,mat)
 for mod in list(ob.modifiers):ob.modifiers.remove(mod)
 return ob
outer=outline(.1335,.0270,.0084);inner=outline(.1235,.0196,.0064)
frame=ring_surface('FRONT_VISOR_FRAME',outer,inner,FRAME)
# Real continuous optical opening in the cradle, so the sensor carrier cannot sit over a solid nose.
def face_solid(name,pts,front,back,mat):
 n=len(pts);vs=[facepos(x,z,d) for d in [front,back] for x,z in pts]
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
 ob=mesh(name,vs,fs,mat)
 for mod in list(ob.modifiers):ob.modifiers.remove(mod)
 return ob
cut=face_solid('TEMP_NOSE_OPENING',inner,-.018,.023,DARK)
bpy.context.view_layer.objects.active=cradle;mod=cradle.modifiers.new('Embedded stereo opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
print('AFTER_NOSE',len(cradle.data.vertices),flush=True)
cradle.data.materials.clear();cradle.data.materials.append(BLACK)
for p in cradle.data.polygons:p.material_index=0
# Dense panel fan follows the bowed face; two precision bores receive the preserved optical layers.
pts=inner;n=len(pts);vs=[];fs=[];layers=12
for depth in [.0030,.0095]:
 vs.append(facepos(0,0,depth))
 for k in range(1,layers+1):
  for x,z in pts:vs.append(facepos(x*k/layers,z*k/layers,depth))
count=1+layers*n
for j in range(n):fs.append((0,1+j,1+(j+1)%n))
for k in range(layers-1):
 for j in range(n):a=1+k*n+j;q=1+k*n+(j+1)%n;fs.append((a,a+n,q+n,q))
fs+= [tuple(count+i for i in reversed(f)) for f in fs.copy()]
for j in range(n):a=1+(layers-1)*n+j;q=1+(layers-1)*n+(j+1)%n;fs.append((a,q,q+count,a+count))
plate=mesh('FRONT_VISOR',vs,fs,PANEL)
for mod in list(plate.modifiers):plate.modifiers.remove(mod)
# Angle each optical stack to the local tangent of the nose, with its rim behind the panel face.
for sign in [-1,1]:
 x=sign*.04532;z=.0805;deriv=.016*x/(.0672**2*math.sqrt(1-(x/.0672)**2));angle=math.atan(deriv);newy=nose_y(x)+.0040
 transform=Matrix.Translation((x,newy,z))@Matrix.Rotation(angle,4,'Z')@Matrix.Translation((-x,.144825,-z))
 for ob in list(s.objects):
  if ob.name.startswith('STEREO_') and ob.name.split('_')[2]==str(sign):ob.matrix_world=transform@ob.matrix_world
 # Some optical names contain more than one descriptive token before the side suffix.
 for ob in list(s.objects):
  if ob.name.startswith('STEREO_INNER_OPTICAL_RING_') and ob.name.endswith('_'+str(sign)):ob.matrix_world=transform@ob.matrix_world
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.00695,depth=.042,location=(x,nose_y(x)+.009,z));cut=bpy.context.object;cut.rotation_euler=(math.pi/2,0,angle)
 bpy.context.view_layer.objects.active=plate;mod=plate.modifiers.new('Inset stereo bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
plate.data.materials.clear();plate.data.materials.append(PANEL)
for p in plate.data.polygons:p.material_index=0
# The lower nose edge is a curved, fine molded return instead of a flat rectangular strip.
curve('VISOR_LOWER_LIP',[facepos(x,z,.0002) for x,z in outer if z<-.001],.00022,FRAME,root)
led=bpy.data.objects['STATUS_LIGHT'];led.location=(0,nose_y(0)+.0013,.0898)
restore_chassis_normals()
# Wrap the rear fascia edges into the new rounded tail; retain the central connector layout.
def fit_tail(p):
 q=p.copy();q.x*=.97;q.y-=.0125*smooth(.68,1,abs(p.x)/.050)
 if q.z>.086:q.z=.086+(q.z-.086)*.55
 return q
for ob in list(s.objects):
 if not ob.name.startswith('REAR_') or ob.name.startswith('REAR_LEG_'):continue
 if ob.type not in {'MESH','CURVE','FONT'}:continue
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');ob=bpy.context.object
 world=ob.matrix_world.copy();inv=world.inverted();coords=[world@v.co for v in ob.data.vertices];normals=[n.vector.copy() for n in ob.data.corner_normals];jac=[];eps=.00001
 for p in coords:
  columns=[]
  for axis in range(3):
   step=Vector((0,0,0));step[axis]=eps;columns.append((fit_tail(p+step)-fit_tail(p-step))/(2*eps))
  jac.append(Matrix(columns).transposed().inverted_safe().transposed())
 for v,p in zip(ob.data.vertices,coords):v.co=inv@fit_tail(p)
 ob.data.update();a=world.to_3x3().inverted().transposed();b=world.to_3x3().transposed();ob.data.normals_split_custom_set([(b@jac[l.vertex_index]@a@n).normalized() for l,n in zip(ob.data.loops,normals)])
# Reproject the existing AERIX mark onto the revised crown.
word=bpy.data.objects['AERIX_WORDMARK'];word.location.y-=.017
for mod in word.modifiers:
 if mod.type=='SHRINKWRAP':mod.target=shell
# Keep clean satin colors; the approved fine material texture remains intact.
for name,loc,target,scale in [('top_body',(0,0,.65),(0,0,.10),.38),('body_contours',(.25,-.46,.46),(0,-.012,.10),.36),('nose_embedded',(.095,-.34,.155),(0,-.132,.087),.170),('nose_top',(0,-.29,.38),(0,-.107,.094),.195),('roof_rear',(.25,.46,.41),(0,.012,.10),.36),('roof_side',(.5,.02,.14),(0,0,.087),.35)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;ob=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(ob);ob.location=loc
 ob.rotation_euler=(0,0,0) if name=='top_body' else (Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.cycles.samples=40;s.render.resolution_percentage=100;s.render.resolution_x=1536;s.render.resolution_y=1024
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=20;s.render.resolution_percentage=70
for name in ([] if '--build-only' in sys.argv else ['top_body','body_contours','roof_rear','roof_side','nose_embedded'] if preview else ['hero','top_body','body_contours','nose_embedded','nose_top']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.resolution_x=1000 if name=='top_body' else 1536;s.render.resolution_y=1400 if name=='top_body' else 1024;bpy.data.objects['STUDIO_GROUND'].hide_render=name=='top_body';s.render.filepath=str(ROOT/'renders/exterior-v16'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V16_COMPLETE')
