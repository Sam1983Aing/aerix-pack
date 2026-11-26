"""Round the exposed rear shell cut edge and correct the fascia return normals."""
import bpy,bmesh,math,json,ast,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parents[2];OUT=R/'renders/exterior-v25'
profile=json.loads((R/'scripts/blender/data/rear-source-profile-v11.json').read_text());toprow=profile['toprow'];bottomrow=profile['bottomrow']
for node in ast.parse((R/'scripts/blender/polish_rear_v23.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'smooth','interp','zfit','zunfit','rear_y','rear_x','top','bottom'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<rear profile>','exec'))
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v22.blend'))
source=bpy.data.objects['BODY_CRADLE'].data;source.calc_loop_triangles();sv=[v.co.copy() for v in source.vertices];st=[tuple(t.vertices) for t in source.loop_triangles];sn=[[source.corner_normals[i].vector.copy() for i in t.loops] for t in source.loop_triangles];source_tree=BVHTree.FromPolygons(sv,st,all_triangles=True)
def original_skin_normal(p):
 q,n,i,d=source_tree.find_nearest(p);a,b,c=st[i];return barycentric_transform(q,sv[a],sv[b],sv[c],*sn[i]).normalized()
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/aerix-exterior-v24.blend'))
row=[Vector(p) for p in bottomrow]
def near(p):return min((p-(a+(b-a)*max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared)))).length for a,b in zip(row,row[1:]))
def pointkey(p):return tuple(round(v,8) for v in p)
def facekey(m,f):return tuple(sorted(pointkey(m.vertices[i].co) for i in f.vertices))
o=bpy.data.objects['BODY_CRADLE'];m=o.data
# Preserve corner normals by face and vertex coordinates across the BMesh edit.
oldfaces={facekey(m,f):{pointkey(m.vertices[m.loops[li].vertex_index].co):m.corner_normals[li].vector.copy() for li in f.loop_indices} for f in m.polygons}
m.calc_loop_triangles();vs=[v.co.copy() for v in m.vertices];ts=[tuple(t.vertices) for t in m.loop_triangles];ns=[[m.corner_normals[i].vector.copy() for i in t.loops] for t in m.loop_triangles];tree=BVHTree.FromPolygons(vs,ts,all_triangles=True)
def old_normal(p):
 q,n,i,d=tree.find_nearest(p);a,b,c=ts[i];return barycentric_transform(q,vs[a],vs[b],vs[c],*ns[i]).normalized()
rim=bpy.data.materials['V23 satin rear shell rim'].copy();rim.name='V25 even rear rim graphite'
p=rim.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.013,.017,.021,1);p.inputs['Metallic'].default_value=.22;p.inputs['Roughness'].default_value=.33
m.materials.append(rim);slot=len(m.materials)-1
bm=bmesh.new();bm.from_mesh(m);bm.normal_update()
edges=[e for e in bm.edges if all(v.co.y>.130 and v.co.z<.0639 and near(v.co)<.000003 for v in e.verts)]
assert len(edges)==28
upper=[e for e in bm.edges if e.is_manifold and all(v.co.y>.127 and abs(v.co.x)>.043 and .063<v.co.z<.089 for v in e.verts) and abs(e.verts[0].co.z-e.verts[1].co.z)>.003 and e.calc_face_angle()>math.radians(50)]
print('CORNER_EDGE_COUNT',len(upper),flush=True)
bmesh.ops.bevel(bm,geom=upper,offset=.00012,segments=6,affect='EDGES',profile=.5,clamp_overlap=True,material=slot)
result=bmesh.ops.bevel(bm,geom=edges,offset=.00018,segments=8,affect='EDGES',profile=.5,clamp_overlap=True,material=slot)
for f in result['faces']:f.smooth=True
bm.to_mesh(m);bm.free();m.update()
if m.attributes.get('custom_normal'):m.attributes.remove(m.attributes['custom_normal'])
# Recover true surface normals at the rear. The old rim override assigned a
# forward normal to some underside faces, producing a bright, knife-like line.
for e in m.edges:
 if all(m.vertices[i].co.y>.126 for i in e.vertices):e.use_edge_sharp=False
for f in m.polygons:
 if f.center.y>.125:f.use_smooth=True
m.update();auto=[n.vector.copy() for n in m.corner_normals];normals=[];changed=0
for f in m.polygons:
 prior=oldfaces.get(facekey(m,f));rimface=f.material_index==slot;old_rim=f.material_index==1
 if old_rim:f.material_index=slot
 for li in f.loop_indices:
  v=m.vertices[m.loops[li].vertex_index].co
  prev=prior.get(pointkey(v)) if prior else None
  if prev is None:prev=old_normal(v)
  # New fillet normals and the cut wall use the actual rounded topology.
  weight=0
  if old_rim and abs(f.normal.y)<.8:prev=original_skin_normal(v)
  elif old_rim:weight=1
  if rimface:weight=1
  if abs(v.x)>.047 and .063<v.z<.089:weight=max(weight,smooth(.126,.139,v.y))
  if v.z>.084:weight*=1-smooth(.084,.089,v.z)
  normals.append(prev.lerp(auto[li],weight).normalized() if weight else prev)
  if weight:changed+=1
 # Keep texture off the narrow return and pinched rear corner lands only.
 if f.center.y>.130 and f.center.z<.084 and (near(f.center)<.003 or abs(f.center.x)>.047):f.material_index=slot
graphite=bpy.data.materials['Graphite'];nodes=graphite.node_tree.nodes;links=graphite.node_tree.links;bsdf=nodes.get('Principled BSDF')
geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
fade=nodes.new('ShaderNodeMapRange');fade.interpolation_type='SMOOTHERSTEP';fade.clamp=True;fade.inputs['From Min'].default_value=.124;fade.inputs['From Max'].default_value=.133;links.new(sep.outputs['Y'],fade.inputs['Value'])
rough=bsdf.inputs['Roughness'].links[0].from_socket;mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(fade.outputs['Result'],mix.inputs[0]);links.new(rough,mix.inputs[1]);mix.inputs[2].default_value=(.33,.33,.33,1);links.new(mix.outputs[0],bsdf.inputs['Roughness'])
bump=next(n for n in nodes if n.type=='BUMP');strength=bump.inputs['Strength'].default_value;mult=nodes.new('ShaderNodeMapRange');mult.inputs['To Min'].default_value=strength;mult.inputs['To Max'].default_value=0;links.new(fade.outputs['Result'],mult.inputs['Value']);links.new(mult.outputs['Result'],bump.inputs['Strength'])
m.normals_split_custom_set(normals);m.update();o['V25 rear rim']='0.18 mm eight-step edge radius, corrected cut-wall normals and restrained satin edge'
# The V23 extruded outer walls blended toward back-face normals over their whole
# thickness. Use the actual wall tangent at both ends of the extrusion instead.
fascia=bpy.data.objects['REAR_FASCIA'];me=fascia.data;fn=[n.vector.copy() for n in me.corner_normals];depths=[]
for v in me.vertices:
 x=v.co.x;z=v.co.z
 for j in range(6):x-=rear_x(x,z)-v.co.x
 depths.append(rear_y(x,z)-v.co.y)
walls=[];vn={}
for f in me.polygons:
 d=[depths[i] for i in f.vertices]
 if max(d)-min(d)>.0018:
  walls.append(f)
  # This extrusion is parallel to Y, so its correct wall normals lie in X/Z.
  n=Vector((f.normal.x,0,f.normal.z)).normalized()
  for i in f.vertices:vn[i]=vn.get(i,Vector())+n*f.area
for i in vn:vn[i].normalize()
for f in walls:
 for li in f.loop_indices:fn[li]=vn[me.loops[li].vertex_index]
for f in me.polygons:
 if f in walls:continue
 for li in f.loop_indices:
  i=me.loops[li].vertex_index
  if i in vn and depths[i]<.0003 and abs(fn[li].y)<.05:fn[li]=vn[i]
me.normals_split_custom_set(fn);me.update();fascia['V25 return normals']='Correct continuous X/Z wall normals; keep inner cap normal separate'
# Native inspection cameras show both the lower seam and each rear corner.
for name,loc,target,scale in [('rear_rim',(0,.32,-.050),(0,.137,.069),.142),('rear_rim_left',(-.15,.30,-.025),(-.027,.134,.069),.117),('rear_rim_right',(.15,.30,-.025),(.027,.134,.069),.117)]:
 data=bpy.data.cameras.new('CAM_'+name);data.type='ORTHO';data.ortho_scale=scale;cam=bpy.data.objects.new('CAM_'+name,data);bpy.context.scene.collection.objects.link(cam);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera=bpy.data.objects['CAM_rear_rim'];bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/aerix-exterior-v25.blend'))
(OUT/'build.json').write_text(json.dumps({'rounded_edges':28,'corner_edges':len(upper),'skin_normal_source':'V22 lower shell','edge_radius_mm':.18,'edge_segments':8,'rear_normals_repaired':changed,'fascia_wall_faces_repaired':len(walls)},indent=2))
if '--preview' in sys.argv:
 for o in list(bpy.data.objects):
  if o.hide_render or o.type in {'LIGHT','CAMERA'} or o.name in {'STUDIO_GROUND','INTERNAL_ENVELOPES'}:bpy.data.objects.remove(o,do_unlink=True)
 for mat in bpy.data.materials:
  if mat.use_nodes:
   bsdf=mat.node_tree.nodes.get('Principled BSDF')
   if bsdf:
    for socket in ['Normal','Roughness']:
     for link in list(bsdf.inputs[socket].links):mat.node_tree.links.remove(link)
    if bsdf.inputs['Roughness'].default_value<.05:bsdf.inputs['Roughness'].default_value=.4
 bpy.ops.export_scene.gltf(filepath=str(R/'exports/aerix-rear-v25-preview.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('V25_REAR_RIM_POLISH_COMPLETE',flush=True)
