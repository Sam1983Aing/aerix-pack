"""Test the four soles, their real mesh attachments and the complete V08 fold."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes, world_solids, audit


def inspect_gear(group):
    scene=bpy.context.scene
    scene.frame_set(1)
    meshes=local_meshes(group)
    solids=world_solids(meshes,{})
    soles={}
    permitted={}
    seating={}
    for side in ('L','R'):
        front='Leg.front.'+side
        rear='Leg.rear.'+side
        permitted[front]={'Motor.F'+side,'Leg.window.'+side,'Arm.F'+side}
        permitted[rear]={'Shell.moulded_fuselage'}
        window=solids['Leg.window.'+side]
        seats=[]
        for p in window.vertices:
            if p.z-window.lo[2]>.0000001: continue
            hit=solids[front].tree.ray_cast(p+Vector((0,0,.0005)),Vector((0,0,-1)),.001)
            assert hit[0] is not None and hit[0].z>=p.z+.00004,('unseated window edge',side,p)
            seats.append((hit[0].z-p.z)*1000)
        seating[side]=round(min(seats),3)
        for name in (front,rear):
            solid=solids[name]
            area=0
            for face in solid.faces:
                a,b,c=[solid.vertices[i] for i in face]
                if max(abs(p.z) for p in (a,b,c))<1.e-7:
                    area+=(b-a).cross(c-a).length*.5e6
            assert abs(solid.lo[2])<1e-7 and area>1.,(name,solid.lo[2],area)
            soles[name]={'z_mm':round(solid.lo[2]*1000,5),'planar_area_mm2':round(area,3)}
    others=[s.lo[2]*1000 for n,s in solids.items() if n not in soles]
    assert min(others)>0
    open_no_blades=[s for n,s in solids.items() if not n.startswith('Propeller.blade.')]
    airframe=[round(1000*(max(s.hi[i] for s in open_no_blades)-min(s.lo[i] for s in open_no_blades)),3)
              for i in (1,0,2)]
    rows=audit(group,range(1,122))
    reference=json.loads((root/'measurements/v08-native-audit.json').read_text())
    for a,b in ((airframe,reference['open_without_propellers_mm']),
                (rows[0]['size_mm'],reference['open_mm']),(rows[-1]['size_mm'],reference['folded_mm'])):
        assert max(abs(v-w) for v,w in zip(a,b))<.03,(a,b)
    initial=set(rows[0]['contacts'])
    for row in rows:
        assert len(row['groups'])==1,(row['frame'],row['groups'][1:])
        new=set(row['contacts'])-initial
        assert not new,(row['frame'],new)
        for n,allowed in permitted.items():
            contacts={b if a==n else a for a,b in row['contacts'] if n in (a,b)}
            required=allowed-{'Arm.F'+n[-1]}
            assert required<=contacts<=allowed,(row['frame'],n,contacts)
    return {'frames':len(rows),'meshes':len(solids),'new_contacts':0,'disconnected_frames':0,
        'sole_contacts':soles,'window_rim_seating_mm':seating,'lowest_other_geometry_open_mm':round(min(others),3),
        'open_mm':rows[0]['size_mm'],'open_without_blades_mm':airframe,'folded_mm':rows[-1]['size_mm']}


if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(root/'exports/drone-v09.glb'))
    result=inspect_gear(bpy.context.scene)
    print(json.dumps(result,indent=2))
    expected=json.loads((root/'measurements/v09-native-audit.json').read_text())
    assert result==expected,(result,expected)
    (root/'measurements/v09-export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
