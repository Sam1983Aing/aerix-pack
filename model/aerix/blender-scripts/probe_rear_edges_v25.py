import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'))
row=[Vector(p) for p in json.loads((R/'scripts/blender/data/rear-source-profile-v11.json').read_text())['bottomrow']]
def near(p):
 return min((p-(a+(b-a)*max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared)))).length for a,b in zip(row,row[1:]))
o=bpy.data.objects['BODY_CRADLE'];bm=bmesh.new();bm.from_mesh(o.data);bm.edges.ensure_lookup_table();bm.normal_update()
edges=[e for e in bm.edges if all(v.co.y>.130 and v.co.z<.0639 and near(v.co)<.000003 for v in e.verts)]
upper=[e for e in bm.edges if e.is_manifold and all(v.co.y>.127 and abs(v.co.x)>.043 and .063<v.co.z<.089 for v in e.verts) and e.calc_face_angle()>math.radians(50)];print('UPPER',len(upper),[(round(e.calc_length(),6),list((e.verts[0].co+e.verts[1].co)/2),round(math.degrees(e.calc_face_angle()))) for e in upper]);print('MATCHED',len(edges),'LENGTH',sum(e.calc_length() for e in edges));print('BOUNDS',[[min(v.co[i] for e in edges for v in e.verts),max(v.co[i] for e in edges for v in e.verts)] for i in range(3)])
print('MATERIAL',[(m.name,tuple(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value),m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value,m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value) for m in o.data.materials]);print('EDGE_ANGLES',[round(math.degrees(e.calc_face_angle()),1) for e in edges]);bm.free()
