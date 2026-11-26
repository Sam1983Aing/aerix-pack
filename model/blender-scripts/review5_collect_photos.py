"""Download the specific repair photographs used in the Stage 5 evidence sheet."""
from pathlib import Path
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

root=Path(__file__).resolve().parents[1]/'references/real/interior'
shots={'gimbal':[(2,2),(4,1),(4,2),(5,3),(6,1),(7,2),(8,1),(9,2),(10,1),(11,2),(12,1),(13,1),(14,1),(15,1),(15,2)],
       'arm':[(10,1),(11,2),(12,1),(13,1),(14,1),(15,2)]}
records=[]
for subject,items in shots.items():
    guide=json.loads((root/f'guide-{subject}.json').read_text())
    for step,no in items:
        data=guide['steps'][step-1]['media']['data']
        if no>len(data): no=1
        entry=data[no-1]
        records.append({'file':f'ifixit-{subject}-{step:02d}-{no}.jpg','image_url':entry['large'],'guide':guide['url'],
                        'step':step,'image':no,'author':guide['author']['username']})
def fetch(record):
    path=root/record['file']
    if not path.exists():
        subprocess.run(['curl','-fsSL','--retry','2','--max-time','30',record['image_url'],'-o',str(path)],check=True)
    with Image.open(path) as im: im.verify()
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(fetch,records))
(root/'repair-photo-index.json').write_text(json.dumps(records,indent=2)+'\n')
