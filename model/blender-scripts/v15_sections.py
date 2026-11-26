"""Save orthographic, physically cut review scenes alongside the assembled master."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from v15_geometry import material
studio=bpy.context.scene
assert Path(bpy.data.filepath).name=='rill15-layout-work.blend'
studio.name='V15 · Assembled'
studio.frame_set(1)
air=bpy.data.collections['V15 | Aircraft']
inside=bpy.data.collections['V15 | Interior blockout']
snapshot=[(o,o.matrix_world.copy()) for o in [*air.objects,*inside.objects] if o.type=='MESH']
tones={'skin':(.43,.47,.43),'shellcut':(.83,.83,.68),'pack':(.31,.142,.058),'packcut':(.44,.21,.082),
       'board':(.027,.16,.10),'tile':(.70,.64,.42),'metal':(.35,.46,.48),'sink':(.10,.17,.20),
       'seat':(.28,.35,.34),'rubber':(.069,.086,.084),'contact':(.62,.36,.14),'flex':(.48,.25,.10),
       'wire':(.11,.125,.13),'glass':(.035,.16,.20),'tim':(.16,.39,.50),'optic':(.28,.25,.36)}
palette={k:material('section '+k,c,.15 if k in ('metal','contact','sink') else 0) for k,c in tones.items()}
def look(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
def light(s,name,position,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj);obj.location=position;look(obj,(0,0,.028))
def cube(s,axis,level):
    m=bpy.data.meshes.new('Section half-space');p=[]
    for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
        q=[.25*x,.25*y,.25*z]
        if q[axis]>0:q[axis]=level
        p.append(q)
    m.from_pydata(p,[],[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    o=bpy.data.objects.new(m.name,m);s.collection.objects.link(o);return o
def review(kind):
    top=kind=='Top';axis,level=(2,.0467) if top else (0,0.)
    s=bpy.data.scenes.new('Review 6 · '+kind+' section');bpy.context.window.scene=s
    s['Cut location in V15 millimetres']='Z = 46.7' if top else 'X = 0.0'
    s['View']='Orthographic service section. Neutral inspection colours. Tail on left, nose on right.'
    s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
    s.render.resolution_x=1580;s.render.resolution_y=800 if top else 620;s.render.resolution_percentage=100
    s.render.film_transparent=True;s.world=bpy.data.worlds.new('Inspection ambient')
    s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.64,.72,.68,1)
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.32
    s.view_settings.view_transform='AgX';s.view_settings.exposure=-1.30;s.view_settings.look='AgX - Medium High Contrast'
    light(s,kind+' · overhead strip',(.09,-.07,.25),3,.2)
    light(s,kind+' · edge strip',(-.12,.13,.14),2.3,.145)
    light(s,kind+' · side fill',(.15,.08,.06),1.3,.14)
    cutter=cube(s,axis,level)
    key='T' if top else 'S'
    for src,mat in snapshot:
        n=src.name
        if n.startswith(('Propeller.','Arm.','Leg.','Hinge.','Motor.','Front.pin','RF.')):continue
        if n=='Shell.RILL':continue
        pts=[(mat@Vector(p))[axis] for p in src.bound_box]
        if min(pts)>level-1.e-7:continue
        mesh=src.data.copy();o=bpy.data.objects.new(key+' | '+n,mesh);s.collection.objects.link(o);o.matrix_world=mat
        cat=src.get('Finish group')
        if cat is None:cat='optic' if n.startswith(('Gimbal.','Camera.')) else 'skin'
        if cat=='pack':cutcolor='packcut'
        elif cat=='skin':cutcolor='shellcut'
        else:cutcolor=cat
        for i in range(len(mesh.materials)):mesh.materials[i]=palette[cat]
        if not mesh.materials:mesh.materials.append(palette[cat])
        if min(pts)<level-1e-7 and max(pts)>level+1e-7:
            cutter.data.materials.clear();cutter.data.materials.append(palette[cutcolor])
            mod=o.modifiers.new('Review plane','BOOLEAN');mod.solver='EXACT';mod.operation='INTERSECT';mod.object=cutter;mod.material_mode='TRANSFER'
            dg=bpy.context.evaluated_depsgraph_get();cut=bpy.data.meshes.new_from_object(o.evaluated_get(dg),depsgraph=dg)
            o.modifiers.clear();o.data=cut;bpy.data.meshes.remove(mesh)
            if not cut.polygons:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(cutter,do_unlink=True)
    data=bpy.data.cameras.new(kind+' section');data.type='ORTHO';data.ortho_scale=.155;data.clip_start=.001
    camera=bpy.data.objects.new(data.name,data);s.collection.objects.link(camera)
    if top:
        camera.location=(0,-.0045,.25);camera.rotation_euler=(0,0,math.pi/2)
    else:
        camera.location=(.24,-.0045,.032);look(camera,(0,-.0045,.032))
    s.camera=camera;s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
    return s
for k in ('Top','Side'):review(k)
bpy.context.window.scene=studio
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
out=root/'blender/drone-v15.blend'
if out.exists() and '--replace-review' not in sys.argv:raise FileExistsError(out)
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)

