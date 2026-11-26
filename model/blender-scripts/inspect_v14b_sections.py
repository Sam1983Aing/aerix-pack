"""Print the sidewall widths of the original casting at the sampled heights."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_v14b import mould_chart, rim_s, rows

*_, grid = mould_chart()
levels = (0, .16, .30, .40, .58, .70, .74)
for row, samples in zip(rows, grid):
    widths = [(round(s-1, 2), round(float(xyz[0]), 1))
              for s, xyz in zip(rim_s, samples) if s >= 1 and round(s-1, 2) in levels]
    print(f'Station {row[0]} mm, (relative height, half-width in mm): {widths}')
