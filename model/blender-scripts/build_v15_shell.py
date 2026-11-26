"""Prepare the immutable outer-skin partitions under the approved V14c datum."""
from pathlib import Path
import bpy,sys,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'))
from v15_shell import split_shell
assert Path(bpy.data.filepath).resolve()==root/'blender/drone-v14c.blend'
bpy.context.scene.frame_set(1)
g=bpy.data.collections['V14c | Aircraft']
mat=bpy.data.materials.new('RILL | inner moulding');mat.diffuse_color=(.16,.175,.17,1);mat.use_nodes=True
bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=.62
report=split_shell(g.objects['Shell.moulded_fuselage'],g,mat)
(root/'measurements/v15-shell.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath='/private/tmp/rill15-shell-work.blend',compress=True)

