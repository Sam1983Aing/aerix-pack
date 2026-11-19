"""Measure the optical axis against the bezel in the unfolded nose-on projection."""
from mathutils import Vector

STACK=('Camera.lens_barrel','Camera.front_glass','Camera.inner_glass','Camera.iris','Camera.receiver')


def midpoint(obj, vertices=None):
    coords=[obj.matrix_world@v.co for v in (obj.data.vertices if vertices is None else vertices)]
    return Vector(tuple((min(p[i] for p in coords)+max(p[i] for p in coords))/2 for i in range(3)))


def alignment(objects):
    bezel=midpoint(objects['Camera.face_trim'])
    result={}
    for name in (*STACK,'Camera.block'):
        coords=midpoint(objects[name])
        result[name]=[round(1000*(coords[i]-bezel[i]),5) for i in (0,2)]
    return result
