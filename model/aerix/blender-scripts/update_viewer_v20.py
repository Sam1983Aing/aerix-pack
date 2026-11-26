"""Expose paired side and joint inspection cameras for the V20 cleanup."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def update(path,pairs):
 s=path.read_text()
 for old,new in pairs:
  if new in s:continue
  assert old in s,(path,old)
  s=s.replace(old,new)
 path.write_text(s)
update(R/'viewer/review.js',[
 ("'17','18','19'].includes(requested)?requested:'19'","'17','18','19','20'].includes(requested)?requested:'20'"),
 ("function view(name){if(name==='single_port')", "function view(name){if(name==='edge_left'||name==='edge_right')focusObject('BODY_CRADLE',.44,new THREE.Vector3(name==='edge_left'?-1:1,.025,0));else if(name==='joint_left'||name==='joint_right')focusObject('HINGE_ROTATING_COLLAR_'+(name==='joint_left'?'RL':'RR'),.185,new THREE.Vector3(name==='joint_left'?-1:1,.40,.45));else if(name==='single_port')"),
 ("if(version==='19'){", "if(version==='20'){setLighting('studio');view('joint_left');}if(version==='19'){")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V19','DESIGN REVIEW / V20'),
 ('<option value="19">','<option value="20">V20 · Rear joints &amp; body seams</option><option value="19">'),
 ('<button data-view="single_port"','<button data-view="joint_left" data-min-version="20">Left rear connection</button><button data-view="joint_right" data-min-version="20">Right rear connection</button><button data-view="edge_left" data-min-version="20">Left body seam</button><button data-view="edge_right" data-min-version="20">Right body seam</button><button data-view="single_port"'),
 ('exports/aerix-review-v19.glb','exports/aerix-review-v20.glb'),
 ('./review.js?v=19.1','./review.js?v=20.1'),
 ('V19 keeps one rear charging/data port. The underside connector and surround are removed, with the curved shell restored between the vents.','V20 smooths the rear arm connections and cleans the shell-to-chassis seam. Compare both sides using the new connection and body-seam views.')
])
