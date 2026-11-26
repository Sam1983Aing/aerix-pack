"""Write the measurement sheet and compare the archived and rendered V01 views."""
import hashlib
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
audit = json.loads((root/'measurements/v01-audit.json').read_text())
sizes = audit['dimensions_mm']
lines = [
    '# V01 dimensions and fold check', '',
    'DJI Mini 2 international. Measured on the evaluated Blender meshes in meters and reported in millimeters. L runs nose to tail, W runs across the arms, H runs vertically. The airframe measurement omits the two blades and cap at each rotor. The complete-pose measurement includes them.', '',
    '| Measurement | DJI (mm) | V01 (mm) | Difference |',
    '|---|---:|---:|---:|',
]
def row(label, reference, value):
    difference = 100 * (value-reference)/reference
    lines.append(f'| {label} | {reference:g} | {value:.3f} | {difference:+.3f}% |')
for label, key, spec in [
    ('Folded, blades parked','121-all',(138,81,58)),
    ('Unfolded airframe','1-airframe',(159,203,56)),
    ('Unfolded, blades extended','1-all',(245,289,56)),
]:
    for axis,ref,val in zip(('L','W','H'),spec,sizes[key]):
        row(f'{label} · {axis}', ref, val)
for pair,diameter in zip(('FR–RL','FL–RR'),sizes['wheelbases']):
    row(f'Diagonal motor spacing in plan · {pair}',213,diameter)
row('Rotor swept diameter · all four',4.7*25.4,sizes['propeller_diameters'][0])
lines.extend(['',
    'The rotor diameter uses the farthest point of the swept blade tip. DJI publishes 4.7 inches. The open pose uses independently oriented blades, since the published envelope does not specify rotor angles. Weight is a reference value (<249 g). This clay model has no assigned component masses.', '',
    '## Folding check', '',
    'The four-second animation uses 121 poses at 30 fps. Frames 1–47 turn the hubs and park the blade pairs. The rear arms turn under the body at frames 48–84. The front arms swing back at frames 85–121. The reverse motion opens the front arms first.', '',
    'The audit evaluates transformed meshes at every integer frame, including the fully folded endpoint. It compares bounding boxes, tests intersecting triangle surfaces, and checks for one solid contained in another. Rigidly joined pieces and intended bearing contacts are excluded. The final pass found zero unexpected intersections in the tested pairs. This is a discrete geometric check. Joint locations were fitted to photographs and represent estimated pivots.', '',
    'The browser played the exported Fold clip to both endpoints. Its whole-model readouts were 245.0 × 289.1 × 56.0 mm open and 138.0 × 81.0 × 58.0 mm folded.', '',
    '[DJI measurements and source notes](../references/spec-sheet.md) · [Machine-readable Blender results](v01-audit.json)', ''])
(root/'measurements/v01.md').write_text('\n'.join(lines))
assert audit['sampled_frames']==121 and not audit['intersections']
for pose in ('folded','unfolded'):
    for view in ('three-quarter','top','side','back','front'):
        name=f'v01-{pose}-{view}.png'
        data=(root/'renders/v01'/name).read_bytes()
        assert struct.unpack('>II',data[16:24]) == (1920,1080)
        assert hashlib.sha256(data).digest()==hashlib.sha256((root/'teach/shots/v01'/name).read_bytes()).digest()
print('Verified ten 1920 × 1080 images and their exact teaching copies.')
