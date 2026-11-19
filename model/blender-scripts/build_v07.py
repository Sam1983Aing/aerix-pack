"""Widen Basalt sleeves in plan, with full rear shoulders and a gentle motor flare."""
from pathlib import Path
import sys
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_arm_revision import build


def sleeve_profile(obj,code):
    vertices=obj.data.vertices
    assert len(vertices)==18*64
    end=obj.matrix_world.inverted()@bpy.data.objects['Motor.'+code].matrix_world.translation
    end.z=0
    length=end.length
    along=end.normalized()
    transverse=Vector((-along.y,along.x,0))
    # These stations are the original Basalt loft rings, in hinge-to-motor coordinates.
    # Their widths interpolate to 9.00 mm halfway between the two axes.
    target_widths={.19:11.4 if code.startswith('R') else 9.68,
                   .40:9.34,.73:8.22,.88:9.55,.95:10.15}
    sections=[]
    for k in range(18):
        ring=vertices[k*64:(k+1)*64]
        center=sum((v.co for v in ring),Vector())/64
        t=round(center.dot(along)/length,3)
        offsets=[(v.co-center).dot(transverse) for v in ring]
        width=(max(offsets)-min(offsets))*1000
        target=target_widths.get(t,width)
        if t in target_widths:
            for vertex,offset in zip(ring,offsets):
                vertex.co+=transverse*(offset*(target/width-1))
        sections.append({'fraction':t,'v06_width_mm':round(width,3),'v07_width_mm':round(target,3)})
    assert all(t in {r['fraction'] for r in sections} for t in target_widths)
    obj.data.update()
    return sections


build('v06','v07',sleeve_profile,'top')
