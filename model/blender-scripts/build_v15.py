"""Build the V15 service assemblies from the approved Review 5 inventory."""
import sys,json,math
from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v15_geometry import Parts,rounded,circle,subtract,evaluated_tree
assert Path(bpy.data.filepath).name=='rill15-shell-work.blend'
scene=bpy.context.scene;scene.frame_set(1)
air=bpy.data.collections['V14c | Aircraft'];air.name='V15 | Aircraft'
air.objects['Drone.V14c'].name='Drone.V15'
body=air.objects['Shell.middle_frame'].parent
interior=bpy.data.collections.new('V15 | Interior blockout');scene.collection.children.link(interior)
parts=Parts(interior,body)

# Raised release tab counts toward overall height. Preserve the three published
# extrema while using the pack photograph for the main casing and tapered tail.
base=25.30;main_h=14.55
rings=[]
for y,w,h,zc in [(-65.5,33.8,13.5,32.56),(-63.0,38.7,main_h,base+main_h/2),
                  (8.15,38.7,main_h,base+main_h/2),(9.5,37.9,14.2,32.87)]:
    rings.append([(x,y,zc+z) for x,z in rounded(w,h,3.80,10)])
pack=parts.loft('Battery.case',rings,'pack',note='Published complete envelope 75 × 38.7 × 19.6 mm. Radii and latch relief are provisional, traced from pack views.')
parts.box('Battery.release_latch',(0,-62.8,(base+19.6+base+main_h+.04)/2),(11,4.6,19.6-main_h-.04),'pack',.9)
# Paired underside bearing strips stop at the pack corner transitions.
for s,k in [(-1,'L'),(1,'R')]:
    parts.box('Bay.guide.'+k,(s*13.4,-27,base-.39),(1.4,68,.7),'seat',.45)
    parts.box('Bay.side_guide.'+k,(s*19.65,-18.2,32.65),(.36,39,1.6),'seat',.15)
# Ribbed frame floor. The four relieved lands leave the belly board exposed.
# The end tabs pick up the inner sidewalls at the two crossmembers.
bay=[(-16.2,-52.5),(16.2,-52.5),(16.6,-49.5),(16.3,-46),(15.5,-44),
     (15.5,-4),(18.1,-1.0),(18.1,2.0),(15.2,4.0),(15.2,8.9),
     (-15.2,8.9),(-15.2,4.0),(-18.1,2.0),(-18.1,-1.0),(-15.5,-4),(-15.5,-44),
     (-16.3,-46),(-16.6,-49.5)]
windows=[[(x,y+c) for x,y in rounded(23,l,1.3)] for c,l in [(-45.7,9.2),(-32,14.5),(-15.4,14.5),(1.1,12)]]
parts.plate('Bay.ribbed_floor',bay,24.13,.408,'seat',windows)
# Top-deck board cut-outs and plated mounting holes follow the isolated photographs.
def simple_board(name,x,y,w,l,z,h,holes=()):
    ol=[(x+a,y+b) for a,b in rounded(w,l,.72)]
    return parts.plate(name,ol,z,h,'board',holes)
simple_board('Board.motor_control',0,-42.35,32.5,32,44,1.0,
             [circle(x,y,1.25) for x,y in [(-12.3,-55),(12.4,-55),(12.4,-31.9)]])
# Battery comb is one blockout, with individually separated contact fingers.
parts.box('Power.contact_carrier',(0,-58.87,43.87),(9.8,.9,1.3),'rubber',.16)
for i in range(6):
    parts.box('Power.contact.%02d'%(i+1),((i-2.5)*1.52,-58.87,42.00),(.59,.56,2.38),'contact',.12)
parts.plate('Battery.contact_receptacle',[(x,y-58.87) for x,y in rounded(10.5,1.7,.33)],base+main_h+.035,.89,'rubber',
            [circle((i-2.5)*1.52,-58.87,.53,16) for i in range(6)])
# A broad main rectangle with a narrower projecting inertial tab is visible in both filings.
nav_outline=[(-15,-26.1),(15,-26.1),(15,-2.8),(9,-2.8),(9,6.8),(-9,6.8),(-9,-2.8),(-15,-2.8)]
parts.plate('Board.navigation',nav_outline,45.6,.9,'board',
            [circle(x,y,.95) for x in (-12.9,12.9) for y in (-24.0,-4.8)])
parts.box('Navigation.ceramic_patch',(0,-14.45,47.98),(18,18,2.86),'tile',.72)
parts.box('Navigation.inertial_cap',(0,1.5,47.24),(12.2,6.8,1.4),'metal',.6)
# Digitised board perimeter in the PD core photograph. The narrow spans run
# past the stow channels, while the four mounting ears retain the full width.
outline_px=[(303,221),(320,218),(325,235),(367,235),(390,224),(536,224),(545,219),(637,219),(641,216),
            (668,216),(678,232),(685,252),(685,369),(679,395),(653,396),(645,382),(551,382),(547,396),
            (459,396),(445,383),(330,383),(324,399),(304,399)]
def core_xy(px,py):
    y=11.0-(px-303)*78/382
    relief=max(0,min(1,(y+63)/6,(-22-y)/4))
    return ((py-307.5)*37/183*(1-.058*relief),y)
core=[core_xy(x,y) for x,y in outline_px]
holes=[circle(*core_xy(x,y),.82) for x,y in [(314,229),(315,393),(655,224),(660,389)]]
parts.plate('Board.core',core,22.2,.85,'board',holes)
# Visible shield outlines and the two cooling-contact islands on the belly face.
for i,(x,y,w,l) in enumerate([(0,-3.8,25.0,20.4),(0,-26.2,23.8,20.1)]):
    parts.box('Core.shield.%d'%(i+1),(x,y,21.60),(w,l,1.12),'metal',1.0)
    parts.box('Cooling.compound.%d'%(i+1),(x,y,20.88),(w-2.8,l-2.8,.26),'tim',1.0)
# A compact lower plate and front/rear ears retain their measured plan extents.
# The local fin field stays inside the narrower sides of the approved casting.
plate=[(-16.15,-66.0),(16.15,-66),(17.6,-63),(17.6,-57.7),(16.25,-56),
       (16.25,5.2),(17.5,6.2),(17.5,8.0),(15.8,9),(-15.8,9),(-17.5,8),
       (-17.5,6.2),(-16.25,5.2),(-16.25,-56),(-17.6,-57.7),(-17.6,-63)]
screw_xy=[(-14.3,6.45),(14.3,6.45),(14.2,-59.6)]
optics=[(-7.65,-48.6),(0,-48.6),(7.65,-48.6)]
parts.plate('Cooling.spreader',plate,19.9,.81,'sink',
            [circle(x,y,1.05) for x,y in screw_xy]+[circle(x,y,2.35) for x,y in optics])
for i,y in enumerate([ -36.6+i*3.25 for i in range(13)]):
    parts.box('Cooling.fin.%02d'%i,(0,y,19.22),(31.5,1.05,1.29),'sink',.35)
for i,(x,y) in enumerate(optics):
    parts.tube(['Belly.IR_left','Belly.vision_camera','Belly.IR_right'][i],[(x,y,19.27),(x,y,22.14)],1.96,'glass')
# Rear sockets on the component face. The open card cage surrounds its card.
parts.box('Core.USB_C',(-9.1,-64.0,24.14),(8.7,5.7,2.10),'metal',.65)
card_x=4.8;card_y=-61.4
parts.box('Storage.microSD',(card_x,card_y,24.01),(11,15,1),'rubber',.5)
for s,tag in [(-1,'L'),(1,'R')]:
    parts.box('Storage.cage_rail.'+tag,(card_x+s*5.87,card_y,24.04),(.55,14.4,1.58),'metal',.15)
parts.box('Storage.cage_roof',(card_x,card_y,25.04),(12.3,14.4,.28),'metal',.38)

def fastener(tag,point,length,axis='Z',outer=1.35):
    x,y,z=point
    # An annular boss and a smaller shank leave a visible bore in section.
    obj=parts.plate(tag+'.boss',circle(0,0,outer),0,length-.38,'seat',[circle(0,0,.72)])
    shaft=parts.tube(tag+'.shank',[(0,0,.08),(0,0,length-.35)],.58,'metal')
    head=parts.tube(tag+'.head',[(0,0,length-.34),(0,0,length)],.98,'metal')
    for o in (obj,shaft,head):
        for v in o.data.vertices:
            p=v.co.copy()
            v.co=Vector((p.x,-p.z,p.y)) if axis=='aft' else p
            v.co+=Vector((x,y,z))*.001
        o.data.update()
for x,y in screw_xy:
    # The through-plate shank uses the hole. The head sits on the belly side.
    parts.tube('Spreader.screw_'+str(x)+'_'+str(y),[(x,y,18.65),(x,y,21.65)],.68,'metal')
for s,k in [(-1,'L'),(1,'R')]:
    fastener('Cover.front.'+k,(s*21.0,18.5,27.6),5)
    fastener('Cover.rear.'+k,(s*20.9,-52.3,28.1),5)
    fastener('Hatch.lower_screw.'+k,(s*10.6,-63.8,16.20),5,'aft')
    parts.box('Bay.retention_tab.'+k,(s*21.2,-62.7,33.7),(1.7,3.4,2.2),'seat',.4)
    parts.box('Roof.lining.'+k,(s*7.9,-5,51.75),(5.1,7.1,.14),'metal',.35)
# Retainer and suspension blockouts are located in the nose canopy.
parts.box('Gimbal.internal_retainer',(0,41.5,44.65),(23.8,13.4,1.25),'seat',2)
for s,k in [(-1,'L'),(1,'R')]:
    for f,y in [('front',45.0),('back',37.9)]:
        parts.tube('Gimbal.isolator.'+k+'.'+f,[(s*9.6,y,41.55),(s*9.6,y,43.97)],1.65,'rubber')
    fastener('Gimbal.mount.'+k,(s*7.0,41.2,40.98),3)
parts.tube('Camera.frame_flex',[(0,35.8,39.1),(0,31.8,40.5),(0,25,36.8),(0,20.4,29),
                               (0,13,24.9),(0,10.5,23.65)],.42,'flex')
# Existing face treatment and bearing placements stay on the approved housing.
# A blind receiver pocket directly behind the barrel is fully enclosed.
head=air.objects['Camera.block']
pocket=parts.box('Temporary receiver pocket',(0,50.3,19.4),(17,6.0,10),'seat',1.3)
bpy.context.view_layer.update();subtract(head,pocket)
parts.box('Camera.imager_carrier',(0,51.1,19.4),(11.6,1.1,7.2),'board',.5)
parts.box('Camera.imager',(0,52.17,19.4),(6.0,.9,4.4),'glass',.25)
# Housing switches and windows are represented from the inside.
parts.box('Interface.front_light',(0,60.6,43.1),(8.1,1,1.05),'glass',.35)
parts.box('Interface.rear_light',(0,-70.1,19.5),(5.1,.9,1.05),'glass',.25)
for i in range(4):
    parts.box('Interface.level_LED.%d'%i,(-4.3+i*1.52,3.1,16),(.75,1,.65),'tile',.22)
parts.box('Interface.power_switch',(5.1,3.1,16.1),(4.0,3.1,1.1),'rubber',.85)

# The swept bores follow section centres on the actual moving beams. Wires
# occupy separate corridors and inherit the corresponding original hinge.
def section_centre(o,origin,dir,t):
    pts=[];vs=[(o.matrix_world@v.co)*1000 for v in o.data.vertices]
    ds=[(v-origin).dot(dir)-t for v in vs]
    for e in o.data.edges:
        a,b=e.vertices
        if ds[a]*ds[b]<0:pts.append(vs[a].lerp(vs[b],ds[a]/(ds[a]-ds[b])))
    return sum(pts,Vector())/len(pts)
for code in ['FR','FL','RR','RL']:
    arm=air.objects['Arm.'+code];parent=arm.parent;front=code[0]=='F'
    basep=parent.matrix_world.translation*1000
    m=air.objects['Motor.'+code]
    vs=[m.matrix_world@v.co for v in m.data.vertices]
    end=Vector([(max(v[i] for v in vs)+min(v[i] for v in vs))*500 for i in range(3)])
    axis=(end-basep).normalized();length=(end-basep).length
    path=[section_centre(arm,basep,axis,t*length) for t in (.15,.23,.34,.49,.65,.76,.83)]
    side=axis.cross(Vector((0,0,1))).normalized()
    bore=parts.tube('Temporary arm passage',path,1.72,'seat',parent)
    bpy.context.view_layer.update();subtract(arm,bore)
    path[0]=path[0].lerp(path[1],.08);path[-1]=path[-1].lerp(path[-2],.08)
    for i in range(3+int(front)):
        # All conductors pass through the same blind channel.
        dy,dz=[(-.64,-.35),(.0,-.48),(.67,-.32),(0,.58)][i]
        parts.tube(('RF.coax.' if i==3 else 'Motor.lead%d.'%(i+1))+code,
                   [p+dy*side+Vector((0,0,dz)) for p in path],.21 if i<3 else .28,'wire',parent)
    if front:
        k=code[1];leg=air.objects['Leg.front.'+k]
        vlo=Vector((0,0,0));vertical=Vector((0,0,1))
        path=[section_centre(leg,vlo,vertical,z) for z in (8,12,17,22,26)]
        bore=parts.tube('Temporary front leg pocket',path,1.66,'seat',parent)
        bpy.context.view_layer.update();subtract(leg,bore)
        # The long slim printed antenna is captive in the foot.
        mid=path[2];parts.loft('RF.foot_antenna.'+k,[
            [(p.x+x,p.y+y,p.z) for x,y in rounded(1.88,.56,.16)] for p in path[1:-1]],'board',parent)
        seat=air.objects['Hinge.socket.'+code]
        for number,y in enumerate((13.75,16.25),1):
            x=(1 if k=='R' else -1)*26.25
            void=parts.tube('Temporary captive screw bore',[(x,y,30.46),(x,y,34.03)],.40,'seat')
            bpy.context.view_layer.update();subtract(seat,void)
            parts.tube('Front.pin_screw.'+code+str(number),[(x,y,30.49),(x,y,33.99)],.28,'metal')
for s,k in [(-1,'L'),(1,'R')]:
    # Simplified fixed-side bundles stop at the frame feed-throughs. The
    # flexible loops concealed inside each pivot need direct donor dimensions.
    parts.tube('Loom.front_frame.'+k,[(s*13,-25.90,44.53),(s*15.7,-24.8,43.9),
        (s*17.1,-19,43.45),(s*17.0,-7,42.8),(s*17.9,6,40.8),(s*19.25,14.6,39.5)],.33,'wire')
    parts.tube('Loom.rear_frame.'+k,[(s*16.6,-54.8,44.4),(s*18.1,-55.8,43.4),
        (s*20.3,-55.9,39.6),(s*20.65,-57.3,33.3),(s*20.0,-57.0,27),
        (s*17.95,-56.2,24.1)],.28,'wire')
parts.box('Board.interconnect',(0,-26.21,45.30),(7.0,2.4,.32),'flex',.27)
# Take a real triangle on the inside face as the root of each supporting
# rib. The upper ledges bear on the underside of the corresponding PCB.
frame=air.objects['Shell.middle_frame'];frame_tree=evaluated_tree(frame)
frame.data.calc_loop_triangles()
for label,y,z,seat_name in [('drive',-30.8,44.0,'Board.motor_control'),
                            ('nav',-13.0,45.6,'Board.navigation'),('tray',-27.0,24.13,'Bay.ribbed_floor')]:
    for s,k in [(-1,'L'),(1,'R')]:
        rz=34.6 if label!='tray' else 23.75
        hit,normal,idx,_=frame_tree.ray_cast(Vector((0,y,rz))*.001,(s,0,0))
        tri=frame.data.loop_triangles[idx]
        assert frame.data.materials[tri.material_index].name=='RILL | inner moulding'
        base_tri=[(frame.matrix_world@frame.data.vertices[i].co)*1000 for i in tri.vertices]
        centre=sum(base_tri,Vector())/3
        foot=sorted([centre+(v-centre)*.78 for v in base_tri],key=lambda p:p.y)
        # Outline a triangular section in the YZ plane, wide on its bearing face.
        def rib(x,h):
            return [(s*x,y-.72,h),(s*x,y,h-.68),(s*x,y+.72,h)]
        if label=='tray':
            spans=[rib(abs(centre.x)-.65,23.90),rib(15.4,z),rib(13.35,z)]
        else:
            spans=[rib(20.10,35),rib(20.03,37.3),rib(19.35,39.4),
                   rib(17.15,z-.65),rib(14.6,z),rib(10.8,z)]
        o=parts.loft('Frame.bearing_'+label+'.'+k,[foot]+spans,'seat')
        # Machine the foot to the actual (curved) casting face. Only the
        # provisional rib is trimmed; the skin is the stationary tool.
        trim=o.modifiers.new('Fit bearing to casting','BOOLEAN');trim.operation='DIFFERENCE'
        trim.solver='EXACT';trim.object=frame
        dg=bpy.context.evaluated_depsgraph_get()
        fitted=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
        o.modifiers.clear();o.data=fitted
        o['Mating parts']='Shell.middle_frame;'+seat_name
bpy.context.view_layer.update()
# Keep serviceable components together when an owner is moved in Blender.
def attach(obj,owner):
    old=obj.matrix_world.copy();obj.parent=owner
    obj.matrix_parent_inverse=owner.matrix_world.inverted()
    obj.matrix_world=old
attach(air.objects['Shell.RILL'],air.objects['Shell.roof_cover'])
for obj in list(interior.objects):
    n=obj.name;owner=None
    if n.startswith('Battery.') and n!='Battery.case':owner='Battery.case'
    elif n.startswith('Navigation.'):owner='Board.navigation'
    elif n.startswith('Power.'):owner='Board.motor_control'
    elif n.startswith(('Core.','Storage.','Belly.','Cooling.compound')):owner='Board.core'
    elif n.startswith(('Cooling.fin.','Spreader.')):owner='Cooling.spreader'
    elif n.startswith('Roof.lining.'):owner='Shell.roof_cover'
    elif n.startswith(('Bay.','Frame.bearing','Cover.','Hatch.lower','Gimbal.mount.','Loom.')):owner='Shell.middle_frame'
    elif n.startswith('Camera.imager'):owner='Camera.block'
    elif n.startswith('Motor.lead') or n.startswith('RF.coax.'):owner='Arm.'+n.split('.')[-1]
    elif n.startswith('RF.foot_antenna.'):owner='Leg.front.'+n.split('.')[-1]
    if owner:attach(obj,bpy.data.objects[owner])
bpy.context.view_layer.update()
scene.camera=bpy.data.objects['Studio.camera.three-quarter']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath='/private/tmp/rill15-layout-work.blend',compress=True)
print('Prepared',len(interior.objects),'review meshes')

