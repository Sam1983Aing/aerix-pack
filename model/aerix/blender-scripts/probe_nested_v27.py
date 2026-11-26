import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-folding-v27.blend'))
s=bpy.context.scene;s.frame_set(361);deps=bpy.context.evaluated_depsgraph_get()
names=['BODY_CRADLE','BODY_SHELL_TOP','ARM_RR','ARM_INLAY_RR','MOTOR_BASE_RR','MOTOR_RR','BLADE_RR_0','BLADE_RR_1','ARM_FR','ARM_INLAY_FR','MOTOR_BASE_FR','MOTOR_FR','BLADE_FR_0','BLADE_FR_1']
data={}
for n in names:
 o=bpy.data.objects[n];ev=o.evaluated_get(deps);m=ev.to_mesh();data[n]=([v.co.copy() for v in m.vertices],[tuple(p.vertices) for p in m.polygons]);ev.to_mesh_clear()
def geometry(n):
 vs,fs=data[n];vs=[bpy.data.objects[n].matrix_world@v for v in vs];return vs,fs
def tree(n):return BVHTree.FromPolygons(*geometry(n))
body=tree('BODY_CRADLE');shell=tree('BODY_SHELL_TOP');out=[]
rear=bpy.data.objects['ARM_RR_ROOT'];pitch=bpy.data.objects['ARM_RR_FOLD_PITCH'];prop=bpy.data.objects['PROPELLER_RR'];axis=Vector((-.054,.095,0)).normalized()
for yaw,tilt,offset,zoff,front_angle in [(y,t,.015,z,f) for y,t,z,f in [(-100,35,-.02,100),(-105,35,-.02,100),(-100,40,-.02,100),(-105,40,-.02,100),(-100,35,-.03,105),(-105,35,-.03,105),(-105,40,-.03,100),(-110,35,-.03,100),(-110,40,-.03,100),(-100,50,-.025,100),(-105,50,-.025,100)]]:
 bpy.data.objects['ARM_FR_ROOT'].rotation_quaternion=Quaternion(Vector((0,0,1)),math.radians(front_angle));bpy.data.objects['PROPELLER_FR'].rotation_quaternion=Quaternion(Vector((0,0,1)),math.radians(-front_angle))
 rear.rotation_quaternion=Quaternion(Vector((0,0,1)),math.radians(yaw));prop.rotation_quaternion=Quaternion(Vector((0,0,1)),math.radians(-yaw));pitch.rotation_quaternion=Quaternion(axis,math.radians(tilt))
 # Adjusting the pivot requires keeping the deployed child's binding consistent.
 direction=Vector((.095,.054,0)).normalized();p0=pitch.location.copy();p1=direction*offset;p1.z=zoff;delta=p1-p0;pitch.location=p1
 for child in pitch.children:child.location-=delta
 bpy.context.view_layer.update();hits={};details={}
 for n in names[2:8]:
  t=tree(n)
  for b,tb in [('BODY_CRADLE',body),('BODY_SHELL_TOP',shell)]+[(f,tree(f)) for f in names[8:]]:
   pairs=t.overlap(tb)
   if pairs:
    hits[n+' / '+b]=len(pairs)
    if yaw==-100 and tilt==35 and offset==.015:
     vs,fs=geometry(n);pts=[vs[v] for a,_ in pairs for v in fs[a]];details[n+' / '+b]=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
 out.append({'yaw':yaw,'tilt':tilt,'pivot_offset':offset,'z_offset':zoff,'front_angle':front_angle,'hits':hits,'contact_bounds':details});print(out[-1],flush=True)
(R/'renders/folding-v27/nesting-candidates.json').write_text(json.dumps(out,indent=2))
