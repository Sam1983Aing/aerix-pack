"""Compact fork and trunnion for V27's additional rear folding axis.

Called by the V27 builder after its pivot hierarchy has been created.
"""
import bpy,math,bmesh
from mathutils import Vector,Matrix

def add_hinges(scene):
    def material(name,color,metal,rough):
        m=bpy.data.materials.new(name);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
        return m
    dark=material('V27 hinge satin graphite',(.009,.011,.013),.16,.36)
    metal=material('V27 hinge machined pin',(.21,.23,.25),.8,.3)
    created=[]
    def finish(obj,parent,mat):
        obj.parent=parent;obj.data.materials.append(mat)
        for face in obj.data.polygons:face.use_smooth=True
        bevel=obj.modifiers.new('Soft machined edge','BEVEL');bevel.width=.00035;bevel.segments=3
        obj.modifiers.new('Surface normals','WEIGHTED_NORMAL')
        created.append(obj);return obj
    for tag in ['RL','RR']:
        sign=-1 if tag.endswith('L') else 1
        d=Vector((sign*.095,.054,0)).normalized();t=Vector((-d.y,d.x,0));up=Vector((0,0,1))
        arm=bpy.data.objects['ARM_'+tag+'_ROOT'];pitch=bpy.data.objects['ARM_'+tag+'_FOLD_PITCH'];axis=pitch.location.copy()
        def link(name,start,end,radius,width,across,parent):
            delta=Vector((end[0]-start[0],end[1]-start[1]));a=math.atan2(delta.y,delta.x)
            outline=[]
            for center,start_angle in [(end,a-math.pi/2),(start,a+math.pi/2)]:
                for j in range(25):
                    angle=start_angle+j*math.pi/24
                    outline.append((center[0]+radius*math.cos(angle),center[1]+radius*math.sin(angle)))
            vs=[tuple(d*r+up*z+t*c) for c in [across-width/2,across+width/2] for r,z in outline];n=len(outline)
            fs=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
            mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update()
            bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
            obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
            return finish(obj,parent,dark)
        # Fixed fork cheeks descend from the rotating collar to the low pin.
        for k,c in enumerate([-.0105,.0105]):
            link(f'HINGE_DROP_FORK_{tag}_{k}',(.006,-.001),(.015,-.020),.0043,.0028,c,arm)
        # Central ear follows the new pitch joint and remains connected to the beam.
        link('HINGE_DROP_EAR_'+tag,(0,0),(.002,.024),.0048,.014,0,pitch)
        for name,radius,length,c,mat in [
            ('AXLE',.0027,.031,0,metal),('END_LEFT',.0041,.0013,-.0157,metal),('END_RIGHT',.0041,.0013,.0157,metal),
            ('SOCKET_LEFT',.0015,.0014,-.0161,dark),('SOCKET_RIGHT',.0015,.0014,.0161,dark)]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=6 if 'SOCKET' in name else 64,radius=radius,depth=length)
            obj=bpy.context.object;obj.name=f'HINGE_DROP_{name}_{tag}'
            obj.location=axis+t*c;obj.rotation_euler=t.to_track_quat('Z','Y').to_euler()
            finish(obj,arm,mat)
    return created

def export_details(objects):
    deps=bpy.context.evaluated_depsgraph_get();details=[]
    for obj in objects:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        local=obj.parent.matrix_world.inverted()@ev.matrix_world
        normal_matrix=local.to_3x3().inverted().transposed()
        pos=[];norm=[]
        for tri in mesh.loop_triangles:
            for loop in tri.loops:
                p=local@mesh.vertices[mesh.loops[loop].vertex_index].co
                n=(normal_matrix@mesh.corner_normals[loop].vector).normalized()
                pos.extend([p.x,p.z,-p.y]);norm.extend([n.x,n.z,-n.y])
        mat=obj.data.materials[0];shader=mat.node_tree.nodes.get('Principled BSDF')
        details.append({'name':obj.name,'parent':obj.parent.name,'positions':pos,'normals':norm,
            'material':{'name':mat.name,'pbrMetallicRoughness':{'baseColorFactor':list(shader.inputs['Base Color'].default_value),
                'metallicFactor':shader.inputs['Metallic'].default_value,'roughnessFactor':shader.inputs['Roughness'].default_value}}})
        ev.to_mesh_clear()
    return details
