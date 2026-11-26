"""Register private source photographs and compose durable matched-view comparisons."""
from pathlib import Path
import json, os, shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from v16_reference import H
root=Path(__file__).resolve().parents[1]
refs=root/'references/real/interior';private=refs/'v16';renders=root/'renders/v16'
viewer=root/'viewer/review7';shots=root/'teach/shots/v16'
size=(1440,830);inverse=np.linalg.inv(H)
def image_to_model(px,py,sign):
    y=-28-(px-size[0]/2)*91/size[0]
    x=sign*(size[1]/2-py)*91/size[0];return x,y
def source_coordinate(px,py,part):
    x,y=image_to_model(px,py,-1 if part=='board-lower' else 1)
    if part=='board-upper':
        a,b,c=inverse @ (x,y,1);return a/c,b/c
    if part=='battery':return 188+(9.5-y)*487/75,242+(19.35-x)*243/38.7
    return 303+(11-y)*382/78,307.5+x*183/37
def register(source,part):
    A=[];b=[]
    for px,py in [(0,0),(size[0],0),(0,size[1]),size]:
        u,v=source_coordinate(px,py,part)
        A.extend([[px,py,1,0,0,0,-px*u,-py*u],[0,0,0,px,py,1,-px*v,-py*v]])
        b.extend([u,v])
    return source.transform(size,Image.Transform.PERSPECTIVE,np.linalg.solve(A,b),Image.Resampling.BICUBIC)
def font(sz,bold=False):
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',sz)
entries=[
 ('battery','pd-battery.jpg','Flight battery','PD filing · isolated flight pack','Label face • rear latch at right'),
 ('board-upper','wd-006.jpg','Main board · shield face','WD filing · internal photographs, figure 7','Port edge at right • board registered on its four mounting holes'),
 ('board-lower','pd-core.jpg','Main board · thermal face','PD filing · isolated core board','Port edge at right • cooling plate removed')]
for part,ref,title,citation,caption in entries:
    r=register(Image.open(refs/ref).convert('RGB'),part)
    photo=private/(part+'-ref.jpg');r.save(photo,quality=95)
    link=viewer/photo.name
    if not link.exists():link.symlink_to(os.path.relpath(photo,viewer))
    im=Image.open(renders/(part+'.png')).convert('RGBA')
    bg=Image.new('RGBA',size,'#828984');bg.alpha_composite(im)
    canvas=Image.new('RGB',(1980,755),'#eeefe9');dr=ImageDraw.Draw(canvas)
    dr.text((42,25),title,font=font(38,True),fill='#1e302c')
    dr.text((42,84),citation,font=font(22),fill='#43534f')
    dr.text((1006,84),'RILL V16 · Blender',font=font(22),fill='#43534f')
    for obj,x in [(r,42),(bg.convert('RGB'),1006)]:
        canvas.paste(obj.resize((932,537),Image.Resampling.LANCZOS),(x,133))
    dr.text((42,695),caption,font=font(20),fill='#41514d')
    plate=private/(part+'-comparison.jpg');canvas.save(plate,quality=94)
    link=viewer/plate.name
    if not link.exists():link.symlink_to(os.path.relpath(plate,viewer))
    shutil.copyfile(renders/(part+'.png'),shots/(part+'.png'))

