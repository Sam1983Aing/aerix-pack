import bpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[2]
def capture_normals(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 vs=[v.co.copy() for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];ns=[[me.corner_normals[i].vector.copy() for i in t.loops] for t in me.loop_triangles]
 tree=BVHTree.FromPolygons(vs,ts,all_triangles=True);ev.to_mesh_clear();return tree,vs,ts,ns

def restore_normals(ob,cache):
 tree,vs,ts,ns=cache;normals=[None]*len(ob.data.loops)
 for face in ob.data.polygons:
  nearest,normal,idx,d=tree.find_nearest(face.center)
  # New pocket walls have their own crisp normals; the original skin keeps its smooth surface.
  new_wall=d>.00001
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   if new_wall:n=face.normal.copy()
   else:
    q,_,idx,_=tree.find_nearest(p);a,b,c=ts[idx];n=barycentric_transform(q,vs[a],vs[b],vs[c],*ns[idx]).normalized()
   normals[li]=n
 ob.data.normals_split_custom_set(normals)

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v13.blend'))
caches={name:capture_normals(bpy.data.objects[name]) for name in ['BODY_CRADLE','HINGE_CHASSIS_MOUNT_FL','HINGE_CHASSIS_MOUNT_FR']};floor=caches['BODY_CRADLE'][0]
def height(x,y):return floor.ray_cast(Vector((x,y,-.1)),Vector((0,0,1)),1)[0].z
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
for name,cache in caches.items():restore_normals(bpy.data.objects[name],cache)
for name in ['BELLY_SPINE','BELLY_SENSOR_BRIDGE','BELLY_PORT_PAD']:
 ob=bpy.data.objects[name]
 for mod in list(ob.modifiers):
  if mod.type in {'BEVEL','WEIGHTED_NORMAL'}:ob.modifiers.remove(mod)
 normals=[];eps=.00001
 for face in ob.data.polygons:
  for li in face.loop_indices:
   p=ob.data.vertices[ob.data.loops[li].vertex_index].co
   if abs(face.normal.z)<.4:n=face.normal.copy()
   else:
    q,_,idx,_=floor.ray_cast(Vector((p.x,p.y,-.1)),Vector((0,0,1)),1);_,vs,ts,ns=caches['BODY_CRADLE'];a,b,c=ts[idx]
    n=barycentric_transform(q,vs[a],vs[b],vs[c],*ns[idx]).normalized();n*=1 if face.normal.z<0 else -1
   normals.append(n)
 ob.data.normals_split_custom_set(normals)
s=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v14.blend'))
for x,y in [(-.025,.0695),(.025,.0695)]:print('APERTURE_HIT',x,y,bpy.data.objects['BODY_CRADLE'].ray_cast(Vector((x,y,-.03)),Vector((0,0,1))))
s.cycles.samples=20;s.render.resolution_percentage=70;s.render.resolution_x=1536;s.render.resolution_y=1024
bpy.data.objects['STUDIO_GROUND'].hide_render=True;bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=False
for name in ['underside_sensors','underside_rear_joint']:
 s.camera=bpy.data.objects['CAM_'+name];s.render.filepath=str(ROOT/'renders/exterior-v14'/(name+'-normals-preview.png'));bpy.ops.render.render(write_still=True)
