import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v23.blend'))
out=[];deps=bpy.context.evaluated_depsgraph_get()
for tag in ['FL','FR','RL','RR']:
 for prefix in ['MOTOR_BASE_','MOTOR_SEAL_']:
  o=bpy.data.objects[prefix+tag];e=o.evaluated_get(deps);me=e.to_mesh()
  out.append(dict(name=o.name,vertices=len(o.data.vertices),faces=len(o.data.polygons),evaluated_vertices=len(me.vertices),modifiers=[(m.name,m.type) for m in o.modifiers],materials=[m.name for m in o.data.materials],custom_normals=o.data.has_custom_normals,matrix=[list(row) for row in o.matrix_world],levels=sorted(__import__('collections').Counter(round(v.co.z,8) for v in me.vertices if v.co.z>.077).items()),bounds=[[min(v.co[i] for v in me.vertices),max(v.co[i] for v in me.vertices)] for i in range(3)]));e.to_mesh_clear()
o=bpy.data.objects['MOTOR_BASE_FR'];e=o.evaluated_get(deps);me=e.to_mesh();print('PROFILE',[(round(v.co.z,8),round(v.co.x-.165,8),round(v.co.y+.14,8)) for v in me.vertices if v.co.z>.077 and abs(v.co.y+.14)<1e-7 and v.co.x>.165]);e.to_mesh_clear();print(json.dumps(out,indent=2));(R/'renders/exterior-v24/native-before.json').write_text(json.dumps(out,indent=2))
