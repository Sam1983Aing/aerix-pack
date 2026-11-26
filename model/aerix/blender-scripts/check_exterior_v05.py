import bpy,json
from pathlib import Path
root=Path(bpy.data.filepath).parents[1]
checks={'four_propeller_groups':len([o for o in bpy.data.objects if o.name.startswith('PROPELLER_')])==4,'eight_blades':len([o for o in bpy.data.objects if o.name.startswith('BLADE_')])==8,'192_winding_loops':len([o for o in bpy.data.objects if o.name.startswith('WINDING_')])==192,'no_live_boolean_cutters':all(m.object is not None for o in bpy.data.objects for m in o.modifiers if m.type=='BOOLEAN'),'two_curved_camera_elements':len([o for o in bpy.data.objects if o.name.startswith('LENS_COATED_ELEMENT_')])==2}
assert all(checks.values()),checks
(root/'renders/exterior-v05/validation.json').write_text(json.dumps(checks,indent=2));print(checks)
