"""Check repaired seam clearance, paired shoulders and preservation of approved parts."""
import bpy,bmesh,math,ast,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
def snapshot():
 d=bpy.context.evaluated_depsgraph_get();out={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in {'STUDIO_GROUND','BODY_CRADLE'} or o.name.startswith('SHELL_SEAM_'):continue
  e=o.evaluated_get(d);m=e.to_mesh();out[o.name]=([tuple(e.matrix_world@v.co) for v in m.vertices],[i.vertex_index for i in m.loops],[x.name if x else None for x in m.materials]);e.to_mesh_clear()
 return out
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v19.blend'));before=snapshot();m=bpy.data.objects['BODY_CRADLE'].data
coords=[tuple(v.co) for v in m.vertices];normals=[tuple(n.vector) for n in m.corner_normals];loops=[l.vertex_index for l in m.loops]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'));after=snapshot();o=bpy.data.objects['BODY_CRADLE'];m=o.data
unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();seen=set();components=[]
for v in bm.verts:
 if v.index in seen:continue
 todo=[v];num=0
 while todo:
  v=todo.pop()
  if v.index in seen:continue
  seen.add(v.index);num+=1;todo.extend(e.other_vert(v) for e in v.link_edges)
 components.append(num)
topology={'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'components':components,'volume_m3':bm.calc_volume(signed=True)};bm.free()
under_error=max((v.co-Vector(coords[v.index])).length for v in m.vertices if coords[v.index][2]<.058)
under_norm=max((m.corner_normals[i].vector-Vector(n)).length for i,n in enumerate(normals) if coords[loops[i]][2]<.0575)
m.calc_loop_triangles();surf=BVHTree.FromPolygons([v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);mirror=[]
for v in m.vertices:
 p=v.co
 if p.x>.043 and .053<p.y<.109 and .0655<p.z<.087:
  d=surf.find_nearest(Vector((-p.x,p.y,p.z)))[3];mirror.append(d)
  if d>.000075:print('MIRROR_OUTLIER',tuple(p),d,flush=True)
for n in ast.parse((R/'scripts/blender/refine_body_v16.py').read_text()).body:
 if isinstance(n,ast.FunctionDef) and n.name=='interpolator':exec(compile(ast.Module(body=[n],type_ignores=[]),'<profile>','exec'))
seam=interpolator([(-.1355,.0940),(-.105,.0922),(-.060,.0920),(.028,.0920),(.077,.0911),(.128,.0900)])
roof=bpy.data.objects['BODY_SHELL_TOP'];clearance=[]
for sign in [-1,1]:
 for j in range(61):
  y=-.075+j*.0018;z=seam(y)-.00105;p=Vector((sign*.15,y,z));d=Vector((-sign,0,0))
  a,pa,_,_=roof.ray_cast(p,d);b,pb,_,_=o.ray_cast(p,d)
  if a and b:clearance.append(abs(pa.x)-abs(pb.x))
checks={'other_approved_exterior_parts_preserved':not unexpected,'roof_geometry_and_material_unchanged':before['BODY_SHELL_TOP']==after['BODY_SHELL_TOP'],'chassis_single_closed_component':topology['nonmanifold_edges']==0 and len(components)==1,'positive_chassis_volume':topology['volume_m3']>0,'no_degenerate_faces':topology['degenerate_faces']==0,'underside_geometry_unchanged':under_error<1e-8,'underside_normals_preserved_within_0_1_degrees':under_norm<.001745,'valid_normals':all(all(math.isfinite(x) for x in n.vector) and n.vector.length>.99 for n in m.corner_normals),'paired_upper_shoulders_within_0_075_mm':max(mirror)<.000075,'body_seam_clearance_at_least_0_35_mm':min(clearance)>.00035,'single_rear_port_preserved':not any(n.startswith('BELLY_PORT_') for n in bpy.data.objects.keys()) and bpy.data.objects.get('REAR_PORT_MOUNT') is not None,'rear_collars_follow_arm_pivots':all(bpy.data.objects['HINGE_ROTATING_COLLAR_'+tag].parent==bpy.data.objects['ARM_'+tag+'_ROOT'] for tag in ['RL','RR'])}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'topology':topology,'underside_max_geometry_error_m':under_error,'underside_max_normal_error':under_norm,'shoulder_mirror_surface_max_error_m':max(mirror),'shoulder_samples':len(mirror),'seam_clearance_min_m':min(clearance),'seam_clearance_max_m':max(clearance),'seam_samples':len(clearance)}
(R/'renders/exterior-v20/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
