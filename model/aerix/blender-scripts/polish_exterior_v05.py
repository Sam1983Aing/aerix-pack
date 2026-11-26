"""Non-destructive exterior polish branch from the accepted v03 silhouette."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v03.blend'))
s=bpy.context.scene;s.cycles.samples=64;s.render.resolution_x=1536;s.render.resolution_y=1024
root=bpy.data.objects['DRONE_ROOT']
BLACK=bpy.data.materials['Graphite'];TI=bpy.data.materials['Titanium — provisional'];SILVER=bpy.data.materials['Machined motor alloy'];COPPER=bpy.data.materials['Copper accent']
def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
RUBBER=material('Optical baffles and rubber',(.006,.008,.009),0,.44)
COIL=material('Lacquered copper windings',(.42,.17,.055),.78,.23)
CHROME=material('Precision steel fasteners',(.32,.36,.4),.88,.24)
SENSOR_COAT=material('Smoked sensor coating',(.008,.025,.033),.25,.10)
GLASS=material('Multi-coated lens glass',(.72,.88,.93),0,.075)
p=GLASS.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.96;p.inputs['IOR'].default_value=1.46
# Fine satin variance affects roughness and normal, not large-scale contour.
def grain(mat,scale,strength,distance,roughrange):
 ns=mat.node_tree.nodes;ls=mat.node_tree.links;p=ns.get('Principled BSDF')
 n=ns.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=2
 b=ns.new('ShaderNodeBump');b.inputs['Strength'].default_value=strength;b.inputs['Distance'].default_value=distance
 ls.new(n.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs['Normal'],p.inputs['Normal'])
 ramp=ns.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=roughrange[0];ramp.inputs['To Max'].default_value=roughrange[1];ls.new(n.outputs['Fac'],ramp.inputs['Value']);ls.new(ramp.outputs['Result'],p.inputs['Roughness'])
grain(TI,950,.22,.00009,(.30,.43));grain(BLACK,780,.16,.000055,(.27,.39));grain(SILVER,1100,.12,.00003,(.20,.3))
TI.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.36,.33,.28,1)
TI.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.83
anis=SILVER.node_tree.nodes.get('Principled BSDF').inputs.get('Anisotropic')
if anis:anis.default_value=.45

def finish(o,name,mat,parent=root,bevel=0):
 o.name=name;o.parent=parent;o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Precision edge bevel','BEVEL');mod.width=bevel;mod.segments=3
 for p in o.data.polygons:p.use_smooth=True
 o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def box(name,loc,size,mat,parent=root,bevel=.0005):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,mat,parent,bevel)
def cyl(name,loc,r,depth,mat,parent=root,axis='Z',vertices=64):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return finish(o,name,mat,parent,.0002)
def ring(name,loc,outer,inner,depth,mat,parent=root,axis='Z'):
 n=80;vs=[]
 for z,r in [(-depth/2,outer),(depth/2,outer),(-depth/2,inner),(depth/2,inner)]:
  for i in range(n):
   a=i*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
 fs=[]
 for i in range(n):
  j=(i+1)%n
  fs.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(n+i,n+j,3*n+j,3*n+i),(j,i,2*n+i,2*n+j)])
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);o.location=loc
 if axis=='Y':o.rotation_euler.x=math.pi/2
 return finish(o,name,mat,parent,.00018)
def curve(name,pts,r,mat,parent,closed=False):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=3
 spl=data.splines.new('POLY');spl.points.add(len(pts)-1)
 for p,co in zip(spl.points,pts):p.co=(*co,1)
 spl.use_cyclic_u=closed;o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.parent=parent;data.materials.append(mat);return o
# Refine crown-to-shoulder break while keeping each section width and height.
from bisect import bisect_right
xs=[0,.35,.58,.70,.78,.88,.96,1];hs=[1,.985,.94,.85,.73,.48,.19,0]
mesh=bpy.data.objects['BODY_SHELL_TOP'].data
for start in range(0,len(mesh.vertices),17):
 row=list(mesh.vertices)[start:start+17]
 if len(row)!=17:continue
 seam=row[0].co.z;half=max(abs(v.co.x) for v in row);height=max(v.co.z for v in row)-seam
 for v in row:
  u=abs(v.co.x)/half;i=min(len(xs)-2,max(0,bisect_right(xs,u)-1));t=(u-xs[i])/(xs[i+1]-xs[i]);f=hs[i]*(1-t)+hs[i+1]*t;v.co.z=seam+height*f
# Socket recesses and washers on all propeller and hinge fasteners.
for tag in ['FL','FR','RL','RR']:
 g=bpy.data.objects['ARM_'+tag+'_ROOT'];prop=bpy.data.objects['PROPELLER_'+tag];pos=bpy.data.objects['MOTOR_'+tag].location
 def attached(o):o.parent=g;o.matrix_parent_inverse=Matrix.Translation(-g.location);return o
 for xx in [-.010,0,.010]:
  cyl('PROP_HEX_SOCKET_'+tag+'_'+str(xx),(xx,0,.0049),.0011,.0003,RUBBER,prop,vertices=6)
  ring('PROP_WASHER_'+tag+'_'+str(xx),(xx,0,.0039),.0028,.0018,.0005,CHROME,prop)
 # Circular flange below open top cage.
 attached(ring('MOTOR_FLANGE_'+tag,(pos.x,pos.y,.105),.0168,.0128,.0012,CHROME))
 attached(ring('MOTOR_TOP_RING_'+tag,(pos.x,pos.y,.115),.0149,.0085,.0018,BLACK))
 # True individual visible winding loops around twelve stator poles.
 for j in range(12):
  a=j*math.tau/12;radial=Vector((math.cos(a),math.sin(a),0));tangent=Vector((-math.sin(a),math.cos(a),0));center=Vector((pos.x,pos.y,.110))+radial*.0112
  for k in range(4):
   pts=[]
   for m in range(24):
    t=m*math.tau/24
    p=center+radial*(k-1.5)*.00055+tangent*(.00145*math.cos(t))+Vector((0,0,.0026*math.sin(t)));pts.append(tuple(p))
   ob=curve('WINDING_'+tag+'_'+str(j)+'_'+str(k),pts,.00025,COIL,root,True);attached(ob)
 for dz in [.089,.0902,.1006,.1018]:attached(ring('MOTOR_TURNED_LINE_'+tag,(pos.x,pos.y,dz),.0171,.0168,.0003,BLACK))
 # Pin plate at hinge with a real rim around the screw socket.
 attached(ring('HINGE_WASHER_'+tag,(g.location.x,g.location.y,.0907),.004,.002,.0008,CHROME))
 # Molded seam around the motor-to-leg housing.
 attached(ring('MOTOR_BASE_SEAM_'+tag,(pos.x,pos.y,.065),.0181,.0178,.0005,RUBBER))
# Replace simple camera face discs with an open barrel and recessed optics.
gimbal=bpy.data.objects['CAMERA_GIMBAL_ROOT']
for o in list(bpy.data.objects):
 if o.name.startswith('LENS_'):bpy.data.objects.remove(o,do_unlink=True)
housing=bpy.data.objects['CAMERA_HOUSING']
bpy.context.view_layer.objects.active=housing
for oldmod in list(housing.modifiers):
 bpy.ops.object.modifier_apply(modifier=oldmod.name)
bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.016,depth=.037,location=(0,-.162,.035),rotation=(math.pi/2,0,0));cut=bpy.context.object
mod=housing.modifiers.new('Lens cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
bpy.context.view_layer.objects.active=housing;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
ring('LENS_BARREL',(0,-.165,.035),.019,.0155,.017,BLACK,gimbal,'Y')
for yy,r,ri in [(-.175,.0175,.0144),(-.178,.0157,.0138),(-.172,.0145,.0127),(-.167,.0135,.0105)]:ring('LENS_RETAINING_'+str(yy),(0,yy,.035),r,ri,.001,BLACK,gimbal,'Y')
cyl('LENS_APERTURE',(0,-.157,.035),.009,.0007,RUBBER,gimbal,'Y')
for yy,r,thick in [(-.176,.0137,.0014),(-.165,.011,.002)]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=(0,yy,.035));o=bpy.context.object;o.scale=(r,thick,r);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'LENS_COATED_ELEMENT_'+str(yy),GLASS,gimbal)
for j in range(64):
 a=j*math.tau/64;box('LENS_GRIP_'+str(j),(.019*math.cos(a),-.164,.035+.019*math.sin(a)),(.00032,.006,.00032),RUBBER,gimbal,.0001)
# Small camera chassis screws, never additional marketing text.
for sign in [-1,1]:
 for z in [.019,.050]:cyl('CAMERA_FASTENER',(sign*.020,-.163,z),.0012,.0008,CHROME,gimbal,'Y')
 # Replace front sensor's flat pupil with a deeper small optical stack.
 x=sign*.044
 for o in list(bpy.data.objects):
  if o.name in ['SENSOR_PUPIL_'+str(sign),'SENSOR_GLASS_'+str(sign)]:bpy.data.objects.remove(o,do_unlink=True)
 ring('SENSOR_OPTICAL_RIM_'+str(sign),(x,-.148,.082),.006,.0048,.0012,BLACK,root,'Y')
 bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=20,location=(x,-.149,.082));o=bpy.context.object;o.scale=(.0047,.0008,.0047);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,'SENSOR_COATED_GLASS_'+str(sign),SENSOR_COAT)
# More precise studio highlights and surface texture; same hero pose.
s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.20
for name,power in [('KEY',8),('FILL',3),('RIM',8)]:bpy.data.lights[name].energy=power
key=bpy.data.lights['KEY'];key.shape='RECTANGLE';key.size=.28;key.size_y=.6
# Fine ground texture ties contact shadows to a realistic product-photo surface.
grain(bpy.data.materials['Studio'],140,.16,.00012,(.6,.75))
# Existing nine review cameras and isolated geometry remain reusable.
s.camera=bpy.data.objects['CAM_hero'];s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v05.blend'))
for name in ['hero','propeller','camera','top','rear']:
 s.camera=bpy.data.objects['CAM_'+name];bpy.data.objects['STUDIO_GROUND'].hide_render=name in ['top','rear']
 s.render.filepath=str(ROOT/'renders/exterior-v05'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('EXTERIOR_V05_COMPLETE')
