"""Make the Review 6 plate and studio contact proof from the saved Blender renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,shutil
root=Path(__file__).resolve().parents[1];out=root/'renders/v15'
shots=root/'teach/shots/v15';shots.mkdir(exist_ok=True)
fontroot=Path('/System/Library/Fonts/Supplemental')
def font(size,bold=False):return ImageFont.truetype(str(fontroot/('Arial Bold.ttf' if bold else 'Arial.ttf')),size)
bg='#f4f3ed';ink='#203932';muted='#536b60';line='#aebbb1'
def text(draw,x,y,s,size,color=ink,bold=False):
    draw.text((x,y),s,font=font(size,bold),fill=color)
def paste(c,n,x,y,w):
    im=Image.open(out/n).convert('RGBA');h=round(im.height*w/im.width)
    im=im.resize((w,h),Image.Resampling.LANCZOS);c.paste(im,(x,y),im);return h
def note(d,x,y,head,body):
    text(d,x,y,head,26,ink,True)
    for i,s in enumerate(body):text(d,x,y+42+i*31,s,22,muted)
c=Image.new('RGB',(1880,1480),bg);d=ImageDraw.Draw(c)
text(d,72,39,'RILL    /    AIRFRAME DEVELOPMENT',21,muted,True)
text(d,1540,39,'V15    /    REVIEW 6',21,muted,True)
text(d,68,83,'Interior sections',67,ink,True)
d.line((72,190,1808,190),fill=line,width=2)
text(d,72,217,'TOP SECTION',20,muted,True);text(d,310,217,'Horizontal cut at Z = 46.7 mm',21,muted)
paste(c,'section-top.png',52,260,1208)
d.line((1295,220,1295,875),fill=line,width=2)
note(d,1340,336,'Motor-control board',['The aft board sits above the battery.','The wire bundles leave on both sides.'])
note(d,1340,502,'Navigation module',['The pale ceramic square sits on the','forward board and faces the roof.'])
note(d,1340,668,'Rear hatch',['The door carries the lower return','around the battery opening.'])
d.line((72,889,1808,889),fill=line,width=2)
text(d,72,912,'SIDE SECTION',20,muted,True);text(d,310,912,'Longitudinal cut at X = 0 mm',21,muted)
paste(c,'section-side.png',52,949,1208)
d.line((1295,922,1295,1405),fill=line,width=2)
note(d,1340,993,'Battery and tray',['The ochre pack sits between the','upper boards and the belly electronics.'])
note(d,1340,1149,'Core and heat spreader',['The core board and finned plate','stack beneath the battery tray.'])
note(d,1340,1301,'Suspended camera',['The front section exposes the','receiver pocket and lens assembly.'])
text(d,72,1431,'Tail at left in both views. Inspection colours identify assemblies.',20,muted)
c.save(out/'review-6-sections.png',optimize=True)
c=Image.new('RGB',(1500,2330),bg);d=ImageDraw.Draw(c)
text(d,58,29,'Exterior comparison',42,ink,True);text(d,58,99,'Approved V14c',23,muted,True);text(d,781,99,'V15',23,muted,True)
report={}
for i,(n,label) in enumerate([('three-quarter','Three-quarter'),('top','Top'),('side','Side'),('front','Front'),('back','Rear')]):
    a=Image.open(root/f'renders/v14c/v14c-unfolded-{n}.png').convert('RGB')
    b=Image.open(out/f'studio-{n}.png').convert('RGB')
    assert a.size==b.size==(1920,1080)
    delta=np.abs(np.asarray(a,dtype=np.int16)-np.asarray(b,dtype=np.int16))
    report[n]={'mean_absolute_difference_8bit':round(float(delta.mean()),4),
               'p99_8bit':float(np.percentile(delta,99)),'max_8bit':int(delta.max())}
    y=150+i*431;text(d,58,y,label,21,ink,True)
    for x,im in [(58,a),(781,b)]:
        # Show the full studio camera frame on both sides.
        im.thumbnail((665,375),Image.Resampling.LANCZOS)
        c.paste(im,(x,y+36))
c.save(out/'studio-comparison.jpg',quality=94)
(root/'measurements/v15-render-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
for f in ['review-6-sections.png','studio-comparison.jpg']:shutil.copyfile(out/f,shots/f)

