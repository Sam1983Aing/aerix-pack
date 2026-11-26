"""Millimetre-space geometry for measured envelopes, channels and mounting seats."""
import bpy,bmesh
from math import pi,cos,sin
from mathutils import Vector,geometry
from mathutils.bvhtree import BVHTree

def rounded(w,h,r,n=6):
    r=min(r,w/2,h/2)
    return [(sx*(w/2-r)+r*cos((i+j/n)*pi/2),sy*(h/2-r)+r*sin((i+j/n)*pi/2))
            for i,(sx,sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))) for j in range(n+1)]
def circle(x,y,r,n=24):
    return [(x+r*cos(i*2*pi/n),y+r*sin(i*2*pi/n)) for i in range(n)]
def inside2(point,poly):
    x,y=point;hit=False
    for (a,b),(c,e) in zip(poly,poly[1:]+poly[:1]):
        if (b>y)!=(e>y) and x<(c-a)*(y-b)/(e-b)+a:hit=not hit
    return hit
def material(name,color,metal=0):
    m=bpy.data.materials.new('RILL | '+name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=m.diffuse_color
    b.inputs['Roughness'].default_value=.48;b.inputs['Metallic'].default_value=metal
    return m
class Parts:
    def __init__(self,coll,parent):
        self.coll=coll;self.parent=parent;self.mats={
            'pack':material('battery graphite',(.17,.19,.19)),
            'board':material('board solder mask',(.045,.17,.125)),
            'tile':material('navigation ceramic',(.70,.63,.43)),
            'metal':material('shield alloy',(.41,.47,.48),.65),
            'sink':material('cooling graphite',(.10,.14,.155),.6),
            'seat':material('carrier polymer',(.27,.29,.277)),
            'rubber':material('isolation rubber',(.042,.044,.048)),
            'contact':material('contact finish',(.55,.32,.103),.75),
            'flex':material('camera flex',(.35,.153,.062)),
            'wire':material('loom sleeve',(.13,.145,.15)),
            'glass':material('sensor window',(.025,.078,.087),.28),
            'tim':material('thermal interface',(.165,.385,.49)) }
    def mesh(self,name,pts,fs,finish,parent=None,note='Photo-registered blockout, depth provisional'):
        parent=parent or self.parent;m=bpy.data.meshes.new(name)
        inv=parent.matrix_world.inverted()
        m.from_pydata([inv@(Vector(p)*.001) for p in pts],[],fs);m.update()
        b=bmesh.new();b.from_mesh(m);bmesh.ops.recalc_face_normals(b,faces=b.faces);b.to_mesh(m);b.free()
        m.materials.append(self.mats[finish]);o=bpy.data.objects.new(name,m);self.coll.objects.link(o)
        o.parent=parent;o['Review 6']=note;o['Finish group']=finish;return o
    def loft(self,name,rings,finish,parent=None,note=None):
        n=len(rings[0]);rows=len(rings);faces=[]
        for j in range(rows-1):
            for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
        faces.extend((tuple(range(n)),tuple(range((rows-1)*n,rows*n))))
        return self.mesh(name,sum(rings,[]),faces,finish,parent,**({'note':note} if note else {}))
    def plate(self,name,outline,z,h,finish,holes=(),parent=None):
        rings=[outline,*holes];xy=sum((list(r) for r in rings),[]);edges=[];j=0
        for ring in rings:
            edges.extend((j+i,j+(i+1)%len(ring)) for i in range(len(ring)));j+=len(ring)
        pts,_,tris,ids,_,_=geometry.delaunay_2d_cdt([Vector(k) for k in xy],edges,[],0,1e-5)
        assert all(len(v)==1 for v in ids),name
        keep=[]
        for tri in tris:
            c=sum((pts[v] for v in tri),Vector((0,0)))/3
            if inside2(c,outline) and not any(inside2(c,hole) for hole in holes):
                keep.append(tuple(ids[v][0] for v in tri))
        n=len(xy)
        fs=keep+[tuple(i+n for i in t) for t in keep]+[(a,b,b+n,a+n) for a,b in edges]
        return self.mesh(name,[(x,y,k) for k in (z,z+h) for x,y in xy],fs,finish,parent)
    def box(self,name,center,dims,finish,r=.5,parent=None):
        x,y,z=center;w,l,h=dims
        return self.plate(name,[(x+a,y+b) for a,b in rounded(w,l,r)],z-h/2,h,finish,parent=parent)
    def tube(self,name,path,r,finish,parent=None):
        rings=[];pts=[Vector(p) for p in path]
        for i,p in enumerate(pts):
            axis=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
            helper=Vector((0,0,1)) if abs(axis.z)<.88 else Vector((1,0,0))
            x=axis.cross(helper).normalized();y=axis.cross(x).normalized()
            rings.append([tuple(p+r*(x*cos(k*pi/6)+y*sin(k*pi/6))) for k in range(12)])
        return self.loft(name,rings,finish,parent)

def evaluated_tree(obj):
    m=obj.data;m.calc_loop_triangles()
    return BVHTree.FromPolygons([obj.matrix_world@v.co for v in m.vertices],[t.vertices[:] for t in m.loop_triangles],all_triangles=True)

def subtract(host,tool):
    """Append an inward-wound void to the exact approved outer triangles."""
    import numpy as np
    original=host.data;original.calc_loop_triangles()
    assert not evaluated_tree(host).overlap(evaluated_tree(tool)),(host.name,'pocket crosses host')
    verts=[v.co.copy() for v in original.vertices];n=len(verts)
    transform=host.matrix_world.inverted()@tool.matrix_world
    verts.extend(transform@v.co for v in tool.data.vertices)
    tris=list(original.loop_triangles);faces=[t.vertices[:] for t in tris]
    tool.data.calc_loop_triangles()
    faces.extend(tuple(n+j for j in reversed(t.vertices[:])) for t in tool.data.loop_triangles)
    m=bpy.data.meshes.new(host.name+' · captive passage');m.from_pydata(verts,[],faces)
    for s in original.materials:m.materials.append(s)
    mat=tool.data.materials[0]
    if mat.name not in m.materials:m.materials.append(mat)
    slot=m.materials.find(mat.name);back=len(faces)-len(tris)
    m.polygons.foreach_set('material_index',np.r_[[t.material_index for t in tris],np.full(back,slot)].astype('i'))
    m.polygons.foreach_set('use_smooth',np.r_[[original.polygons[t.polygon_index].use_smooth for t in tris],np.ones(back)].astype(bool))
    ids=np.array([t.loops[:] for t in tris]).flatten()
    for layer in original.uv_layers:
        old=np.asarray([v.uv[:] for v in layer.data],dtype='f')
        target=m.uv_layers.new(name=layer.name)
        target.data.foreach_set('uv',np.vstack((old[ids],np.zeros((3*back,2),dtype='f'))).ravel())
    old=np.asarray([v.vector[:] for v in original.corner_normals],dtype='f')
    m.normals_split_custom_set(np.vstack((old[ids],np.zeros((3*back,3),dtype='f'))).tolist())
    m.update();host.data=m;bpy.data.objects.remove(tool,do_unlink=True)

