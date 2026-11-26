"""Add a reversible folding rig to V25; retain every exterior mesh/material."""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
R=Path(__file__).resolve().parents[2];OUT=R/'renders/folding-v27';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'scripts/blender'))
from folding_hinge_details_v27 import add_hinges,export_details
source=R/'blender/aerix-exterior-v25.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.context.scene;s.frame_set(1);s.render.fps=30;s.frame_start=1;s.frame_end=361
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
pitch_pivots={};pitch_axes={};pitch_children={}
for tag in ['RL','RR']:
 arm=bpy.data.objects['ARM_'+tag+'_ROOT'];sign=-1 if tag.endswith('L') else 1
 direction=Vector((sign*.095,.054,0)).normalized()
 offset=direction*.015;offset.z=-.020
 axis=Vector((-direction.y,direction.x,0))
 group=bpy.data.objects.new('ARM_'+tag+'_FOLD_PITCH',None);s.collection.objects.link(group)
 group.parent=arm;group.location=offset;group.empty_display_size=.008
 children=[o for o in arm.children if o!=group and not o.name.startswith('HINGE_')]
 bpy.context.view_layer.update()
 for obj in children:
  world=obj.matrix_world.copy();obj.parent=group;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_world=world
 pitch_pivots[tag]=list(offset);pitch_axes[tag]=axis;pitch_children[tag]=[o.name for o in children]
bpy.context.view_layer.update()
hinge_details=add_hinges(s)
bpy.context.view_layer.update()
def smooth(u,a,b):
 t=max(0.,min(1.,(u-a)/(b-a)));return t*t*(3-2*t)
tracks={};axes={}
for tag in tags:
 for n in ['ARM_'+tag+'_ROOT','PROPELLER_'+tag,f'BLADE_FOLD_{tag}_0',f'BLADE_FOLD_{tag}_1']:
  tracks[n]=[];axes[n]=Vector((0,0,1))
 if tag.startswith('R'):
  n='ARM_'+tag+'_FOLD_PITCH';tracks[n]=[];axes[n]=pitch_axes[tag]
for frame in range(1,362):
 u=(frame-1)/360
 for tag in tags:
  sign=-1 if tag.endswith('L') else 1;front=tag.startswith('F')
  angle=math.radians(sign*(100 if front else -105))*smooth(u,.72 if front else .46,1. if front else .72)
  values={'ARM_'+tag+'_ROOT':angle,'PROPELLER_'+tag:initial[tag]*(1-smooth(u,0,.12))-angle}
  for k in [0,1]:values[f'BLADE_FOLD_{tag}_{k}']=math.radians(-(1 if k==0 else -1)*82)*smooth(u,.12,.27)
  if not front:values['ARM_'+tag+'_FOLD_PITCH']=math.radians(35)*smooth(u,.27,.46)
  for name,a in values.items():
   obj=bpy.data.objects[name];obj.rotation_mode='QUATERNION';q=Quaternion(axes[name],a);obj.rotation_quaternion=q
   obj.keyframe_insert(data_path='rotation_quaternion',frame=frame,group='Folding')
   tracks[name].append([q.x,q.z,-q.y,q.w])
for action in bpy.data.actions:
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
for label,frame in [('Deployed',1),('Rotors parked',44),('Blades reversed',98),('Rear arms lowered',167),('Rear arms nested',260),('Fully folded',361)]:
 s.timeline_markers.new(label,frame=frame)
s.frame_set(1);bpy.context.view_layer.update();after=snapshot()
max_error=max((Vector(a)-Vector(b)).length for n,(vs,h) in before.items() for a,b in zip(vs,after[n][0]))
checks={'all_source_meshes_retained':before.keys()<=after.keys(),'only_hinge_details_added':set(after)-set(before)=={o.name for o in hinge_details},'topology_normals_material_assignments_preserved':all(v[1]==after[n][1] for n,v in before.items()),'deployed_vertices_preserved':max_error<1e-7,'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==source_hash}
assert all(checks.values()),checks
s.camera=bpy.data.objects.get('CAM_hero',s.camera)
s['folding_notes']='V27: front blades point toward the nose; rear arms lower on a secondary shoulder hinge and swing forward beneath the front pair. V25 exterior geometry retained.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-folding-v27.blend'))
config={'source':'exports/aerix-review-v25.glb','duration':12,'fps':30,'samples':361,'tracks':tracks,'pitch_pivots':pitch_pivots,'pitch_children':pitch_children,'hinge_details':export_details(hinge_details),'phases':[{'label':'Parking propellers','end':.12},{'label':'Reversing blade folds','end':.27},{'label':'Lowering rear arms','end':.46},{'label':'Nesting rear arms','end':.72},{'label':'Tucking front arms','end':1}]}
(OUT/'fold-animation.json').write_text(json.dumps(config))
(OUT/'preservation-validation.json').write_text(json.dumps({'checks':checks,'source_sha256':source_hash,'preserved_meshes':len(before),'added_hinge_meshes':len(hinge_details),'maximum_deployed_vertex_error_m':max_error},indent=2))
print('V27_FOLD_RIG_COMPLETE',checks,flush=True)
