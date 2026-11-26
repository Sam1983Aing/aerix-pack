"""Shape the registered lens board, bonded objective body and retaining seats."""
import bpy,math
from mathutils import Vector
from v15_geometry import rounded,circle,evaluated_tree

def build_camera(p,air,inside,head,replace,turn,bevel,mate,join,recolor):
    zc=19.4
    body=air.objects['Drone.V17']
    # Enlarge only V15's inward-facing receiver-pocket vertices. This retains
    # the original exterior mesh, UVs, bore floor and all finished optical faces.
    mesh=head.data
    inner_slot=mesh.materials.find('RILL | carrier polymer')
    ids={i for f in mesh.polygons if f.material_index==inner_slot for i in f.vertices}
    assert ids and not any(set(f.vertices)&ids for f in mesh.polygons if f.material_index!=inner_slot)
    points={i:head.matrix_world@mesh.vertices[i].co*1000 for i in ids}
    lo=[min(v[k] for v in points.values()) for k in range(3)]
    hi=[max(v[k] for v in points.values()) for k in range(3)]
    bounds=[(-11.70,11.70),(46.00,53.985),(10.78,28.02)]
    inverse=head.matrix_world.inverted()
    for i,v in points.items():
        xyz=[a+(b-a)*(v[k]-lo[k])/(hi[k]-lo[k]) for k,(a,b) in enumerate(bounds)]
        mesh.vertices[i].co=inverse@(Vector(xyz)*.001)
    mesh.update();bpy.context.view_layer.update()
    def faceplate(name,outline,y,h,finish,holes=(),owner=head,edge=.03):
        # Profile is drafted in transverse coordinates; rotate it into XZ.
        o=p.plate(name,outline,y,h,finish,holes,body)
        for v in o.data.vertices:
            x,t,k=v.co;v.co=(x,k,.0194-t)
        o.data.update();o.parent=owner;o.matrix_parent_inverse=owner.matrix_world.inverted()
        if edge:bevel(o,edge)
        return o
    # The two gold eyelets and the stepped lower-right corner resolve the handedness.
    perimeter=[(10.62,-7.42),(10.39,-7.73),(8.8,-7.81),(-9.68,-7.72),(-10.34,-7.40),
      (-10.53,-6.79),(-10.53,5.76),(-10.20,5.97),(-8.77,5.97),(-8.53,6.15),(-8.50,7.38),
      (-8.15,7.63),(5.52,7.63),(5.60,7.45),(10.32,7.45),(10.62,7.20)]
    holes=[(9.07,-6.05),(-9.03,-6.12)]
    pcb=replace('Camera.imager_carrier',faceplate('new imager PCB',perimeter,47.64,.67,'mask',
                [circle(x,t,.49,48) for x,t in holes],edge=.035))
    recolor(pcb,['edge'])
    for f in pcb.data.polygons:
        if abs(f.normal.y)<.50:f.material_index=1
    # Dark polymer board seats abut the rear wall of the reprofiled pocket.
    # Use the actual surface plane in the saved geometry for both supports.
    wall=evaluated_tree(head)
    for j,(x,t) in enumerate(holes):
        z=zc-t
        hit=wall.ray_cast(Vector((x,47.52,z))*.001,(0,-1,0))[0];assert hit is not None
        start=hit.y*1000+(.032 if j==1 else 0.)
        mount=turn('Camera.board_seat.'+str(j+1),x,z,[(start,.86),(start+.12,.88),(47.52,.79),
                   (47.64,.77),(47.64,.53),(start,.53)],'poly',head,axis='Y',closed=True)
        mate(mount,pcb,*([head] if j==0 else []))
        rim=turn('Camera.board_eyelet.'+str(j+1),x,z,[(48.31,.74),(48.355,.79),(48.39,.73),
                 (48.39,.49),(48.335,.465),(47.69,.465),(47.69,.478),(48.31,.478)],'copper',pcb,axis='Y',n=64,closed=True)
        mate(rim,pcb)
    rx=air.objects['Camera.receiver']
    end=min((rx.matrix_world@v.co).y for v in rx.data.vertices)*1000
    n=112
    def curved_row(y,half_x,half_z,power):
        row=[]
        for i in range(n):
            a=i*math.tau/n;cs=math.cos(a);sn=math.sin(a)
            r=(abs(cs/half_x)**power+abs(sn/half_z)**power)**(-1/power)
            row.append((r*cs,y,zc+r*sn))
        return row
    # Single closed module. The front lands on the existing optical receiver;
    # the approved lens crowns, iris and barrel remain on their original axis.
    profile=[(48.31,8.40,6.49,4.9),(48.43,8.57,6.62,4.7),(48.72,8.60,6.68,4.7),
             (48.97,8.42,6.56,4.3),(49.21,8.18,6.44,3.8),(49.53,7.62,6.33,3.3),
             (49.83,7.10,6.29,2.6),(50.04,6.64,6.27,2.11),(50.18,6.51,6.26,2),
             (50.54,6.48,6.24,2),(50.63,6.36,6.14,2),(50.68,6.11,5.92,2),
             (51.03,6.11,5.92,2),(51.13,6.23,6.02,2),(51.28,6.24,6.02,2),
             (51.37,6.11,5.91,2),(51.49,5.84,5.71,2),(52.13,5.76,5.64,2),
             (52.26,5.64,5.57,2),(52.33,5.39,5.38,2),(52.69,5.35,5.35,2),
             (52.78,5.17,5.17,2),(53.50,4.81,4.81,2),(end,4.69,4.69,2)]
    pkg=replace('Camera.imager',p.loft('new bonded objective',[curved_row(*q) for q in profile],'poly',pcb))
    recolor(pkg,['bond','barrel'])
    for f in pkg.data.polygons:
        j=f.index//n
        if len(f.vertices)==4:
            f.use_smooth=True;f.material_index=1 if j in (1,2,3,4) else 2 if j>=8 else 0
    mate(pkg,pcb,rx)
    # The bead around the original square module is irregular in the service photo.
    # Draw its footprint on the carrier as a thin, closed adhesive flange.
    outline=[];hole=[]
    for i in range(n):
        a=math.tau*i/n;c,s=math.cos(a),math.sin(a)
        r=(abs(c/8.63)**5+abs(s/6.77)**5)**(-.2)
        outer=r+.20+.20*(.5+.5*math.sin(5*a+.4))+.095*math.cos(11*a)+.16*max(0,math.cos(4*a-2.4))**5
        nearest=min(math.hypot(outer*c-x,-outer*s-t) for x,t in holes)
        keep=max(0,min(1,(nearest-.88)/.80))
        outer=r+.08+(outer-r-.08)*keep*keep*(3-2*keep)
        outline.append((outer*c,-outer*s));hole.append((r*c,-r*s))
    bond=faceplate('Camera.objective_bond',outline,48.31,.12,'bond',[hole],pcb,edge=.015)
    mate(bond,pcb)
    # Distinct resolved passives. The right-hand edge shows a stacked bank;
    # the left edge has a large ceramic package and small tinned components.
    features=[(9.43,-3.68,1.06,.54),(-9.45,-3.77,.64,1.00),(-9.50,-2.30,.68,.89),
              (-9.36,.16,.51,.46),(-9.27,2.32,.49,.57),(-9.24,4.32,.66,.92),
              (9.44,3.64,.47,.68),(9.62,4.62,.36,.52)]
    bodies=[];ends=[]
    for x,t,w,h in features:
        def rect(cx,cy,ux,uy):
            return [(cx+a,cy+b) for a,b in rounded(ux,uy,min(ux,uy)*.15,4)]
        along_x=w>h
        if along_x:
            bodies.append(faceplate('Ceramic dielectric',rect(x,t,w*.58,h),48.31,.22,'ceramic',owner=pcb,edge=.026))
            for s in (-1,1):
                ends.append(faceplate('Tinned land',rect(x+s*w*.395,t,w*.21,h),48.31,.22,'tin',owner=pcb,edge=.016))
        else:
            bodies.append(faceplate('Ceramic dielectric',rect(x,t,w,h*.58),48.31,.22,'ceramic',owner=pcb,edge=.026))
            for s in (-1,1):
                ends.append(faceplate('Tinned land',rect(x,t+s*h*.395,w,h*.21),48.31,.22,'tin',owner=pcb,edge=.016))
    components=join(bodies+ends,'Camera.board_passives');mate(components,pcb)

