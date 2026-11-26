"""Check exterior triangle fidelity, fold transforms, interior fit and paired contacts."""
from pathlib import Path
from itertools import combinations
from types import SimpleNamespace
import sys,json,math
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
revision=Path(bpy.data.filepath).stem.removeprefix('drone-')
assert revision in ('v15','v16','v17','v18')
interior_collection='V15 | Interior blockout' if revision=='v15' else revision.upper()+' | Interior'
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from check_v04_assembly import local_meshes,world_solids
shells={'Shell.roof_cover','Shell.battery_door','Shell.belly_cover','Shell.middle_frame'}
def rows(objects,interior,frames):
    meshes=local_meshes(SimpleNamespace(objects=objects));cache={};tested={}
    pairs=list(combinations(sorted(meshes),2));allrows=[];intrusive=set();surfaces=set()
    for f in frames:
        bpy.context.scene.frame_set(f);solids=world_solids(meshes,cache);exterior=set();added=set()
        for pair in pairs:
            a,b=[solids[k] for k in pair]
            if a.gap_box(b)>1e-8:continue
            mem=tested.get(pair)
            if mem is None or mem[0] is not a or mem[1] is not b:
                contact=a.contacts(b)
                tested[pair]=(a,b,contact)
            else:contact=mem[2]
            if not contact:continue
            if set(pair)&interior:added.add(pair);intrusive.add(pair)
            else:
                canonical=tuple(sorted('Shell.moulded_fuselage' if k in shells else k for k in pair))
                if canonical[0]!=canonical[1]:exterior.add(canonical)
        allrows.append((exterior,added))
    return allrows,intrusive
def collection(name):return list(bpy.data.collections[name].objects)
scene=bpy.context.scene;scene.frame_set(1)
air=collection(revision.upper()+' | Aircraft');inside=collection(interior_collection)
ints={o.name for o in inside}
quick='--quick' in sys.argv
frames=[1] if quick else list(range(1,122))
checks,new=rows(air+inside,ints,frames)
scene.frame_set(1)
seats={}
for rib in inside:
    if 'Mating parts' not in rib:continue
    for name in rib['Mating parts'].split(';'):
        pair=tuple(sorted((rib.name,name)))
        # Confirm material volume at the actual bearing interface. Do not
        # excuse collisions merely because the parts share an attachment.
        check=rib.copy();scene.collection.objects.link(check)
        mod=check.modifiers.new('Bearing volume','BOOLEAN');mod.operation='INTERSECT'
        mod.solver='EXACT';mod.object=bpy.data.objects[name]
        dg=bpy.context.evaluated_depsgraph_get();evaluated=check.evaluated_get(dg)
        bm=bmesh.new();bm.from_mesh(evaluated.data)
        if not bm.faces:vol=0.
        else:
            import numpy as np
            points=np.array([v.co[:] for v in bm.verts]);centre=points.mean(axis=0)
            # Coincident bearing faces can be returned as a single open sheet.
            # Such a planar polygon has area and zero enclosed volume.
            flat=np.linalg.matrix_rank(points-centre,tol=1e-8)<3
            bmesh.ops.translate(bm,vec=-Vector(centre),verts=bm.verts)
            vol=0. if flat else abs(bm.calc_volume(signed=True))*1e9
        bm.free();bpy.data.objects.remove(check,do_unlink=True)
        assert vol<.0002,(pair,vol)
        if pair in new:seats[pair]=round(vol,8)
new-=set(seats)
print('NON-MATING CONTACTS OF INTERIOR',len(new),sorted(new),'verified bearing contacts',len(seats),flush=True)
def joined(names):return [[a,b] for a,b in sorted(names)]
if quick:
    (root/f'measurements/{revision}-fit-trial.json').write_text(json.dumps(joined(new),indent=1)+'\n')
else:
    newper={str(f):joined(v-set(seats)) for f,(_,v) in zip(frames,checks) if v-set(seats)}
    current=bpy.data.filepath
    def transforms(names):
        poses=[]
        for f in frames:
            bpy.context.scene.frame_set(f)
            poses.append({n:tuple(x for row in bpy.data.objects[n].matrix_world for x in row) for n in names})
        return poses
    names=[o.name for o in air if o.type=='MESH' and o.name not in shells]
    rev=transforms(names)
    bpy.ops.wm.open_mainfile(filepath=str(root/'blender/drone-v14c.blend'))
    orig=transforms(names)
    worst=max(abs(a-b) for f,g in zip(rev,orig) for n in names for a,b in zip(f[n],g[n]))
    prior,_=rows(collection('V14c | Aircraft'),set(),frames)
    gained=set();lost=set()
    for (a,_),(b,__) in zip(checks,prior):
        gained.update(a-b);lost.update(b-a)
    report={'frames':len(frames),'unchanged_mesh_tracks':len(names),'max_world_transform_delta':worst,
            'new_exterior_contacts':joined(gained),'removed_exterior_contacts':joined(lost),
            'interior_contact_pairs':joined(new),'frames_with_interior_contacts':list(newper),
            'designed_stationary_bearings':[{'parts':pair,'intersecting_volume_mm3':v} for pair,v in sorted(seats.items())]}
    (root/f'measurements/{revision}-fold.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FOLD RESULT',report,flush=True)
    assert not gained and not lost and not new and worst<1e-7,report

