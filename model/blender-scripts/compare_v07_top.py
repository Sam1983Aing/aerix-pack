"""Register overhead views by open motor diagonal and center for the V07 arm review."""
from pathlib import Path
import math
import sys
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parents[1]
preview='--preview' in sys.argv
v07=(root/'measurements/v07-arm-preview.png' if preview else root/'renders/v07/v07-unfolded-top.png')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
# A physical scale of 3.4 px/mm crops the long blade tips and centers attention on the arms.
panel_w,panel_h=754,646
scale=3.4
native_scale=1920/500
rear_y=78-math.sqrt(213**2-172**2)
model_center=(960,540+(78+rear_y)*.5*native_scale)

def panel(path,reference=False):
    with Image.open(path) as src:
        if reference:
            # DJI studio photo has the nose up. Its opposing hub centers provide the scale.
            # Measurements are approximate due to perspective; no non-uniform deformation.
            im=src.convert('RGB').transpose(Image.Transpose.ROTATE_180)
            corners=[(305,416),(974,416),(326,892),(956,892)]
            cx=src.width-1-sum(x for x,_ in corners)/4
            cy=src.height-1-sum(y for _,y in corners)/4
            s=(math.dist(corners[0],corners[3])+math.dist(corners[1],corners[2]))/(2*213)
        else:
            im=src.convert('RGB')
            cx,cy=model_center
            s=native_scale
        ratio=s/scale
        return im.transform((panel_w,panel_h),Image.Transform.AFFINE,
                (ratio,0,cx-ratio*panel_w/2,0,ratio,cy-ratio*panel_h/2),Image.Resampling.BICUBIC)

def board(first,first_label,path,product=False):
    sheet=Image.new('RGB',(2*panel_w+6,panel_h+52),'#f1f1ed')
    draw=ImageDraw.Draw(sheet)
    for x,img,label in ((0,panel(first,product),first_label),(panel_w+6,panel(v07),'V07  /  revised arms')):
        sheet.paste(img,(x,52))
        draw.text((x+15,12),label,font=font,fill='#202320')
    path.parent.mkdir(exist_ok=True,parents=True)
    sheet.save(path,quality=94,subsampling=0)

folder=root/'references/real/mini-2'
board(folder/'top.jpg','DJI Mini 2  /  product reference',
      folder/('v07-preview-private.jpg' if preview else 'v07-top-comparison.jpg'),True)
if not preview:
    board(root/'renders/v06/v06-unfolded-top.png','V06  /  previous arms',
          root/'renders/v07/comparisons/v06-v07-top.jpg')
