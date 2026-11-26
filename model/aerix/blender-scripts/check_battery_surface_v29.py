"""Check that the cartridge booleans no longer tilt the main planar surface normals."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v29.blend'))
deps=bpy.context.evaluated_depsgraph_get();results=[]
for name in ['BAT29_CARTRIDGE_TRAY','BAT29_SIDE_SERVICE_COVER','BAT29_TOP_LID','BAT29_KEYED_PORT_SHROUD']:
 obj=bpy.data.objects[name].evaluated_get(deps);mesh=obj.to_mesh();angles=[]
 for face in mesh.polygons:
  if face.area>2e-6 and max(abs(x) for x in face.normal)>.99999:
   angles.extend(math.degrees(mesh.corner_normals[i].vector.angle(face.normal)) for i in face.loop_indices)
 maximum=max(angles,default=0);assert maximum<.5,(name,maximum)
 results.append({'object':name,'corners_checked':len(angles),'maximum_normal_deviation_degrees':maximum});obj.to_mesh_clear()
report=R/'renders/battery-v29/surface-validation.json';data=json.loads(report.read_text());data['planar_normal_checks']=results;data['normal_tolerance_degrees']=.5;report.write_text(json.dumps(data,indent=2))
print('V29_SURFACES_PASS',results,flush=True)
