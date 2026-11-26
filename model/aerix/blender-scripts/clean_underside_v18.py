"""Clean fitted underside borders in planar space before wrapping to the chassis."""
import bpy,bmesh,math,ast,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v18';OUT.mkdir(exist_ok=True)
# The pre-aperture chassis supplies an uninterrupted curved surface and its normals.
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v13.blend'))
ev=bpy.data.objects['BODY_CRADLE'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
vs0=[v.co.copy() for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];ns=[[me.corner_normals[i].vector.copy() for i in t.loops] for t in me.loop_triangles]
tree=BVHTree.FromPolygons(vs0,ts,all_triangles=True);ev.to_mesh_clear()
def surface(x,y):
 p,n,i,d=tree.ray_cast(Vector((x,y,-.1)),Vector((0,0,1)),1)
 if p is None:raise ValueError(('Surface missed',x,y))
 a,b,c=ts[i];normal=barycentric_transform(p,vs0[a],vs0[b],vs0[c],*ns[i]).normalized()
 return p.z,normal
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
POD=bpy.data.materials['V09 satin molded graphite'];DARK=bpy.data.materials['V09 deep recess'];PANEL=bpy.data.materials['V14 fine textured access panels']
for filename,names in [('refine_underside_v14.py',['rounded','densify','slab']),('refine_front_arms_v09.py',['mesh'])]:
 for node in ast.parse((R/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
def remove(name):
 o=bpy.data.objects.get(name)
 if o:bpy.data.objects.remove(o,do_unlink=True)
def apply(o):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
def cut(o,pts):
 cutter=slab('TEMP_CLEAN_CUT',pts,-.015,.015,DARK)
 for m in list(cutter.modifiers):cutter.modifiers.remove(m)
 bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Clean planar opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)
def planar_panel(name,w,l,r,x,y,depth,holes):
 # Dense concentric strips avoid large non-planar n-gons on the final curved panel.
 pts=densify(rounded(w,l,r,x,y,steps=24));n=len(pts);layers=20;xy=[(x,y)]
 for k in range(1,layers+1):xy.extend((x+(a-x)*k/layers,y+(b-y)*k/layers) for a,b in pts)
 count=len(xy);vs=[(a,b,z) for z in [0,depth] for a,b in xy];front=[(0,1+(j+1)%n,1+j) for j in range(n)]
 for k in range(layers-1):
  a=1+k*n;b=a+n
  for j in range(n):q=(j+1)%n;front.append((a+j,a+q,b+q,b+j))
 fs=front+[tuple(count+i for i in reversed(f)) for f in front];a=1+(layers-1)*n
 for j in range(n):q=(j+1)%n;fs.append((a+j,a+q,count+a+q,count+a+j))
 o=mesh(name,vs,fs,POD)
 for m in list(o.modifiers):o.modifiers.remove(m)
 for pts in holes:cut(o,pts)
 return o
def soften_and_wrap(o,offset,edge,mat):
 # Fillets are built while faces are planar. Warping afterwards keeps the radius
 # consistent rather than clamping it unpredictably against tiny Boolean edges.
 if edge:
  m=o.modifiers.new('Continuous molded edge radius','BEVEL');m.width=edge;m.segments=4;m.limit_method='ANGLE';m.angle_limit=.5;m.use_clamp_overlap=False;m.harden_normals=True
  m=o.modifiers.new('Planar face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50
 apply(o);me=o.data;me.update();normal=[n.vector.copy() for n in me.corner_normals]
 for p in me.polygons:
  for li in p.loop_indices:
   if normal[li].length<.5:normal[li]=p.normal.copy()
 samples={v.index:surface(v.co.x,v.co.y) for v in me.vertices}
 for v in me.vertices:v.co.z+=samples[v.index][0]+offset
 me.update();warped=[]
 for li,n in zip(me.loops,normal):
  h,sn=samples[li.vertex_index];fx=-sn.x/sn.z;fy=-sn.y/sn.z
  warped.append(Vector((n.x-fx*n.z,n.y-fy*n.z,n.z)).normalized())
 me.normals_split_custom_set(warped);me.materials.clear();me.materials.append(mat)
 for p in me.polygons:p.material_index=0
 o['edge_finish']='V18: explicit four-segment fillet formed before surface fitting'
 return o
def panel(name,w,l,r,x,y,offset,depth,edge,mat,holes=[]):
 remove(name);return soften_and_wrap(planar_panel(name,w,l,r,x,y,depth,holes),offset,edge,mat)
door_cut=rounded(.0648,.1248,.0085,0,-.012,steps=32)
circle=lambda x,y,r:[(x+r*math.cos(j*math.tau/128),y+r*math.sin(j*math.tau/128)) for j in range(128)]
panel('BELLY_SPINE',.087,.198,.013,0,-.015,-.00060,.0015,.00018,POD,[door_cut]+[circle(x,.0695,.0096) for x in [-.025,.025]])
panel('BELLY_SERVICE_PANEL',.0638,.1238,.008,0,-.012,-.00062,.002,.00022,PANEL)
panel('BELLY_SENSOR_BRIDGE',.084,.030,.011,0,.0695,-.0010,.0015,.00018,POD,[circle(x,.0695,.0096) for x in [-.025,.025]])
panel('BELLY_PORT_PAD',.027,.022,.0045,0,.1215,-.00070,.0015,.00018,POD,[rounded(.0164,.0073,.0032,0,.1215,steps=24)])
panel('BELLY_PANEL_REVEAL',.0651,.1251,.0086,0,-.012,.00035,.0012,.00008,DARK,[rounded(.0635,.1235,.00785,0,-.012,steps=32)])
# Rebuild the small tunnels as smooth radiused openings; keep the actual recesses.
for sign in [-1,1]:
 x=sign*.0328;y=.1215
 name='BELLY_VENT_TUNNEL_'+str(sign);remove(name)
 profiles=[(.0198,.0044,.0021,.00022),(.01978,.00438,.00209,.00008),(.0196,.0042,.0020,0),(.0182,.0028,.0013,0),(.01788,.00248,.00114,.00008),(.0178,.0024,.0011,.00022),(.0178,.0024,.0011,.004),(.0198,.0044,.0021,.004)]
 outlines=[rounded(w,l,r,x,y,steps=24) for w,l,r,z in profiles]
 counts=[max(1,math.ceil(max(math.dist(p[j],p[(j+1)%len(p)]) for p in outlines)/.001)) for j in range(len(outlines[0]))]
 outlines=[densify(p,counts) for p in outlines];n=len(outlines[0]);vs=[(xx,yy,profile[3]) for profile,pts in zip(profiles,outlines) for xx,yy in pts];fs=[]
 for k in range(len(profiles)):
  kk=(k+1)%len(profiles)
  for j in range(n):q=(j+1)%n;fs.append((k*n+j,k*n+q,kk*n+q,kk*n+j))
 o=mesh(name,vs,fs,POD)
 for m in list(o.modifiers):o.modifiers.remove(m)
 soften_and_wrap(o,-.0004,0,POD)
 # The lips of the sensor sockets track the bridge; their inner wells stay aligned
 # with the existing glass and retaining rings.
 name='DOWN_SENSOR_HOUSING_'+str(sign);old=bpy.data.objects[name];oldface=min(v.co.z for v in old.data.vertices)+.00012;remove(name)
 radial=[(.0108,'outer',.00015),(.0108,'outer',0),(.0106,'outer',-.00015),(.0103,'outer',-.00020),(.00995,'blend',0),(.0096,'inner',.00050),(.00935,'inner',.00050),(.0080,'inner',.00050),(.0075,'inner',.00050),(.0074,'inner',.00065),(.0074,'inner',.0045),(.0103,'inner',.0045)]
 vs=[];n=160
 for r,kind,dz in radial:
  for j in range(n):
   a=j*math.tau/n;xx=sign*.025+r*math.cos(a);yy=.0695+r*math.sin(a);base=surface(xx,yy)[0]-.00104
   z=base+dz if kind=='outer' else (base+oldface+.0005)/2 if kind=='blend' else oldface+dz
   vs.append((xx,yy,z))
 fs=[]
 for k in range(len(radial)):
  for j in range(n):q=(j+1)%n;kk=(k+1)%len(radial);fs.append((k*n+j,k*n+q,kk*n+q,kk*n+j))
 o=mesh(name,vs,fs,POD)
 for m in list(o.modifiers):o.modifiers.remove(m)
 # Tiny fillet at the inner shoulder; generous profile rings define the outer lip.
 m=o.modifiers.new('Socket inner edge finish','BEVEL');m.width=.00006;m.segments=3;m.limit_method='ANGLE';m.angle_limit=.7

# Recover the smooth original skin normals around the vents and openings. Keep the
# pocket walls and all of the upper chassis geometry/normal data untouched.
o=bpy.data.objects['BODY_CRADLE'];me=o.data;normals=[n.vector.copy() for n in me.corner_normals];fixed=0
attr=me.attributes['custom_normal'];prop=next(p.identifier for p in attr.data[0].bl_rna.properties if p.type=='INT' and p.is_array);encoded=[tuple(getattr(d,prop)) for d in attr.data]
original_sharp=[e.use_edge_sharp for e in me.edges];changed_loops=set()
for p in me.polygons:
 if any(me.vertices[v].co.z>.058 for v in p.vertices) or p.normal.z>-.4:continue
 q,n,i,d=tree.find_nearest(p.center)
 if d>.00012 or p.normal.dot(n)<.6:continue
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co;h,sn=surface(v.x,v.y)
  if abs(v.z-h)<.00015:normals[li]=sn;fixed+=1;changed_loops.add(li)
me.normals_split_custom_set(normals)
# Setting custom normals re-encodes even unchanged corners. Restore the original
# packed values outside the underside so the previously approved upper finish is exact.
for e,sharp in zip(me.edges,original_sharp):e.use_edge_sharp=sharp
for i,value in enumerate(encoded):
 if i not in changed_loops:setattr(me.attributes['custom_normal'].data[i],prop,value)
me.update()
print('RESTORED_UNDERSIDE_CORNERS',fixed,flush=True)
s.frame_set(1);s.camera=bpy.data.objects['CAM_hero'];bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'))
if '--preview' in sys.argv:
 s.cycles.samples=32;s.render.resolution_percentage=80;s.render.resolution_x=1300;s.render.resolution_y=1400;bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
 s.camera=bpy.data.objects['CAM_underside_body'];s.camera.data.ortho_scale=.30;s.render.filepath=str(OUT/'underside-preview.png');bpy.ops.render.render(write_still=True)
print('V18_BUILD_COMPLETE',flush=True)
