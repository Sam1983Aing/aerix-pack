"""Verify the board datums, battery pins, earlier reviewed parts and V17 fold tracks."""
from pathlib import Path
import json,sys
import bpy
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from check_v17_registration import mesh_digest
from v18_reference import gps_datum

def points(o):
    return np.asarray([o.matrix_world@v.co for v in o.data.vertices],dtype=float)*1000

def compare_data(version):
    s=bpy.data.scenes[version+' · Assembled'];bpy.context.window.scene=s;s.frame_set(1)
    air=bpy.data.collections[version+' | Aircraft']
    inside=bpy.data.collections[version+' | Interior']
    pins=[f'Power.contact.{i:02d}' for i in range(1,7)]
    pts={n:points(s.objects[n]) for n in pins+['Board.navigation','Board.motor_control']}
    nav=pts['Board.navigation'];holes=[]
    for x,y in gps_datum:
        ring=nav[np.abs(np.hypot(nav[:,0]-x,nav[:,1]-y)-.95)<.0001]
        assert len(ring)>=48,(version,x,y)
        holes.append(((ring.min(axis=0)+ring.max(axis=0))/2)[:2])
    mounts={n:[round(float(pts[n][:,2].min()),6),round(float(pts[n][:,2].max()),6)]
            for n in ('Board.navigation','Board.motor_control')}
    retain={o.name:mesh_digest(o) for o in [*air.objects,*inside.objects] if o.type=='MESH'
            and o.name not in ('Board.navigation','Board.motor_control') and not o.name.startswith(('Navigation.','ESC.','Power.'))}
    reviewed={o.name for o in inside.objects if o.get('Review 7 part') or o.get('V17 service group')}
    tracked=sorted({o.name for o in air.objects if o.type=='MESH'} | reviewed |
                   {'Board.navigation','Board.motor_control','Gimbal.yaw','Gimbal.roll','Gimbal.pitch'})
    poses=[]
    for i in range(1,122):
        s.frame_set(i)
        poses.append(np.asarray([s.objects[n].matrix_world for n in tracked]))
    return pts,holes,mounts,retain,reviewed,tracked,poses

assert Path(bpy.data.filepath).name=='drone-v18.blend'
new=compare_data('V18')
bpy.ops.wm.open_mainfile(filepath=str(root/'blender/drone-v17.blend'))
old=compare_data('V17')
for n in old[0]:
    if n.startswith('Power.'):assert np.array_equal(old[0][n],new[0][n]),n
assert old[2:6]==new[2:6]
assert np.allclose(old[1],new[1],rtol=0,atol=1e-5)
assert all(np.array_equal(x,y) for x,y in zip(old[6],new[6]))
fold=json.loads((root/'measurements/v18-fold.json').read_text())
contacts={tuple(sorted(i['parts'])) for i in fold['designed_stationary_bearings']}
support=[sorted((board,'Frame.bearing_'+bearing+'.'+side))
         for board,bearing in [('Board.motor_control','drive'),('Board.navigation','nav')] for side in ('L','R')]
assert all(tuple(pair) in contacts for pair in support)
for i in range(1,7):
    pin=f'ESC.contact_tail.{i:02d}'
    assert tuple(sorted((pin,f'Power.contact.{i:02d}'))) in contacts
    assert tuple(sorted((pin,'Power.contact_carrier'))) in contacts
report={'baseline':'V17','substrate_bottom_and_top_mm':new[2],'preserved_tips':6,
        'gps_bore_centres_mm':np.round(new[1],5).tolist(),'four_board_supports_seated':support,
        'unchanged_meshes_outside_board_work':len(new[3]),'previously_reviewed_internal_meshes':len(new[4]),
        'matching_transform_tracks':len(new[5]),'identical_frames':len(new[6])}
(root/'measurements/v18-registration.json').write_text(json.dumps(report,indent=2)+'\n')
print('V18 REGISTRATION',report)

