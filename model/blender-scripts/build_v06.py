"""Increase the exposed sleeve width and depth on V05."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_arm_revision import build

def fuller(obj,code):
    # Original V03 loft order: 64 perimeter vertices per longitudinal ring.
    verts=obj.data.vertices
    assert len(verts)==18*64
    centers=[sum((v.co for v in verts[k:k+64]),Vector())/64 for k in range(0,len(verts),64)]
    motor=bpy.data.objects['Motor.'+code]
    end=obj.matrix_world.inverted()@motor.matrix_world.translation
    end.z=0
    length=end.length
    along=end.normalized()
    across=Vector((-along.y,along.x,0))
    sections=[]
    for k,center in enumerate(centers):
        t=center.dot(along)/length
        ring=verts[k*64:(k+1)*64]
        offsets=[v.co-center for v in ring]
        def span(direction):
            coords=[v.co.dot(direction) for v in ring]
            return (max(coords)-min(coords))*1000
        vertical=Vector((0,0,1))
        before=(span(across),span(vertical))
        if .18<t<.96:
            # Taper back into the motor boss; leave the complete bearing/copper cuff untouched.
            blend=min(1.,(.985-t)/.17)
            for vert,offset in zip(ring,offsets):
                vert.co+=across*(offset.dot(across)*.060*blend)
                # Most added depth goes under the shoulder to leave room above for parked blades.
                vert.co.z+=offset.z*(.14 if offset.z>0 else .33)*blend
        sections.append((round(t,3),*[round(v,3) for v in (*before,span(across),span(vertical))]))
    obj.data.update()
    return sections


build('v05','v06',fuller,'three-quarter')
