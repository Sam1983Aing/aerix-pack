import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];O=R/'renders/site-v01';bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-interior-v30.blend'));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.render.resolution_x=1800;s.render.resolution_y=1350;s.render.resolution_percentage=100;s.render.film_transparent=True;s.render.image_settings.color_mode='RGBA';s.render.image_settings.file_format='PNG'
for o in s.objects:
 if o.name=='STUDIO_GROUND' or (o.type=='LIGHT' and o.name.startswith(('LIGHT_REAR','LENS_'))):o.hide_render=True
model=[o for o in s.objects if o.type in {'MESH','CURVE','FONT'} and not o.hide_render]
def descendants(name):o=bpy.data.objects[name];return {o,*o.children_recursive}
allparts=set(model);optics=descendants('CAMERA_GIMBAL_ROOT');battery=descendants('BATTERY_ROOT');board=descendants('FLIGHT_COMPUTER_ROOT')
for name,fr,shown,direction in [('hero',400,allparts,(.48,-.90,.53)),('folded',361,allparts,(.43,-.9,.73)),('complete-exploded',521,allparts,(.65,-1.0,.5)),('optics',821,optics,(1.0,-1.2,.55)),('battery',671,battery,(.7,-1.1,.72)),('computer',1371,board,(.65,-1,1.4))]:
 s.frame_set(fr)
 for o in model:o.hide_render=o not in shown
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();points=[o.evaluated_get(dg).matrix_world@Vector(p) for o in shown if o.type in {'MESH','CURVE','FONT'} for p in o.evaluated_get(dg).bound_box];lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)]);target=(lo+hi)/2
 data=bpy.data.cameras.new('SITE_'+name);data.type='ORTHO';cam=bpy.data.objects.new(data.name,data);s.collection.objects.link(cam);cam.location=target+Vector(direction).normalized()*.95;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();inv=cam.matrix_world.inverted();coords=[inv@p for p in points];w=max(v.x for v in coords)-min(v.x for v in coords);h=max(v.y for v in coords)-min(v.y for v in coords);data.ortho_scale=max(w,h*4/3)*1.13;s.camera=cam;s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);print('SITE_RENDER',name,flush=True)
