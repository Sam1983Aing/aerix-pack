"""Validate edge cleanup, watertight parts and preservation of the approved exterior."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
REBUILT={'BELLY_SPINE','BELLY_SERVICE_PANEL','BELLY_SENSOR_BRIDGE','BELLY_PORT_PAD','BELLY_PANEL_REVEAL','BELLY_VENT_TUNNEL_-1','BELLY_VENT_TUNNEL_1','DOWN_SENSOR_HOUSING_-1','DOWN_SENSOR_HOUSING_1'}
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND' or o.name in REBUILT:continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();out[o.name]=([tuple(ev.matrix_world@v.co) for v in me.vertices],[i.vertex_index for i in me.loops],[m.name if m else None for m in me.materials]);ev.to_mesh_clear()
 return out
def upper_normals():
 me=bpy.data.objects['BODY_CRADLE'].data
 return {li:tuple(me.corner_normals[li].vector) for p in me.polygons if p.center.z>.061 for li in p.loop_indices}
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'));before=snapshot();oldnormals=upper_normals()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v18.blend'));after=snapshot();deps=bpy.context.evaluated_depsgraph_get()
changed=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)]
newnormals=upper_normals();normal_error=max((Vector(n)-Vector(newnormals[li])).length for li,n in oldnormals.items())
topo={}
for name in sorted(REBUILT|{'BODY_CRADLE'}):
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 topo[name]={'vertices':len(bm.verts),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'volume_m3':abs(bm.calc_volume()),'invalid_normals':sum(not all(math.isfinite(v) for v in n.vector) or n.vector.length<.99 for n in me.corner_normals)}
 bm.free();ev.to_mesh_clear()
cradle=bpy.data.objects['BODY_CRADLE'].evaluated_get(deps)
apertures=[(0,-.012,.063),(-.025,.0695,.062),(.025,.0695,.062),(0,.1215,.075),(-.0328,.1215,.074),(.0328,.1215,.074)]
openings=[]
for x,y,limit in apertures:
 hit,p,n,i=cradle.ray_cast(Vector((x,y,-.03)),Vector((0,0,1)));openings.append(not hit or p.z>=limit-1e-6)
clearances=[]
for sign in [-1,1]:
 housing=bpy.data.objects['DOWN_SENSOR_HOUSING_'+str(sign)].evaluated_get(deps);trim=bpy.data.objects['DOWN_SENSOR_EDGE_'+str(sign)].evaluated_get(deps)
 for j in range(64):
  a=j*math.tau/64;p=Vector((sign*.025+.0089*math.cos(a),.0695+.0089*math.sin(a),-.03));d=Vector((0,0,1))
  h,hp,_,_=housing.ray_cast(housing.matrix_world.inverted()@p,d);t,tp,_,_=trim.ray_cast(trim.matrix_world.inverted()@p,d)
  assert h and t
  clearances.append((housing.matrix_world@hp).z-(trim.matrix_world@tp).z)
checks={'all_other_exterior_geometry_and_materials_preserved':not changed,'upper_chassis_normals_preserved':normal_error<.0002,'closed_parts':all(t['nonmanifold_edges']==0 and t['volume_m3']>1e-14 for t in topo.values()),'no_degenerate_faces':all(t['degenerate_faces']==0 for t in topo.values()),'finite_unit_normals':all(t['invalid_normals']==0 for t in topo.values()),'six_real_apertures_preserved':all(openings),'circular_sensor_trim_clear_of_surround':min(clearances)>.00010,'camera_preserved':all(before.get(n)==after.get(n) for n in before if n.startswith(('LENS_','CAMERA_','GIMBAL_'))),'four_arm_pivots':all(bpy.data.objects['ARM_UNDER_INSERT_'+t].parent==bpy.data.objects['ARM_'+t+'_ROOT'] for t in ['FL','FR','RL','RR'])}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':changed,'upper_normal_max_vector_error':normal_error,'sensor_trim_min_clearance_m':min(clearances),'topology':topo,'apertures':openings};(R/'renders/exterior-v18/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
