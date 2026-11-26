"""Generate original RILL film artwork and trace observable PCB mounting lands."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from v16_reference import top, bottom, lower_field, pd_holes

root=Path(__file__).resolve().parents[1]
private=root/'references/real/interior'
assets=root/'blender/materials/v16'
assets.mkdir(parents=True,exist_ok=True)
def font(size,bold=False):
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',size)
# Projected pack coordinates: horizontal is -aircraft Y, vertical is +aircraft X.
im=Image.new('RGB',(2048,1056),(147,148,143))
draw=ImageDraw.Draw(im)
def pack_uv(u,v):
    return ((u-188)/487*2048,(v-242)/243*1056)
def rect(d,points,fill):
    a,b,c,e=points
    d.rectangle([pack_uv(a,b),pack_uv(c,e)],fill=fill)
rect(draw,(207,322,311,440),(132,134,130))
label=Image.new('RGB',(1420,525),(31,34,33));p=ImageDraw.Draw(label)
paper=(207,209,200);dim=(167,173,165)
p.text((43,22),'RILL',font=font(96,True),fill=paper)
p.text((312,40),'FLIGHT BATTERY',font=font(39,True),fill=paper)
p.text((315,96),'RECHARGEABLE  /  TWO-CELL PACK',font=font(19),fill=dim)
p.line((48,157,1367,157),fill=(116,121,114),width=3)
p.text((48,178),'7.7 V',font=font(53,True),fill=paper)
p.text((325,178),'2250 mAh',font=font(53,True),fill=paper)
p.text((725,186),'17.32 Wh',font=font(40),fill=paper)
p.text((50,264),'RATED VOLTAGE',font=font(18),fill=dim)
p.text((328,264),'RATED CAPACITY',font=font(18),fill=dim)
p.text((725,264),'NOMINAL ENERGY',font=font(18),fill=dim)
p.text((48,325),'RILL  /  ENERGY SYSTEMS',font=font(21,True),fill=paper)
p.line((915,317,915,493),fill=(118,124,117),width=2)
for j,line in enumerate(['PACK   /   02','CELL ARRANGEMENT       2S','NOMINAL       7.7 V DC','SERIES   R16       LOT 01']):
    p.text((942,326+j*40),line,font=font(17,j==0),fill=paper)

p.text((48,374),'Two-cell rechargeable flight pack.  Use the matching charge interface.',font=font(20),fill=paper)
p.text((48,412),'Handle by the case.  Keep the contact recess clean and dry.',font=font(20),fill=paper)
p.text((48,463),'BATCH   R16   /   01',font=font(18),fill=dim)
p.rounded_rectangle((1150,29,1365,124),radius=8,outline=dim,width=3)
p.text((1180,55),'PACK 02',font=font(29,True),fill=paper)
# The donor's main legend reads from the opposite end to the thumb catch.
im.paste(label.rotate(180),tuple(round(v) for v in pack_uv(235,293)))
im.save(assets/'pack-film.png',optimize=True)

# Restrict footprint extraction to visibly populated, unobstructed board areas.
# No photo pixels are copied into the authored maps or the exported models.
fields={
 'upper':('wd-006.jpg',top,[[(442,310),(513,310),(533,267),(603,270),(608,360),(440,354)],
                            [(92,312),(127,313),(113,336),(93,335)]]),
 'lower':('pd-core.jpg',lower_field,[[(594,255),(626,246),(623,275),(646,275),(650,290),(670,292),(677,368),(653,367),(605,374),(585,368)],
                                [(313,269),(334,269),(330,374),(311,370)],
                                [(538,250),(551,250),(551,366),(538,373)]])}
marked={}
def islands(mask):
    from collections import deque
    marks=mask.copy()
    for yy,xx in zip(*mask.nonzero()):
        if not marks[yy,xx]:continue
        marks[yy,xx]=False; q=deque([(yy,xx)]);points=[]
        while q:
            y,x=q.popleft();points.append((x,y))
            for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=ny<marks.shape[0] and 0<=nx<marks.shape[1] and marks[ny,nx]:
                    marks[ny,nx]=False;q.append((ny,nx))
        yield points
for face,(filename,mapper,polys) in fields.items():
    src=Image.open(private/filename).convert('RGB');rgb=np.asarray(src,dtype=float)
    roi=Image.new('1',src.size);dd=ImageDraw.Draw(roi)
    for poly in polys:dd.polygon(poly,fill=1)
    roi=np.array(roi).astype(bool);red,green,blue=rgb.transpose(2,0,1)
    gold=(red>112)&(green>85)&(red>blue*1.27)&(green>blue*1.12)&roi
    tin=(np.minimum(np.minimum(red,green),blue)>110)&~gold&roi
    out=[]
    for style,mask in [('gold',gold),('tin',tin)]:
        for blob in islands(mask):
            if not 2<=len(blob)<=140:continue
            arr=np.asarray(blob);lo=arr.min(axis=0);hi=arr.max(axis=0);span=hi-lo+1
            if max(span)>15 or len(blob)/np.prod(span)<.32:continue
            u,v=arr.mean(axis=0);x,y=mapper(u,v)
            xa,ya=mapper(u+span[0],v);xb,yb=mapper(u,v+span[1])
            out.append([style,round(x,4),round(y,4),round(max(.12,abs(xb-x)),4),round(max(.12,abs(ya-y)),4)])
    marked[face]=out
    atlas=Image.new('RGB',(2048,1073),(39,42,39));a=ImageDraw.Draw(atlas)
    def uv(x,y):return ((11.5-y)/79.5*2047,((19.3-x) if face=='upper' else (x+19.3))/38.6*1072)
    for style,x,y,w,l in out:
        u,v=uv(x,y);wx=l/79.5*2048;hy=w/38.6*1073
        bounds=(u-wx/2,v-hy/2,u+wx/2,v+hy/2)
        if style=='gold':a.ellipse(bounds,fill=(189,153,77))
        else:a.rounded_rectangle(bounds,radius=min(3,wx/3,hy/3),fill=(162,166,163))
    # Bare copper around all four measured mounting holes.
    for pxy in pd_holes:
        x,y=bottom(*pxy);u,v=uv(x,y)
        a.rounded_rectangle((u-54,v-52,u+54,v+52),radius=15,fill=(179,147,78))
    atlas.save(assets/('board-'+face+'.png'),optimize=True)
    colors=np.asarray(atlas)
    copper=colors[:,:,0]>100
    packed=np.empty_like(colors);packed[:,:,0]=255
    packed[:,:,1]=np.where(copper,91,143);packed[:,:,2]=np.where(copper,191,0)
    Image.fromarray(packed).save(assets/('board-'+face+'-orm.png'),optimize=True)

print('Photo-derived lands by face:',{k:len(v) for k,v in marked.items()})


# Neutral tangent normals from a repeating fine polymer or rolled-sheet microfinish.
rng=np.random.default_rng(716)
for key,amp in [('polymer',.050),('metal',.060)]:
    field=rng.standard_normal((512,512))
    if key=='metal':
        field=sum(np.roll(field,k,axis=1) for k in range(9))/3
    else:
        field=(field+np.roll(field,1,0)+np.roll(field,1,1))/1.73
    dx=(np.roll(field,-1,1)-np.roll(field,1,1))*amp
    dy=(np.roll(field,-1,0)-np.roll(field,1,0))*amp
    normal=np.stack([-dx,dy,np.ones_like(dx)],axis=-1)
    normal/=np.linalg.norm(normal,axis=2,keepdims=True)
    Image.fromarray(((normal*.5+.5)*255+.5).astype('uint8')).save(assets/(key+'-normal.png'))
