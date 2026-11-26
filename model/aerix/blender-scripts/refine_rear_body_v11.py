"""Reference-led tail shell, integrated rear fascia, recessed port and cooling slots."""
import bpy,math,ast,bmesh,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v10.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for filename,names in [('polish_exterior_v05.py',['material','finish','ring','curve','box','cyl']),('refine_front_arms_v09.py',['mesh']),('refine_reference_v08.py',['upperrow'])]:
 for node in ast.parse((ROOT/'scripts/blender'/filename).read_text()).body:
  if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
TI=bpy.data.materials['Titanium — provisional'];BLACK=bpy.data.materials['Graphite'];POD=bpy.data.materials['V09 satin molded graphite'];DARK=bpy.data.materials['V09 deep recess'];EDGE=bpy.data.materials['V09 machined edge'];BOLT=bpy.data.materials['V09 fastener gunmetal'];GOLD=bpy.data.materials['V09 champagne blade tip']
# The front and middle use the exact V08 rows; only the final tail stations change.
sections=[(-.139,.048,.085,.008),(-.137,.057,.085,.010),(-.129,.067,.087,.017),(-.110,.073,.089,.027),(-.083,.076,.091,.034),(-.050,.076,.092,.037),(-.016,.0725,.093,.039),(.014,.068,.093,.040),(.035,.0615,.093,.040),(.051,.0545,.0925,.0385),(.065,.052,.092,.0365),(.079,.054,.091,.033),(.092,.061,.090,.029),(.103,.063,.0895,.026),(.117,.060,.089,.021),(.129,.0565,.0885,.014),(.139,.052,.0875,.008),(.143,.0505,.087,.006),(.144,.050,.087,.006)]
def lowerrow(y,w,z,h):
 d=.024+.025*max(0,1-(y/.15)**6)
 t=max(0,min(1,(y-.117)/.027));d=d*(1-t)+.038*t
 row=[(0,z-d),(.50*w,z-d*.99),(.75*w,z-d*.93),(.91*w,z-d*.77),(.985*w,z-d*.48),(.999*w,z-.009),(w,z)]
 return [(-x,y,zz) for x,zz in reversed(row[1:])]+[(x,y,zz) for x,zz in row]
def bent_row(fn,section):
 y,w,z,h=section;t=max(0,min(1,(y-.117)/.027))
 result=[]
 for x,yy,zz in fn(*section):
  if fn==upperrow:
   blend=t*t*(3-2*t);brow=z+h*(1-(x/w)**2);zz=zz*(1-blend)+brow*blend
  result.append((x,yy-.006*t*(abs(x)/w)**6,zz))
 return result
def replace_shell(name,fn,mat):
 rows=[bent_row(fn,row) for row in sections];n=len(rows[0]);vs=[v for row in rows for v in row];fs=[]
 for i in range(len(rows)-1):
  for j in range(n-1):a=i*n+j;fs.append((a,a+1,a+n+1,a+n))
 # Preserve the nose return. The rear edge ends at the fascia, with a true wall rim.
 seam=sections[0][2];bottom=[]
 for j in range(n):
  if j in [0,n-1]:bottom.append(j)
  else:x,y,z=vs[j];bottom.append(len(vs));vs.append((x,y,seam))
 for j in range(n-1):
  face=list(dict.fromkeys([j,j+1,bottom[j+1],bottom[j]]))
  if len(face)>=3:fs.append(tuple(face))
 ob=bpy.data.objects[name];me=bpy.data.meshes.new(name+'_V11');me.from_pydata(vs,[],fs);me.update();ob.data=me;me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 for m in list(ob.modifiers):ob.modifiers.remove(m)
 m=ob.modifiers.new('Controlled shoulder radii','SUBSURF');m.levels=2
 m=ob.modifiers.new('Shell wall','SOLIDIFY');m.thickness=.0018;m.offset=-1
 return ob
shell=replace_shell('BODY_SHELL_TOP',upperrow,TI);cradle=replace_shell('BODY_CRADLE',lowerrow,BLACK)
# Continuous side assembly reveals follow the altered tail outline.
for sign in [-1,1]:
 ob=bpy.data.objects['SHELL_SEAM_'+str(sign)];data=bpy.data.curves.new('V11 shell assembly reveal','CURVE');data.dimensions='3D';data.bevel_depth=.00035;data.bevel_resolution=3
 pts=[(sign*w*.995,y-.006*max(0,min(1,(y-.117)/.027)),z-.0012) for y,w,z,h in sections[1:-1]]
 sp=data.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for bp,p in zip(sp.bezier_points,pts):bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
 ob.data=data;data.materials.append(BLACK)
for ob in list(bpy.data.objects):
 if ob.name.startswith('REAR_') and not ob.name.startswith('REAR_LEG_'):bpy.data.objects.remove(ob,do_unlink=True)
# Shell end profiles provide the real mating contour for the graphite fascia.
def fitted_edge(ob):
 # Use the evaluated shell edge, to avoid a raw-cage
 # mismatch along the rounded rear corners.
 wall=ob.modifiers.get('Shell wall');wall.show_viewport=False;bpy.context.view_layer.update()
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
 candidates=[v for v in bm.verts if v.is_boundary and v.co.y>.140]
 center=min(candidates,key=lambda v:(abs(v.co.x),-v.co.y));chain=[center]
 for edge in [e for e in center.link_edges if e.is_boundary]:
  prev=center;v=edge.other_vert(center)
  for step in range(1000):
   if abs(v.co.x)>.05015 or v.co.y<.135:break
   chain.append(v);nexts=[e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v)!=prev]
   if not nexts:break
   prev,v=v,nexts[0]
 result=sorted([tuple(v.co) for v in chain],key=lambda p:p[0]);bm.free();ev.to_mesh_clear();wall.show_viewport=True;bpy.context.view_layer.update()
 return result
toprow=fitted_edge(shell);bottomrow=fitted_edge(cradle)
def interp(row,x,axis=2):
 for a,b in zip(row,row[1:]):
  if a[0]<=x<=b[0]:
   t=(x-a[0])/(b[0]-a[0]);return a[axis]*(1-t)+b[axis]*t
 return row[0][axis] if x<row[0][0] else row[-1][axis]
def front_y(x,z):
 bottom=interp(bottomrow,x);top=interp(toprow,x)-.0015;t=max(0,min(1,(z-bottom)/max(.001,top-bottom)))
 return interp(bottomrow,x,1)*(1-t)+interp(toprow,x,1)*t-.00010+.00012*math.sin(math.pi*t)
panel_halfwidth=.0498
while any(interp(toprow,sign*panel_halfwidth)-.0015-interp(bottomrow,sign*panel_halfwidth)-.00015<.0005 for sign in [-1,1]):panel_halfwidth-=.00005
cols=80;rows=12;vs=[]
for j in range(rows+1):
 t=j/rows
 for i in range(cols+1):
  x=(i/cols*2-1)*panel_halfwidth;bottom=interp(bottomrow,x)+.00015;top=interp(toprow,x)-.0015;z=bottom*(1-t)+top*t;vs.append((x,front_y(x,z),z))
fs=[]
for j in range(rows):
 for i in range(cols):a=j*(cols+1)+i;fs.append((a,a+cols+1,a+cols+2,a+1))
fascia=mesh('REAR_FASCIA',vs,fs,POD)
for m in list(fascia.modifiers):fascia.modifiers.remove(m)
m=fascia.modifiers.new('Rear panel thickness','SOLIDIFY');m.thickness=.0024;m.offset=-1
bpy.context.view_layer.objects.active=fascia;bpy.ops.object.modifier_apply(modifier=m.name)
# Rounded rectangle loops in the X/Z plane; extrusions face +Y toward the rear.
def outline(w,h,r,cx=0,cz=0):
 pts=[]
 for xx,zz,base in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(9):a=math.radians(base+j*90/8);pts.append((cx+xx+r*math.cos(a),cz+zz+r*math.sin(a)))
 return pts
def slab(name,w,h,r,cx,cz,y0,y1,mat,bent=False,bevel=0):
 pts=outline(w,h,r,cx,cz);n=len(pts);vs=[]
 for y in [y0,y1]:
  for x,z in pts:vs.append((x,(front_y(x,z)+y if bent else y),z))
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return mesh(name,vs,fs,mat,bevel=bevel)
def cut_hole(w,h,r,cx,cz):
 cut=slab('TEMP_REAR_CUT',w,h,r,cx,cz,.130,.153,DARK)
 for m in list(cut.modifiers):cut.modifiers.remove(m)
 bpy.context.view_layer.objects.active=fascia;m=fascia.modifiers.new('Actual recessed opening','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)
def rim(name,outer,inner,cx,cz,y0,y1,mat,bent=False):
 op=outline(*outer,cx,cz);ip=outline(*inner,cx,cz);n=len(op);vs=[]
 for pts,y in [(op,y0),(op,y1),(ip,y0),(ip,y1)]:
  vs.extend((x,(front_y(x,z)+y if bent else y),z) for x,z in pts)
 fs=[]
 for i in range(n):
  q=(i+1)%n;fs.extend([(i,q,n+q,n+i),(2*n+q,2*n+i,3*n+i,3*n+q),(n+i,n+q,3*n+q,3*n+i),(q,i,2*n+i,2*n+q)])
 return mesh(name,vs,fs,mat,bevel=.00008)
# One recessed charging socket, including its mounting pocket, liner and contacts.
portz=.0790;cut_hole(.0214,.0108,.0028,0,portz)
rim('REAR_PORT_MOUNT',(.0211,.0105,.0027),(.0157,.0077,.0021),0,portz,.1389,.14355,POD)
rim('REAR_PORT_LINER',(.0157,.0077,.0021),(.0130,.0051,.0019),0,portz,.1389,.1428,DARK)
rim('REAR_PORT_METAL_SHELL',(.0138,.0059,.0021),(.0126,.0047,.0018),0,portz,.1390,.14255,EDGE)
slab('REAR_PORT_CAVITY',.014,.0061,.0018,0,portz,.1378,.1388,DARK)
slab('REAR_PORT_TONGUE',.0098,.00070,.0003,0,portz,.1388,.1417,DARK)
for j in range(12):
 x=(j-5.5)*.00068
 for sign in [-1,1]:box('REAR_PORT_CONTACT_'+str(j)+'_'+str(sign),(x,.1406,portz+sign*.00040),(.00030,.00145,.00009),GOLD,bevel=.00003)
# Paired capsule slots have actual depth and recessed internal baffles.
for sign in [-1,1]:
 for j,z in enumerate([.0815,.0764]):
  x=sign*.025;tag=str(sign)+'_'+str(j);cut_hole(.0135,.0032,.0015,x,z)
  slab('REAR_VENT_BACK_'+tag,.0134,.0031,.0014,x,z,.1381,.1385,DARK)
  rim('REAR_VENT_TUNNEL_'+tag,(.0137,.0034,.00155),(.0128,.0025,.00115),x,z,-.0047,-.00022,POD,bent=True)
  for k in range(6):box('REAR_VENT_BAFFLE_'+tag+'_'+str(k),(x+(k-2.5)*.00165,.1391,z),(.0004,.0012,.0018),DARK,bevel=.00012)
# Flush lower cover and a fine upper/lower housing split, as in the rear reference.
coverz=.0595;cut_hole(.057,.0150,.0033,0,coverz)
cover=slab('REAR_ACCESS_COVER',.0564,.0144,.0030,0,coverz,-.0024,-.00022,POD,bent=True,bevel=.00022)
for sign in [-1,1]:
 x=sign*.0195;z=.0553;y=front_y(x,z)-.00030
 ring('REAR_ACCESS_COUNTERBORE_'+str(sign),(x,y,z),.0027,.0017,.0004,DARK,axis='Y')
 cyl('REAR_ACCESS_FASTENER_'+str(sign),(x,y-.00012,z),.0019,.00035,BOLT,axis='Y')
 cyl('REAR_ACCESS_HEX_'+str(sign),(x,y+.00009,z),.00086,.00008,DARK,axis='Y',vertices=6)
pts=[(x,front_y(x,.0692)+.00008,.0692) for x in [(-1+2*i/80)*.048 for i in range(81)]]
curve('REAR_HOUSING_REVEAL',pts,.00016,DARK,root)
# Restrained outer corner radii leave the recesses legible at grazing angles.
m=fascia.modifiers.new('Fascia edge radii','BEVEL');m.width=.00015;m.segments=3
fascia.modifiers.new('Weighted fascia normals','WEIGHTED_NORMAL')
# Review views include a full rear perspective and focused panel/connector views.
for name,loc,target,scale in [('rear_three_quarter',(.39,.64,.43),(0,.015,.071),.68),('rear_body',(0,.40,.174),(0,.122,.076),.180),('rear_port',(.035,.252,.127),(0,.143,.0785),.077)]:
 d=bpy.data.cameras.new('CAM_'+name);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new('CAM_'+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.cycles.samples=40;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;bpy.data.objects['STUDIO_GROUND'].hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v11.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=20;s.render.resolution_percentage=70
for name in (['rear_body','rear_port'] if preview else ['hero','rear_three_quarter','rear_body','rear_port']):
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v11'/(name+('-preview' if preview else '')+'.png'));bpy.ops.render.render(write_still=True)
print('V11_COMPLETE')
