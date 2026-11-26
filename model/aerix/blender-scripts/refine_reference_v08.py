"""Reference-led compound shell curves and integrated stereo fascia."""
import bpy,math,ast,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v07.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT'];TI=bpy.data.materials['Titanium — provisional'];BLACK=bpy.data.materials['Graphite']
for node in ast.parse((ROOT/'scripts/blender/polish_exterior_v05.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['material','finish','ring','curve','box','cyl']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<helpers>','exec'))
# y, outer half width, seam height, crown rise. Added rear-waist stations preserve the S return.
sections=[(-.139,.048,.085,.008),(-.137,.057,.085,.010),(-.129,.067,.087,.017),(-.110,.073,.089,.027),(-.083,.076,.091,.034),(-.050,.076,.092,.037),(-.016,.0725,.093,.039),(.014,.068,.093,.040),(.035,.0615,.093,.040),(.051,.0545,.0925,.0385),(.065,.052,.092,.0365),(.079,.054,.091,.033),(.092,.061,.090,.029),(.103,.063,.0895,.026),(.117,.0595,.089,.021),(.129,.051,.088,.014),(.136,.044,.087,.008),(.139,.037,.087,.004)]

def upperrow(y,w,z,h):
 # Ridge stays continuous while the outer strip rises and turns inward around the arm root.
 g=math.exp(-((y-.059)/.039)**2)
 ridge=.66*w + .005*g
 edge=.94*w-.0025*g
 # Cross-section broad convex roof -> bevelled ridge -> side facet -> steep scalloped return.
 row=[(0,z+h),(.30*w,z+h*.978),(.56*w,z+h*.920),(ridge-.0010,z+h*.875),(ridge,z+h*.862),(ridge+.0010,z+h*.835),
      (edge-.001,z+h*(.22+.18*g)+.001),(edge,z+h*(.22+.18*g)),(edge+.0007,z+h*(.19+.17*g)),(.997*w,z+.001),(w,z)]
 return [(-x,y,zz) for x,zz in reversed(row[1:])]+[(x,y,zz) for x,zz in row]

def lowerrow(y,w,z,h):
 d=.024+.025*max(0,1-(y/.15)**6)
 row=[(0,z-d),(.50*w,z-d*.99),(.75*w,z-d*.93),(.91*w,z-d*.77),(.985*w,z-d*.48),(.999*w,z-.009),(w,z)]
 return [(-x,y,zz) for x,zz in reversed(row[1:])]+[(x,y,zz) for x,zz in row]

def replace_shell(name,rowfn,upper,mat):
 rows=[rowfn(*r) for r in sections];n=len(rows[0]);vs=[v for row in rows for v in row];fs=[]
 for i in range(len(rows)-1):
  for j in range(n-1):
   a=i*n+j;fs.append((a,a+1,a+n+1,a+n))
 # Quad end returns avoid subdivision pinching from a large n-gon cap.
 for ri in [0,len(rows)-1]:
  base=ri*n;seam=sections[ri][2];bottom=[]
  for j in range(n):
   if j in [0,n-1]:bottom.append(base+j)
   else:
    x,y,zz=vs[base+j];bottom.append(len(vs));vs.append((x,y,seam))
  for j in range(n-1):
   face=list(dict.fromkeys([base+j,base+j+1,bottom[j+1],bottom[j]]))
   if len(face)>=3:fs.append(tuple(face))
 me=bpy.data.meshes.new(name+'_V08');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects[name];o.data=me;me.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 mod=o.modifiers.new('Controlled shoulder radii','SUBSURF');mod.levels=2
 mod=o.modifiers.new('Shell wall','SOLIDIFY');mod.thickness=.0018;mod.offset=-1
 return o
shell=replace_shell('BODY_SHELL_TOP',upperrow,True,TI);cradle=replace_shell('BODY_CRADLE',lowerrow,False,BLACK)
for o in list(bpy.data.objects):
 if o.name.startswith('SHELL_SEAM_'):bpy.data.objects.remove(o,do_unlink=True)
for sign in [-1,1]:
 pts=[(sign*w*.995,y,z-.0012) for y,w,z,h in sections[1:-1]]
 # Interpolated seam rather than angular polyline, tied to the new shell contour.
 data=bpy.data.curves.new('Shell assembly reveal','CURVE');data.dimensions='3D';data.bevel_depth=.00035;data.bevel_resolution=3
 sp=data.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for bp,p in zip(sp.bezier_points,pts):bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
 o=bpy.data.objects.new('SHELL_SEAM_'+str(sign),data);s.collection.objects.link(o);o.parent=root;data.materials.append(BLACK)
# More neutral fine satin finish; keep the authored microtexture at close range.
p=TI.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.285,.270,.248,1);p.inputs['Metallic'].default_value=.74
for node in TI.node_tree.nodes:
 if node.bl_idname=='ShaderNodeMapRange':node.inputs['To Min'].default_value=.37;node.inputs['To Max'].default_value=.46
 if node.bl_idname=='ShaderNodeTexNoise' and node.inputs['Scale'].default_value==950:node.inputs['Scale'].default_value=420
# Restore the slim visor and build a curved return between the border and lens panel.
FRAME=bpy.data.materials['Visor satin graphite frame'];p=FRAME.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.026,.029,.032,1);p.inputs['Roughness'].default_value=.29
# Frame is vertically slimmer; retain lens clearance at the curved ends.
for name in ['FRONT_VISOR_FRAME','VISOR_OUTER_BORDER','VISOR_INNER_BORDER']:
 ob=bpy.data.objects[name]
 if ob.type=='MESH':
  for v in ob.data.vertices:v.co.z=.0815+(v.co.z-.0815)*.94
 else:
  for sp in ob.data.splines:
   for p in sp.points:p.co.z=.0815+(p.co.z-.0815)*.94
# Continuous concave bevel into the smoked panel, strongest at its rounded end returns.
ns={}
for node in ast.parse((ROOT/'scripts/blender/refine_visor_v07.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['outline','pos']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<fascia helpers>','exec'),globals(),ns)
outline=ns['outline'];pos=ns['pos'];outer=outline(.115,.0205,.007);inner=outline(.107,.0165,.0056);n=len(outer);vs=[]
for t in [0,.16,.40,.70,1]:
 for (xo,zo),(xi,zi) in zip(outer,inner):
  x=xo*(1-t)+xi*t;z=zo*(1-t)+zi*t;xx,yy,zz=pos(x,z,-.1464+.0034*math.sin(t*math.pi/2));vs.append((xx,yy,zz))
fs=[]
for j in range(4):
 for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
me=bpy.data.meshes.new('Visor curved inner return');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('VISOR_RECESSED_RETURN',me);s.collection.objects.link(o);finish(o,o.name,FRAME)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Recut the backplate pockets to the revised lens centers and diameters.
# Leaving the earlier bores produces unwanted reflective crescents in the GLB.
bpy.data.objects.remove(bpy.data.objects['FRONT_VISOR'],do_unlink=True)
border=outline(.115,.0205,.007);nn=len(border)
vs=[pos(x,z,-.144) for x,z in border]+[pos(x,z,-.136) for x,z in border]
fs=[tuple(range(nn-1,-1,-1)),tuple(range(nn,2*nn))]+[(i,(i+1)%nn,(i+1)%nn+nn,i+nn) for i in range(nn)]
me=bpy.data.meshes.new('Stereo aligned backplate');me.from_pydata(vs,[],fs);me.update();plate=bpy.data.objects.new('FRONT_VISOR',me);s.collection.objects.link(plate);finish(plate,plate.name,bpy.data.materials['Continuous smoked visor'])
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for sign in [-1,1]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.00672,depth=.025,location=(sign*.044*1.03,-.143,.0805),rotation=(math.pi/2,0,0));cut=bpy.context.object
 bpy.context.view_layer.objects.active=plate;mod=plate.modifiers.new('Aligned stereo recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Slim the lens rims and make their convex glass darker and less blue.
for o in bpy.data.objects:
 if o.name.startswith('STEREO_'):
  o.location.x*=1.03
  if o.type=='MESH':
   o.scale.x*=.90
   if abs(o.rotation_euler.x)>1:o.scale.y*=.90
   else:o.scale.z*=.90
for name,col,metal,rough in [('Stereo blue green multilayer coating',(.003,.009,.012),.38,.10),('Stereo central convex element',(.002,.007,.010),.27,.07),('Stereo central pupil',(.001,.003,.005),.2,.06),('Optical anodized rings',(.005,.007,.009),.4,.27)]:
 p=bpy.data.materials[name].node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
# Larger central dome / smaller pupil give the lenses a convex, optical appearance.
for sign in [-1,1]:
 pupil=bpy.data.objects['STEREO_PUPIL_'+str(sign)];pupil.scale.x*=.75;pupil.scale.z*=.75;pupil.location.y-=.00012
 glass=bpy.data.objects['STEREO_GLASS_'+str(sign)+'_1'];glass.scale.y*=1.25
# Rectangular catchlights are reflected from lights, not painted on the lenses.
light=bpy.data.lights['OPTICAL_CATCHLIGHT'];light.energy=.065;light.size=.018;light.size_y=.028
# Review camera matches the reference crop while retaining hero overview.
d=bpy.data.cameras.new('CAM_body');d.type='ORTHO';d.ortho_scale=.35;o=bpy.data.objects.new('CAM_body',d);s.collection.objects.link(o);o.location=(.26,-.54,.48);o.rotation_euler=(Vector((0,-.012,.101))-o.location).to_track_quat('-Z','Y').to_euler()
# Project a finely tessellated wordmark vertically onto the crown; this retains all strokes.
word=bpy.data.objects['AERIX_WORDMARK'];assert word.data.body=='AERIX',word.data.body
for mod in list(word.modifiers):word.modifiers.remove(mod)
bpy.ops.object.select_all(action='DESELECT');word.select_set(True);bpy.context.view_layer.objects.active=word
word.location.z=.145;bpy.ops.object.convert(target='MESH');word=bpy.context.object
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
bm=bmesh.new();bm.from_mesh(word.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True);bm.to_mesh(word.data);bm.free()
mod=word.modifiers.new('Printed wordmark projection','SHRINKWRAP');mod.target=shell;mod.wrap_method='PROJECT';mod.use_project_z=True;mod.use_negative_direction=True;mod.use_positive_direction=False;mod.offset=.0001
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.cycles.samples=32;bpy.data.objects['STUDIO_GROUND'].hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v08.blend'))
preview='--preview' in sys.argv or '--rear-preview' in sys.argv
if preview:s.render.resolution_percentage=65;s.cycles.samples=20
for name in (['rear'] if '--rear-preview' in sys.argv else ['body','visor'] if preview else ['hero','body','visor','top','rear']):
 s.camera=bpy.data.objects['CAM_'+name];bpy.data.objects['STUDIO_GROUND'].hide_render=name in ['top','rear'];s.render.filepath=str(ROOT/'renders/exterior-v08'/((name+'-preview.png') if preview else name+'.png'));bpy.ops.render.render(write_still=True)
print('V08_COMPLETE')
