"""Make private product-photo comparisons with the reference and review model nose-up.
The top board uses opposing motor centres to set scale and translation independently.
"""
from pathlib import Path
from math import dist,sqrt
import sys
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
private=root/'references/real/mini-2'
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',26)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
PW,PH=890,746
def placed(source,center,px_per_mm,scale,frame):
    ratio=px_per_mm/scale
    return source.convert('RGB').transform(frame,Image.Transform.AFFINE,
        (ratio,0,center[0]-ratio*frame[0]/2,0,ratio,center[1]-ratio*frame[1]/2),
        Image.Resampling.BICUBIC,fillcolor='#ffffff')

draft='--draft' in sys.argv
real=Image.open(private/'top.jpg')
hubs=[(305,416),(974,416),(326,892),(956,892)]
px=(dist(hubs[0],hubs[3])+dist(hubs[1],hubs[2]))/(2*213)
real_center=tuple(sum(c)/4 for c in zip(*hubs))
avi=Image.open(root/('measurements/v08-draft-1-top.png' if draft else 'renders/v08/v08-unfolded-top.png')).transpose(Image.Transpose.ROTATE_180)
sp=avi.width/500
y_avg=39.7-sqrt(213**2-171.5**2)/2
avi_center=(avi.width/2-.5,avi.height/2-.5-y_avg*sp)
board=Image.new('RGB',(2*PW+4,PH+83),'#f3f3ef')
d=ImageDraw.Draw(board)
for x,img,center,s,headline,note in [(0,real,real_center,px,'DJI Mini 2','DJI product photograph'),
    (PW+4,avi,avi_center,sp,'RILL V08','Blender render')]:
    board.paste(placed(img,center,s,3.25,(PW,PH)),(x,83))
    d.text((x+18,10),headline,font=font,fill='#252925')
    d.text((x+18,46),note+'   /   213 mm diagonal registration',font=small,fill='#454945')
board.save(private/('v08-trial-comparison.jpg' if draft else 'v08-top-comparison.jpg'),quality=95,subsampling=0)

if draft: sys.exit(0)

for source,render,label in [('front.jpg','near-level','Front three-quarter'),('folded.jpg','folded','Folded three-quarter')]:
    studio=Image.open(private/f'v08-{render}-render.png').convert('RGBA')
    box=studio.getchannel('A').getbbox()
    studio=studio.crop(box)
    final=Image.new('RGB',(2*PW+4,560),'white')
    d=ImageDraw.Draw(final)
    # Bounding rectangles crop the source's white field only. Preserve each image's aspect ratio.
    bounds=(96,423,1178,797) if render=='near-level' else (253,385,1000,912)
    original=Image.open(private/source).crop(bounds)
    for x,im,title in [(0,original,'DJI Mini 2'),(PW+4,studio,'RILL V08')]:
        im.thumbnail((PW-38,430),Image.Resampling.LANCZOS)
        pos=(x+(PW-im.width)//2,88+(440-im.height)//2)
        final.paste(im,pos,im if im.mode=='RGBA' else None)
        d.text((x+18,13),title,font=font,fill='#252925')
        d.text((x+18,50),label+'   /   approximate camera match',font=small,fill='#454945')
    final.save(private/f'v08-{render}-comparison.jpg',quality=94,subsampling=0)

# The live viewer is perspective. Register the photograph approximately to the
# captured motor centres and retain the unaltered viewer screenshot and controls.
shot=Image.open(root/'teach/shots/v08/viewer-v08-top.jpg').convert('RGB')
if shot.size==(820,983):
    review=Image.new('RGB',(1646,983),'#eeeeea')
    view_hubs=[(205,389),(615,389),(228,672),(591,672)]
    live_px=(dist(view_hubs[0],view_hubs[3])+dist(view_hubs[1],view_hubs[2]))/(2*213)
    live_cy=sum(y for x,y in view_hubs)/4
    shift=(live_cy-983/2)*px/live_px
    photo=placed(real,(real_center[0],real_center[1]-shift),px,live_px,shot.size)
    review.paste(photo,(0,0))
    review.paste(shot,(826,0))
    d=ImageDraw.Draw(review)
    d.text((28,20),'DJI Mini 2',font=font,fill='#242824')
    d.text((28,916),'DJI product photograph',font=small,fill='#454945')
    review.save(private/'v08-live-top-comparison.jpg',quality=92,subsampling=0)
