"""Consistent native close-ups of all three refined interior layers."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];O=R/'renders/interior-v30';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v30.blend'));s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.render.resolution_x=1600;s.render.resolution_y=1250;s.render.resolution_percentage=100
for o in s.objects:
 if o.type=='LIGHT' and o.name.startswith(('LIGHT_REAR','LENS_')):o.hide_render=True
bpy.data.objects['STUDIO_GROUND'].hide_render=True
model=[o for o in s.objects if o.type in {'MESH','CURVE','FONT'} and not o.hide_render]
def desc(n):o=bpy.data.objects[n];return {o,*o.children_recursive}
therm=desc('THERMAL_ROOT');board=desc('FLIGHT_COMPUTER_ROOT');tray=desc('INTERNAL_SUPPORT_ROOT');battery=desc('BATTERY_ROOT')
d=bpy.data.lights.new('V30_MACRO_FILL','AREA');d.energy=.7;d.shape='DISK';d.size=.20;d.color=(.83,.91,1);fill=bpy.data.objects.new(d.name,d);s.collection.objects.link(fill)
def framecam(n,shown,direction,margin=1.2):
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in shown:
  if o.type in {'MESH','CURVE','FONT'}:
   e=o.evaluated_get(dg);pts.extend(e.matrix_world@Vector(p) for p in e.bound_box)
 lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);target=(lo+hi)*.5
 cam=bpy.data.cameras.new('V30_CAM_'+n);cam.type='ORTHO';o=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(o);o.location=target+Vector(direction).normalized()*.6;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();inv=o.matrix_world.inverted();v=[inv@p for p in pts];w=max(p.x for p in v)-min(p.x for p in v);h=max(p.y for p in v)-min(p.y for p in v);cam.ortho_scale=max(w,h*s.render.resolution_x/s.render.resolution_y)*margin;s.camera=o
 fill.data.energy=.7
 fill.location=target+Vector((-.22,-.27,.24) if direction[2]>=0 else (-.22,.27,-.24));fill.rotation_euler=(target-fill.location).to_track_quat('-Z','Y').to_euler()
views=[('02-thermal-closed',400,therm,(.7,-1,1.4)),('02-thermal-exploded',1221,therm,(.8,-1.2,.3)),('02-thermal-underside',400,therm,(.7,-1,-1.1)),('03-computer-closed',400,board,(.7,-1,1.65)),('03-computer-exploded',1371,board,(.7,-1,1.35)),('03-computer-macro',400,{o for o in board if o.name.startswith(('FC30_PROCESSOR','FC30_CPU','FC30_MEMORY','FC30_MASKED','FC30_VIA'))},(.5,-.7,1.5)),('04-tray-closed',400,tray,(.7,-1,1.5)),('04-tray-exploded',1521,tray,(.7,-1,1.25)),('04-tray-underside',400,tray,(.7,-1,-1)),('stack-closed',400,therm|board|tray,(.65,-1,.7)),('stack-exploded',1091,therm|board|tray,(.8,-1.2,.8)),('all-four-layers',1091,battery|therm|board|tray,(.8,-1.2,.75))]
if '--quick' in sys.argv:s.cycles.samples=24;s.render.resolution_x=1400;s.render.resolution_y=1100;views=[v for v in views if v[0] in ['02-thermal-closed','03-computer-closed','04-tray-closed','stack-exploded']]
if '--only' in sys.argv:views=[v for v in views if v[0] in sys.argv[sys.argv.index('--only')+1:]]
for n,fr,shown,direction in views:
 s.frame_set(fr)
 visible=board if n=='03-computer-macro' else shown
 for o in model:o.hide_render=o not in visible
 framecam(n,shown,direction);s.render.filepath=str(O/(n+'.png'));bpy.ops.render.render(write_still=True);print('V30_RENDER',n,flush=True)
