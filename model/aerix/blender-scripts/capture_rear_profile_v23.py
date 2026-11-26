import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
source=(R/'scripts/blender/refine_rear_body_v11.py').read_text().split('# Rounded rectangle loops')[0]
exec(compile(source,'<original rear surface>','exec'))
(R/'renders/exterior-v23/original-rear-profile.json').write_text(json.dumps({'toprow':toprow,'bottomrow':bottomrow,'panel_halfwidth':panel_halfwidth},indent=2))
(R/'scripts/blender/data').mkdir(exist_ok=True)
(R/'scripts/blender/data/rear-source-profile-v11.json').write_text(json.dumps({'toprow':toprow,'bottomrow':bottomrow,'panel_halfwidth':panel_halfwidth},indent=2))
print('PROFILE',panel_halfwidth,[(x,interp(bottomrow,x),interp(toprow,x),front_y(x,.06)) for x in [0,.02,.035,.045,.049]],flush=True)
