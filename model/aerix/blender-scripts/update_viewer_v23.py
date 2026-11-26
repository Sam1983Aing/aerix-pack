"""Expose the cleaned rear shell, vents, and cover in V23."""
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
 ("'20','21','22'].includes(requested)?requested:'22'","'20','21','22','23'].includes(requested)?requested:'23'"),
 ("function view(name){if(name==='front_finish'", "function view(name){if(name==='rear_finish')focusObject('REAR_FASCIA',.13,new THREE.Vector3(0,.06,-1));else if(name==='rear_left_finish'||name==='rear_right_finish')focusObject('REAR_FASCIA',.17,new THREE.Vector3(name==='rear_left_finish'?-.50:.50,.18,-1));else if(name==='rear_vents_finish')focusObject('REAR_VENT_TUNNEL_-1_0',.049,new THREE.Vector3(-.05,.12,-1));else if(name==='rear_cover_finish')focusObject('REAR_ACCESS_COVER',.095,new THREE.Vector3(0,.05,-1));else if(name==='front_finish'"),
 ("if(version==='22'){", "if(version==='23'){setLighting('underside');document.querySelector('#light').value='underside';view('rear_finish');}if(version==='22'){")
])
update(R/'viewer/index.html',[
 ('DESIGN REVIEW / V22','DESIGN REVIEW / V23'),
 ('<option value="22">','<option value="23">V23 · Clean rear edges</option><option value="22">'),
 ('<button data-view="front_finish"','<button data-view="rear_finish" data-min-version="23">Rear finish</button><button data-view="rear_left_finish" data-min-version="23">Left rear edge</button><button data-view="rear_right_finish" data-min-version="23">Right rear edge</button><button data-view="rear_vents_finish" data-min-version="23">Rear vent edges</button><button data-view="rear_cover_finish" data-min-version="23">Rear cover border</button><button data-view="front_finish"'),
 ('exports/aerix-review-v22.glb','exports/aerix-review-v23.glb'),
 ('./review.js?v=22.1','./review.js?v=23.1'),
 ('V22 cleans the front titanium lip and smooths the curved visor highlight. Use Front finish and the left/right nose views to inspect the edge. All earlier underside refinements are included.','V23 cleans the rear titanium edge, curved header, vent lips, connector surround and lower cover border. Use Rear finish and the rear detail views to inspect the satin finish. Earlier front and underside refinements are included.')
])
