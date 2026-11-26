"""Bake Cycles floor shadows for the orbit viewer, with one sample every four fold frames."""
from pathlib import Path
from tempfile import TemporaryDirectory

import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve() == root/'blender/drone-v14.blend'
scene = bpy.context.scene
aircraft = bpy.data.collections['V14 | Aircraft']
floor = bpy.data.objects['Studio.floor']
camera = scene.camera.copy()
camera.data = camera.data.copy()
scene.collection.objects.link(camera)
camera.location = (0,0,.52)
camera.rotation_euler = (0,0,0)
camera.data.ortho_scale = .48
scene.camera = camera
tile = 384
columns = 6
scene.render.resolution_x = scene.render.resolution_y = tile
scene.render.resolution_percentage = 100
scene.cycles.samples = 20
scene.cycles.use_denoising = True
scene.render.image_settings.file_format = 'PNG'

def plate(directory, frame):
    scene.frame_set(frame)
    output = Path(directory)/'plate.png'
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(output),check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    data = np.empty(tile*tile*4, dtype=np.float32)
    image.pixels.foreach_get(data)
    bpy.data.images.remove(image)
    return data.reshape(tile,tile,4)[:,:,:3] @ np.array([.2126,.7152,.0722],dtype=np.float32)

atlas = np.zeros((columns*tile, columns*tile, 4),dtype=np.float32)
atlas[:,:,3] = 1
with TemporaryDirectory(dir=root/'measurements') as stage:
    meshes = [o for o in aircraft.objects if o.type=='MESH']
    for obj in meshes:
        obj.hide_render = True
    open_floor = plate(stage,1)
    top = floor.location.z
    folded_floor = plate(stage,121)
    bottom = floor.location.z
    for obj in meshes:
        obj.hide_render = False
        obj.visible_camera = False
    axis = np.clip((1-np.abs(np.linspace(-1,1,tile)))*12,0,1)
    feather = np.minimum(axis[np.newaxis,:],axis[:,np.newaxis])
    for i,frame in enumerate(range(1,122,4)):
        lit = plate(stage,frame)
        fraction = (floor.location.z-top)/(bottom-top)
        bare = open_floor*(1-fraction)+folded_floor*fraction
        alpha = np.clip(1-lit/np.maximum(bare,.01),0,.92)*feather
        # The edge of a plate meets the same background as an empty studio.
        alpha = np.clip((alpha-.009)/.991,0,1)
        row,col = divmod(i,columns)
        atlas[row*tile:(row+1)*tile,col*tile:(col+1)*tile,:3] = alpha[:,:,None]
image = bpy.data.images.new('V14 floor shadows',width=columns*tile,height=columns*tile,alpha=False,is_data=True)
image.pixels.foreach_set(atlas.ravel())
image.file_format = 'PNG'
dest=root/'viewer/v14-floor-shadows.png'
image.filepath_raw = str(dest.with_suffix('.pending.png'))
image.save()
Path(image.filepath_raw).replace(dest)
print('Saved 31 studio shadow plates.')
