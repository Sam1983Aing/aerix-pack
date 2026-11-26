"""Publish V18 to the local inspection viewer after GLB validation."""
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
 ("(version==='17'?'?rev=2':","(version==='18'?'?rev=1':version==='17'?'?rev=2':"),
 ("'15','16','17'].includes(requested)?requested:'17'","'15','16','17','18'].includes(requested)?requested:'18'"),
 ("function view(name){if(name==='main_camera')", "function view(name){if(name==='under_edges')focusObject('BODY_CRADLE',.42,new THREE.Vector3(0,-1,-.0001));else if(name==='main_camera')"),
 ("if(version==='17'){setLighting('studio');view('main_camera');}","if(version==='18'){setLighting('underside');document.querySelector('#light').value='underside';view('under_edges');}if(version==='17'){setLighting('studio');view('main_camera');}")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V17','DESIGN REVIEW / V18'),
 ('<option value="17">','<option value="18">V18 · Clean underside edges</option><option value="17">'),
 ('<button data-view="under_body"','<button data-view="under_edges" data-min-version="18">Underside edges</button><button data-view="under_body"'),
 ('exports/aerix-review-v17.glb','exports/aerix-review-v18.glb'),
 ('./review.js?v=17.1','./review.js?v=18.1'),
 ('V17 rebuilds the main camera with a rounded housing, circular gimbal drums, machined lens rings and recessed layered optics.','V18 cleans up the underside panel edges, sensor surrounds and vent openings with smoother fitted rims.')
])
