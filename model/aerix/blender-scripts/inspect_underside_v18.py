import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];out=R/'renders/exterior-v18';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v17.blend'))
stats={}
for o in bpy.context.scene.objects:
 if o.type=='MESH' and (o.name.startswith(('BELLY_','DOWN_SENSOR_')) or o.name=='BODY_CRADLE'):
  stats[o.name]={'verts':len(o.data.vertices),'faces':len(o.data.polygons),'custom_normals':o.data.has_custom_normals,'modifiers':[(m.name,m.type,getattr(m,'width',None)) for m in o.modifiers],'bounds':[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)]}
(out/'inspection.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats),flush=True)
s=bpy.context.scene;s.cycles.samples=24;s.render.resolution_percentage=80;s.render.resolution_x=1300;s.render.resolution_y=1400
bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
s.camera=bpy.data.objects['CAM_underside_body'];s.camera.data.ortho_scale=.30;s.render.filepath=str(out/'before.png');bpy.ops.render.render(write_still=True)
