"""Finish materials, the optical windows, socket stampings and card enclosure."""
import bpy,math
from mathutils import Vector
from v15_geometry import rounded

def finish_review_parts(coll,parts,case,pcb,assets,mating):
    def imgtex(m,key,space):
        path=str(assets/key)
        img=next((im for im in bpy.data.images if im.get('V16 asset')==key),None)
        if img is None:
            img=bpy.data.images.load(path);img['V16 asset']=key;img.colorspace_settings.name=space;img.pack()
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;return node
    for face,mat_name in [('upper','component face solder mask'),('lower','thermal face solder mask')]:
        m=bpy.data.materials['RILL | '+mat_name];nodes=m.node_tree.nodes;links=m.node_tree.links
        tex=imgtex(m,'board-'+face+'-orm.png','Non-Color')
        sep=nodes.new('ShaderNodeSeparateColor');links.new(tex.outputs['Color'],sep.inputs[0])
        bsdf=nodes.get('Principled BSDF')
        links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    mats={parts.mats[n] for n in ('nickel','stamp','darkshield','sd','polymer','latch')}
    mats.add(bpy.data.materials['RILL | printed pack film'])
    for m in mats:
        polymer=m in (parts.mats['polymer'],parts.mats['latch'],bpy.data.materials['RILL | printed pack film'])
        tex=imgtex(m,('polymer' if polymer else 'metal')+'-normal.png','Non-Color')
        nodes=m.node_tree.nodes;links=m.node_tree.links
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.57 if polymer else .78
        links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
    # Give the two remaining socket shields small real formed lips.
    old=coll.objects['Storage.cage_roof']
    rows=[]
    for w,l,z in [(15.45,15.65,24.90),(15.70,15.89,24.96),(15.70,15.89,25.05),(15.16,15.35,25.17)]:
        rows.append([(4.60+x,-60.63+y,z) for x,y in rounded(w,l,.77,10)])
    roof=parts.loft('Formed card cage',rows,'sd',pcb)
    bpy.data.objects.remove(old,do_unlink=True);roof.name='Storage.cage_roof'
    for tag in ('L','R'):
        rail=coll.objects['Storage.cage_rail.'+tag]
        for v in rail.data.vertices:
            v.co.z=(23.05 if v.co.z*1000<24.04 else 24.90)*.001
        rail.data.update()
        mating(rail,pcb,roof)
    contact=coll.objects['Battery.contact_receptacle']
    for v in contact.data.vertices:
        if v.co.z*1000<40:v.co.z=.03985
    contact.data.update();mating(contact,case)
    # Three separate planes of the stamped lip; a low crown inside the contact envelope.
    crown=parts.loft('Storage.cage_pressing',[
        [(4.60+x,-60.55+y,z) for x,y in rounded(w,l,r,10)]
        for w,l,r,z in [(14.0,13.9,1.55,25.17),(13.5,13.4,1.4,25.23),(12.5,12.4,1.3,25.24)]],'sd',pcb)
    mating(crown,roof)
    usb=coll.objects['Core.USB_C']
    feet=[]
    for x in (-12.3,-5.9):
        foot=parts.box('USB solder foot',(x,-63.8,23.07),(.53,1.55,.04),'tin',.12,pcb)
        feet.append(foot);mating(foot,pcb,usb)
        foot.name='Core.USB_mount.'+('L' if x<-9 else 'R')
    tabs=[]
    for idx,y in enumerate((-65.71,-62.26)):
        for x in (-11.35,-7.15):
            def ring(w,l,z):
                return [(x+a,y+b,z) for a,b in rounded(w,l,.14)]
            tabs.append(parts.loft('Socket pressings',[ring(.79,.72,25.19),ring(.68,.62,25.26),
                       ring(.49,.45,25.28)],'stamp',pcb))
    bpy.ops.object.select_all(action='DESELECT')
    for o in tabs:o.select_set(True)
    bpy.context.view_layer.objects.active=tabs[0];bpy.ops.object.join()
    tabs[0].name='Core.USB_pressings';mating(tabs[0],usb)
    # Keep the same three barrels in the same spreader holes while turning
    # the flat V15 faces into recessed windows with bevelled black surrounds.
    for name,x,window in [('Belly.vision_camera',0,1.14),('Belly.IR_left',-7.65,1.36),('Belly.IR_right',7.65,1.36)]:
        o=coll.objects[name]
        profile=[(1.86,22.14),(1.96,22.04),(1.96,19.44),(1.88,19.29),(1.68,19.27),
                 (window+.21,19.32),(window+.10,19.47),(window,19.57),(window*.88,19.52),
                 (window*.64,19.48),(window*.30,19.45),(.025,19.44)]
        rings=[[(x+r*math.cos(k*math.tau/64),-48.6+r*math.sin(k*math.tau/64),z)
                for k in range(64)] for r,z in profile]
        form=parts.loft('Turned receiver',rings,'black',pcb)
        form.data.materials.append(parts.mats['lens']);form.data.materials.append(parts.mats['chip'])
        for idx,p in enumerate(form.data.polygons):
            if idx<64*(len(rings)-1):
                j=idx//64;p.use_smooth=j not in (3,4);p.material_index=1 if j>=7 else 2 if j==5 else 0
        o.data=form.data;bpy.data.objects.remove(form,do_unlink=True)
    bpy.context.view_layer.update()
    for o in coll.objects:
        if o.type!='MESH' or not any(m in mats for m in o.data.materials):continue
        mesh=o.data
        if mesh.uv_layers:continue
        uv=mesh.uv_layers.new(name='Microfinish')
        for p in mesh.polygons:
            n=p.normal;axis=max(range(3),key=lambda i:abs(n[i]))
            for i in p.loop_indices:
                v=o.matrix_world@mesh.vertices[mesh.loops[i].vertex_index].co
                s,t=(v.y,v.z) if axis==0 else (v.x,v.z) if axis==1 else (v.y,v.x)
                uv.data[i].uv=(s/.022,t/.022)

