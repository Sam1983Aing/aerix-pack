"""Add matched close-ups of the four polished motor-support junctions."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'viewer/review.js';s=p.read_text()
assert "'22','23'].includes(requested)?requested:'23'" in s
s=s.replace("'22','23'].includes(requested)?requested:'23'","'22','23','24'].includes(requested)?requested:'24'")
s=s.replace("function view(name){if(name==='rear_finish'", "function view(name){if(name.startsWith('support_')){const tag=name.slice(8);focusObject('MOTOR_SEAL_'+tag,.086,new THREE.Vector3(tag.endsWith('L')?-1:1,.10,tag.startsWith('F')?.35:-.35));controls.target.y-=.006;camera.position.y-=.006;controls.update();}else if(name==='rear_finish'")
s=s.replace("if(version==='23'){", "if(version==='24'){setLighting('studio');document.querySelector('#light').value='studio';view('support_FR');}if(version==='23'){")
p.write_text(s)
p=R/'viewer/index.html';s=p.read_text().replace('DESIGN REVIEW / V23','DESIGN REVIEW / V24').replace('<option value="23">','<option value="24">V24 · Smooth motor supports</option><option value="23">').replace('exports/aerix-review-v23.glb','exports/aerix-review-v24.glb').replace('./review.js?v=23.1','./review.js?v=24.1')
buttons=''.join('<button data-view="support_'+tag+'" data-min-version="24">'+label+' support</button>' for tag,label in [('FL','Front left'),('FR','Front right'),('RL','Rear left'),('RR','Rear right')])
s=s.replace('<button data-view="rear_finish"',buttons+'<button data-view="rear_finish"')
s=s.replace('V23 cleans the rear titanium edge, curved header, vent lips, connector surround and lower cover border. Use Rear finish and the rear detail views to inspect the satin finish. Earlier front and underside refinements are included.','V24 smooths the black rounded shoulder beneath each motor and gives all four supports a consistent satin finish. Use the four support views to inspect the junctions. Earlier body, rear and underside refinements are included.')
p.write_text(s)
