"""Detail the suspended Mini-class camera assembly inside the approved V16 nose."""
from pathlib import Path
import sys,math,bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from v15_geometry import Parts,rounded,circle,material,evaluated_tree
assert Path(bpy.data.filepath).name=='drone-v16.blend'
scene=bpy.data.scenes['V16 · Assembled'];bpy.context.window.scene=scene;scene.frame_set(1)
scene.name='V17 · Assembled'
air=bpy.data.collections['V16 | Aircraft'];air.name='V17 | Aircraft'
inside=bpy.data.collections['V16 | Interior'];inside.name='V17 | Interior'
body=air.objects['Drone.V16'];body.name='Drone.V17'
head=air.objects['Camera.block'];frame=air.objects['Shell.middle_frame']
p=Parts.__new__(Parts);p.coll=inside;p.parent=body
def surface(name,rgb,rough,metal=0):
    m=material(name,rgb,metal);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=rough
    return m
p.mats={
 'frame':surface('suspension moulding',(.036,.041,.042),.44),
 'spider':surface('gimbal carrier satin',(.044,.050,.052),.36,.18),
 'rubber':surface('damper silicone',(.022,.023,.025),.74),
 'shaft':surface('bearing steel',(.46,.49,.51),.29,.87),
 'dark':surface('blackened mount hardware',(.050,.052,.049),.33,.67),
 'copper':surface('camera contact plating',(.66,.43,.12),.32,.75),
 'mask':surface('camera substrate mask',(.018,.025,.024),.43),
 'edge':surface('camera laminate edge',(.116,.099,.069),.64),
 'poly':surface('module lens mount',(.021,.024,.026),.42),
 'bond':surface('module bond line',(.018,.020,.021),.24),
 'barrel':surface('objective sleeve',(.039,.041,.043),.37),
 'ceramic':surface('camera ceramic package',(.49,.386,.239),.49),
 'tin':surface('camera solder',(.49,.50,.50),.33,.78),
 'cable':surface('camera harness jacket',(.025,.027,.029),.41),
 'strand':surface('camera loom edge',(.066,.059,.049),.44),
 'flex':surface('flex termination',(.27,.125,.049),.46),
 'ink':surface('camera board ink',(.59,.59,.52),.60)}
def attach(o,parent):
    bpy.context.view_layer.update();mat=o.matrix_world.copy();o.parent=parent
    o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_world=mat
def remove_old(name,new):
    old=inside.objects[name]
    for c in list(old.children):attach(c,new)
    bpy.data.objects.remove(old,do_unlink=True);new.name=name;new.data.name=name;return new
def mate(o,*others):o['Mating parts']=';'.join(n if isinstance(n,str) else n.name for n in others)
def soften(poly,r=.21):
    out=[]
    for i,P in enumerate(poly):
        a,b,c=map(Vector,(poly[i-1],P,poly[(i+1)%len(poly)]))
        start=b+(a-b)*r;end=b+(c-b)*r
        for j in range(6):
            t=j/5;out.append(tuple(start*(1-t)**2+b*2*t*(1-t)+end*t*t))
    return out
def outline(right):
    return soften(right+[(-x,y) for x,y in reversed(right)])
def bevel(o,width):
    mod=o.modifiers.new('Edge radii','BEVEL');mod.width=width*.001;mod.segments=3
    mod.limit_method='ANGLE';mod.angle_limit=.48
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
    o.modifiers.clear();o.data=mesh
    return o
def difference(o,tool):
    bpy.context.view_layer.update();m=o.modifiers.new('Service cut','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=tool
    dg=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
    o.modifiers.clear();o.data=mesh;bpy.data.objects.remove(tool,do_unlink=True)
def turn(name,x,y,zprofile,finish,parent=None,axis='Z',n=72,closed=False):
    rows=[[(x+rad*math.cos(i*math.tau/n),y+rad*math.sin(i*math.tau/n),level)
           if axis=='Z' else (x+rad*math.cos(i*math.tau/n),level,y+rad*math.sin(i*math.tau/n))
           for i in range(n)] for level,rad in zprofile]
    if closed:
        faces=[(j*n+i,j*n+(i+1)%n,((j+1)%len(rows))*n+(i+1)%n,((j+1)%len(rows))*n+i)
               for j in range(len(rows)) for i in range(n)]
        o=p.mesh(name,sum(rows,[]),faces,finish,parent)
    else:o=p.loft(name,rows,finish,parent)
    for face in o.data.polygons:
        if len(face.vertices)!=4:continue
        if axis=='Z':face.use_smooth=abs(face.normal.z)<.90
        else:face.use_smooth=abs(face.normal.y)<.90
    return o
def rect(cx,cy,w,h,r):return [(cx+x,cy+y) for x,y in rounded(w,h,r,7)]
def ringslab(name,shape,low,high,kind,parent=None,fillet=.09):
    obj=p.plate(name,shape,low,high-low,kind,parent=parent);return bevel(obj,fillet)
def packset(o,group,why):
    o['V17 service group']=group;o['Evidence']=why
    if 'Review 6' in o:del o['Review 6']
def recolor(o,mats):
    for key in mats:o.data.materials.append(p.mats[key])
def world_z(o):return max((o.matrix_world@v.co).z for v in o.data.vertices)*1000

# Four bobbins connect a pierced fixed frame to a separate floating spider.
eye=[(s*9.6,y) for s in (-1,1) for y in (37.9,45.0)]
outside=outline([(8.05,29.20),(9.35,29.65),(10.65,31.72),(11.69,34.20),
 (12.03,36.49),(12.08,38.83),(10.90,39.83),(9.64,40.72),(9.55,41.74),
 (10.32,42.78),(11.90,43.69),(12.24,45.20),(12.00,46.61),(10.90,47.57),
 (8.92,48.16),(6.84,48.15),(3.02,47.93)])
opening=outline([(7.3,33.0),(8.02,34.9),(7.25,37.9),(5.25,40.3),(5.25,42.15),(7.45,44.4),(7.45,47.0)])
fixed=remove_old('Gimbal.internal_retainer',bevel(p.plate('new perimeter bracket',outside,43.95,1.06,'frame',
      [opening]+[circle(x,y,1.31,56) for x,y in eye]+[circle(s*7,41.2,.76,48) for s in (-1,1)],body),.12))
# The aft arch has a curved crown at either shoulder. Refine the planar faces before
# shaping them so long triangulation diagonals do not cross the level board seat.
import bmesh
bm=bmesh.new();bm.from_mesh(fixed.data)
for _ in range(5):
    long=[e for e in bm.edges if min(v.co.y for v in e.verts)<.034 and e.calc_length()>.00125]
    if not long:break
    bmesh.ops.subdivide_edges(bm,edges=long,cuts=1,use_grid_fill=True)
for face in bm.faces:
    if min(v.co.y for v in face.verts)<.034 and abs(face.normal.z)>.99:face.smooth=True
for v in bm.verts:
    x,y,z=v.co*1000
    aft=max(0,min(1,(32.60-y)/3.1));shoulder=max(0,min(1,(abs(x)-6.35)/2.6))
    v.co.z+=.001*1.72*aft*aft*(3-2*aft)*shoulder*shoulder*(3-2*shoulder)
bm.normal_update();bm.to_mesh(fixed.data);bm.free()
fixed.data.update();attach(fixed,frame)
spider_outline=outline([(2.6,35.90),(9.4,35.52),(11.8,36.05),(12.0,38.14),(11.30,39.07),
  (8.9,39.30),(4.7,40.49),(4.7,42.3),(8.7,43.48),(10.98,43.52),(12.05,44.18),
  (11.87,46.1),(10.27,47.0),(8.5,46.9),(4.0,45.18),(2.6,45.61)])
spider=bevel(p.plate('Gimbal.suspended_spider',spider_outline,40.54,.80,'spider',
                    [circle(x,y,1.31,56) for x,y in eye]+[circle(0,42,2.47,72)],body),.09)
for sign,side in [(-1,'L'),(1,'R')]:
    for suffix,y in [('front',45.),('back',37.9)]:
        name='Gimbal.isolator.'+side+'.'+suffix
        form=[(40.12,1.28),(40.18,1.61),(40.32,1.73),(40.48,1.71),(40.54,1.61),
              (40.54,1.24),(41.42,1.24),(41.42,1.59),(41.49,1.72),(41.70,1.73),
              (41.91,1.58),(42.20,1.28),(42.46,1.16),(42.7,1.16),(42.98,1.30),
              (43.29,1.62),(43.55,1.77),(43.79,1.73),(43.95,1.56),(43.95,1.24),
              (45.07,1.24),(45.07,1.62),(45.13,1.75),(45.28,1.68),(45.40,1.36),(45.44,.87),(45.43,.60),(45.36,.48),(45.10,.44),(40.32,.44),(40.12,.56)]
        o=remove_old(name,turn('new captured damper',sign*9.6,y,form,'rubber',spider,closed=True))
        mate(o,fixed,spider)
    # Both mount stations stay at their approved centres. Machine the foot against the cast inner face.
    x=sign*7.;y=41.2
    socket=air.objects['Shell.gimbal_socket'];land=world_z(socket)
    spans=[(2.55,38.55,land,.70,.34),(2.62,38.55,37.87,.78,.34),
           (3.25,38.83,38.37,.79,.35),(4.4,39.43,39.03,.86,.39),
           (5.70,40.36,39.64,1.02,.46),(6.71,41.04,40.11,1.19,.60),
           (7,41.2,40.48,1.26,.70),(7,41.2,43.74,1.26,.70),(7,41.2,43.95,1.36,.70)]
    seat_rings=[]
    for chain,k in [(spans,3),(list(reversed(spans)),4)]:
        for row in chain:
            xx,yy,z=row[:3];seat_rings.append([(sign*xx+row[k]*math.cos(i*math.tau/64),
                 yy+row[k]*math.sin(i*math.tau/64),z) for i in range(64)])
    faces=[(j*64+i,j*64+(i+1)%64,((j+1)%len(seat_rings))*64+(i+1)%64,((j+1)%len(seat_rings))*64+i)
           for j in range(len(seat_rings)) for i in range(64)]
    boss=remove_old('Gimbal.mount.'+side+'.boss',p.mesh('new seat',sum(seat_rings,[]),faces,'frame',frame))
    mate(boss,fixed,socket)
    difference(spider,p.plate('temporary boss clearance',circle(x,y,1.53,64),40.40,1.12,'frame',parent=body))
    shank=remove_old('Gimbal.mount.'+side+'.shank',turn('new mount screw shank',x,y,
                     [(42.49,.39),(42.60,.54),(44.65,.54),(45.01,.57)],'dark',frame))
    screw=remove_old('Gimbal.mount.'+side+'.head',turn('new recessed screw head',x,y,
          [(45.01,.96),(45.07,1.13),(45.19,1.15),(45.38,1.00),(45.49,.76)],'dark',frame))
    cross=[(-.13,-.61),(.13,-.61),(.13,-.16),(.56,-.16),(.56,.16),(.13,.16),
           (.13,.61),(-.13,.61),(-.13,.16),(-.56,.16),(-.56,-.16),(-.13,-.16)]
    difference(screw,p.plate('temporary drive punch',[(x+a,y+b) for a,b in cross],45.22,.5,'dark',parent=frame))
    mate(screw,fixed,shank)
socket=air.objects['Shell.gimbal_socket'];top=world_z(socket)
shaft=turn('Gimbal.suspension_hub',0,42,[(top,2.76),(top+.13,2.92),(38.15,2.92),
        (38.32,2.30),(39.62,2.30),(39.82,2.95),(40.34,3.08),(40.54,2.98),(40.54,2.40),
        (41.34,2.40),(41.34,3.03),(41.48,3.15),(41.67,3.05),(41.73,2.80)],'spider',spider)
mate(shaft,spider,socket)
bearing=turn('Gimbal.bearing_race',0,42,[(41.73,2.84),(41.78,2.95),(42.00,2.95),(42.12,2.76),
 (42.12,2.44),(42.05,2.39),(42.08,2.03),(42.15,1.96),(42.15,1.47),(42.02,1.37),(41.73,1.37)],'shaft',spider,closed=True)
mate(bearing,shaft)
ret=turn('Gimbal.bearing_seal',0,42,[(41.73,1.30),(41.85,1.33),(42.09,1.28),(42.12,.96)],'dark',spider)
mate(ret,shaft)
# Rear interface card, its visible contacts and the captured flat harness socket.
board=bevel(p.plate('Gimbal.interface_board',rect(0,33.63,10.9,4.78,.39),45.01,.52,'mask',
                    [circle(x,32.22,.43,36) for x in (-4.53,4.53)],fixed),.035)
mate(board,fixed)
header=bevel(p.plate('Gimbal.interface_socket',rect(0,34.68,5.75,1.58,.17),45.53,.71,'poly',parent=board),.067)
mate(header,board)
for side in (-1,1):
    a=turn('Gimbal.board_eyelet.'+('L' if side<0 else 'R'),side*4.53,32.22,
           [(45.53,.72),(45.555,.72),(45.555,.45),(45.53,.45)],'copper',board,n=44,closed=True)
    mate(a,board)
def join(objs,name):
    bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();objs[0].name=name
    return objs[0]
contacts=[p.box('Header contact',((i-5)*.40,34.65,46.272),(.20,.70,.064),'tin',.046,header) for i in range(11)]
mate(join(contacts,'Gimbal.interface_contacts'),header)
# Route the installed lead from the socket mouth to the V16 board header.
# A smooth fluted jacket transitions into the flat flex termination at the board.
core=inside.objects['Core.flex_sockets']
tree=evaluated_tree(core);tip=tree.ray_cast(Vector((-.00760,.013,.02179)),(0,-1,0))[0]
assert tip is not None
tip_y=1000*tip.y
keys=[(0,35.47,45.92),(0,36.4,45.92),(.70,37.40,46.34),(2.40,37.93,46.63),
 (4.70,38.72,46.76),(5.62,39.80,46.71),(5.22,40.84,46.62),(2.45,41.23,46.52),
 (-2.0,41.20,46.59),(-5.18,40.63,46.65),(-6.05,39.39,46.72),(-5.49,37.36,46.71),
 (-4.91,34.48,46.63),(-4.94,31.15,46.46),(-4.75,29.10,45.84),(-4.42,27.60,42.75),
 (-4.21,24.6,36.05),(-4.7,21.1,30.15),(-5.85,16.63,25.06),(-7.03,13.09,22.65),
 (-7.6,11.43,21.79),(-7.6,tip_y,21.79)]
keys=list(map(Vector,keys))
def samples(keys):
    path=[]
    for j,(a,b) in enumerate(zip(keys,keys[1:])):
        prev=keys[max(0,j-1)];nxt=keys[min(j+2,len(keys)-1)]
        for i in range(7):
            t=i/7;path.append((2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*(b-prev)/2+
                  (-2*t**3+3*t*t)*b+(t**3-t*t)*(nxt-a)/2)
    return path+[keys[-1]]
path=samples(keys);rows=[];n=32
for i,loc in enumerate(path):
    axis=(path[min(i+1,len(path)-1)]-path[max(0,i-1)]).normalized()
    v=axis.cross(Vector((0,0,1))).normalized();w=axis.cross(v).normalized()
    t=i/(len(path)-1);end=max(0,min(1,(t-.87)/.10));start=max(0,1-t/.09)
    width=.53+.84*end+.73*start;thick=.285-.14*end-.105*start
    rows.append([tuple(loc+math.cos(a:=k*math.tau/n)*width*v*(1+.05*math.cos(5*a+i*.12))+
                 math.sin(a)*thick*w*(1+.07*math.cos(5*a+i*.12))) for k in range(n)])
# Termination rings follow the actual connector planes; use the maximum noseward
# tangent to the board socket where the photographed flex is inserted.
for m,row in [(0,rows[0]),(-1,rows[-1])]:
    corrected=[]
    for x,y,z in row:
        if m==0:new_y=35.47
        else:
            hit=tree.ray_cast(Vector((x,12,z))*.001,(0,-1,0))[0]
            assert hit is not None
            new_y=hit.y*1000
        corrected.append((x,new_y,z))
    rows[m]=corrected
loom=remove_old('Camera.frame_flex',p.loft('new formed camera harness',rows,'cable',fixed))
recolor(loom,['strand','flex'])
for face in loom.data.polygons:
    i=face.index//n;k=face.index%n
    if i>=len(rows)-10:face.material_index=2
    elif i<len(rows)-1 and (k+i//5)%n in (3,4,13):face.material_index=1
    face.use_smooth=len(face.vertices)==4
mate(loom,core,header)
# Retaining arch over the fixed-frame run, attached on the outer crossbar.
# The black loom remains continuous through this open-sided clip.

def vertical_section(name,profile,cy,depth,mat,owner):
    obj=p.plate(name,[(x,-z) for x,z in profile],cy-depth/2,depth,mat,parent=body)
    for vert in obj.data.vertices:
        x,z,y=vert.co;vert.co=(x,y,-z)
    obj.data.update();attach(obj,owner)
    return bevel(obj,.070)
bridge=vertical_section('Gimbal.loom_clip',soften([(-8.27,45.01),(-8.27,46.90),(-8.16,47.35),
  (-7.83,47.55),(-5.29,47.55),(-5.15,47.45),(-5.15,47.16),(-7.51,47.16),(-7.78,46.96),
  (-7.79,45.01)],.14),39.70,.93,'frame',fixed)
mate(bridge,fixed)
cheeks=[]
for sign in (-1,1):
    cheeks.append(p.box('Socket side cheek',(sign*2.61,34.62,46.35),(.42,1.28,.22),'poly',.08,header))
    for yy in (33.46,34.42):
        cheeks.append(p.box('Board contact',(sign*4.24,yy,45.555),(.52,.42,.05),'tin',.075,board))
cheek=join(cheeks,'Gimbal.socket_cheeks_and_pads');mate(cheek,board,header)
# Model only the photographically resolved harness; the hinge lead inside the
# potted motor remains a closed service interface.
from v17_camera import build_camera
build_camera(p,air,inside,head,remove_old,turn,bevel,mate,join,recolor)
for o in inside.objects:
    if o.name.startswith(('Gimbal.','Camera.frame_flex')):
        packset(o,'Suspension','iFixit 149750 cover and steps 13–15; installed cable path fitted in the approved nose')
    elif o.name.startswith('Camera.'):
        packset(o,'Lens module','iFixit 154241 cover; closed barrel and board relief; concealed depths fitted')
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'blender/drone-v17.blend'),compress=True)

