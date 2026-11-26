import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];O=R/'renders/exterior-v21';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v20.blend'));d=bpy.context.evaluated_depsgraph_get();report={}
for o in bpy.context.scene.objects:
 if o.name.startswith(('DOWN_SENSOR_','BELLY_SERVICE','BELLY_SENSOR','BELLY_PANEL','BELLY_SPINE')):
  e=o.evaluated_get(d);m=e.to_mesh();coords=[e.matrix_world@v.co for v in m.vertices]
  report[o.name]={'bounds':[[min(p[i] for p in coords),max(p[i] for p in coords)] for i in range(3)],'vertices':len(m.vertices),'modifiers':[(q.name,q.type) for q in o.modifiers],'material':[q.name for q in m.materials]};e.to_mesh_clear()
(O/'before-geometry.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
s=bpy.context.scene;s.cycles.samples=24;s.render.resolution_x=1400;s.render.resolution_y=1100;s.render.resolution_percentage=85;bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
for name in ['underside_sensors','underside_body']:
 s.camera=bpy.data.objects['CAM_'+name];s.camera.data.ortho_scale=.105 if name=='underside_sensors' else .25;s.render.filepath=str(O/('before-native-'+name+'.png'));bpy.ops.render.render(write_still=True)
