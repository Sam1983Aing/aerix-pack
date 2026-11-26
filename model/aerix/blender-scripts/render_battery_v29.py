import bpy,json,sys,re
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];O=R/'renders/battery-v29';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v29.blend'));s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.render.resolution_percentage=100;s.render.resolution_x=1600;s.render.resolution_y=1250
for o in s.objects:
 if o.type=='LIGHT' and (o.name.startswith('LIGHT_REAR') or o.name.startswith('LENS_')):o.hide_render=True
bpy.data.objects['STUDIO_GROUND'].hide_render=True
# Local studio softboxes expose material grain and rolled edges consistently.
def area(n,p,energy,size,target,color):
 d=bpy.data.lights.new(n,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
# Existing scene is kept; add a low-power grazing fill for the battery's dark surfaces.
area('B29_MACRO_FILL',(-.24,-.32,.38),.6,.22,(0,-.02,.1),(.82,.9,1.0))
root=bpy.data.objects['BATTERY_ROOT'];parts={root,*root.children_recursive};model=[o for o in s.objects if o.type in {'MESH','FONT','CURVE'} and o.name!='STUDIO_GROUND' and not o.hide_render]
def framecam(n,objects,dir,margin=1.2):
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();points=[]
 for o in objects:
  if o.type not in {'MESH','FONT','CURVE'}:continue
  e=o.evaluated_get(deps);points.extend(e.matrix_world@Vector(v) for v in e.bound_box)
 lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)]);target=(lo+hi)*.5
 d=bpy.data.cameras.new('CAM_B29_'+n);d.type='ORTHO';o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=target+Vector(dir).normalized()*.6;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();inv=o.matrix_world.inverted();view=[inv@p for p in points];w=max(v.x for v in view)-min(v.x for v in view);h=max(v.y for v in view)-min(v.y for v in view);d.ortho_scale=max(w,h*s.render.resolution_x/s.render.resolution_y)*margin;s.camera=o
views=[('closed',400,parts,(.7,-1,1.25),1.2),('closed-rear',400,parts,(-.75,1,1.0),1.2),('closed-underside',400,parts,(.7,-1,-1),1.2),('lid-off',587,parts,(.7,-1,1.4),1.2),('exploded',671,parts,(.8,-1.2,.85),1.2),('bms',400,{o for o in parts if re.match(r'BAT29_(BMS|POWER|BALANCE|CELL_CONTACT|CELL_SENSE|KEYED_PORT|GOLD_CONTACT|CONTACT_|PORT_)',o.name)},(.35,-.6,1.5),1.15)]
views.extend([('open-tray',400,parts-{bpy.data.objects['BATTERY_LID_ROOT'],*bpy.data.objects['BATTERY_LID_ROOT'].children_recursive,bpy.data.objects['BATTERY_SIDE_COVER_ROOT'],*bpy.data.objects['BATTERY_SIDE_COVER_ROOT'].children_recursive},(.7,-1,1.5),1.2),('foil-cell',400,{bpy.data.objects['CELL_4_ROOT'],*bpy.data.objects['CELL_4_ROOT'].children_recursive},(.7,-1,1.25),1.2)])
if '--quick' in sys.argv:views=[v for v in views if v[0] in ['closed','lid-off','exploded']];s.cycles.samples=32;s.render.resolution_x=1400;s.render.resolution_y=1100
if '--only' in sys.argv:views=[v for v in views if v[0] in sys.argv[sys.argv.index('--only')+1:]]
for n,fr,shown,direction,margin in views:
 s.frame_set(fr)
 # Camera and lighting track the cartridge's world-space assembled or body-exploded position.
 for o in model:o.hide_render=o not in shown
 framecam(n,shown,direction,margin)
 # Position macro fill near the actual target height.
 bpy.data.objects['B29_MACRO_FILL'].location.z=.38+(root.location.z if root.location.z else 0)
 s.render.filepath=str(O/(n+'.png'));bpy.ops.render.render(write_still=True);print('B29_RENDER',n,flush=True)
