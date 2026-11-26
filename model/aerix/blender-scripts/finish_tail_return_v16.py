"""Close the shaped tail header between the revised hood and inset rear fascia."""
import bpy,math,ast,bmesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
s=bpy.context.scene;root=bpy.data.objects['DRONE_ROOT']
for node in ast.parse((ROOT/'scripts/blender/refine_front_arms_v09.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='mesh':exec(compile(ast.Module(body=[node],type_ignores=[]),'<mesh>','exec'))
for node in ast.parse((ROOT/'scripts/blender/refine_body_v16.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['smooth','interpolator']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shape>','exec'))
profile=interpolator([(0,1),(.3,.990),(.55,.955),(.66,.915),(.70,.888),(.72,.867),(.745,.816),(.91,.255),(.97,.071),(1,0)])
old=bpy.data.objects.get('REAR_HOOD_RETURN')
if old:bpy.data.objects.remove(old,do_unlink=True)
cols=129;rows=7;vs=[]
for back in [False,True]:
 for k in range(rows):
  t=k/(rows-1)
  for j in range(cols):
   x=-.0482+.0964*j/(cols-1);u=abs(x)/.0488
   top=.090+.0054*profile(u)-.0008
   bottom=.0865-.0035*smooth(.83,1,u)
   y0=.1434-.0125*smooth(.68,1,abs(x/.97)/.050)
   y1=.143-.015*smooth(.70,1,u)-.00015
   y=y0+(y1-y0)*smooth(0,1,t)-(.006 if back else 0)
   vs.append((x,y,bottom+(top-bottom)*t))
count=cols*rows;fs=[]
for k in range(rows-1):
 for j in range(cols-1):
  a=k*cols+j;b=a+1;fs.extend([(a,a+cols,b+cols,b),(count+b,count+b+cols,count+a+cols,count+a)])
perimeter=list(range(cols))+[k*cols+cols-1 for k in range(1,rows)]+[(rows-1)*cols+j for j in range(cols-2,-1,-1)]+[k*cols for k in range(rows-2,0,-1)]
for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):fs.append((a,b,b+count,a+count))
ob=mesh('REAR_HOOD_RETURN',vs,fs,bpy.data.materials['Visor satin graphite frame'],bevel=.00016)
for mod in list(ob.modifiers):
 if mod.type=='WEIGHTED_NORMAL':ob.modifiers.remove(mod)
# Save with the standard overview and studio state.
s.camera=bpy.data.objects['CAM_hero'];bpy.data.objects['STUDIO_GROUND'].hide_render=False;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
s.camera=bpy.data.objects['CAM_rear_body'];s.cycles.samples=24;s.render.resolution_x=1536;s.render.resolution_y=1024;s.render.resolution_percentage=70;s.render.filepath=str(ROOT/'renders/exterior-v16/rear_body-final-preview.png');bpy.ops.render.render(write_still=True)
