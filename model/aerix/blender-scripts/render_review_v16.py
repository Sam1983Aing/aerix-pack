"""Render the final V16 shell, integrated nose, hinge junctions and retained underside."""
import bpy,sys,argparse
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/aerix-exterior-v16.blend'))
s=bpy.context.scene;s.cycles.samples=40;s.render.resolution_percentage=100
parser=argparse.ArgumentParser();parser.add_argument('--views',nargs='+',default=['hero','top_body','body_contours','nose_embedded','nose_top','rear_connection','front_hinge','underside_body','rear_body','roof_rear','roof_side'])
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
for name in args.views:
 s.render.resolution_x=1100 if name=='top_body' else 1200 if name=='underside_body' else 1536;s.render.resolution_y=1500 if name in ['top_body','underside_body'] else 1024
 s.camera=bpy.data.objects['CAM_'+name];under=name=='underside_body';bpy.data.objects['STUDIO_GROUND'].hide_render=under or name=='top_body';bpy.data.objects['LIGHT_REAR_INSPECTION_UNDER'].hide_render=not under
 s.render.filepath=str(ROOT/'renders/exterior-v16'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('V16_RENDERS_COMPLETE')
