"""Model the photo-visible ESC and navigation board assemblies in the approved aircraft."""
import math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v15_geometry import Parts,rounded,circle,material
from v18_reference import *

assert Path(bpy.data.filepath).name=='drone-v17.blend'
scene=bpy.data.scenes['V17 · Assembled'];bpy.context.window.scene=scene;scene.frame_set(1)
scene.name='V18 · Assembled'
coll=bpy.data.collections['V17 | Interior'];coll.name='V18 | Interior'
air=bpy.data.collections['V17 | Aircraft'];air.name='V18 | Aircraft'
root_obj=air.objects['Drone.V17'];root_obj.name='Drone.V18'
p=Parts.__new__(Parts);p.coll=coll;p.parent=root_obj
def finish(name,color,rough,metal=0):
    m=material(name,color,metal)
    m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=rough
    return m
p.mats={
 'edge':finish('graphite laminate edge',(.085,.074,.051),.62),
 'epoxy':finish('moulded board packages',(.016,.019,.020),.56),
 'socket':finish('connector thermoplastic',(.026,.025,.025),.40),
 'silver':finish('component solder',(.58,.61,.58),.28,.85),
 'gold':finish('contact flash',(.71,.47,.16),.32,.79),
 'tin':finish('component terminations',(.45,.46,.45),.38,.78),
 'capacitor':finish('ceramic package body',(.39,.30,.20),.55),
 'dark':finish('dark resistor coat',(.048,.050,.052),.55),
 'ivory':finish('nylon eyelet',(.81,.80,.74),.44),
 'clay':finish('ceramic antenna edge',(.41,.227,.146),.50),
 'patch':finish('antenna top metallisation',(.75,.73,.67),.47,.39),
 'blue':finish('blue grey encapsulant',(.177,.294,.37),.24),
 'can':finish('rolled receiver shielding',(.47,.49,.48),.32,.80),
 'stamp':finish('shield pressing',(.41,.43,.42),.38,.77)}
assets=root/'blender/materials/v18'
for key in matrices:
    m=finish('board finish '+key,(.1,.1,.1),.5);p.mats[key]=m
    bs=m.node_tree.nodes.get('Principled BSDF')
    def tex(suffix,space):
        ext='.png' if suffix else '.jpg'
        im=bpy.data.images.load(str(assets/(key+suffix+ext)));im.colorspace_settings.name=space;im.pack()
        t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;return t
    color=tex('','sRGB');orm=tex('-orm','Non-Color');separate=m.node_tree.nodes.new('ShaderNodeSeparateColor')
    for source,target in [(color.outputs['Color'],bs.inputs['Base Color']),(orm.outputs['Color'],separate.inputs[0]),
        (separate.outputs['Green'],bs.inputs['Roughness']),(separate.outputs['Blue'],bs.inputs['Metallic'])]:
        m.node_tree.links.new(source,target)
    bs.inputs['Specular IOR Level'].default_value=.22
    if key.startswith('esc'):
        chip=finish('package lettering '+key,(.025,.026,.025),.60)
        chip.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.18
        im=bpy.data.images.load(str(assets/(key+'-packages.png')));im.pack()
        sampler=chip.node_tree.nodes.new('ShaderNodeTexImage');sampler.image=im
        chip.node_tree.links.new(sampler.outputs['Color'],chip.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
        p.mats[key+' package']=chip
def face_uv(o,key):
    m=o.data;uv=m.uv_layers.get('Board face registration') or m.uv_layers.new(name='Board face registration')
    inv=np.linalg.inv(matrices[key]);x0,y0,x1,y1=texture_bounds[key]
    for loop in m.loops:
        x,y,z=o.matrix_world@m.vertices[loop.vertex_index].co*1000
        u,v=project(inv,x,y);uv.data[loop.index].uv=((u-x0)/(x1-x0),1-(v-y0)/(y1-y0))
def mate(o,*parts):o['Mating parts']=';'.join(s if isinstance(s,str) else s.name for s in parts)
def label(o,tag):
    o['V18 board']=tag
    if 'Review 6' in o:del o['Review 6']
    return o
def replace(name,new):
    old=coll.objects[name];old.name='Superseded '+name
    bpy.context.view_layer.update()
    for child in list(old.children):
        mw=child.matrix_world.copy();child.parent=new;child.matrix_parent_inverse=new.matrix_world.inverted();child.matrix_world=mw
    bpy.data.objects.remove(old,do_unlink=True);new.name=name;new.data.name=name
    return new
def xy(key,a,b):return project(matrices[key],a,b)
def outline(key,poly):return [xy(key,a,b) for a,b in poly]
def rounded_poly(a,b,c,d,r,n=5):
    return [((a+c)/2+x,(b+d)/2+y) for x,y in rounded(c-a,d-b,r,n)]
def soften(poly,r=.11):
    result=[]
    for i,pos in enumerate(poly):
        a,b,c=map(np.array,(poly[i-1],pos,poly[(i+1)%len(poly)]))
        v=b+(a-b)*r;w=b+(c-b)*r
        for t in (0,.33,.67,1.):result.append(tuple(v*(1-t)**2+2*b*t*(1-t)+w*t*t))
    return result

# A batch holds the distinct closed islands belonging to one service component.
# Coordinates are in millimetres. Each package, pin and contact has physical relief.
class Batch:
    def __init__(self):
        self.v=[];self.faces=[];self.material=[];self.smooth=[]
    def ringform(self,rows,mat,smooth=False,loop=False):
        start=len(self.v);n=len(rows[0]);h=len(rows);self.v.extend(pt for row in rows for pt in row)
        count=h if loop else h-1
        for j in range(count):
            k=(j+1)%h
            for i in range(n):
                self.faces.append(tuple(start+o for o in (j*n+i,j*n+(i+1)%n,k*n+(i+1)%n,k*n+i)))
                self.material.append(mat);self.smooth.append(smooth)
        if not loop:
            self.faces.extend([tuple(start+i for i in range(n)),tuple(start+(h-1)*n+i for i in range(n))])
            self.material.extend([mat,mat]);self.smooth.extend([False,False])
    def shape(self,poly,z,h,mat,bevel=.07):
        pts=np.asarray(poly);ctr=pts.mean(axis=0);extent=max(.00001,np.min(np.ptp(pts,axis=0)))
        b=min(bevel,abs(h)*.27,extent*.14);k=1-2*b/extent
        rows=[]
        for scale,level in [(k,z),(1,z+math.copysign(b,h)),(1,z+h-math.copysign(b,h)),(k,z+h)]:
            rows.append([(x,y,level) for x,y in ctr+(pts-ctr)*scale])
        self.ringform(rows,mat)
    def rect(self,key,rect,z,h,mat,r=2,bevel=.055):
        self.shape(outline(key,rounded_poly(*rect,r)),z,h,mat,bevel)
    def round(self,x,y,profile,mat,loop=False):
        self.ringform([[(a,b,z) for a,b in circle(x,y,r,64)] for z,r in profile],mat,True,loop)
    def save(self,name,owner,tag,*contacts):
        keys=list(dict.fromkeys(self.material));o=p.mesh(name,self.v,self.faces,keys[0],owner)
        for k in keys[1:]:o.data.materials.append(p.mats[k])
        for f,m,s in zip(o.data.polygons,self.material,self.smooth):f.material_index=keys.index(m);f.use_smooth=s
        label(o,tag)
        if contacts:mate(o,*contacts)
        return o

def make_board(name,key,poly,holes,z,h):
    edge=outline(key,soften(poly,.065))
    if key=='esc':
        # Keep the V17 rear edge at the pack header. The photographic projection
        # extends part of this small tongue 0.34 mm into the metal contact path.
        edge=[(x,max(y,-58.35)) for x,y in edge]
    board=replace(name,p.plate('Detailed laminate',edge,z,h,'edge',
           [circle(x,y,r,72) for (x,y),r in holes],parent=root_obj))
    label(board,key);m=board.data;uv=m.uv_layers.new(name='Board face registration')
    for face in (key,key+'-back'):m.materials.append(p.mats[face])
    for poly in m.polygons:
        if abs(poly.normal.z)<.99:continue
        upper=poly.normal.z>0;face=key if upper else key+'-back';poly.material_index=1 if upper else 2
        inv=np.linalg.inv(matrices[face]);x0,y0,x1,y1=texture_bounds[face]
        for index in poly.loop_indices:
            x,y,z=board.matrix_world@m.vertices[m.loops[index].vertex_index].co*1000
            u,v=project(inv,x,y);uv.data[index].uv=((u-x0)/(x1-x0),1-(v-y0)/(y1-y0))
    return board

esc_diameters=[1.60,2.57,2.58]
drive=make_board('Board.motor_control','esc',esc_outline,[(xy('esc',*pt),r) for pt,r in zip(esc_holes,esc_diameters)],44,1)
nav=make_board('Board.navigation','gps',gps_outline,[(pt,.95) for pt in gps_datum],45.6,.9)

def package(batch,key,rect,z,h,legs=0):
    a,b,c,d=rect;batch.rect(key,rect,z,h,'epoxy',min(2,(d-b)*.13))
    batch.material[-1]=key+' package'
    if not legs:return
    for vertical in (True,False):
        for i in range(legs):
            t=(i+.5)/legs
            for sign in (-1,1):
                if vertical:
                    cy=b+(d-b)*(.07+.86*t);x=a if sign==-1 else c
                    box=(x-3.15,cy-.67,x+.12,cy+.67) if sign<0 else (x-.12,cy-.67,x+3.15,cy+.67)
                else:
                    cx=a+(c-a)*(.07+.86*t);y=b if sign==-1 else d
                    box=(cx-.67,y-3.15,cx+.67,y+.12) if sign<0 else (cx-.67,y-.12,cx+.67,y+3.15)
                batch.rect(key,box,z,h*.31,'tin',.27,.016)
def smd(batch,key,rect,z,h,mat):
    a,b,c,d=rect;vertical=(d-b)>(c-a)
    if vertical:
        q=(d-b)*.23;strips=[(a,b,c,b+q),(a,b+q,c,d-q),(a,d-q,c,d)]
    else:
        q=(c-a)*.23;strips=[(a,b,a+q,d),(a+q,b,c-q,d),(c-q,b,c,d)]
    for box,finish in zip(strips,['tin',mat,'tin']):batch.rect(key,box,z,h,finish,.5,.018)
def socket(batch,key,rect,z,h,pins):
    a,b,c,d=rect
    batch.rect(key,(a,b,c,d),z,h*.35,'socket',1)
    for q in [(a,b,c,b+2.3),(a,d-2.3,c,d),(a,b+2.3,a+1.9,d-2.3),(c-1.9,b+2.3,c,d-2.3)]:
        batch.rect(key,q,z+h*.35,h*.65,'epoxy',.6)
    for i in range(pins):
        x=a+3+(c-a-6)*(i+.5)/pins
        for v in (b+2.5,d-3.9):
            batch.rect(key,(x-.52,v,x+.52,v+1.35),z+h*.35,h*.43,'gold',.16,.009)

upper=Batch()
for rect in upper_chips:package(upper,'esc',rect,45.,.70)
package(upper,'esc',(314,220,391,292),45.,.86,13)
package(upper,'esc',(470,235,529,286),45.,.88,5)
package(upper,'esc',(352,110,404,140),45.,.65)
for i,rect in enumerate(upper_passives):smd(upper,'esc',rect,45.,.27,'capacitor' if i%3 else 'dark')
socket(upper,'esc',(336,390,412,414),45.,.74,17)
face_uv(upper.save('ESC.power_face',drive,'esc',drive),'esc')
# Four triplets of slightly drawn solder fillets at the lead lands.
joints=Batch()
for i,(u,v) in enumerate([(242,128),(268,127),(294,127),(449,121),(477,119),(501,116),
                           (235,419),(263,418),(291,417),(458,421),(489,421),(515,422)]):
    rows=[]
    for dz,k,offset in [(0,.83,0),(.14,1,0),(.37,.92,0),(.62,.68,.8),(.89,.34,2.8),(1.02,.08,4.0)]:
        pts=[]
        for j in range(40):
            a=j*math.tau/40
            x=u+10.3*k*math.cos(a)*(1+.09*math.sin(3*a+i));y=v+12*k*math.sin(a)+(offset if v>300 else -offset)
            pts.append((*xy('esc',x,y),45+dz))
        rows.append(pts)
    joints.ringform(rows,'silver',True)
joints.save('ESC.motor_solder_joints',drive,'esc',drive)
lower=Batch()
for rect in lower_chips:package(lower,'esc-back',rect,44.,-.65,7)
for i,rect in enumerate(lower_passives):
    # A neighbouring V17 rib bears on this face in the RILL casting.
    if rect==(244,338,259,351):
        a,b,c,d=rect;rect=(a+9,b,c+9,d)
    smd(lower,'esc-back',rect,44.,-.43,'dark' if i>=18 else 'capacitor')
face_uv(lower.save('ESC.reverse_face',drive,'esc',drive),'esc-back')

# Trim the nylon grommet to one bearing face and leave a small axial relief at the other.
x,y=xy('esc',549,366);eye=Batch()
eye.round(x,y,[(43.84,2.73),(43.95,2.77),(43.95,2.51),(45.,2.51),(45.,2.71),(45.13,2.69),
               (45.19,2.49),(45.17,1.72),(45.07,1.58),(43.96,1.58),(43.86,1.67)],'ivory',True)
eye.save('ESC.insulating_bushing',drive,'esc',drive)
# The board header registers to the six existing battery tip axes. Its front tongue
# seats against the board underside and the contacts drop into the fitted pack interface.
axes=[(i-2.5)*1.52 for i in range(6)]
header=p.plate('ESC header moulding',[(a,b-56.93) for a,b in rounded(10.0,4.88,.35)],43.19,.81,'socket',
               [[(x+a,-58.87+b) for a,b in rounded(.67,.65,.10)] for x in axes],drive)
carrier=replace('Power.contact_carrier',label(header,'esc'));mate(carrier,drive)
for i,x in enumerate(axes):
    base=coll.objects['Power.contact.%02d'%(i+1)];label(base,'esc')
    # Preserve the six engagement ends. Above each end a formed metal tail
    # emerges through the keyed header and clears the battery thumb catch.
    profile=[(-59.08,43.19),(-58.66,43.19),(-58.66,44.00),(-58.44,44.00),(-58.44,44.20),
             (-58.68,44.31),(-59.48,45.11),(-59.74,45.30),(-60.55,45.30),(-60.76,45.27),
             (-60.76,45.09),(-60.55,45.04),(-59.82,45.04),(-59.67,44.98),(-59.09,44.37),(-59.08,44.23)]
    terminal=p.plate('ESC.contact_tail.%02d'%(i+1),profile,x-.235,.47,'gold',parent=drive)
    for v in terminal.data.vertices:
        y,z,a=v.co;v.co=(a,y,z)
    terminal.data.update();label(terminal,'esc');mate(terminal,base,carrier)
    base.data.materials.clear();base.data.materials.append(p.mats['gold'])
    if 'Mating parts' in base:del base['Mating parts']
ends=Batch()
for i in range(6):
    u,v=[(552,211),(553,231),(554,252),(555,273),(556,295),(557,316)][i]
    rows=[]
    for h,k in [(0,.86),(.10,1),(.22,.90),(.27,.64)]:
        rows.append([(*xy('esc',u+a*k,v+b*k),45+h) for a,b in rounded(20,10,4,7)])
    ends.ringform(rows,'silver',True)
ends.save('ESC.header_solder_tails',drive,'esc',drive)

# Soldered feet on the reverse of the header are visible with the board removed.
feet=Batch()
for x in axes:
    rows=[[(a+x,b+cy,z) for a,b in rounded(w,h,min(w,h)*.34,6)]
          for z,cy,w,h in [(44,-53.99,.75,.98),(43.90,-53.99,.93,1.00),
                            (43.72,-54.04,.77,.85),(43.61,-54.19,.50,.56),(43.56,-54.29,.23,.28)]]
    feet.ringform(rows,'silver',True)
feet.save('ESC.header_solder_feet',drive,'esc',drive,carrier)

# Navigation board. Its ceramic dielectric, face plating and offset feed joint
# are distinct layers. The face and raised cover reproduce the visible outlines.
patch=Batch()
shape=[(246,79),(248,70),(258,66),(417,66),(434,79),(440,239),(435,249),(425,255),(261,255),(249,247)]
patch.shape(outline('gps',soften(shape,.12)),46.50,2.52,'clay',.19)
tile=replace('Navigation.ceramic_patch',patch.save('GPS dielectric',nav,'gps',nav))
foil=Batch()
foilpoly=[(273,102),(290,82),(426,82),(433,220),(417,237),(277,237)]
foil.shape(outline('gps',soften(foilpoly,.07)),49.02,.15,'patch',.035)
face=foil.save('Navigation.patch_plating',nav,'gps',tile)
x,y=xy('gps',327,163);feed=Batch()
feed.round(x,y,[(49.17,1.36),(49.21,1.46),(49.37,1.39),(49.56,1.14),(49.72,.80),(49.82,.34),(49.85,.035)],'silver')
feed.save('Navigation.antenna_feed_joint',nav,'gps',face)
blue=Batch()
tab=[(254,290),(263,278),(289,276),(329,278),(369,275),(392,278),(402,285),(406,315),(403,333),
     (396,340),(366,341),(334,339),(290,342),(269,339),(260,331)]
pts=np.array(outline('gps',soften(tab,.19)));ctr=pts.mean(axis=0);rows=[]
for h,k in [(0,.90),(.16,.96),(.53,1),(1.12,.97),(1.36,.88),(1.49,.60),(1.53,.18)]:
    rows.append([(x,y,46.5+h) for x,y in ctr+(pts-ctr)*k])
blue.ringform(rows,'blue',True)
cap=replace('Navigation.inertial_cap',blue.save('GPS covered tab',nav,'gps',nav))
# Formed metal shield on the reverse and its two shallow embosses.
lid=Batch()
shield=[(300,198),(303,185),(312,178),(324,176),(357,177),(368,181),(377,190),(386,195),
        (425,198),(437,204),(443,215),(448,288),(444,299),(435,308),(315,305),(305,300),(301,289)]
lid.shape(outline('gps-back',soften(shield,.13)),45.60,-1.20,'can',.13)
can=lid.save('Navigation.formed_shield',nav,'gps',nav)
# Rounded perimeter of the stamped sheet, set inside the rolled top edge.
rim=Batch();perimeter=np.array(outline('gps-back',soften(shield,.13)));centre=perimeter.mean(axis=0)
rim.ringform([[(x,y,z) for x,y in centre+(perimeter-centre)*k] for k,z in
              [(.963,44.40),(.963,44.35),(.956,44.30),(.943,44.30),(.938,44.36),(.938,44.40)]],'can',True,True)
rim.save('Navigation.shield_lip',nav,'gps',can)
boss=Batch()
for box,r in [((313,182,366,207),7),((355,245,389,278),4)]:
    boss.rect('gps-back',box,44.40,-.17,'stamp',r,.05)
boss.save('Navigation.shield_pressings',nav,'gps',can)
signal=Batch();socket(signal,'gps-back',(316,112,387,137),45.60,-.66,18)
for i,rect in enumerate(gps_passives):smd(signal,'gps-back',rect,45.6,-.28,'dark' if i in (6,7) else 'capacitor')
signal.save('Navigation.reverse_connector_field',nav,'gps',nav)

# Use a metric UV for a fine brushed finish. This packaged normal map was
# authored for the existing V16 rolled metal and contains no source pixels.
brush=bpy.data.images.load(str(root/'blender/materials/v16/metal-normal.png'),check_existing=True)
brush.colorspace_settings.name='Non-Color';brush.pack()
for key in ('can','stamp'):
    mat=p.mats[key];bs=mat.node_tree.nodes.get('Principled BSDF')
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=brush
    nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.92
    mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
for obj in coll.objects:
    if obj.get('V18 board')!='gps' or not any(m in (p.mats['can'],p.mats['stamp']) for m in obj.data.materials):continue
    uv=obj.data.uv_layers.new(name='Rolled metal')
    for loop in obj.data.loops:
        v=obj.matrix_world@obj.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(v.x/.017,v.y/.017)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/'blender/drone-v18.blend'),compress=True)

