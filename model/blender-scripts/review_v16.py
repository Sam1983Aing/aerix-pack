"""Create linked native inspection scenes, static review GLBs and matching orthos."""
from pathlib import Path
import bpy,math,sys
from mathutils import Vector, Matrix
root=Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).name=='drone-v16.blend'
main=bpy.data.scenes['V16 · Assembled'];bpy.context.window.scene=main
coll=bpy.data.collections['V16 | Interior']
model_sets={key:[(o,o.matrix_world.copy()) for o in coll.objects if o.get('Review 7 part')==key]
            for key in ['Battery','Main board']}
output=root/'renders/v16';viewer=root/'viewer/review7'
def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def lamp(s,name,pos,power,size,size_y,aimpoint):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='RECTANGLE';data.size=size;data.size_y=size_y
    obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj);obj.location=pos;aim(obj,aimpoint)
def scene_for(key):
    scene=bpy.data.scenes.new('Review 7 · '+key);bpy.context.window.scene=scene
    objs=[]
    for origin,mat in model_sets[key]:
        copy=bpy.data.objects.new('Inspection | '+origin.name,origin.data)
        scene.collection.objects.link(copy);copy.matrix_world=mat;objs.append(copy)
    scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.render.resolution_x=1440;scene.render.resolution_y=830;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.world=bpy.data.worlds.new(key+' soft box')
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value=(.69,.72,.76,1);bg.inputs['Strength'].default_value=.20
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=-.53 if key=='Battery' else .05
    target=(0,-.028,.034 if key=='Battery' else .022)
    for sign in (1,-1):
        lamp(scene,key+' long softbox',(.130,-.105,sign*.14),.49,.11,.045,target)
        lamp(scene,key+' cross strip',(-.13,.10,sign*.115),.30,.10,.04,target)
        lamp(scene,key+' edge',(.12,.09,sign*.065),.10,.05,.018,target)
    camera_data=bpy.data.cameras.new(key+' macro');camera_data.type='ORTHO';camera_data.ortho_scale=.091
    camera_data.clip_start=.001;camera=bpy.data.objects.new(camera_data.name,camera_data)
    scene.collection.objects.link(camera);scene.camera=camera
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(viewer/('battery.glb' if key=='Battery' else 'board.glb')),
       export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,
       export_yup=True,export_cameras=False,export_lights=False)
    views=[('battery',1)] if key=='Battery' else [('board-lower',-1),('board-upper',1)]
    for name,sgn in views:
        # Right points aft on both faces, exactly as on the reference photographs.
        camera.location=Vector(target)+Vector((0,0,sgn*.18))
        orient=Matrix([Vector((0,-1,0)),Vector((sgn,0,0)),Vector((0,0,sgn))]).transposed()
        camera.rotation_euler=orient.to_euler()
        scene.render.filepath=str(output/(name+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name)
    bpy.ops.object.select_all(action='DESELECT')
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
for key in model_sets: scene_for(key)
bpy.context.window.scene=main;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'blender/drone-v16.blend'),compress=True)

