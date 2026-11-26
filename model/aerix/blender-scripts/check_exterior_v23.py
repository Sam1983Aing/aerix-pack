"""Validate cleaned rear surfaces, actual openings, and preservation of V22."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
REBUILT={'REAR_FASCIA','REAR_ACCESS_COVER','REAR_ACCESS_GASKET','REAR_PORT_MOUNT','REAR_PORT_LINER','REAR_PORT_METAL_SHELL','REAR_HOUSING_REVEAL','REAR_HOOD_RETURN'}|{'REAR_VENT_TUNNEL_'+str(sign)+'_'+str(j) for sign in [-1,1] for j in [0,1]}
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();result={}
 for o in bpy.context.scene.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name in REBUILT|{'STUDIO_GROUND','BODY_CRADLE','BODY_SHELL_TOP'}:continue
  ev=o.evaluated_get(deps);m=ev.to_mesh();result[o.name]=([tuple(ev.matrix_world@v.co) for v in m.vertices],[i.vertex_index for i in m.loops],[q.name if q else None for q in m.materials]);ev.to_mesh_clear()
 return result
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'));before=snapshot();oldroof=[tuple(v.co) for v in bpy.data.objects['BODY_SHELL_TOP'].data.vertices];oldcradle=[tuple(v.co) for v in bpy.data.objects['BODY_CRADLE'].data.vertices];oldns=[tuple(n.vector) for n in bpy.data.objects['BODY_CRADLE'].data.corner_normals];visor_ns=[tuple(n.vector) for n in bpy.data.objects['FRONT_VISOR'].data.corner_normals]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'));after=snapshot();unexpected=[n for n in before.keys()|after.keys() if before.get(n)!=after.get(n)];topology={}
for name in REBUILT|{'BODY_CRADLE','BODY_SHELL_TOP'}:
 o=bpy.data.objects[name]
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seen=set();components=0
 for start in bm.verts:
  if start.index in seen:continue
  components+=1;todo=[start]
  while todo:
   v=todo.pop()
   if v.index in seen:continue
   seen.add(v.index);todo.extend(e.other_vert(v) for e in v.link_edges)
 topology[name]={'vertices':len(bm.verts),'components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-16 for f in bm.faces),'positive_volume':bm.calc_volume(signed=True)>0,'invalid_normals':sum(not all(math.isfinite(x) for x in n.vector) or n.vector.length<.99 for n in o.data.corner_normals)};bm.free()
cm=bpy.data.objects['BODY_CRADLE'].data;outside=[v.index for v in cm.vertices if (oldcradle[v.index][1]<=.116 or oldcradle[v.index][2]<=.084) and tuple(v.co)!=oldcradle[v.index]]
def angle(a,b):return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))))))
rim_loops={li for p in cm.polygons if cm.materials[p.material_index].name=='V23 satin rear shell rim' for li in p.loop_indices}
normal_error=max(angle(oldns[i],n.vector) for i,n in enumerate(cm.corner_normals) if i not in rim_loops and (cm.vertices[cm.loops[i].vertex_index].co.y<=.112 or cm.vertices[cm.loops[i].vertex_index].co.z<=.083))
fascia=bpy.data.objects['REAR_FASCIA'];tree=BVHTree.FromPolygons([v.co for v in fascia.data.vertices],[tuple(p.vertices) for p in fascia.data.polygons]);openings=[]
for x,z in [(0,.079),(0,.0595)]+[(sign*.025*.97,z) for sign in [-1,1] for z in [.0815,.0764]]:
 p,n,i,d=tree.ray_cast(Vector((x,.16,z)),Vector((0,-1,0)),.035);openings.append(p is None)
roof=bpy.data.objects['BODY_SHELL_TOP'];surfaces={o.name:BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons]) for o in [roof,bpy.data.objects['BODY_CRADLE'],bpy.data.objects['REAR_HOOD_RETURN']]};boundary=list(roof['top_boundary_edges']);probes=[]
for ia,ib in zip(boundary[::2],boundary[1::2]):
 a=roof.data.vertices[ia].co;b=roof.data.vertices[ib].co
 if min(a.y,b.y)<.130 or ia%5:continue
 q=(a+b)*.5;d=b-a;n=Vector((d.y,-d.x,0)).normalized()
 if n.dot(Vector((q.x,q.y,0)))<0:n.negate()
 q.z-=.0010;hits={}
 for name,t in surfaces.items():
  p,no,index,dist=t.ray_cast(q+n*.003,-n,.012)
  if p is not None:hits[name]=dist
 if 'BODY_SHELL_TOP' in hits and len(hits)>1:probes.append({'x':q.x,'clearance_mm':1000*(min(v for k,v in hits.items() if k!='BODY_SHELL_TOP')-hits['BODY_SHELL_TOP'])})
checks={'other_geometry_and_materials_preserved':not unexpected,'roof_silhouette_preserved':oldroof==[tuple(v.co) for v in roof.data.vertices],'chassis_change_limited_to_rear_upper_edge':not outside,'prior_chassis_normals_within_0_05_degrees':normal_error<.05,'V22_visor_normals_exactly_preserved':visor_ns==[tuple(n.vector) for n in bpy.data.objects['FRONT_VISOR'].data.corner_normals],'closed_connected_positive_meshes':all(t['components']==1 and t['nonmanifold_edges']==0 and t['positive_volume'] for t in topology.values()),'no_degenerate_faces_or_invalid_normals':all(t['degenerate_faces']==0 and t['invalid_normals']==0 for t in topology.values()),'all_six_rear_panel_apertures_open':all(openings),'rear_lip_separation_above_0_25_mm':len(probes)>15 and min(p['clearance_mm'] for p in probes)>.25,'single_port_and_contacts_preserved':not any(n.startswith('BELLY_PORT_') for n in bpy.data.objects.keys()) and sum(n.startswith('REAR_PORT_CONTACT_') for n in bpy.data.objects.keys())==24}
report={'checks':checks,'preserved_objects':len(before),'unexpected_changes':unexpected,'topology':topology,'maximum_other_chassis_normal_error_degrees':normal_error,'rear_clearance_probes':probes};(R/'renders/exterior-v23/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);assert all(checks.values())
