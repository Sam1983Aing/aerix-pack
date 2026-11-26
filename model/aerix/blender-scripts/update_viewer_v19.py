"""Expose the single rear port in the V19 inspection viewer."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def update(path,pairs):
 s=path.read_text()
 for old,new in pairs:
  if new in s:continue
  if old not in s:raise ValueError(('Viewer source changed',str(path),old))
  s=s.replace(old,new)
 path.write_text(s)
update(R/'viewer/review.js',[
 ("'16','17','18'].includes(requested)?requested:'18'","'16','17','18','19'].includes(requested)?requested:'19'"),
 ("function view(name){if(name==='under_edges')","function view(name){if(name==='single_port'){focusObject('REAR_FASCIA',.22,new THREE.Vector3(.14,-.68,-1));const offset=new THREE.Vector3(0,-.016,.025);controls.target.add(offset);camera.position.add(offset);controls.update();}else if(name==='under_edges')"),
 ("if(version==='18'){", "if(version==='19'){setLighting('underside');document.querySelector('#light').value='underside';view('single_port');}if(version==='18'){")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V18','DESIGN REVIEW / V19'),
 ('<option value="18">','<option value="19">V19 · Single rear port</option><option value="18">'),
 ('<button data-view="under_edges"','<button data-view="single_port" data-min-version="19">Rear &amp; underside</button><button data-view="under_edges"'),
 ('exports/aerix-review-v18.glb','exports/aerix-review-v19.glb'),
 ('./review.js?v=18.1','./review.js?v=19.1'),
 ('V18 cleans up the underside panel edges, sensor surrounds and vent openings with smoother fitted rims.','V19 keeps one rear charging/data port. The underside connector and surround are removed, with the curved shell restored between the vents.')
])
