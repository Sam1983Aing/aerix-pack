"""Add a reversible folding rig to V25; retain every exterior mesh/material."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];OUT=R/'renders/folding-v26';OUT.mkdir(exist_ok=True)
source=R/'blender/aerix-exterior-v25.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.context.scene;s.frame_set(1);s.render.fps=30;s.frame_start=1;s.frame_end=241
tags=['FL','FR','RL','RR']
def snapshot():
 deps=bpy.context.evaluated_depsgraph_get();out={}
 for o in s.objects:
  if o.type not in {'MESH','CURVE','FONT'} or o.hide_render or o.name=='STUDIO_GROUND':continue
  ev=o.evaluated_get(deps);m=ev.to_mesh()
  out[o.name]=([tuple(ev.matrix_world@v.co) for v in m.vertices],
   hashlib.sha256(repr(([tuple(p.vertices) for p in m.polygons],[tuple(n.vector) for n in m.corner_normals],[q.name if q else None for q in m.materials])).encode()).hexdigest())
  ev.to_mesh_clear()
 return out
before=snapshot();initial={t:bpy.data.objects['PROPELLER_'+t].rotation_euler.z for t in tags}
for tag in tags:
 prop=bpy.data.objects['PROPELLER_'+tag]
 for k in [0,1]:
  blade=bpy.data.objects[f'BLADE_{tag}_{k}'];world=blade.matrix_world.copy()
  pivot=bpy.data.objects.new(f'BLADE_FOLD_{tag}_{k}',None);s.collection.objects.link(pivot)
  pivot.parent=prop;pivot.location=((1 if k==0 else -1)*.01,0,0);pivot.empty_display_size=.005
  bpy.context.view_layer.update();blade.parent=pivot;blade.matrix_parent_inverse=Matrix.Identity(4);blade.matrix_world=world
bpy.context.view_layer.update()
def smooth(u,a,b):
 t=max(0.,min(1.,(u-a)/(b-a)));return t*t*(3-2*t)
tracks={}
for tag in tags:
 for n in ['ARM_'+tag+'_ROOT','PROPELLER_'+tag,f'BLADE_FOLD_{tag}_0',f'BLADE_FOLD_{tag}_1']:tracks[n]=[]
for frame in range(1,242):
 u=(frame-1)/240
 for tag in tags:
  sign=-1 if tag.endswith('L') else 1;front=tag.startswith('F')
  angle=math.radians(sign*(105 if front else 45))*smooth(u,.70 if front else .38,1. if front else .70)
  values={'ARM_'+tag+'_ROOT':angle,'PROPELLER_'+tag:initial[tag]*(1-smooth(u,0,.18))-angle}
  for k in [0,1]:values[f'BLADE_FOLD_{tag}_{k}']=math.radians((1 if front else -1)*(1 if k==0 else -1)*82)*smooth(u,.18,.38)
  for name,a in values.items():
   obj=bpy.data.objects[name];obj.rotation_mode='XYZ';obj.rotation_euler.z=a;obj.keyframe_insert(data_path='rotation_euler',index=2,frame=frame,group='Folding')
   tracks[name].append(a)
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
for label,frame in [('Deployed',1),('Rotors parked',44),('Blades folded',92),('Rear arms tucked',169),('Fully folded',241)]:
 s.timeline_markers.new(label,frame=frame)
s.frame_set(1);bpy.context.view_layer.update();after=snapshot()
max_error=max((Vector(a)-Vector(b)).length for n,(vs,h) in before.items() for a,b in zip(vs,after[n][0]))
checks={'same_visible_meshes':before.keys()==after.keys(),'topology_normals_material_assignments_preserved':all(v[1]==after[n][1] for n,v in before.items()),'deployed_vertices_preserved':max_error<1e-7,'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_hash}
assert all(checks.values()),checks
s.camera=bpy.data.objects.get('CAM_hero',s.camera)
s['folding_notes']='V25 exterior, rearward arm-fold study. Timeline 1–241: park rotors, fold blades, rear arms, front arms. Existing front hinge-cap seating overlaps are retained.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-folding-v26.blend'))
config={'source':'exports/aerix-review-v25.glb','duration':8,'fps':30,'samples':241,'tracks':tracks,'phases':[{'label':'Park rotors','end':.18},{'label':'Fold blades','end':.38},{'label':'Tuck rear arms','end':.70},{'label':'Tuck front arms','end':1}]}
(OUT/'fold-animation.json').write_text(json.dumps(config))
(OUT/'preservation-validation.json').write_text(json.dumps({'checks':checks,'source_sha256':source_hash,'visible_meshes':len(before),'maximum_deployed_vertex_error_m':max_error},indent=2))
print('V26_FOLD_RIG_COMPLETE',checks,flush=True)
