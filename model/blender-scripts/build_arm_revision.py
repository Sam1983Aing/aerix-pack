"""Apply a sleeve profile to the prior version and verify the fold before publication."""
from pathlib import Path
import json
import sys
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import audit
from check_v05_gimbal import check_contacts
from check_v06_clearance import protected_skin


def build(prior,version,shape,preview_view):
    scene=bpy.context.scene
    group=bpy.data.collections[prior.upper()+' | Aircraft']
    assert Path(bpy.data.filepath).resolve()==ROOT/f'blender/drone-{prior}.blend'
    codes=('FL','FR','RL','RR')
    frames=range(1,122)
    scene.frame_set(1)
    def matrix_samples():
        out=[]
        for frame in frames:
            scene.frame_set(frame)
            out.append([tuple(v for row in bpy.data.objects['Hinge.axis.'+c].matrix_world for v in row) for c in codes])
        scene.frame_set(1)
        return out


    pivots=matrix_samples()
    before=audit(group,frames)
    original={o.name:[v.co.copy() for v in o.data.vertices] for o in group.objects if o.name.startswith('Arm.')}
    sections={c:shape(bpy.data.objects['Arm.'+c],c) for c in codes}
    assert matrix_samples()==pivots
    after=audit(group,frames)
    for a,b in zip(before,after):
        assert a['contacts']==b['contacts'],(a['frame'],set(a['contacts'])^set(b['contacts']))
    report=check_contacts(after)
    report['reshaped_skin_clearance_floor_mm']=protected_skin(group,original)
    report.update(arm_contact_sets_unchanged=True,pivot_matrix_max_error=0,sections=sections)
    print('Geometry check', {k:v for k,v in report.items() if k!='sections'},flush=True)
    if '--preview' in sys.argv:
        scene.camera=bpy.data.objects['Studio.camera.'+preview_view]
        scene.render.filepath=str(ROOT/f'measurements/{version}-arm-preview.png')
        bpy.ops.render.render(write_still=True)
        sys.exit(0)
    blend=ROOT/f'blender/drone-{version}.blend'
    glb=ROOT/f'exports/drone-{version}.glb'
    assert not blend.exists() and not glb.exists()
    bpy.data.objects['Drone.'+prior.upper()].name='Drone.'+version.upper()
    group.name=version.upper()+' | Aircraft'
    bpy.ops.object.select_all(action='DESELECT')
    for obj in group.objects:obj.select_set(True)
    pending=ROOT/f'exports/pending-{version}.glb'
    bpy.ops.export_scene.gltf(filepath=str(pending),use_selection=True,export_apply=True,
        export_animation_mode='NLA_TRACKS',export_animations=True,export_frame_range=True,export_force_sampling=True)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    pending.rename(glb)
    (ROOT/f'measurements/{version}-audit.json').write_text(json.dumps(report,indent=2)+'\n')
