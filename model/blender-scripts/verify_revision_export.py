"""Compare changed native surfaces with the exported GLB, in meters."""
from pathlib import Path
from mathutils.bvhtree import BVHTree
import bpy
import json

root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
scene.frame_set(1)
version=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert version in ('v02','v03','v04','v05','v06','v07','v08','v09','v10','v12','v13','v14a','v14b','v14c')
prefixes={'v14c':('Shell.moulded_fuselage',),'v14b':('Shell.moulded_fuselage',),'v14a':('Shell.moulded_fuselage','Camera.block','Camera.face_trim','Camera.lens_barrel'),'v13':('Shell.moulded_fuselage','Gimbal.pitch_cover.','Arm.F','Hinge.socket.F','Hinge.pin.F'),'v12':('Shell.moulded_fuselage',),'v10':('Camera.',),'v09':('Leg.front.','Leg.rear.','Leg.window.'),'v02':('Shell.',),'v03':('Arm.','Hinge.mount.','Hinge.pin.'),'v04':('Motor.','Propeller.','Shell.','Seat.'),'v05':('Camera.','Gimbal.'),'v06':('Arm.',),'v07':('Arm.',),'v08':('Shell.','Arm.','Hinge.','Gimbal.','Camera.','Motor.','Leg.','Propeller.')}[version]
native_names=[o.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(prefixes)]
assert len(native_names)=={'v02':8,'v03':12,'v04':30,'v05':14,'v06':4,'v07':4,'v08':70,'v09':6,'v10':7,'v12':1,'v13':9,'v14a':4,'v14b':1,'v14c':1}[version]


def surface(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    coords=[ev.matrix_world@v.co for v in me.vertices]
    me.calc_loop_triangles()
    triangles=[tuple(t.vertices) for t in me.loop_triangles]
    tree=BVHTree.FromPolygons(coords,triangles,all_triangles=True)
    ev.to_mesh_clear()
    return coords,tree


native={}
for name in native_names:
    obj=bpy.data.objects[name]
    duplicate=obj.data.copy()
    assert not duplicate.validate(),f'Saved mesh failed Blender validation: {name}'
    bpy.data.meshes.remove(duplicate)
    native[name]=surface(obj)
fps, fps_base = scene.render.fps, scene.render.fps_base
bpy.ops.wm.read_factory_settings(use_empty=True)
# glTF keys are in seconds. Match the source timebase before importing.
bpy.context.scene.render.fps=fps
bpy.context.scene.render.fps_base=fps_base
bpy.ops.import_scene.gltf(filepath=str(root/f'exports/drone-{version}.glb'))
bpy.context.scene.frame_set(1)
errors={}
for name,(points,tree) in native.items():
    exported,other=surface(bpy.data.objects[name])
    error=max(max(other.find_nearest(p)[3] for p in points),
              max(tree.find_nearest(p)[3] for p in exported))*1000
    errors[name]=round(error,6)
assert max(errors.values())<.01,errors
print('Native/export surface deviations (mm):',errors)
(root/f'measurements/{version}-export-check.json').write_text(json.dumps(errors,indent=2)+'\n')
