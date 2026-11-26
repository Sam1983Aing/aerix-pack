"""Record planar shading accuracy for the machined and circuit-board surfaces."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'renders/interior-v30';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v30.blend'));s=bpy.context.scene;s.frame_set(400);d=bpy.context.evaluated_depsgraph_get();report=json.loads((O/'surface-validation.json').read_text());results=[]
for item in report['planar_corrections']:
 o=bpy.data.objects[item['object']].evaluated_get(d);m=o.to_mesh();angles=[]
 for p in m.polygons:
  if p.area>2e-6 and max(abs(v) for v in p.normal)>.99999:angles.extend(math.degrees(m.corner_normals[i].vector.angle(p.normal)) for i in p.loop_indices)
 worst=max(angles,default=0);results.append({'object':item['object'],'corners':len(angles),'maximum_deviation_degrees':worst});o.to_mesh_clear()
report['planar_normal_checks']=results;report['maximum_deviation_degrees']=max(v['maximum_deviation_degrees'] for v in results);report['tolerance_degrees']=.5;report['passed']=report['maximum_deviation_degrees']<.5;(O/'surface-validation.json').write_text(json.dumps(report,indent=2));print('V30_SURFACES',report['passed'],report['maximum_deviation_degrees'],flush=True);assert report['passed']
