"""Reference-led shell facets, dark composite blades, and recessed stereo optics."""
import bpy, math, json, ast, bmesh, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v05.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
BLACK=bpy.data.materials['Graphite'];TI=bpy.data.materials['Titanium — provisional']
# Reuse geometry primitives without executing the earlier build.
tree=ast.parse((ROOT/'scripts/blender/polish_exterior_v05.py').read_text())
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['material','finish','box','cyl','ring']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<geometry helpers>','exec'))
sections=[(-.139,.047,.085,.006),(-.137,.056,.085,.008),(-.129,.066,.087,.015),(-.106,.074,.089,.026),(-.068,.076,.091,.034),(-.018,.073,.093,.036),(.028,.065,.093,.036),(.060,.058,.092,.033),(.080,.058,.091,.030),(.098,.063,.090,.026),(.117,.059,.089,.021),(.134,.048,.087,.010),(.138,.039,.087,.004)]
# Support loops concentrate the radius at the crown/shoulder break.
profile=[(0,1),(.32,.998),(.62,.985),(.65,.981),(.67,.972),(.69,.944),(.94,.24),(.98,.07),(1,0)]
profile=[(-u,h) for u,h in reversed(profile[1:])]+profile
verts=[(u*w,y,z+h*f) for y,w,z,h in sections for u,f in profile];n=len(profile)
faces=[]
for i in range(len(sections)-1):
 for j in range(n-1):
  a=i*n+j;faces.append((a,a+1,a+n+1,a+n))
faces.extend([tuple(range(n-1,-1,-1)),tuple((len(sections)-1)*n+j for j in range(n))])
ob=bpy.data.objects['BODY_SHELL_TOP'];me=bpy.data.meshes.new('Defined crown and shoulder panels');me.from_pydata(verts,[],faces);me.update();ob.data=me;me.materials.append(TI)
for p in me.polygons:p.use_smooth=True
# Grow the cradle and the existing seam to match the new section widths.
oldwidth=[.045,.056,.064,.069,.070,.066,.060,.054,.054,.059,.055,.045,.038]
cradle=bpy.data.objects['BODY_CRADLE']
for i,v in enumerate(cradle.data.vertices):v.co.x*=sections[i//17][1]/oldwidth[i//17]
for sign in [-1,1]:
 seam=bpy.data.objects['SHELL_SEAM_'+str(sign)]
 for bp,(y,w,z,h) in zip(seam.data.splines[0].bezier_points,sections[1:-1]):bp.co=(sign*w*.98,y,z-.0012)
word=bpy.data.objects['AERIX_WORDMARK'];word.location.z=.1205;word.rotation_euler.x=math.radians(13)
# Satin titanium and a dedicated darker, less specular blade finish.
p=TI.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.29,.275,.25,1);p.inputs['Metallic'].default_value=.65
for node in TI.node_tree.nodes:
 if node.bl_idname=='ShaderNodeMapRange':node.inputs['To Min'].default_value=.43;node.inputs['To Max'].default_value=.51
blade=bpy.data.materials['Satin carbon-composite propellers'];p=blade.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.004,.005,.006,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.52;p.inputs['Specular IOR Level'].default_value=.22
# Replace all old protruding front sensor pieces; preserve downward optics.
for o in list(bpy.data.objects):
 if o.name.startswith(('FRONT_SENSOR_','SENSOR_RIM_','SENSOR_PUPIL_','SENSOR_GLASS_','SENSOR_OPTICAL_','SENSOR_COATED_')):bpy.data.objects.remove(o,do_unlink=True)
visor=bpy.data.objects['FRONT_VISOR'];bpy.context.view_layer.objects.active=visor
for mod in list(visor.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
DARK=material('Stereo optical recess',(.002,.003,.004),0,.32)
IRIS=material('Stereo internal lens coating',(.008,.020,.022),.35,.19)
GLASS=material('Stereo clear curved glass',(.018,.038,.043),.4,.10);p=GLASS.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.25;p.inputs['IOR'].default_value=1.46
for sign in [-1,1]:
 x=sign*.044;z=.0815
 bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.0075,depth=.025,location=(x,-.143,z),rotation=(math.pi/2,0,0));cut=bpy.context.object
 bpy.context.view_layer.objects.active=visor;mod=visor.modifiers.new('Recessed stereo lens bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 ring('STEREO_SOCKET_'+str(sign),(x,-.140,z),.00745,.0058,.007,DARK,axis='Y')
 ring('STEREO_FRONT_RIM_'+str(sign),(x,-.1436,z),.0074,.0065,.0006,BLACK,axis='Y')
 ring('STEREO_INNER_RIM_'+str(sign),(x,-.1426,z),.0059,.00465,.0007,BLACK,axis='Y')
 cyl('STEREO_BACKING_'+str(sign),(x,-.137,z),.0058,.0005,DARK,axis='Y')
 ring('STEREO_IRIS_'+str(sign),(x,-.138,z),.0044,.0026,.0004,IRIS,axis='Y')
 cyl('STEREO_PUPIL_'+str(sign),(x,-.1382,z),.0025,.0003,DARK,axis='Y')
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(x,-.1424,z));o=bpy.context.object;o.scale=(.00465,.00065,.00465);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'STEREO_GLASS_'+str(sign),GLASS)
# Fine concentric optical features read through the smoked cover in a product shot.
for sign in [-1,1]:
 x=sign*.044;z=.0815
 ring('STEREO_VISIBLE_IRIS_'+str(sign),(x,-.14306,z),.0031,.0020,.00012,IRIS,axis='Y')
 cyl('STEREO_CENTER_'+str(sign),(x,-.14312,z),.00185,.0001,DARK,axis='Y')
# Normals on replaced geometry.
for obj in [ob,visor,cradle]:
 bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1);bpy.data.objects['STUDIO_GROUND'].hide_render=False
s.cycles.samples=32;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v06.blend'))
preview='--preview' in sys.argv
if preview:s.cycles.samples=24;s.render.resolution_percentage=65
for name in (['hero'] if preview else ['hero','camera','top','front']):
 s.camera=bpy.data.objects['CAM_'+name];bpy.data.objects['STUDIO_GROUND'].hide_render=name in ['top','front']
 s.render.filepath=str(ROOT/'renders/exterior-v06'/('preview.png' if preview else name+'.png'));bpy.ops.render.render(write_still=True)
print('EXTERIOR_V06_COMPLETE')
