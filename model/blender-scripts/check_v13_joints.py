"""Check the actual camera cap seats and front joint geometry in the scene and GLB."""
from pathlib import Path
import json
import sys
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes,world_solids
from check_v09_gear import inspect_gear
from v10_alignment import alignment


def check_joints(group):
    scene=bpy.context.scene
    scene.frame_set(1)
    meshes=local_meshes(group)
    cache={}
    solids=world_solids(meshes,cache)
    result={}
    selective=set()
    for label in ('L','R'):
        cap='Gimbal.pitch_cover.'+label
        trunnion='Gimbal.trunnion.'+label
        cheek=solids[cap]
        contacts={n for n,s in solids.items() if n!=cap and cheek.contacts(s)}
        assert contacts=={trunnion},(cap,contacts)
        material=group.objects[cap].data.materials[0]
        assert material==group.objects['Camera.block'].data.materials[0]
        trim=solids['Camera.face_trim']
        gap=(trim.lo[1]-cheek.hi[1])*1000
        assert gap>3, (cap,gap)
        result['bezel_setback_mm_'+label]=round(gap,3)
        moving='Arm.F'+label
        seat='Hinge.socket.F'+label
        pin='Hinge.pin.F'+label
        assert 'Hinge.bracket.F'+label not in meshes
        assert solids[pin].contacts(solids[moving])
        assert solids[seat].contacts(solids[pin])
        assert solids[seat].contacts(solids['Shell.moulded_fuselage'])
        selective.update((seat,pin,moving,'Shell.moulded_fuselage'))
        result['seat_to_arm_axial_gap_mm_'+label]=round(1000*(solids[moving].lo[2]-solids[seat].hi[2]),3)
        assert result['seat_to_arm_axial_gap_mm_'+label]>.65
    checks={k:meshes[k] for k in selective}
    for frame in range(1,122):
        scene.frame_set(frame)
        s=world_solids(checks,cache)
        for label in ('L','R'):
            moving,seat,pin=(s[p+'F'+label] for p in ('Arm.','Hinge.socket.','Hinge.pin.'))
            assert moving.contacts(pin) and seat.contacts(pin),(frame,label,'pivot seat')
            assert not moving.contacts(seat) and not moving.contacts(s['Shell.moulded_fuselage']),(frame,label,'arm rub')
    scene.frame_set(1)
    return result


if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(root/'exports/drone-v13.glb'))
    scene=bpy.context.scene
    result=check_joints(scene)
    result['fold']=inspect_gear(scene)
    result['optical_center_xz_mm']=alignment(scene.objects)
    expected=json.loads((root/'measurements/v13-native-audit.json').read_text())
    for key in result:
        if key!='optical_center_xz_mm': assert result[key]==expected[key],(key,result[key],expected[key])
    assert all(max(map(abs,v))<.001 for v in result['optical_center_xz_mm'].values())
    (root/'measurements/v13-export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Verified both camera caps, both front bearing seats, and the exported fold.')
