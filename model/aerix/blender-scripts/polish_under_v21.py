"""Continuous sensor-ring and access-panel edge profiles, without clamped micro-bevels."""
import bpy,bmesh,math,ast,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v21';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v13.blend'))
e=bpy.data.objects['BODY_CRADLE'].evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();sv=[v.co.copy() for v in m.vertices];st=[tuple(t.vertices) for t in m.loop_triangles];sn=[[m.corner_normals[i].vector.copy() for i in t.loops] for t in m.loop_triangles];tree=BVHTree.FromPolygons(sv,st,all_triangles=True);e.to_mesh_clear()
def surface(x,y):
 p,n,i,d=tree.ray_cast(Vector((x,y,-.1)),Vector((0,0,1)),1);assert p is not None
 a,b,c=st[i];n=barycentric_transform(p,sv[a],sv[b],sv[c],*sn[i]).normalized();return p.z,n
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'));s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for file,names in [('polish_exterior_v05.py',['material']),('refine_underside_v14.py',['rounded','densify'])]:
 for n in ast.parse((R/'scripts/blender'/file).read_text()).body:
  if isinstance(n,ast.FunctionDef) and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),'<helpers>','exec'))
TRIM=material('V21 clean satin underside graphite',(.011,.014,.017),.18,.39)
DOOR=material('V21 satin access panel',(.013,.016,.019),.08,.46)
METAL=material('V21 satin sensor retaining alloy',(.026,.032,.038),.64,.33)
DARK=material('V21 optical recess graphite',(.003,.004,.005),.05,.45)
# Roughness-only microtexture on broad faces; edge reflections use geometric normals.
for mat,lo,hi in [(TRIM,.37,.41),(DOOR,.44,.48)]:
 ns=mat.node_tree.nodes;ls=mat.node_tree.links;n=ns.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=720;n.inputs['Detail'].default_value=1
 ramp=ns.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=lo;ramp.inputs['To Max'].default_value=hi;ls.new(n.outputs['Fac'],ramp.inputs['Value']);ls.new(ramp.outputs['Result'],ns.get('Principled BSDF').inputs['Roughness'])
def remove(name):
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
def mesh(name,vs,fs,mat,normals=None):
 remove(name);me=bpy.data.meshes.new(name+' continuous profiles');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);o.parent=root;me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 if normals:me.normals_split_custom_set([normals[l.vertex_index] for l in me.loops])
 return o
def capture(o):
 m=o.data;m.calc_loop_triangles();vs=[v.co.copy() for v in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles];ns=[[m.corner_normals[i].vector.copy() for i in t.loops] for t in m.loop_triangles]
 return BVHTree.FromPolygons(vs,ts,all_triangles=True),vs,ts,ns
def cut(o,pts):
 n=len(pts);c=mesh('V21 temporary aperture',[(x,y,z) for z in [-.02,.02] for x,y in pts],[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],DARK)
 bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Hidden aperture wall','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=c;bpy.ops.object.modifier_apply(modifier=mod.name);remove(c.name)
def outline(w,l,r,cx,cy):
 # Uniform straight segments and 48 steps per quarter-circle; corresponding rows
 # share vertex counts so the narrow edge strips remain evenly tessellated.
 pts=rounded(w,l,r,cx,cy,steps=48);counts=[1 if i%49!=48 else 32 for i in range(len(pts))];return densify(pts,counts)
def panel(name,w,l,r,cx,cy,offset,depth,bevel,mat,holes=[]):
 rings=[];norms=[];small=outline(w-2*bevel,l-2*bevel,r-bevel,cx,cy);N=len(small)
 for k in range(1,21):
  t=k/20;rings.append([(cx+(x-cx)*t,cy+(y-cy)*t,0) for x,y in small]);norms.append([Vector((0,0,-1))]*N)
 for j in range(1,9):
  a=math.pi/2*j/8;inc=bevel*math.sin(a);pts=outline(w-2*bevel+2*inc,l-2*bevel+2*inc,r-bevel+inc,cx,cy)
  rings.append([(x,y,bevel*(1-math.cos(a))) for x,y in pts]);nn=[]
  for i,(x,y) in enumerate(pts):
   prev=Vector((*pts[(i-1)%N],0));nex=Vector((*pts[(i+1)%N],0));t=nex-prev;out=Vector((t.y,-t.x,0)).normalized();nn.append(Vector((out.x*math.sin(a),out.y*math.sin(a),-math.cos(a))))
  norms.append(nn)
 outer=rings[-1];rings.append([(x,y,depth) for x,y,z in outer]);norms.append([Vector((0,0,1))]*N)
 # Back cap uses the same dense radial construction as the front.
 for k in range(19,0,-1):
  t=k/20;rings.append([(cx+(x-cx)*t,cy+(y-cy)*t,depth) for x,y,z in outer]);norms.append([Vector((0,0,1))]*N)
 vs=[(cx,cy,0)]+[p for row in rings for p in row]+[(cx,cy,depth)];vn=[Vector((0,0,-1))]+[n for row in norms for n in row]+[Vector((0,0,1))];fs=[(0,1+(j+1)%N,1+j) for j in range(N)]
 for k in range(len(rings)-1):
  a=1+k*N;b=a+N
  for j in range(N):q=(j+1)%N;fs.append((a+j,a+q,b+q,b+j))
 last=1+(len(rings)-1)*N;fs.extend((len(vs)-1,last+j,last+(j+1)%N) for j in range(N))
 o=mesh(name,vs,fs,mat,vn);cache=capture(o)
 for pts in holes:cut(o,pts)
 # Restore the analytic planar fillet normals after any hidden Boolean apertures.
 tr,cv,ct,cn=cache;ns=[]
 for p in o.data.polygons:
  q,n,i,d=tr.find_nearest(p.center)
  for li in p.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co
   if d>.000001:n=p.normal.copy()
   else:
    q,_,i,_=tr.find_nearest(v);a,b,c=ct[i];n=barycentric_transform(q,cv[a],cv[b],cv[c],*cn[i]).normalized()
   ns.append(n)
 heights={v.index:surface(v.co.x,v.co.y) for v in o.data.vertices}
 for v in o.data.vertices:v.co.z+=heights[v.index][0]+offset
 o.data.update();warped=[]
 for li,n in zip(o.data.loops,ns):
  h,sn=heights[li.vertex_index];fx=-sn.x/sn.z;fy=-sn.y/sn.z;warped.append(Vector((n.x-fx*n.z,n.y-fy*n.z,n.z)).normalized())
 o.data.normals_split_custom_set(warped);o['V21 finish']='Explicit eight-step rolled edge; analytic surface normals'
 return o
circle=lambda x,y,r:[(x+r*math.cos(j*math.tau/256),y+r*math.sin(j*math.tau/256)) for j in range(256)]
panel('BELLY_SPINE',.087,.198,.013,0,-.015,-.00060,.0015,.00024,TRIM,[rounded(.0648,.1248,.0085,0,-.012,steps=48)]+[circle(x,.0695,.0096) for x in [-.025,.025]])
panel('BELLY_SERVICE_PANEL',.0638,.1238,.008,0,-.012,-.00056,.002,.00028,DOOR)
panel('BELLY_SENSOR_BRIDGE',.084,.030,.011,0,.0695,-.0010,.0015,.00026,TRIM,[circle(x,.0695,.0096) for x in [-.025,.025]])
# A single recessed channel liner, sufficiently behind the door's finished lip.
op=outline(.0651,.1251,.00865,0,-.012);ip=outline(.0634,.1234,.0078,0,-.012);N=len(op);vs=[]
for pts,dz in [(op,.00020),(ip,.00020),(ip,.0015),(op,.0015)]:vs.extend((x,y,surface(x,y)[0]+dz) for x,y in pts)
fs=[]
for k in range(4):
 for j in range(N):q=(j+1)%N;kk=(k+1)%4;fs.append((k*N+j,k*N+q,kk*N+q,kk*N+j))
mesh('BELLY_PANEL_REVEAL',vs,fs,DARK)
def lathe(name,profile,x,y,mat,warp=None):
 N=256;vs=[]
 for k,(r,z) in enumerate(profile):
  for j in range(N):
   a=j*math.tau/N;xx=x+r*math.cos(a);yy=y+r*math.sin(a);zz=warp(k,xx,yy,z) if warp else z;vs.append((xx,yy,zz))
 fs=[]
 for k in range(len(profile)):
  kk=(k+1)%len(profile)
  for j in range(N):q=(j+1)%N;fs.append((k*N+j,k*N+q,kk*N+q,kk*N+j))
 o=mesh(name,vs,fs,mat)
 # Continuous normals from the explicit profile, with no modifier clamping.
 return o
def ring(name,x,y,ro,ri,z0,z1,fillet,mat):
 profile=[]
 for cr,cz,a0 in [(ro-fillet,z0+fillet,-90),(ro-fillet,z1-fillet,0),(ri+fillet,z1-fillet,90),(ri+fillet,z0+fillet,180)]:
  for j in range(9):a=math.radians(a0+90*j/8);profile.append((cr+fillet*math.cos(a),cz+fillet*math.sin(a)))
 return lathe(name,profile,x,y,mat)
for sign in [-1,1]:
 x=sign*.025;y=.0695;face=bpy.data.objects['DOWN_SENSOR_EDGE_'+str(sign)].location.z-.00022
 # Smooth transition from the curved bridge flange into a flat concentric seat.
 profile=[(.0108,0),(.01078,0),(.01070,0),(.01055,0),(.01030,0),(.01005,0),(.00980,0),(.00950,0),(.00935,0),(.0075,0),(.0074,0),(.0074,.0045),(.0103,.0045)]
 blends=[0,0,.02,.10,.27,.52,.78,.95,1,1,1,1,1];lifts=[.00018,.00004,-.00008,-.00013,-.00014,-.00010,-.00004,0,0,0,.00010,0,0]
 def warp(k,xx,yy,z):
  t=blends[k];return (surface(xx,yy)[0]-.0010)*(1-t)+(face+.00050)*t+lifts[k]+z
 lathe('DOWN_SENSOR_HOUSING_'+str(sign),profile,x,y,TRIM,warp)
 ring('DOWN_SENSOR_EDGE_'+str(sign),x,y,.00915,.00865,face+.00006,face+.00068,.00009,METAL)
 ring('DOWN_SENSOR_RETAINING_'+str(sign),x,y,.00855,.00685,face+.00030,face+.00150,.00010,DARK)
 for j,r in enumerate([.00675,.00570,.00485]):
  z0=face+.000875+j*.00048;ring('DOWN_SENSOR_BAFFLE_'+str(sign)+'_'+str(j),x,y,r,r-.00040,z0,z0+.00035,.00006,METAL if j==0 else DARK)
 # This old ring cut across the convex glass element and caused a broken bright
 # outline. Its real aperture function is covered by the innermost baffle.
 remove('DOWN_SENSOR_INNER_TRACE_'+str(sign))
 # Keep the glass geometry/position but use its smooth optical normals directly.
 glass=bpy.data.objects['DOWN_SENSOR_COATED_GLASS_'+str(sign)]
 for mod in list(glass.modifiers):
  if mod.type=='WEIGHTED_NORMAL':glass.modifiers.remove(mod)
for name,loc,target,scale in [('under_finish',(0,.012,-.42),(0,.012,.046),.235),('sensor_finish',(.014,.079,-.24),(0,.0695,.044),.104),('panel_finish',(.035,-.042,-.30),(0,-.012,.044),.159)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,data);s.collection.objects.link(o);o.location=loc
 forward=(Vector(target)-o.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward).normalized();from mathutils import Matrix;o.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler()
s.frame_set(1);s.camera=bpy.data.objects['CAM_hero'];bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v21.blend'))
if '--preview' in sys.argv:
 s.cycles.samples=24;s.render.resolution_x=1300;s.render.resolution_y=1500;s.render.resolution_percentage=85;bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
 for name in ['under_finish','sensor_finish','panel_finish']:
  s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(OUT/(name+'-native.png'));bpy.ops.render.render(write_still=True)
print('V21_UNDERSIDE_COMPLETE',flush=True)
