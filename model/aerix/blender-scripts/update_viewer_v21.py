"""Show the clean underside sensor rims and access-panel border in V21."""
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
 ("'18','19','20'].includes(requested)?requested:'20'","'18','19','20','21'].includes(requested)?requested:'21'"),
 ("function view(name){if(name==='edge_left'", "function view(name){if(name==='sensor_rims')focusObject('BELLY_SENSOR_BRIDGE',.16,new THREE.Vector3(0,-1,-.05));else if(name==='panel_border')focusObject('BELLY_SERVICE_PANEL',.25,new THREE.Vector3(0,-1,-.025));else if(name==='underside_finish')focusObject('BELLY_SPINE',.38,new THREE.Vector3(0,-1,-.001));else if(name==='edge_left'"),
 ("if(version==='20'){", "if(version==='21'){setLighting('underside');document.querySelector('#light').value='underside';view('underside_finish');}if(version==='20'){")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V20','DESIGN REVIEW / V21'),
 ('<option value="20">','<option value="21">V21 · Sensor rims &amp; panel edges</option><option value="20">'),
 ('<button data-view="joint_left"','<button data-view="underside_finish" data-min-version="21">Underside finish</button><button data-view="sensor_rims" data-min-version="21">Sensor rims</button><button data-view="panel_border" data-min-version="21">Panel border</button><button data-view="joint_left"'),
 ('exports/aerix-review-v20.glb','exports/aerix-review-v21.glb'),
 ('./review.js?v=20.1','./review.js?v=21.1'),
 ('V20 smooths the rear arm connections and cleans the shell-to-chassis seam. Compare both sides using the new connection and body-seam views.','V21 refines the underside sensor rings and rounded access-panel border with continuous rims and a cleaner satin finish. Use Sensor rims and Panel border for close inspection.')
])
