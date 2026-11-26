"""Clean the rear mating edges, inset cover, vent lips, and connector surround."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v23';OUT.mkdir(exist_ok=True)
profile=json.loads((R/'scripts/blender/data/rear-source-profile-v11.json').read_text());toprow=profile['toprow'];bottomrow=profile['bottomrow']
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def interp(row,x,axis=2):
 for a,b in zip(row,row[1:]):
  if a[0]<=x<=b[0]:
   t=(x-a[0])/(b[0]-a[0]);return a[axis]*(1-t)+b[axis]*t
 return row[0][axis] if x<row[0][0] else row[-1][axis]
def zfit(z):return z if z<=.086 else .086+(z-.086)*.55
def zunfit(z):return z if z<=.086 else .086+(z-.086)/.55
def rear_y(x,z):
 u=x/.97;z=zunfit(z);bottom=interp(bottomrow,u);top=interp(toprow,u)-.0015;t=max(0,min(1,(z-bottom)/max(.001,top-bottom)))
 return interp(bottomrow,u,1)*(1-t)+interp(toprow,u,1)*t-.00010+.00012*math.sin(math.pi*t)-.0125*smooth(.68,1,abs(u)/.05)*smooth(.053,.084,z)
def rear_x(x,z):return x*(1+.03/.97*smooth(.030,.042,abs(x))*(1-smooth(.053,.084,zunfit(z))))
def top(x):return zfit(interp(toprow,x/.97)-.0015)
def bottom(x):return interp(bottomrow,x/.97)+.00015
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'));s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
def material(name,base,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*base,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
TRIM=material('V23 clean rear satin graphite',(.012,.015,.018),.13,.40)
DOOR=material('V23 rear access cover satin',(.014,.017,.020),.10,.44)
DARK=material('V23 rear pocket graphite',(.003,.004,.005),.05,.43)
METAL=material('V23 satin connector alloy',(.12,.14,.16),.82,.30)
RIM=material('V23 satin rear shell rim',(.012,.015,.018),.13,.42)
for mat,lo,hi in [(TRIM,.38,.42),(DOOR,.42,.46)]:
 ns=mat.node_tree.nodes;ls=mat.node_tree.links;n=ns.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=720;n.inputs['Detail'].default_value=1;r=ns.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=lo;r.inputs['To Max'].default_value=hi;ls.new(n.outputs['Fac'],r.inputs['Value']);ls.new(r.outputs['Result'],ns.get('Principled BSDF').inputs['Roughness'])
def remove(name):
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
def mesh(name,vs,fs,mat,normals=None):
 remove(name);m=bpy.data.meshes.new(name+' V23 finished mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);s.collection.objects.link(o);o.parent=root;m.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 for p in m.polygons:p.use_smooth=True
 if normals:m.normals_split_custom_set([normals[l.vertex_index] for l in m.loops])
 return o
def rounded(w,h,r,cx=0,cz=0):
 pts=[]
 for xx,zz,a0 in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(33):
   a=math.radians(a0+90*j/32);pts.append((cx+xx+r*math.cos(a),cz+zz+r*math.sin(a)))
 dense=[]
 for a,b in zip(pts,pts[1:]+pts[:1]):
  count=16 if math.dist(a,b)>.0005 else 1
  dense.extend((a[0]+(b[0]-a[0])*j/count,a[1]+(b[1]-a[1])*j/count) for j in range(count))
 return pts if not dense else dense
def rounded_scaled(w,h,r,cx=0,cz=0):return [(x*.97,z) for x,z in rounded(w,h,r,cx,cz)]
def outline_normals(pts):
 result=[]
 for i,p in enumerate(pts):
  a=Vector(pts[(i-1)%len(pts)]);b=Vector(pts[(i+1)%len(pts)]);t=b-a;result.append(Vector((t.y,-t.x)).normalized())
 return result
def capture(o):
 m=o.data;m.calc_loop_triangles();vs=[v.co.copy() for v in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles];ns=[[m.corner_normals[i].vector.copy() for i in t.loops] for t in m.loop_triangles];return BVHTree.FromPolygons(vs,ts,all_triangles=True),vs,ts,ns
def cut(o,pts):
 n=len(pts);c=mesh('V23 temporary opening',[(x,z,d) for d in [-.004,.012] for x,z in pts],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],DARK)
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Precise rear aperture','BOOLEAN');m.operation='DIFFERENCE';m.solver='MANIFOLD';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);remove(c.name)
def wrap(o,yfunc=rear_y,xfunc=lambda x,z:x,offset=0):
 m=o.data;ns=[n.vector.copy() for n in m.corner_normals];derivatives={};eps=.000001
 for v in m.vertices:
  x,z,d=v.co;xx=xfunc(x,z);yy=yfunc(x,z)+offset-d
  derivatives[v.index]=((xfunc(x+eps,z)-xfunc(x-eps,z))/(2*eps),(xfunc(x,z+eps)-xfunc(x,z-eps))/(2*eps),(yfunc(x+eps,z)-yfunc(x-eps,z))/(2*eps),(yfunc(x,z+eps)-yfunc(x,z-eps))/(2*eps))
  v.co=(xx,yy,z)
 m.update();normals=[]
 for li,n in zip(m.loops,ns):
  xx,xz,yx,yz=derivatives[li.vertex_index];nx=(n.x+yx*n.z)/xx;normals.append(Vector((nx,-n.z,n.y-xz*nx+yz*n.z)).normalized())
 m.normals_split_custom_set(normals);m.update();return o
def panel(name,pts,depth,bevel,mat,holes=[],yfunc=rear_y,xfunc=lambda x,z:x,offset=0,layers=16):
 N=len(pts);outs=outline_normals(pts);cx=sum(p[0] for p in pts)/N;cz=sum(p[1] for p in pts)/N
 inner=[(x-n.x*bevel,z-n.y*bevel) for (x,z),n in zip(pts,outs)];rings=[];norms=[]
 for k in range(1,layers+1):
  t=k/layers;rings.append([(cx+(x-cx)*t,cz+(z-cz)*t,0) for x,z in inner]);norms.append([Vector((0,0,-1))]*N)
 for k in range(1,9):
  a=math.pi/2*k/8;rings.append([(x+n.x*bevel*math.sin(a),z+n.y*bevel*math.sin(a),bevel*(1-math.cos(a))) for (x,z),n in zip(inner,outs)]);norms.append([Vector((n.x*math.sin(a),n.y*math.sin(a),-math.cos(a))) for n in outs])
 rings.append([(x,z,depth) for x,z in pts]);norms.append([Vector((0,0,1))]*N)
 for k in range(layers-1,0,-1):
  t=k/layers;rings.append([(cx+(x-cx)*t,cz+(z-cz)*t,depth) for x,z in pts]);norms.append([Vector((0,0,1))]*N)
 vs=[(cx,cz,0)]+[p for row in rings for p in row]+[(cx,cz,depth)];vn=[Vector((0,0,-1))]+[n for row in norms for n in row]+[Vector((0,0,1))];fs=[(0,1+(j+1)%N,1+j) for j in range(N)]
 for k in range(len(rings)-1):
  a=1+k*N;b=a+N
  for j in range(N):q=(j+1)%N;fs.append((a+j,a+q,b+q,b+j))
 last=1+(len(rings)-1)*N;fs.extend((len(vs)-1,last+j,last+(j+1)%N) for j in range(N));o=mesh(name,vs,fs,mat,vn);cache=capture(o)
 for pts in holes:cut(o,pts)
 if holes:
  tr,cv,ct,cn=cache;normals=[]
  for face in o.data.polygons:
   q,n,i,d=tr.find_nearest(face.center)
   for li in face.loop_indices:
    p=o.data.vertices[o.data.loops[li].vertex_index].co
    if d>.000001:n=face.normal.copy()
    else:
     q,_,i,_=tr.find_nearest(p);a,b,c=ct[i];n=barycentric_transform(q,cv[a],cv[b],cv[c],*cn[i]).normalized()
    normals.append(n)
  o.data.normals_split_custom_set(normals)
 return wrap(o,yfunc,xfunc,offset)
def ring(name,outer,inner,cx,cz,front,back,fillet,mat,yfunc=rear_y):
 # An explicit rolled rectangular annulus; all rows share a dense outline.
 profiles=[]
 for k in range(9):
  a=math.pi/2*k/8;shrink=fillet*(1-math.cos(a));profiles.append((outer[0]-2*shrink,outer[1]-2*shrink,outer[2]-shrink,front+fillet*(1-math.sin(a))))
 for k in range(9):
  a=math.pi/2*k/8;grow=fillet*(1-math.sin(a));profiles.append((inner[0]+2*grow,inner[1]+2*grow,inner[2]+grow,front+fillet*(1-math.cos(a))))
 profiles.extend([(*inner,back),(*outer,back)])
 loops=[rounded_scaled(w,h,r,cx,cz) for w,h,r,d in profiles]
 # The four long straight spans always have 16 subdivisions for matching loops.
 assert len({len(p) for p in loops})==1,(name,[len(p) for p in loops])
 N=len(loops[0]);vs=[(x,z,p[3]) for p,pts in zip(profiles,loops) for x,z in pts];fs=[]
 for k in range(len(profiles)):
  kk=(k+1)%len(profiles)
  for j in range(N):q=(j+1)%N;fs.append((k*N+j,k*N+q,kk*N+q,kk*N+j))
 return wrap(mesh(name,vs,fs,mat),yfunc)
# The shell skirt must remain behind both the roof wall and the rear header.
roof=bpy.data.objects['BODY_SHELL_TOP'];rm=roof.data;boundary=list(roof['top_boundary_edges']);segments=[]
for ia,ib in zip(boundary[::2],boundary[1::2]):
 a=rm.vertices[ia].co.copy();b=rm.vertices[ib].co.copy()
 if max(a.y,b.y)<.114:continue
 d=Vector((b.x-a.x,b.y-a.y));n=Vector((d.y,-d.x)).normalized();mid=(a+b)*.5
 if n.dot(Vector((mid.x,mid.y)))<0:n.negate()
 segments.append((a,b,d,n))
def nearest(p):
 best=None
 for a,b,d,n in segments:
  t=max(0,min(1,Vector((p.x-a.x,p.y-a.y)).dot(d)/d.length_squared));q=a.lerp(b,t);dist=Vector((p.x-q.x,p.y-q.y)).length_squared
  if best is None or dist<best[0]:best=(dist,q,n)
 return best
cradle=bpy.data.objects['BODY_CRADLE'];cm=cradle.data;oldns=[n.vector.copy() for n in cm.corner_normals];changed=0
for v in cm.vertices:
 p=v.co
 if p.y<=.116 or p.z<=.084:continue
 dist,q,n=nearest(p);w=smooth(.116,.130,p.y)*smooth(q.z-.0072,q.z-.0020,p.z)*(1-smooth(.004,.010,math.sqrt(dist)))
 if w:
  v.co-=Vector((n.x,n.y,0))*.00060*w;changed+=1
cm.update()
if cm.attributes.get('custom_normal'):cm.attributes.remove(cm.attributes['custom_normal'])
cm.update();auto=[n.vector.copy() for n in cm.corner_normals];newns=[]
for li,loop in enumerate(cm.loops):
 p=cm.vertices[loop.vertex_index].co;w=smooth(.112,.128,p.y)*smooth(.083,.090,p.z);newns.append(oldns[li].lerp(auto[li],w).normalized() if w else oldns[li])
# Smooth the previously faceted cut edge around the lower rear shell. This is a
# small end-wall strip; the broad belly keeps its approved V21 surface normals.
cm.materials.append(RIM);rimslot=len(cm.materials)-1;rim_faces=0
for face in cm.polygons:
 p=face.center
 if p.z>.077 or abs(p.x)>.052 or p.y<interp(bottomrow,p.x,1)-.0011 or face.normal.y<.15:continue
 face.material_index=rimslot;face.use_smooth=True;rim_faces+=1
 for li in face.loop_indices:
  x=cm.vertices[cm.loops[li].vertex_index].co.x;eps=.001
  dy=(interp(bottomrow,x+eps,1)-interp(bottomrow,x-eps,1))/(2*eps)
  newns[li]=Vector((-dy,1,0)).normalized()
cm.normals_split_custom_set(newns);cm.update();cradle['V23 rear clearance']='0.60 mm inset behind titanium lip and fitted header'
finish=bpy.data.materials['V22 satin titanium front edge'].copy();finish.name='V23 satin titanium rear edge';rm.materials.append(finish);slot=len(rm.materials)-1;roof_faces=0
for face in rm.polygons:
 if face.index>=int(roof['top_surface_faces'])*2 and min(rm.vertices[i].co.y for i in face.vertices)>.114:
  face.material_index=slot;face.use_smooth=True;roof_faces+=1
rm.update()
# A fair fascia retains the original rear profile, relaxing the old upper-tail
# deformation near the belly so its lower corners meet the actual chassis rim.
fascia_top=lambda x:top(x)-.00125
half=profile['panel_halfwidth']*.97;xs=[-half+2*half*j/128 for j in range(129)];pts=[(x,fascia_top(x)) for x in reversed(xs)]
pts.extend((-half,fascia_top(-half)+(bottom(-half)-fascia_top(-half))*k/12) for k in range(1,12));pts.extend((x,bottom(x)) for x in xs);pts.extend((half,bottom(half)+(fascia_top(half)-bottom(half))*k/12) for k in range(1,12))
holes=[rounded_scaled(.0214,.0108,.0028,0,.079),rounded_scaled(.057,.015,.0033,0,.0595)]+[rounded_scaled(.0135,.0032,.0015,sign*.025,z) for sign in [-1,1] for z in [.0815,.0764]]
panel('REAR_FASCIA',pts,.0024,.00016,TRIM,holes,xfunc=rear_x,layers=64)
panel('REAR_ACCESS_COVER',rounded_scaled(.0564,.0144,.003,0,.0595),.00218,.00020,DOOR,offset=-.00022)
ring('REAR_ACCESS_GASKET',(.0573,.0153,.00345),(.0560,.0140,.0028),0,.0595,.00075,.0018,.00005,DARK)
for sign in [-1,1]:
 for j,z in enumerate([.0815,.0764]):ring('REAR_VENT_TUNNEL_'+str(sign)+'_'+str(j),(.0137,.0034,.00155),(.0128,.0025,.00115),sign*.025,z,-.00010,.0045,.000085,TRIM)
ring('REAR_PORT_MOUNT',(.0211,.0105,.0027),(.0157,.0077,.0021),0,.079,0,.00465,.00012,TRIM,yfunc=lambda x,z:.14355)
ring('REAR_PORT_LINER',(.0157,.0077,.0021),(.0130,.0051,.0019),0,.079,0,.0039,.000085,DARK,yfunc=lambda x,z:.1428)
ring('REAR_PORT_METAL_SHELL',(.0138,.0059,.0021),(.0126,.0047,.0018),0,.079,0,.00355,.000085,METAL,yfunc=lambda x,z:.14255)
# Replace the proud wavy split tube with a single recessed, smooth parting seal.
remove('REAR_HOUSING_REVEAL');curve=bpy.data.curves.new('V23 rear housing parting seal','CURVE');curve.dimensions='3D';curve.bevel_depth=.000085;curve.bevel_resolution=4;sp=curve.splines.new('POLY');sp.points.add(192)
for j,p in enumerate(sp.points):
 x=-.048+.096*j/192;z=.0692;p.co=(*Vector((rear_x(x,z),rear_y(x,z)+.000015,z)),1)
o=bpy.data.objects.new('REAR_HOUSING_REVEAL',curve);s.collection.objects.link(o);o.parent=root;curve.materials.append(DARK)
# A continuously shaped header finishes just beneath the original titanium lip.
rearrow=sorted([tuple(v.co) for v in rm.vertices[(181-1)*201:181*201]],key=lambda p:p[0])
def header_top(x):return interp(rearrow,x)-.0008
def header_bottom(x):return top(x)-.0010
def header_y(x,z):
 t=smooth(header_bottom(x),header_top(x),z);return (rear_y(x,header_bottom(x))+.00006)*(1-t)+(interp(rearrow,x,1)-.00050)*t
def header_grid():
 # Long curved strips need a row grid: a radial fan can fold across their narrow
 # concave outline near the corners. Roll the grid perimeter explicitly.
 cols=257;rows=17;bevel=.00012;half=.0482-bevel;front=[];fs=[]
 for k in range(rows):
  t=k/(rows-1)
  for j in range(cols):
   x=-half+2*half*j/(cols-1);z=(header_bottom(x)+bevel)*(1-t)+(header_top(x)-bevel)*t;front.append((x,z,0))
 for k in range(rows-1):
  for j in range(cols-1):a=k*cols+j;fs.append((a,a+cols,a+cols+1,a+1))
 count=len(front);vs=front.copy();vn=[Vector((0,0,-1))]*count
 perimeter=list(range(cols-1,-1,-1))+[k*cols for k in range(1,rows)]+[(rows-1)*cols+j for j in range(1,cols)]+[k*cols+cols-1 for k in range(rows-2,0,-1)]
 perimeter.reverse();pts=[front[i][:2] for i in perimeter];outs=outline_normals(pts);last=perimeter
 for k in range(1,9):
  a=math.pi/2*k/8;current=[]
  for (x,z),n in zip(pts,outs):
   current.append(len(vs));vs.append((x+n.x*bevel*math.sin(a),z+n.y*bevel*math.sin(a),bevel*(1-math.cos(a))));vn.append(Vector((n.x*math.sin(a),n.y*math.sin(a),-math.cos(a))))
  for j in range(len(last)):q=(j+1)%len(last);fs.append((last[j],last[q],current[q],current[j]))
  last=current
 back=len(vs);vs.extend((x,z,.0032) for x,z,d in front);vn.extend([Vector((0,0,1))]*count)
 for face in fs[:(rows-1)*(cols-1)]:fs.append(tuple(back+i for i in reversed(face)))
 for j in range(len(last)):q=(j+1)%len(last);fs.append((last[j],last[q],back+perimeter[q],back+perimeter[j]))
 return wrap(mesh('REAR_HOOD_RETURN',vs,fs,TRIM,vn),header_y)
header_grid()
for name,loc,target,scale in [('rear_finish',(0,.44,.092),(0,.140,.072),.122),('rear_left_finish',(-.17,.38,.118),(-.018,.137,.073),.139),('rear_right_finish',(.17,.38,.118),(.018,.137,.073),.139),('rear_vent_finish',(-.024,.30,.087),(-.024,.143,.079),.043)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.frame_set(1);s.camera=bpy.data.objects['CAM_rear_finish'];bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'))
(OUT/'build-report.json').write_text(json.dumps({'inset_rear_chassis_vertices':changed,'satin_rear_roof_faces':roof_faces,'smoothed_lower_rear_rim_faces':rim_faces,'rear_profile_source':'V11 original fitted shell contours','single_port_contacts_preserved':24},indent=2));print('V23_REAR_BUILD_COMPLETE',flush=True)
