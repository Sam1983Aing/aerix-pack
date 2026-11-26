"""Preservation, topology, symmetry, fitted perimeter and embedded optic checks."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
def revised(name):return name in {'BODY_CRADLE','BODY_SHELL_TOP','AERIX_WORDMARK','STATUS_LIGHT'} or (name.startswith('REAR_') and not name.startswith('REAR_LEG_')) or name.startswith(('FRONT_VISOR','VISOR_','STEREO_','SHELL_SEAM_'))
def snapshot():
 out={};deps=bpy.context.evaluated_depsgraph_get()
 for ob in bpy.context.scene.objects:
  if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.name=='STUDIO_GROUND' or revised(ob.name):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();out[ob.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[p.vertex_index for p in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'));before=snapshot();belly_before=[v.co.copy() for v in bpy.data.objects['BODY_CRADLE'].data.vertices if v.co.z<.060]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v15.blend'));after=snapshot();deps=bpy.context.evaluated_depsgraph_get();s=bpy.context.scene
unexpected=[];maximum=0
for name in before.keys()|after.keys():
 if name not in before or name not in after:unexpected.append(name);continue
 a,b=before[name],after[name]
 if len(a[0])!=len(b[0]) or a[1:]!=b[1:]:unexpected.append(name);continue
 error=max((Vector(x)-Vector(y)).length for x,y in zip(a[0],b[0]));maximum=max(maximum,error)
 if error>1e-7:unexpected.append(name)
def topo(ob):
 ev=ob.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();seen=set();components=[]
 for start in bm.verts:
  if start.index in seen:continue
  todo=[start];size=0
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);size+=1;todo.extend(e.other_vert(v) for e in v.link_edges)
  components.append(size)
 report={'vertices':len(bm.verts),'components':len(components),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free();ev.to_mesh_clear();return report
names=['BODY_SHELL_TOP','BODY_CRADLE','FRONT_VISOR_FRAME','FRONT_VISOR','REAR_HOOD_RETURN'];topology={name:topo(bpy.data.objects[name]) for name in names}
shell=bpy.data.objects['BODY_SHELL_TOP'];coords=[v.co.copy() for v in shell.data.vertices];tree=kdtree.KDTree(len(coords))
for i,p in enumerate(coords):tree.insert(p,i)
tree.balance();symmetry=max(tree.find(Vector((-p.x,p.y,p.z)))[2] for p in coords)
cradle=bpy.data.objects['BODY_CRADLE'];ctree=kdtree.KDTree(len(cradle.data.vertices))
for i,v in enumerate(cradle.data.vertices):ctree.insert(v.co,i)
ctree.balance();surface=BVHTree.FromObject(cradle,deps);belly_error=max(surface.find_nearest(p)[3] for p in belly_before)
# The unthickened roof must not fold over itself around the nose and tail corners.
folds=sum(face.normal.z<-.000001 for face in shell.data.polygons)
# Sample the shell perimeter and find the chassis return directly below it.
bm=bmesh.new();bm.from_mesh(shell.data);boundary={v.index for e in bm.edges if e.is_boundary for v in e.verts};bm.free();samples=[];ev=cradle.evaluated_get(deps)
for i in sorted(boundary)[::12]:
 p=coords[i]
 if min(math.hypot(p.x-x,p.y-y) for x,y in [(-.085,-.089),(.085,-.089),(-.070,.086),(.070,.086)])<.017:continue
 origin=Vector((p.x*.997,p.y*.997,p.z+.010));hit,point,normal,idx=ev.ray_cast(origin,Vector((0,0,-1)))
 samples.append({'point':list(p),'hit':hit,'gap_m':p.z-point.z if hit else None})
def nose_y(x):return -.1355-.016*math.sqrt(max(.000001,1-(x/.0672)**2))
recesses={}
for ob in s.objects:
 if ob.name.startswith('STEREO_'):
  ev=ob.evaluated_get(deps);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];recesses[ob.name]=min(p.y-nose_y(p.x) for p in ps);ev.to_mesh_clear()
checks={'approved_arms_motors_and_underside_details_preserved':not unexpected,'lower_belly_surface_preserved':belly_error<1e-7,'primary_parts_closed_manifold':all(v['nonmanifold_edges']==0 for v in topology.values()),'chassis_one_connected_component':topology['BODY_CRADLE']['components']==1,'shell_bilaterally_symmetric':symmetry<1e-7,'no_roof_surface_foldovers':folds==0,'shell_perimeter_meets_upper_chassis':all(p['hit'] and -.001<p['gap_m']<.0030 for p in samples),'all_front_optics_inside_nose_envelope':min(recesses.values())>.002,'four_independent_rotors':all(bpy.data.objects['PROPELLER_'+tag].parent==bpy.data.objects['ARM_'+tag+'_ROOT'] for tag in ['FL','FR','RL','RR']),'materials_assigned':all(m for n in names for m in bpy.data.objects[n].data.materials)}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'max_preserved_world_error_m':maximum,'lower_belly_surface_error_m':belly_error,'symmetry_error_m':symmetry,'roof_foldover_faces':folds,'topology':topology,'perimeter_fit_samples':samples,'optics_depth_behind_nose_m':recesses};(ROOT/'renders/exterior-v15/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert all(checks.values())
