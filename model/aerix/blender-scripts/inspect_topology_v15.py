import bpy,bmesh,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v15.blend'))
bm=bmesh.new();bm.from_mesh(bpy.data.objects['BODY_CRADLE'].data)
print('EDGE_TYPES',collections.Counter(len(e.link_faces) for e in bm.edges if not e.is_manifold))
for group in range(5):
 es=[e for e in bm.edges if len(e.link_faces)==group]
 if es:
  ps=[(e.verts[0].co+e.verts[1].co)/2 for e in es];print('LOC',group,len(es),[(min(p[i] for p in ps),max(p[i] for p in ps)) for i in range(3)])
  if group!=2:print('SAMPLE',[(tuple(p),e.calc_length()) for p,e in list(zip(ps,es))[:15]])
