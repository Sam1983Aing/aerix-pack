"""Expose the cleaned front lip and curved visor in the V22 review."""
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
 ("'19','20','21'].includes(requested)?requested:'21'","'19','20','21','22'].includes(requested)?requested:'22'"),
 ("function view(name){if(name==='sensor_rims'", "function view(name){if(name==='front_finish')focusObject('FRONT_VISOR_FRAME',.18,new THREE.Vector3(0,.17,1));else if(name==='nose_left_finish'||name==='nose_right_finish')focusObject('FRONT_VISOR_FRAME',.21,new THREE.Vector3(name==='nose_left_finish'?-.5:.5,.25,1));else if(name==='sensor_rims'"),
 ("if(version==='21'){", "if(version==='22'){setLighting('studio');document.querySelector('#light').value='studio';view('front_finish');}if(version==='21'){")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V21','DESIGN REVIEW / V22'),
 ('<option value="21">','<option value="22">V22 · Clean front face</option><option value="21">'),
 ('<button data-view="underside_finish"','<button data-view="front_finish" data-min-version="22">Front finish</button><button data-view="nose_left_finish" data-min-version="22">Left nose edge</button><button data-view="nose_right_finish" data-min-version="22">Right nose edge</button><button data-view="underside_finish"'),
 ('exports/aerix-review-v21.glb','exports/aerix-review-v22.glb'),
 ('./review.js?v=21.1','./review.js?v=22.1'),
 ('V21 refines the underside sensor rings and rounded access-panel border with continuous rims and a cleaner satin finish. Use Sensor rims and Panel border for close inspection.','V22 cleans the front titanium lip and smooths the curved visor highlight. Use Front finish and the left/right nose views to inspect the edge. All earlier underside refinements are included.')
])
