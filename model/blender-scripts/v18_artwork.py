"""Draw neutral PCB finishes from the locations of visible lands in the filing photos."""
from collections import deque
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from v18_reference import photos,upper_chips,lower_chips
root=Path(__file__).resolve().parents[1]
dest=root/'blender/materials/v18'
from v18_reference import texture_bounds as bounds
regions={'esc':[(221,151,508,386),(386,198,533,337),(221,315,427,341)],
 'esc-back':[(213,95,469,381),(201,240,273,379)],'gps':[],'gps-back':[(261,63,289,108),(263,198,280,232),(335,112,438,174)]}
exclude={'esc':upper_chips+[(301,206,406,310),(461,227,537,299),(227,246,271,293),(441,364,510,399),(483,299,525,335)],
 'esc-back':lower_chips+[(216,165,276,217),(397,86,469,104),(200,207,252,249),(204,185,220,204)],
 'gps':[],'gps-back':[(317,114,387,138)]}
legends={'esc':[(352,418,'R I L L',7),(424,386,'DRIVE  /  18',5)],'esc-back':[(392,87,'RILL     D18',6)],
 'gps':[(185,108,'RILL',6),(185,119,'N18',5)],'gps-back':[(259,278,'N18',5)]}
pads={'esc':[(233,226,9.2),(233,313,7.0),(329,122,3),(429,115,3.1),(325,428,3.5),
 (351,428,3),(372,428,3),(388,427,3),(415,426,3),(295,199,3.4),(315,200,2.9),
 (342,332,4),(353,332,4),(365,332,3.7),(375,332,3.8),(386,332,4),(397,331,4),(459,329,4)],
 'esc-back':[(485,211,11),(486,239,11),(266,94,3.7)],'gps':[(182,96,5.2),(469,205,5.1)],
 'gps-back':[(214,262,5.8),(486,168,6),(338,157,3),(349,158,3),(361,158,3),(373,159,3)]}
rings={'esc':[(565,134,7),(578,400,7.8),(575,220,6),(579,305,6)],'esc-back':[(524,117,7),(539,361,7)],
 'gps':[(181,60,21),(461,63,20),(181,241,22),(467,241,21)],'gps-back':[(214,297,21),(489,304,21),(218,131,20),(483,137,20)]}
def spots(mask):
    mark=mask.copy()
    for y,x in zip(*mask.nonzero()):
        if not mark[y,x]:continue
        mark[y,x]=False;todo=deque([(x,y)]);blob=[]
        while todo:
            u,v=todo.pop();blob.append((u,v))
            for a,b in ((u+1,v),(u-1,v),(u,v+1),(u,v-1)):
                if 0<=b<mark.shape[0] and 0<=a<mark.shape[1] and mark[b,a]:
                    mark[b,a]=False;todo.append((a,b))
        yield np.array(blob)
def create():
    metrics={}
    for key,src in photos.items():
        src_im=Image.open(root/'references/real/interior'/src).convert('RGB')
        area=Image.new('1',src_im.size);d=ImageDraw.Draw(area)
        for box in regions[key]:d.rectangle(box,fill=1)
        for box in exclude[key]:d.rectangle(box,fill=0)
        rgb=np.array(src_im);bright=(np.min(rgb,axis=2)>100)&np.array(area)
        x0,y0,x1,y1=bounds[key];scale=5
        wh=((x1-x0)*scale,(y1-y0)*scale)
        im=Image.new('RGB',wh,(39,41,41));orm=Image.new('RGB',wh,(255,147,0))
        paint=ImageDraw.Draw(im);coat=ImageDraw.Draw(orm)
        def xy(x,y):return ((x-x0)*scale,(y-y0)*scale)
        def mark(box,col,metal,rad=1,ellipse=False):
            a,b,c,e=box;bb=(*xy(a,b),*xy(c,e))
            for brush,ink in ((paint,col),(coat,(255,90 if metal else 147,metal))):
                if ellipse:brush.ellipse(bb,fill=ink)
                else:brush.rounded_rectangle(bb,radius=rad*scale,fill=ink)
        count=0
        for blob in spots(bright):
            if not 3<=len(blob)<=80:continue
            lo=blob.min(axis=0);hi=blob.max(axis=0);size=hi-lo+1
            if size.max()>12 or len(blob)/size.prod()<.42:continue
            x,y=blob.mean(axis=0);w,h=size*.79
            mark((x-w/2,y-h/2,x+w/2,y+h/2),(161,161,151),175,.45);count+=1
        for x,y,r in pads[key]+rings[key]:
            mark((x-r,y-r,x+r,y+r),(173,140,73),191,ellipse=True)
        if key=='esc-back':
            # The filing shows a pale inspection sticker at this position.
            # Draw a neutral inspection mark inside the same circular footprint.
            bb=(*xy(224,168),*xy(268,211));paint.ellipse(bb,fill=(191,194,184))
            coat.ellipse(bb,fill=(255,182,0))
            label=Image.new('RGBA',(40*scale,20*scale))
            letter=ImageDraw.Draw(label)
            letter.text((1,0),'QC',font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',15*scale),fill=(58,61,59))
            label=label.rotate(34,Image.Resampling.BICUBIC,expand=True)
            im.paste(label,(int((246-x0)*scale-label.width/2),int((190-y0)*scale-label.height/2)),label)
        if key=='gps-back':
            for box in [(262,232,274,237),(280,232,291,237),(267,278,293,288)]:
                mark(box,(177,145,81),185)
            paint.arc((*xy(255,248),*xy(292,281)),122,348,fill=(197,203,193),width=scale)
        for x,y,txt,pt in legends[key]:
            ff=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',pt*scale)
            paint.text(xy(x,y),txt,font=ff,fill=(190,194,178))
        # Microfinish is original artwork. Small printed annotations replace the
        # donor identifiers, and surface contrast follows exposed pad boundaries.
        rgb=np.asarray(im,dtype=np.int16)
        rng=np.random.default_rng(1800+list(photos).index(key))
        noise=rng.normal(0,1.6,rgb.shape[:2])
        im=Image.fromarray(np.uint8(np.clip(rgb+noise[:,:,None],0,255)))
        if key.startswith('esc'):
            packages=Image.new('RGB',wh,(31,34,34));ink=ImageDraw.Draw(packages)
            chip_labels=[(323,240,'RILL',9),(323,255,'D18',5.5),(479,247,'P18',6)] if key=='esc' else [
                (a+6,b+12,'R18',4.5) for a,b,c,d in lower_chips]
            for x,y,txt,pt in chip_labels:
                ff=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',int(pt*scale))
                ink.text(xy(x,y),txt,font=ff,fill=(104,105,93))
            for a,b,c,d in (upper_chips+[(314,220,391,292),(470,235,529,286)] if key=='esc' else lower_chips):
                dot=(*xy(a+2,b+2),*xy(a+4.4,b+4.4));ink.ellipse(dot,fill=(80,81,75))
            packages.save(dest/(key+'-packages.png'),optimize=True)
        im.save(dest/(key+'.jpg'),quality=95,subsampling=0,optimize=True);orm.save(dest/(key+'-orm.png'),optimize=True)
        metrics[key]=count
    print('Resolved solder lands',metrics)
if __name__=='__main__':create()

