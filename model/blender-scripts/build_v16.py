"""Detail the closed battery and two populated faces of the V15 core PCB."""
import math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v15_geometry import Parts, rounded, circle, material
from v16_reference import top, bottom, lower_field, top_lids, bottom_lids, pressings
assert Path(bpy.data.filepath).name=='drone-v15.blend'
scene=bpy.data.scenes['V15 · Assembled']
bpy.context.window.scene=scene
scene.name='V16 · Assembled';scene.frame_set(1)
for s in list(bpy.data.scenes):
    if s!=scene: bpy.data.scenes.remove(s)
air=bpy.data.collections['V15 | Aircraft'];air.name='V16 | Aircraft'
coll=bpy.data.collections['V15 | Interior blockout'];coll.name='V16 | Interior'
air.objects['Drone.V15'].name='Drone.V16'
case=coll.objects['Battery.case'];pcb=coll.objects['Board.core']
parts=Parts.__new__(Parts);parts.coll=coll;parts.parent=pcb
assets=root/'blender/materials/v16'
def finish(label,color,rough,metal=0):
    m=material(label,color,metal);m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=rough
    return m
parts.mats={
 'polymer':finish('warm grey pack moulding',(.29,.30,.28),.43),
 'latch':finish('thumb catch satin',(.31,.32,.295),.42),
 'black':finish('socket insulator',(.023,.026,.025),.49),
 'mask':finish('exposed laminate edge',(.113,.099,.064),.64),
 'nickel':finish('shield nickel silver',(.61,.63,.62),.35,.84),
 'darkshield':finish('dark finished shielding',(.18,.195,.202),.38,.81),
 'stamp':finish('pressed tinned alloy',(.56,.59,.59),.32,.83),
 'sd':finish('card cage stainless',(.49,.52,.52),.32,.78),
 'tin':finish('solder termination',(.49,.51,.49),.37,.76),
 'gold':finish('plated contact',(.69,.45,.15),.37,.72),
 'chip':finish('epoxy package',(.026,.032,.034),.60),
 'ceramic':finish('ceramic passive',(.32,.267,.204),.54),
 'paste':finish('blue thermal compound',(.055,.37,.48),.77),
 'lens':finish('optical window',(.012,.022,.024),.18,.21)}
def swap(obj,mat):
    obj.data.materials.clear();obj.data.materials.append(parts.mats[mat])
def textured(name,filename,rough):
    m=finish(name,(.4,.4,.4),rough)
    nodes=m.node_tree.nodes;t=nodes.new('ShaderNodeTexImage')
    img=bpy.data.images.load(str(assets/filename));img.pack();t.image=img;t.interpolation='Linear'
    m.node_tree.links.new(t.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    return m
def uvfinish(o,faces):
    m=o.data
    uv=m.uv_layers.new(name='Service artwork')
    slots={key:len(m.materials)+i for i,key in enumerate(faces)}
    for mat,mapper in faces.values():m.materials.append(mat)
    for p in m.polygons:
        n=(o.matrix_world.to_3x3()@p.normal).normalized()
        key='upper' if n.z>.80 else 'lower' if n.z<-.80 else None
        if key not in faces:continue
        p.material_index=slots[key]
        for i in p.loop_indices:
            pt=o.matrix_world@m.vertices[m.loops[i].vertex_index].co
            uv.data[i].uv=faces[key][1](pt.x*1000,pt.y*1000)
def attach(o,owner):
    bpy.context.view_layer.update()
    mat=o.matrix_world.copy();o.parent=owner;o.matrix_parent_inverse=owner.matrix_world.inverted();o.matrix_world=mat
def replace(name,new):
    old=coll.objects[name];old.name='Replaced '+name
    for child in list(old.children):attach(child,new)
    bpy.data.objects.remove(old,do_unlink=True);new.name=name;new.data.name=name
    return new
def mating(o,*others):
    names=[x if isinstance(x,str) else x.name for x in others]
    o['Mating parts']=';'.join(names)
def note(o,source):
    o['Evidence']=source
    if 'Review 6' in o:del o['Review 6']
    return o
def loft(name,out,z0,z1,mat,owner=pcb,lip=.12):
    # Stepped and rolled sheet edges produce a narrow highlight around the lid.
    cx=sum(x for x,y in out)/len(out);cy=sum(y for x,y in out)/len(out)
    def ring(k,z):
        return [(cx+(x-cx)*k,cy+(y-cy)*k,z) for x,y in out]
    direction=1 if z1>z0 else -1
    radius=min(lip,abs(z1-z0)*.34)
    return parts.loft(name,[ring(.98,z0),ring(1,z0+direction*radius),ring(1,z1-direction*radius),ring(.975,z1)],mat,owner)
def rect_px(proj,x0,y0,x1,y1,r):
    return [proj((x0+x1)/2+x,(y0+y1)/2+y) for x,y in rounded(x1-x0,y1-y0,r)]
def merge(objects,name):
    # Retain separate materials and islands on a serviceable assembly.
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    obj=objects[0];bpy.context.view_layer.objects.active=obj
    bpy.ops.object.join();obj.name=name;obj.data.name=name
    return obj
# Soften the end transitions inside the previous pack profile. The long full-width
# region and the four published extrema keep their V15 support locations.
case_rows=[(-65.5,33.8,13.5,32.56),(-63.,38.7,14.55,32.575),(8.15,38.7,14.55,32.575),(9.5,37.9,14.2,32.87)]
rows=case_rows
for step in range(3):
    new=[rows[0]]
    for a,b in zip(rows,rows[1:]):
        for t in (.12,.88):
            new.append(tuple((1-t)*v+t*w for v,w in zip(a,b)))
    new.append(rows[-1]);rows=new
profile=[[(x,y,z+zc) for x,z in rounded(w,h,3.8,16)] for y,w,h,zc in rows]
case=replace('Battery.case',parts.loft('Pack shell with radiused ends',profile,'polymer',case.parent))
swap(case,'polymer')
uvfinish(case,{'upper':(textured('printed pack film','pack-film.png',.46),lambda x,y:((9.5-y)/75,(x+19.35)/38.7))})
for p in case.data.polygons:
    if len(p.vertices)==4:p.use_smooth=True
# Preserve planar faces and blend across the radiused case shoulders.
for p in case.data.polygons:
    if abs(p.normal.z)>.998 or abs(p.normal.x)>.998:p.use_smooth=False
note(case,'PD isolated pack • published external envelope. Label is original RILL artwork.')
# One continuous piece with four grip valleys running across its width.
# The high points stay within the V15 latch height.
grip=[]
for i in range(81):
    t=i/80;y=-65.05+4.68*t
    value=.5-.5*math.cos(2*math.pi*(t*4))
    h=44.89-.32*(1-value)**2
    if i in (0,80):h-=.23
    w=8.95-.38*(abs(2*t-1)**6)
    grip.append([(-w+.34,y,39.85),(w-.34,y,39.85),(w,y,40.23),(w,y,h-.25),
                 (w-.12,y,h-.08),(w-.33,y,h),(-w+.33,y,h),(-w+.12,y,h-.08),(-w,y,h-.25),(-w,y,40.23)])
# Maintain the exact 44.9 mm pack extreme on ridge crowns.
high=max(max(z for x,y,z in r) for r in grip)
grip=[[(x,y,z+(44.9-high) if z>44 else z) for x,y,z in r] for r in grip]
latch=replace('Battery.release_latch',parts.loft('new thumb catch',grip,'latch',case))
for p in latch.data.polygons:
    if len(p.vertices)==4:p.use_smooth=True
mating(latch,case);note(latch,'PD isolated pack • ribbed thumb catch and rounded ends')
sock=coll.objects['Battery.contact_receptacle'];swap(sock,'black')
# Gold recessed throats within the approved contact apertures.
sock.data.materials.append(parts.mats['gold'])
for polygon in sock.data.polygons:
    pos=sock.matrix_world@polygon.center
    if abs(polygon.normal.z)<.1 and any(abs(math.hypot(pos.x*1000-(i-2.5)*1.52,pos.y*1000+58.87)-.52)<.045 for i in range(6)):
        polygon.material_index=1
note(sock,'Rear contact interface • plated walls of the six existing apertures')

swap(pcb,'mask')
uvfinish(pcb,{'upper':(textured('component face solder mask','board-upper.png',.49),
                        lambda x,y:((11.5-y)/79.5,1-(19.3-x)/38.6)),
              'lower':(textured('thermal face solder mask','board-lower.png',.50),
                        lambda x,y:((11.5-y)/79.5,1-(x+19.3)/38.6))})
note(pcb,'PD board ruler, WD installed & stripped shield faces • four retained hole centres.')
def cut_solid(obj,cutter):
    bpy.context.view_layer.update()
    mod=obj.modifiers.new('Form clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;mod.solver='EXACT'
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    obj.modifiers.clear();obj.data=mesh;bpy.data.objects.remove(cutter,do_unlink=True)
def soften_outline(poly):
    out=[]
    for i,p in enumerate(poly):
        a=Vector(poly[i-1]);b=Vector(p);c=Vector(poly[(i+1)%len(poly)])
        start=b+(a-b)*.16;end=b+(c-b)*.16
        for j in range(5):
            t=j/4
            out.append(tuple(start*(1-t)**2+2*b*(1-t)*t+end*t*t))
    return out
# WD figure 7 resolves the obscured front notch in the PD face photo.
# Its four locating holes and the board registration remain fixed.
notch=[(112,366),(119,342),(127,329),(136,322),(148,317),(169,315),
       (206,317),(218,320),(226,327),(231,343),(244,351),(246,401),(104,401)]
cut_solid(pcb,parts.loft('Temporary outline cutter',[[(x,y,z) for x,y in
          soften_outline([top(*p) for p in notch])] for z in (21.5,24.2)],'mask',pcb))
for idx,poly in enumerate(top_lids):
    lid=loft('Core.upper_lid.'+str(idx+1),soften_outline([top(*p) for p in poly]),23.05,23.72,'nickel' if idx==0 else 'darkshield',lip=.24)
    mating(lid,pcb);note(lid,'WD figure 7 • traced metal cover')
    if idx==1:
        for sign in (-1,1):
            relief=parts.box('Temporary skirt notch',(sign*17.2,-27.,24.23),(8.25,1.68,2.04),'mask',.60)
            bpy.context.view_layer.update()
            cut=lid.modifiers.new('Relief for retained tray bearing','BOOLEAN')
            cut.operation='DIFFERENCE';cut.object=relief;cut.solver='EXACT'
            fitted=bpy.data.meshes.new_from_object(lid.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            lid.modifiers.clear();lid.data=fitted;bpy.data.objects.remove(relief,do_unlink=True)
    if idx==2:
        px,py=top(456,172)
        bore=parts.plate('Temporary shield opening',circle(px,py,1.22,48),22.99,.98,'mask',parent=pcb)
        cut_solid(lid,bore)
    additions=[]
    for k,(a,b,c,e) in enumerate(pressings[idx]):
        out=rect_px(top,a,b,c,e,min(4,(c-a)/5,(e-b)/5))
        if idx==2:
            out=soften_outline([top(*p) for p in [(465,226),(473,215),(485,209),(493,211),
                (502,220),(513,237),(510,247),(501,256),(490,259),(480,248),(469,239)]])
        cx=sum(p[0] for p in out)/len(out);cy=sum(p[1] for p in out)/len(out)
        def ring(scale,z):return [(cx+(x-cx)*scale,cy+(y-cy)*scale,z) for x,y in out]
        rings=[ring(1,23.72),ring(.97,23.79),ring(.91,23.89),ring(.85,23.92),ring(.80,23.84)]
        additions.append(parts.loft('Emboss '+str(k),rings,'stamp' if idx in (0,2) else 'darkshield',pcb))
    stamp=merge(additions,'Core.upper_pressing.'+str(idx+1)) if len(additions)>1 else additions[0]
    stamp.name='Core.upper_pressing.'+str(idx+1)
    mating(stamp,lid);note(stamp,'WD figure 7 • visible shallow pressings')
def lower_lid_point(u,v):
    # Preserve the front land. Extend the far shield towards the retained sensor carrier.
    return bottom(u+max(0,min(20,(u-452)*.255)),v)
for idx,poly in enumerate(bottom_lids):
    lower_proj=bottom if idx==0 else lower_lid_point
    lid=replace('Core.shield.'+str(idx+1),loft('new cooling lid',soften_outline([lower_proj(*p) for p in poly]),22.20,21.04,'nickel'))
    mating(lid,pcb);note(lid,'PD core • cooling-face metal lid beneath compound')
    # Unequal deposited ribbons follow the photographed endpoints.
    groups=[[(361,265,360,375,9),(373,282,374,376,5),(397,248,395,375,10),
             (410,268,411,373,5),(429,245,430,373,10)],
            [(455,283,457,370,5),(474,266,475,388,10),(488,281,488,326,4),(506,270,508,387,11)]]
    streaks=[]
    for k,(x0,y0,x1,y1,width) in enumerate(groups[idx]):
        left=[];right=[]
        for j in range(15):
            t=j/14;mid=x0+(x1-x0)*t+.75*math.sin(t*9+k*1.3)
            half=width*(.49+.51*math.sin(math.pi*t)**.33)*(.93+.07*math.sin(27*t+k))*.69
            yy=y0+(y1-y0)*t
            left.append(lower_proj(mid-half,yy));right.append(lower_proj(mid+half,yy))
        streaks.append(loft('Compound bead',left+right[::-1],21.04,20.75,'paste',lip=.085))
    paste=replace('Cooling.compound.'+str(idx+1),merge(streaks,'new contact compound'))
    mating(paste,lid);note(paste,'PD core • individual visible blue contact tracks; compressed thickness retained')
# Replace the solid USB plug proxy with a hollow metal shell and a visible tongue.
usb_y=[-66.85,-66.62,-61.3,-61.15]
def usb_loop(w,h,y):
    return [(-9.1+x,y,24.14+z) for x,z in rounded(w,h,min(h*.43,.70),8)]
rings=[usb_loop(w,h,y) for w,h,y in [(8.49,1.99,usb_y[0]),(8.70,2.10,usb_y[1]),
 (8.70,2.10,usb_y[2]),(8.48,2.00,usb_y[3]),(7.96,1.50,usb_y[3]),
 (7.96,1.50,usb_y[2]),(7.96,1.50,usb_y[1]),(8.04,1.56,usb_y[0])]]
n=len(rings[0])
faces=[(j*n+i,j*n+(i+1)%n,((j+1)%len(rings))*n+(i+1)%n,((j+1)%len(rings))*n+i)
       for j in range(len(rings)) for i in range(n)]
usb=replace('Core.USB_C',parts.mesh('new USB shell',sum(rings,[]),faces,'sd',pcb))
note(usb,'WD figure 7 • formed open rear socket in the retained V15 envelope')
tongue=parts.box('Core.USB_tongue',(-9.1,-63.91,24.14),(6.15,4.56,.27),'black',.30)
pins=[parts.box('USB finger',(-11.15+i*.37,-65.23,24.285),(.15,1.13,.02),'gold',.055) for i in range(12)]
gold=merge(pins,'Core.USB_lands');mating(gold,tongue)
# Back wall ties the tongue to the connector; its cross-section fits inside the rolled metal.
back=parts.loft('Core.USB_insert',[usb_loop(7.96,1.50,y) for y in (-61.63,-61.35)],'black',pcb)
mating(back,usb,tongue)
# Sleeve guard makes a thin open aperture at the card cage lip.
for nobj in ['Storage.cage_rail.L','Storage.cage_rail.R','Storage.cage_roof']:swap(coll.objects[nobj],'sd')
# The exposed components and paired terminals below are picked individually on the photos.
packages={
 'upper':[(469,328,11,17,'chip'),(537,329,17,15,'chip'),(542,289,10,8,'chip'),
          (558,295,8,5,'chip'),(584,274,14,6,'ceramic'),(544,310,5,10,'ceramic'),
          (484,314,7,4,'ceramic'),(484,320,7,4,'ceramic'),(598,301,6,5,'chip')],
 'lower':[(634,348,24,24,'chip'),(632,315,17,17,'chip'),(603,309,21,33,'nickel'),
          (670,341,12,6,'ceramic'),(670,350,12,6,'ceramic'),(668,289,7,5,'ceramic'),
          (619,311,5,9,'ceramic'),(649,326,4,10,'ceramic'),(640,262,13,16,'chip')]}
for face,coordinates in packages.items():
    proj,base,sign=(top,23.05,1) if face=='upper' else (lower_field,22.2,-1)
    objs=[]
    for k,(u,v,w,h,finish_id) in enumerate(coordinates):
        out=rect_px(proj,u-w/2,v-h/2,u+w/2,v+h/2,min(1,w*.14))
        hei=.26 if finish_id=='ceramic' else .36
        objs.append(loft('Package',out,base,base+sign*hei,finish_id,lip=.055))
        if finish_id=='ceramic':
            for edge in [-1,1]:
                a=u+edge*w*.38
                cap=rect_px(proj,a-w*.10,v-h*.42,a+w*.10,v+h*.42,.25)
                objs.append(loft('Termination',cap,base+sign*hei,base+sign*(hei+.025),'tin',lip=.006))
        if face=='lower' and k in (0,1,8):
            dot=[proj(u+math.cos(i*math.tau/36)*w*.32,v+math.sin(i*math.tau/36)*h*.32) for i in range(36)]
            objs.append(loft('Interface deposit',dot,base+sign*hei,base+sign*(hei+.053),'paste',lip=.015))
    bank=merge(objs,'Core.packages.'+face);mating(bank,pcb);note(bank,'WD figure 7 / PD core • identifiable exposed packages and tinned ends')
# Recessed optical windows and their common carrier, registered to the V15 apertures.
optics=[(-7.65,-48.6),(0,-48.6),(7.65,-48.6)]
outline=[(x,y-48.6) for x,y in rounded(20.0,5.6,1.15)]
carrier=parts.plate('Core.optical_carrier',outline,21.17,1.03,'black',
                    [circle(x,y,2.03,44) for x,y in optics])
mating(carrier,pcb);note(carrier,'PD core • three-window carrier at V15 optical centres')
for nobj in ['Belly.IR_left','Belly.vision_camera','Belly.IR_right']:swap(coll.objects[nobj],'lens')
# The paired board-side cable connectors visible ahead of the large thermal lid.
plugs=[]
for k,(u,v) in enumerate([(315,270),(315,351)]):
    out=rect_px(bottom,u-6,v-17,u+6,v+17,1.5)
    plugs.append(loft('Flex connector',out,22.20,21.56,'black'))
    # Metal cover and the exposed terminal comb all belong to the same housing.
    plugs.append(loft('Flex retainer',rect_px(bottom,u-5,v-16,u+2,v+16,1),21.56,21.49,'tin',lip=.015))
    for j in range(10):
        yy=v-13+j*2.8
        plugs.append(loft('Flex contact',rect_px(bottom,u+3,yy,u+5.2,yy+1.3,.25),21.56,21.52,'gold',lip=.01))
group=merge(plugs,'Core.flex_sockets');mating(group,pcb);note(group,'PD core • paired signal headers at board nose, detached cables omitted')
from v16_finish import finish_review_parts
finish_review_parts(coll,parts,case,pcb,assets,mating)
# Establish the review sets without duplicating the assembled master.
bpy.context.view_layer.update()
for obj in coll.objects:
    if obj.name.startswith(('Battery.','Core.','Cooling.compound','Storage.','Belly.')) or obj==pcb:
        obj['Review 7 part']='Battery' if obj.name.startswith('Battery.') else 'Main board'
# Save only after all replacements and hierarchy updates have been evaluated.
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='DESELECT')
stage=root/'blender/drone-v16.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(stage),compress=True)
print('Saved V16 with',sum('Review 7 part' in o for o in coll.objects),'review objects')

