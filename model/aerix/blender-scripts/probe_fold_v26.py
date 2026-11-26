import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v25.blend'))
bpy.context.scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get()
names=['BODY_CRADLE','BODY_SHELL_TOP','REAR_FASCIA','FRONT_VISOR_FRAME']
for tag in ['FR','RR']:
 names += [p+tag for p in ['ARM_','ARM_INLAY_','MOTOR_BASE_','MOTOR_','HINGE_CAP_','HINGE_ROTATING_COLLAR_']]
data={}
for name in names:
 o=bpy.data.objects[name];ev=o.evaluated_get(deps);m=ev.to_mesh()
 data[name]=([ev.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);ev.to_mesh_clear()
fixed={n:BVHTree.FromPolygons(*data[n]) for n in names[:4]}
pivots={tag:bpy.data.objects['ARM_'+tag+'_ROOT'].matrix_world.translation.copy() for tag in ['FR','RR']}
def tree(n,angle):
 p=pivots[n[-2:]];M=Matrix.Translation(p)@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-p)
 vs,fs=data[n];return BVHTree.FromPolygons([M@v for v in vs],fs)
result=[]
for f,r in [(0,0),(100,0),(105,0),(108,0),(105,35),(105,40),(105,45),(108,45),(100,-64),(105,-64)]:
 trees={n:tree(n,f if n.endswith('FR') else r) for n in names[4:]};hits={}
 for n,t in trees.items():
  for name,b in fixed.items():
   pairs=t.overlap(b)
   if pairs:hits[n+' / '+name]=len(pairs)
 for n,t in trees.items():
  if not n.endswith('FR'):continue
  for other,ot in trees.items():
   if not other.endswith('RR'):continue
   pairs=t.overlap(ot)
   if pairs:hits[n+' / '+other]=len(pairs)
 result.append({'front':f,'rear':r,'hits':hits});print(result[-1],flush=True)
(R/'renders/folding-v26/candidate-clearance.json').write_text(json.dumps(result,indent=2))
