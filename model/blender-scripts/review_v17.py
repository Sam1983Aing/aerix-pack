"""Build inspection scenes from the mounted component meshes, export and render the same views."""
import sys,json,math,bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
revision=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert revision in ('v17','v18')
main=bpy.data.scenes[revision.upper()+' · Assembled'];bpy.context.window.scene=main;main.frame_set(1)
outside=bpy.data.collections[revision.upper()+' | Aircraft'];inside=bpy.data.collections[revision.upper()+' | Interior']
if revision=='v17':
    from v17_views import views
    assembly=[o for o in [*outside.objects,*inside.objects] if o.type=='MESH' and
              (o.name.startswith(('Camera.','Gimbal.')) or o.name=='Shell.gimbal_socket')]
    core=[o for o in assembly if o.name.startswith('Camera.') and o.name not in ('Camera.block','Camera.face_trim','Camera.frame_flex') and not o.name.startswith('Camera.board_seat.')]
    suspension=[o for o in assembly if o.get('V17 service group')=='Suspension' or o.name=='Shell.gimbal_socket']
    sets={'gimbal':assembly,'camera':core,'carrier':suspension}
else:
    from v18_reference import views
    sets={part:[o for o in inside.objects if o.get('V18 board')==part] for part in ('esc','gps')}
out=root/'renders'/revision;web=root/'viewer/review7'/revision
def model_light(scene,name,origin,energy,size,target):
    l=bpy.data.lights.new(name,'AREA');l.energy=energy;l.shape='RECTANGLE';l.size=size[0];l.size_y=size[1]
    o=bpy.data.objects.new(name,l);scene.collection.objects.link(o);o.location=origin;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
def to_web(v):return [v.x,v.z,-v.y]
pub={}
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='METAL';prefs.refresh_devices()
    for dev in prefs.devices:dev.use=dev.type=='METAL'
    gpu=any(dev.use for dev in prefs.devices)
except Exception:gpu=False
for name,cfg in views.items():
    native='Review 7 · '+cfg['title']
    if native in bpy.data.scenes:bpy.data.scenes.remove(bpy.data.scenes[native])
    scene=bpy.data.scenes.new(native);bpy.context.window.scene=scene
    objs=[]
    for src in sets[cfg['set']]:
        o=bpy.data.objects.new(name+' | '+src.name,src.data);scene.collection.objects.link(o)
        o.matrix_world=src.matrix_world.copy();objs.append(o)
    scene.render.engine='CYCLES';scene.cycles.device='GPU' if gpu else 'CPU'
    scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.render.film_transparent=True
    scene.render.resolution_x=1220;scene.render.resolution_y=842;scene.render.resolution_percentage=100
    scene.world=bpy.data.worlds.new(name+' macro surround');scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=(.85,.88,.9,1);bg.inputs['Strength'].default_value=.48
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    if revision=='v18':
        scene.view_settings.exposure=-.65
        bg.inputs['Strength'].default_value=.22
    target=Vector(cfg['target'])*.001;direction=Vector(cfg['dir']).normalized();up=Vector(cfg['up'])
    side=up.cross(direction).normalized();up=direction.cross(side).normalized()
    from mathutils import Matrix
    data=bpy.data.cameras.new(name+' inspection');data.type='ORTHO';data.ortho_scale=.001*cfg['width'];data.clip_start=.0003
    cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam)
    cam.location=target+direction*.18;cam.rotation_euler=Matrix([side,up,direction]).transposed().to_euler();scene.camera=cam
    sign=-1 if direction.z<0 else 1
    model_light(scene,name+' broad key',target+Vector((-.045,.084,.105*sign)),.38,(.085,.046),target)
    model_light(scene,name+' silver edge',target+Vector((.065,-.035,.060*sign)),.34,(.080,.021),target)
    model_light(scene,name+' optical strip',target+Vector((.042,.102,.015*sign)),.15,(.015,.057),target)
    bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    if name==cfg['set']:
        bpy.ops.export_scene.gltf(filepath=str(web/(cfg['set']+'.glb')),export_format='GLB',use_selection=True,
         use_active_scene=True,export_animations=False,export_lights=False,export_cameras=False,export_yup=True)
    bpy.ops.object.select_all(action='DESELECT')
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=scene.name)
    pub[name]={'title':cfg['title'],'target':to_web(target),'direction':to_web(direction),'up':to_web(up),
               'width':cfg['width']*.001,'source':cfg['source']}
    if revision=='v18':pub[name].update(part=cfg['part'],asset=cfg['set'])
    print('REVIEW',name,'objects',len(objs),flush=True)
(web/'views.json').write_text(json.dumps(pub,indent=2)+'\n')
bpy.context.window.scene=main;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'blender'/('drone-'+revision+'.blend')),compress=True)

