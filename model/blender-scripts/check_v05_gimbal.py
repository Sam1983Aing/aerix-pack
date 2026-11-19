"""Verify the designed suspension path, optical seats and every non-mating clearance."""
from pathlib import Path
import sys,json,math
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_v04_assembly import audit,local_meshes,world_solids

def check_contacts(rows):
    def pair(a,b):return tuple(sorted((a,b)))
    required={pair(a,b) for a,b in [
        ('Gimbal.yaw_boss','Shell.lower_chassis'),('Gimbal.yaw_boss','Gimbal.yaw_hanger'),
        ('Gimbal.yaw_hanger','Gimbal.roll_spindle'),('Gimbal.roll_spindle','Gimbal.rear_carrier'),
        ('Camera.block','Camera.lens_barrel'),('Camera.lens_barrel','Camera.front_glass'),
        ('Camera.lens_barrel','Camera.inner_glass'),('Camera.lens_barrel','Camera.iris'),
        ('Camera.lens_barrel','Camera.receiver')]}
    for side in ('L','R'):
        for a,b in [('Gimbal.rear_carrier','Gimbal.yoke.'+side),
                    ('Gimbal.yoke.'+side,'Gimbal.trunnion.'+side),
                    ('Gimbal.trunnion.'+side,'Camera.block')]:
            required.add(pair(a,b))
    allowed=required|{pair('Gimbal.yaw_boss',n) for n in ('Shell.waist_gasket','Shell.nose_hood')}
    allowed.add(pair('Camera.block','Camera.receiver'))
    for row in rows:
        contacts=set(map(tuple,row['contacts']))
        focus={p for p in contacts if any(n.startswith(('Gimbal.','Camera.')) for n in p)}
        assert not required-focus,('Missing designed seats',row['frame'],required-focus)
        assert not focus-allowed,('Unexpected contact',row['frame'],focus-allowed)
        assert len(row['groups'])==1,('Detached meshes',row['frame'],row['groups'][1:])
    base=json.loads((ROOT/'measurements/v04-audit.json').read_text())
    for row,key in [(rows[0],'open_mm'),(rows[-1],'folded_mm')]:
        assert max(abs(a-b) for a,b in zip(row['size_mm'],base[key]))<.0011,(key,row['size_mm'])
    return {'frames_checked':len(rows),'mesh_count':len(rows[0]['groups'][0]),'required_contacts_per_frame':len(required),
            'unexpected_gimbal_contacts':0,'disconnected_frames':0,'open_mm':rows[0]['size_mm'],'folded_mm':rows[-1]['size_mm']}

def folding_clearance(scene):
    # An enclosing box can only underestimate separation. Take the minimum
    # over every optical/suspension part and every moving arm or blade assembly.
    meshes=local_meshes(scene)
    camera=[n for n in meshes if n.startswith(('Gimbal.','Camera.'))]
    moving=[n for n in meshes if n.startswith(('Arm.','Hinge.pin.','Motor.','Propeller.','Leg.front.'))]
    cache={}
    closest=(float('inf'),)
    for frame in range(1,122):
        scene.frame_set(frame)
        solids=world_solids({n:meshes[n] for n in camera+moving},cache)
        for a in camera:
            for b in moving:
                x,y=solids[a],solids[b]
                gap=math.sqrt(sum(max(0,x.lo[i]-y.hi[i],y.lo[i]-x.hi[i])**2 for i in range(3)))
                closest=min(closest,(gap,frame,a,b))
    scene.frame_set(1)
    return {'minimum_box_gap_mm':round(closest[0]*1000,4),'frame':closest[1],'parts':closest[2:]}


if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports/drone-v05.glb'))
    result=check_contacts(audit(bpy.context.scene,range(1,122)))
    result['fold_clearance']=folding_clearance(bpy.context.scene)
    (ROOT/'measurements/v05-export-assembly.json').write_text(json.dumps(result,indent=2)+'\n')
