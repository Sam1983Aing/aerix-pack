"""Sample major-body, blade and arm clearances through the folding study."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-folding-v26.blend'))
s=bpy.context.scene;s.frame_set(1);deps=bpy.context.evaluated_depsgraph_get()
fixed=['BODY_CRADLE','BODY_SHELL_TOP','REAR_FASCIA','FRONT_VISOR_FRAME','CAMERA_HOUSING','LENS_BARREL']
tags=['FL','FR','RL','RR'];moving=[];tag_of={}
for tag in tags:
 for name in [p+tag for p in ['ARM_','ARM_INLAY_','MOTOR_BASE_','MOTOR_','FOOT_PAD_']]+[f'BLADE_{tag}_{k}' for k in [0,1]]:
  moving.append(name);tag_of[name]=tag
geometry={}
for name in fixed+moving:
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);mesh=ev.to_mesh()
 geometry[name]=([v.co.copy() for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons]);ev.to_mesh_clear()
def surface(name):
 o=bpy.data.objects[name];vertices,faces=geometry[name];vs=[o.matrix_world@v for v in vertices]
 return {'vs':vs,'fs':faces,'box':[(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]}
def overlaps(a,b):return all(a['box'][i][0]<b['box'][i][1] and b['box'][i][0]<a['box'][i][1] for i in range(3))
def tree(d):
 if 'tree' not in d:d['tree']=BVHTree.FromPolygons(d['vs'],d['fs'])
 return d['tree']
static={n:surface(n) for n in fixed};hits=[];bounds={}
frames=sorted(set(range(1,242,4))|{44,92,169,241})
for frame in frames:
 s.frame_set(frame);bpy.context.view_layer.update();surfaces={n:surface(n) for n in moving};pairs=[]
 for name,a in surfaces.items():
  for other,b in static.items():
   if overlaps(a,b):pairs.append((name,other,a,b))
 for i,name in enumerate(moving):
  a=surfaces[name]
  for other in moving[i+1:]:
   if tag_of[name]==tag_of[other] and not(name.startswith('BLADE_') or other.startswith('BLADE_')):continue
   b=surfaces[other]
   if overlaps(a,b):pairs.append((name,other,a,b))
 for name,other,a,b in pairs:
  contacts=tree(a).overlap(tree(b))
  if contacts:hits.append({'frame':frame,'a':name,'b':other,'triangle_pairs':len(contacts)})
 if frame in [1,241]:
  all_surfaces=list(surfaces.values())+list(static.values())
  bounds[str(frame)]=[max(d['box'][i][1] for d in all_surfaces)-min(d['box'][i][0] for d in all_surfaces) for i in range(3)]
 if frame%40==1:print('CLEARANCE_FRAME',frame,'contacts',len(hits),flush=True)
report={'sampled_frames':frames,'sampled_surfaces':fixed+moving,'intersections':hits,'major_component_bounds_m':bounds,'scope':'Triangle-surface checks on body, camera, arm beams, motor housings, feet and all eight blades. Existing hinge-cap seating overlaps and small fastener interfaces are outside this check.'}
(R/'renders/folding-v26/clearance-validation.json').write_text(json.dumps(report,indent=2));print('CLEARANCE_COMPLETE',len(hits),bounds,flush=True)
assert not hits,hits[:10]
