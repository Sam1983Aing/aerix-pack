"""Compare the left and right corners under the battery hatch using mirrored cameras."""
from pathlib import Path
import runpy
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from render_v14b import render_details

VIEWS = {
    f'{label}-corner': ((side*.016, -.063, .0175), (side*.165, -.128, -.043), .071)
    for label, side in [('left', -1), ('right', 1)]
}
VIEWS['rear-return'] = ((0, -.063, .020), (.014, -.195, -.039), .071)

if __name__ == '__main__':
    version = Path(bpy.data.filepath).stem.removeprefix('drone-')
    assert version in ('v14b', 'v14c')
    dest = ROOT / ('teach/shots/v14c' if version == 'v14b' else 'renders/v14c')
    render_details(dest, version, views=VIEWS)
    if version == 'v14c':
        try:
            runpy.run_path(str(ROOT/'scripts/render_revision.py'), run_name='__main__')
        except SystemExit as end:
            if end.code:
                raise
        from v09_gear_views import render_photos
        render_photos(bpy.context.scene, version, False)
