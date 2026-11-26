import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v25.blend'))
bpy.context.scene.frame_set(1)
deps=bpy.context.evaluated_depsgraph_get();out={}
for o in bpy.context.scene.objects:
 if (o.name.startswith(('ARM_','HINGE_','PROPELLER_','BLADE_','PROP_','MOTOR_')) and ('FR' in o.name or 'RR' in o.name)) or o.name in ['BODY_SHELL_TOP','BODY_CRADLE']:
  d={'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'world_origin':list(o.matrix_world.translation)}
  if o.type in {'MESH','CURVE'}:
   ev=o.evaluated_get(deps);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices]
   d['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)];ev.to_mesh_clear()
  out[o.name]=d
(R/'renders/folding-v26').mkdir(exist_ok=True)
(R/'renders/folding-v26/inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps({n:d for n,d in out.items() if n.startswith(('ARM_','PROPELLER_','BLADE_','PROP_')) or n in ['BODY_SHELL_TOP','BODY_CRADLE']},indent=2),flush=True)
