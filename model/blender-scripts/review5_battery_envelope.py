"""Compare the published battery bounding box with the uncut exterior projections."""
import json
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

root = Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath).resolve() == root / "blender/drone-v14c.blend"
body = bpy.data.objects["Shell.moulded_fuselage"]
mesh = body.data
tree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in mesh.vertices],
                            [list(p.vertices) for p in mesh.polygons])
width, length, height = 38.7, 75.0, 19.6
tail = -66.0
floors, ceilings = [], []
misses = []
for i in range(40):
    x = -width / 2 + width * i / 39
    for j in range(76):
        y = tail + length * j / 75
        bottom = tree.ray_cast((x / 1000, y / 1000, -0.1), (0, 0, 1))[0]
        top = tree.ray_cast((x / 1000, y / 1000, 0.1), (0, 0, -1))[0]
        if bottom is None or top is None:
            misses.append([x, y])
            continue
        floors.append((bottom.z * 1000, x, y))
        ceilings.append((top.z * 1000, x, y))
floor, ceiling = max(floors), min(ceilings)
base_range = [round(floor[0], 2), round(ceiling[0] - height, 2)] if not misses else None
report = {"source": bpy.path.basename(bpy.data.filepath), "tail_y_mm_estimated": tail,
          "pack_LWH_mm_published": [length, width, height], "sampled_columns": 40 * 76,
          "misses": len(misses), "common_base_z_interval_mm": base_range,
          "highest_lower_surface_zxy_mm": list(map(lambda v: round(v, 3), floor)),
          "lowest_upper_surface_zxy_mm": list(map(lambda v: round(v, 3), ceiling)),
          "limits": "Outer skin only, sampled columns, no wall, rails, bosses or other parts subtracted. No assembly clearance measurement."}
(root / "measurements/review5-battery-envelope.json").write_text(json.dumps(report, indent=2) + "\n")
print(report)
