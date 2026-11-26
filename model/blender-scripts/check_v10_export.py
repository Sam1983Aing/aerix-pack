"""Check the delivered optical axis, full fold and all four foot contacts."""
import json
import sys
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from v10_alignment import alignment
from check_v09_gear import inspect_gear

revision=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v10'
assert revision in ('v10','v11','v12')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(root/f'exports/drone-{revision}.glb'))
result=inspect_gear(bpy.context.scene)
result['after_xz_mm']=alignment(bpy.data.objects)
native=json.loads((root/'measurements/v10-native-audit.json').read_text())
assert all(max(map(abs,v))<.001 for v in result['after_xz_mm'].values())
for key,value in result.items():
    if key!='after_xz_mm':
        assert native[key]==value,key
(root/f'measurements/{revision}-export-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('Re-imported optics are centered to 0.001 mm. Geometry and folding checks agree with the native model.')
