"""Compare both delivered GLBs in Blender at native time, including the sleeve widths."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import audit
from check_v05_gimbal import check_contacts


def section_widths(code,stations):
    obj=bpy.data.objects['Arm.'+code]
    start=bpy.data.objects['Hinge.axis.'+code].matrix_world.translation
    motor=bpy.data.objects['Motor.'+code].matrix_world.translation
    axis=motor-start
    axis.z=0
    length=axis.length
    axis.normalize()
    transverse=Vector((-axis.y,axis.x,0))
    mesh=obj.data
    mesh.calc_loop_triangles()
    verts=[obj.matrix_world@v.co-start for v in mesh.vertices]
    widths=[]
    for t in stations:
        station=t*length
        cross=[]
        for tri in mesh.loop_triangles:
            points=[verts[i] for i in tri.vertices]
            for a,b in zip(points,points[1:]+points[:1]):
                u,v=a.dot(axis),b.dot(axis)
                if min(u,v)<station<=max(u,v):
                    cross.append(a.lerp(b,(station-u)/(v-u)).dot(transverse))
        widths.append(round((max(cross)-min(cross))*1000,3))
    return widths


runs=[]
widths={}
target=sys.argv[-1] if '--' in sys.argv else 'v06'
prior={'v06':'v05','v07':'v06'}[target]
stations=(.19,.25,.50,.73,.75,.88,.95) if target=='v07' else (.25,.50,.75)
for version in (prior,target):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(ROOT/f'exports/drone-{version}.glb'))
    scene.frame_set(1)
    widths[version]={code:section_widths(code,stations) for code in ('FL','FR','RL','RR')}
    runs.append(audit(scene,range(1,122)))
for old,new in zip(*runs):
    assert old['contacts']==new['contacts'],(new['frame'],set(old['contacts'])^set(new['contacts']))
result=check_contacts(runs[-1])
result[f'matches_{prior}_contact_pairs_every_frame']=True
result['section_widths_mm']=widths
result['fractions_from_hinge']=stations
if target=='v07':
    for code,values in widths[target].items():
        assert abs(values[stations.index(.50)]-9)<.03,(code,values)
        assert values[stations.index(.88)]>values[stations.index(.73)]
    assert widths[target]['RR'][0]>widths[target]['FR'][0]+1
(ROOT/f'measurements/{target}-export-assembly.json').write_text(json.dumps(result,indent=2)+'\n')
