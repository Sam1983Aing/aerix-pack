"""Native interior inspection renders and assembly clearance sampling."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];OUT=R/'renders/interior-v28';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v28.blend'));s=bpy.context.scene;s.frame_set(400)
config=json.loads((OUT/'integration-config.json').read_text());added=config['new_mesh_names'];d=bpy.context.evaluated_depsgraph_get()
def surface(o):
 e=o.evaluated_get(d);m=e.to_mesh();v=[e.matrix_world@q.co for q in m.vertices];p=[tuple(p.vertices) for p in m.polygons];e.to_mesh_clear()
 return {'v':v,'p':p,'box':[(min(x[i] for x in v),max(x[i] for x in v)) for i in range(3)],'tree':None}
def tree(a):
 if a['tree'] is None:a['tree']=BVHTree.FromPolygons(a['v'],a['p'])
 return a['tree']
def check(a,b):
 if not all(a['box'][i][0]<b['box'][i][1] and b['box'][i][0]<a['box'][i][1] for i in range(3)):return 0
 return len(tree(a).overlap(tree(b)))
static={n:surface(bpy.data.objects[n]) for n in ['BODY_SHELL_TOP','BODY_CRADLE','FRONT_VISOR_FRAME','FRONT_VISOR','REAR_FASCIA','CAMERA_HOUSING']}
internal={n:surface(bpy.data.objects[n]) for n in added};hits=[]
for name,a in internal.items():
 for name2,b in static.items():
  count=check(a,b)
  if count:hits.append({'internal':name,'exterior':name2,'triangle_pairs':count})
print('STATIC_FIT_HITS',json.dumps(hits),flush=True)
# Sample the existing arm/rotor mechanism against the added internals throughout its unchanged motion.
foldhits=[];moving=[p+t for t in ['FL','FR','RL','RR'] for p in ['ARM_','ARM_INLAY_','MOTOR_','MOTOR_BASE_','FOOT_PAD_']]+[f'BLADE_{t}_{k}' for t in ['FL','FR','RL','RR'] for k in [0,1]]
for frame in sorted(set(range(1,362,12))|{44,98,167,260,361}):
 s.frame_set(frame);bpy.context.view_layer.update()
 for n in moving:
  a=surface(bpy.data.objects[n])
  for ni,b in internal.items():
   count=check(a,b)
   if count:foldhits.append({'frame':frame,'moving':n,'internal':ni,'triangle_pairs':count})
s.frame_set(400);bpy.context.view_layer.update();before={o.name:[v for row in o.matrix_world for v in row] for o in s.objects if o.type not in {'CAMERA','LIGHT'}}
s.frame_set(971);bpy.context.view_layer.update();err=max(abs(a-b) for o in s.objects if o.name in before for a,b in zip(before[o.name],[v for row in o.matrix_world for v in row]))
report={'shell_surface_intersections':hits,'fold_surface_intersections':foldhits,'reassembly_matrix_max_error':err,'fold_samples':35,'scope':'Added internal meshes against shell, cradle, front face, rear fascia and camera housing; major arm/motor/foot/blade surfaces sampled through folding. Surface intersections do not prove containment; fastener seats and internal part-to-part fits are reviewed separately.'}
(OUT/'fit-validation.json').write_text(json.dumps(report,indent=2));print('FIT_COMPLETE',len(hits),len(foldhits),err,flush=True)
if '--check-only' in sys.argv:sys.exit(0)
# Native Cycles views use identical studio settings and the real source master.
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True;s.render.resolution_percentage=100;s.render.resolution_x=1400;s.render.resolution_y=1100
s.world.color=(.12,.12,.12)
for o in s.objects:
 if o.type=='LIGHT' and o.name.startswith('LIGHT_REAR_INSPECTION'):o.hide_render=True
bpy.data.objects['STUDIO_GROUND'].hide_render=True
model=[o for o in s.objects if o.type in {'MESH','FONT','CURVE'} and not o.hide_render]
def camera(n,loc,target,scale):
 d=bpy.data.cameras.new('V28_CAM_'+n);d.type='ORTHO';d.ortho_scale=scale;o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def desc(n):o=bpy.data.objects[n];return {o,*o.children_recursive}
views=[('assembled',400,(.54,-.82,.62),(0,-.005,.075),.67,None),('exploded',521,(.58,-.90,.69),(0,-.01,.210),.72,None),('open_fit',400,(.35,-.48,.64),(0,.0,.080),.35,set(model)-desc('SHELL_REVEAL_ROOT')),('battery',671,(.28,-.42,.67),(0,-.017,.35),.30,desc('BATTERY_ROOT')),('computer',521,(.23,-.31,.47),(0,-.017,.18),.34,desc('FLIGHT_COMPUTER_ROOT')|desc('THERMAL_ROOT')|desc('INTERNAL_SUPPORT_ROOT')),('optics',821,(.32,-.50,.21),(0,-.255,.034),.29,desc('CAMERA_GIMBAL_ROOT'))]
for name,frame,loc,target,scale,visible in views:
 if '--quick' in sys.argv and name not in ['assembled','exploded','open_fit']:continue
 s.frame_set(frame);s.camera=camera(name,loc,target,scale)
 for o in model:o.hide_render=visible is not None and o not in visible
 s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
