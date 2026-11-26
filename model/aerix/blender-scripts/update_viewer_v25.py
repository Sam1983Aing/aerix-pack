from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'viewer/review.js';s=p.read_text();assert "'23','24'].includes(requested)?requested:'24'" in s
s=s.replace("'23','24'].includes(requested)?requested:'24'","'23','24','25'].includes(requested)?requested:'25'")
s=s.replace("function view(name){if(name.startsWith('support_'))", "function view(name){if(['rear_rim','rear_rim_left','rear_rim_right'].includes(name)){const side=name==='rear_rim_left'?-1:name==='rear_rim_right'?1:0;focusObject('REAR_FASCIA',side===0?.17:.135,new THREE.Vector3(side*.58,-.72,-1));const offset=new THREE.Vector3(side*.025,-.003,0);controls.target.add(offset);camera.position.add(offset);controls.update();}else if(name.startsWith('support_'))")
s=s.replace("if(version==='24'){", "if(version==='25'){setLighting('underside');document.querySelector('#light').value='underside';view('rear_rim');}if(version==='24'){")
s=s.replace("(version==='18'?'?rev=1':","(version==='25'?'?rev=2':version==='18'?'?rev=1':")
p.write_text(s)
p=R/'viewer/index.html';s=p.read_text().replace('DESIGN REVIEW / V24','DESIGN REVIEW / V25').replace('<option value="24">','<option value="25">V25 · Polished rear rim</option><option value="24">').replace('exports/aerix-review-v24.glb','exports/aerix-review-v25.glb').replace('./review.js?v=24.1','./review.js?v=25.2')
buttons=''.join('<button data-view="'+name+'" data-min-version="25">'+label+'</button>' for name,label in [('rear_rim','Rear rim'),('rear_rim_left','Left rim corner'),('rear_rim_right','Right rim corner')])
s=s.replace('<button data-view="support_FL"',buttons+'<button data-view="support_FL"')
s=s.replace('V24 smooths the black rounded shoulder beneath each motor and gives all four supports a consistent satin finish. Use the four support views to inspect the junctions. Earlier body, rear and underside refinements are included.','V25 rounds the lower rear rim, softens its corner edges and cleans the panel return shading. Use Rear rim and the two corner views to inspect it from underneath. The V24 motor-support refinements are included.')
p.write_text(s)
