"""Build the Review 4 reference pairs and archive identically framed before/after shots."""
from pathlib import Path
from shutil import copy2
import sys
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parents[1]
version=sys.argv[1] if len(sys.argv)>1 else 'v02'
assert version in ('v02','v03','v04','v05','v06','v07','v08','v09','v10','v11','v12','v13','v14','v14a','v14b','v14c')
before,feature,prior,detail={
    'v02':('v01','shell','grey blockout','shell'),
    'v03':('v02','arms and hinges','Basalt shell','arm-hinge'),
    'v04':('v03','motors and propellers','Basalt arms','motor-propeller'),
    'v05':('v04','gimbal and optics','Basalt motors','gimbal'),
    'v06':('v05','arm proportions','Basalt gimbal','arm'),
    'v07':('v06','arm shoulders and flares','Basalt arms','rear-arm'),
    'v08':('v07','Mini 2 remodel','Basalt','nose-shoulder'),
    'v09':('v08','landing gear','RILL','front-gear'),
    'v10':('v09','centred camera','RILL','camera'),
    'v11':('v10','materials','RILL','material'),
    'v12':('v11','vents and hatch','RILL','hatch'),
    'v13':('v12','front joints','RILL','camera-sides'),
    'v14':('v13','studio lighting','neutral studio','lens'),
    'v14c':('v14b','rear corners','sidewall finish','lens'),
    'v14b':('v14a','sidewall finish','edge polish','lens'),
    'v14a':('v14','edge polish','studio lighting','lens')
}[version]
source=root/'concepts/02-basalt'
renders=root/'renders'/version
dest=renders/'comparisons'
archive=root/'teach/shots'/version
dest.mkdir(exist_ok=True)
archive.mkdir(parents=True,exist_ok=True)
views=('three-quarter','front','side','top','back')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',28)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)


def pair(paths,labels,width=1088):
    h=width*9//16
    sheet=Image.new('RGB',(2*width+6,h+58),'#f1f1ed')
    draw=ImageDraw.Draw(sheet)
    for x,path,label in zip((0,width+6),paths,labels):
        with Image.open(path) as im:
            sheet.paste(im.convert('RGB').resize((width,h),Image.Resampling.LANCZOS),(x,58))
        draw.text((x+19,15),label,fill='#202320',font=font)
    return sheet


for view in views:
    ref=source/'three-quarter.png' if view=='three-quarter' else source/'orthographic'/f'{view}.png'
    result=renders/f'{version}-unfolded-{view}.png'
    label=view.replace('-',' ').capitalize()
    if version in ('v08','v09','v10','v11','v12','v13','v14','v14a','v14b','v14c'): ref=root/f'renders/{before}/{before}-unfolded-{view}.png'
    ref_label={'v08':'V07 Basalt','v09':'V08 RILL','v10':'V09 RILL','v11':'V10 RILL','v12':'V11 RILL','v13':'V12 RILL','v14':'V13 neutral studio','v14a':'V14 studio','v14b':'V14a edge polish','v14c':'V14b sidewalls'}.get(version,'Basalt reference')
    ref_file=before if version in ('v08','v09','v10','v11','v12','v13','v14','v14a','v14b','v14c') else 'basalt'
    sheet=pair([ref,result],[ref_label+'  /  '+label,version.upper()+' '+feature+'  /  '+label])
    sheet.save(dest/f'{version}-vs-{ref_file}-{view}.jpg',quality=94,subsampling=0)
    for pose in ('unfolded','folded'):
        for stage,when in ((before,'before'),(version,'after')):
            shot=root/f'renders/{stage}/{stage}-{pose}-{view}.png'
            with Image.open(shot) as im: assert im.size==(1920,1080)
            copy2(shot,archive/f'{when}-{shot.name}')
closeup=f'{version}-{detail}-closeup.png'
copy2(renders/closeup,archive/('after-'+closeup))
# One compact inspection sheet per pose for the video edit.
for pose in ('unfolded','folded'):
    board=Image.new('RGB',(1292,5*382+52),'#f1f1ed')
    draw=ImageDraw.Draw(board)
    draw.text((12,10),before.upper()+' '+prior,fill='#202320',font=font)
    draw.text((660,10),version.upper()+(' ' if version in ('v08','v09','v10','v11','v12','v13','v14','v14a','v14b','v14c') else ' Basalt ')+feature,fill='#202320',font=font)
    for i,view in enumerate(views):
        y=52+i*382
        for x,stage in ((0,before),(652,version)):
            path=root/f'renders/{stage}/{stage}-{pose}-{view}.png'
            with Image.open(path) as im:
                board.paste(im.convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(x,y+22))
            draw.text((x+9,y),view.replace('-',' ').capitalize(),fill='#343832',font=small)
    board.save(archive/f'{before}-{version}-{pose}.jpg',quality=90)

summary=Image.new('RGB',(1000,len(views)*309),'#f1f1ed')
for i,view in enumerate(views):
    with Image.open(dest/f'{version}-vs-{ref_file}-{view}.jpg') as sheet:
        sheet.thumbnail((1000,309),Image.Resampling.LANCZOS)
        summary.paste(sheet,(0,i*309))
summary.save(dest/f'{version}-reference-sheet.jpg',quality=92)

if version=='v03':
    # Common normalized crop from the locked three-quarter composition.
    # It exposes one complete arm where the propeller clears its shoulder.
    crop=(.595,.303,.893,.54)
    large=Image.new('RGB',(2054,540),'#f1f1ed')
    draw=ImageDraw.Draw(large)
    for x,path,label in ((0,source/'three-quarter.png','Basalt reference'),
                         (1030,renders/'v03-unfolded-three-quarter.png','V03 arm and hinge')):
        with Image.open(path) as im:
            w,h=im.size
            bounds=tuple(round(f*n) for f,n in zip(crop,(w,h,w,h)))
            height=round((bounds[3]-bounds[1])*1024/(bounds[2]-bounds[0]))
            resized=im.convert('RGB').crop(bounds).resize((1024,height),Image.Resampling.LANCZOS)
            large.paste(resized,(x,55))
        draw.text((x+18,13),label,fill='#202320',font=font)
    large.crop((0,0,2054,height+55)).save(dest/'v03-arm-detail-vs-basalt.jpg',quality=94)

if version=='v04':
    copy2(renders/'v04-rear-attachments-closeup.png',archive/'after-v04-rear-attachments-closeup.png')
    # Both top views use the very same 500 mm orthographic camera. Crop in world space.
    paths=[source/'orthographic/top.png',renders/'v04-unfolded-top.png']
    sheet=Image.new('RGB',(1158,1050),'#f1f1ed')
    draw=ImageDraw.Draw(sheet)
    for x,path,label in zip((0,582),paths,('Basalt top reference','V04 shell')):
        with Image.open(path) as im:
            w,h=im.size
            crop=im.crop(tuple(round(f*n) for f,n in zip((.40,.188,.60,.758),(w,h,w,h))))
            sheet.paste(crop.convert('RGB').resize((576,round(576*crop.height/crop.width)),Image.Resampling.LANCZOS),(x,59))
        draw.text((x+16,14),label,fill='#202320',font=font)
    sheet.crop((0,0,1158,59+round(576*crop.height/crop.width))).save(dest/'v04-shell-top-vs-basalt.jpg',quality=94)

    pair([archive/'before-v03-rear-attachments-closeup.png',renders/'v04-rear-attachments-closeup.png'],
         ['V03 underside','V04 underside'],width=960).save(dest/'v03-v04-rear-attachments.jpg',quality=93)

if version=='v05':
    pair([archive/'before-v04-gimbal-closeup.png',renders/'v05-gimbal-closeup.png'],
         ['V04 camera','V05 gimbal and optics'],width=960).save(dest/'v04-v05-gimbal.jpg',quality=94)
    # Normalize the crop to the full front view to preserve angular size in both images.
    paths=(source/'orthographic/front.png',renders/'v05-unfolded-front.png')
    board=Image.new('RGB',(1110,525),'#f1f1ed')
    draw=ImageDraw.Draw(board)
    for x,path,label in zip((0,558),paths,('Basalt front reference','V05 camera')):
        with Image.open(path) as im:
            w,h=im.size
            rect=tuple(round(v*dim) for v,dim in zip((.451,.425,.549,.572),(w,h,w,h)))
            crop=im.crop(rect)
            board.paste(crop.resize((552,round(552*crop.height/crop.width)),Image.Resampling.LANCZOS),(x,57))
        draw.text((x+14,13),label,font=font,fill='#202320')
    board.save(dest/'v05-lens-vs-basalt.jpg',quality=95)

if version=='v06':
    # Place the two requested views together and show the same unobscured arm
    # at matching magnification across concept, prior model and new model.
    panels=[Image.open(dest/f'v06-vs-{ref_file}-{view}.jpg') for view in ('top','three-quarter')]
    board=Image.new('RGB',(panels[0].width,sum(p.height for p in panels)),'#f1f1ed')
    y=0
    for panel in panels:
        board.paste(panel,(0,y))
        y+=panel.height
        panel.close()
    board.save(dest/'v06-top-and-three-quarter.jpg',quality=93)
    crop=(.595,.303,.893,.540)
    detail=Image.new('RGB',(1602,300),'#f1f1ed')
    draw=ImageDraw.Draw(detail)
    for i,(label,path) in enumerate([('Basalt reference',source/'three-quarter.png'),
                                    ('V05',root/'renders/v05/v05-unfolded-three-quarter.png'),
                                    ('V06',renders/'v06-unfolded-three-quarter.png')]):
        with Image.open(path) as im:
            w,h=im.size
            part=im.crop(tuple(round(f*n) for f,n in zip(crop,(w,h,w,h))))
            height=round(part.height*530/part.width)
            x=i*536
            detail.paste(part.convert('RGB').resize((530,height),Image.Resampling.LANCZOS),(x,51))
            draw.text((x+12,10),label,font=font,fill='#202320')
    detail.crop((0,0,1602,51+height)).save(dest/'v06-front-arm-detail.jpg',quality=95)

if version=='v10':
    sheet=pair([archive/'before-v09-camera-closeup.png',renders/'v10-camera-closeup.png'],
               ['V09  /  camera face','V10  /  centered optics'],width=960)
    sheet.save(dest/'v09-v10-camera-alignment.jpg',quality=95,subsampling=0)
    copy2(dest/'v09-v10-camera-alignment.jpg',archive/'v09-v10-camera-alignment.jpg')

if version=='v11':
    # Material, framing and illumination can be reviewed independently in each pair.
    for subject,old,new in [
        ('motor',archive/'before-v10-material-closeup.png',renders/'v11-material-closeup.png'),
        ('lens',root/'renders/v10/v10-camera-closeup.png',renders/'v11-camera-closeup.png')]:
        sheet=pair([old,new],['V10  /  '+subject,'V11  /  '+subject],width=960)
        filename='v10-v11-'+subject+'.jpg'
        sheet.save(dest/filename,quality=95,subsampling=0)
        copy2(dest/filename,archive/filename)
    copy2(root/'renders/v10/v10-camera-closeup.png',archive/'before-v10-camera-closeup.png')
    copy2(renders/'v11-camera-closeup.png',archive/'after-v11-camera-closeup.png')

if version=='v12':
    for name,label in [('hatch-closeup','Side vent and hatch'),('folded-hatch','Folded hatch')]:
        old=archive/f'before-v11-{name}.png'
        new=renders/f'v12-{name}.png'
        sheet=pair([old,new],['V11  /  '+label,'V12  /  '+label],width=960)
        filename=f'v11-v12-{name}.jpg'
        sheet.save(dest/filename,quality=95,subsampling=0)
        copy2(dest/filename,archive/filename)
        copy2(new,archive/('after-'+new.name))

if version=='v13':
    for name,label in [('camera-sides','Camera side covers'),('front-root-left','Left front hinge'),('front-root-right','Right front hinge')]:
        old=archive/f'before-v12-{name}-closeup.png'
        new=renders/f'v13-{name}-closeup.png'
        filename=f'v12-v13-{name}.jpg'
        pair([old,new],['V12  /  '+label,'V13  /  '+label],width=960).save(dest/filename,quality=95,subsampling=0)
        copy2(dest/filename,archive/filename)
        copy2(new,archive/('after-'+new.name))
    with Image.open(dest/'v12-v13-front-root-left.jpg') as left, Image.open(dest/'v12-v13-front-root-right.jpg') as right:
        hinges=Image.new('RGB',(left.width,left.height+right.height+6),'#f1f1ed')
        hinges.paste(left)
        hinges.paste(right,(0,left.height+6))
        hinges.save(dest/'v12-v13-front-hinges.jpg',quality=95,subsampling=0)

if version=='v14':
    shots = [
        ('unfolded-three-quarter','Unfolded','v13-unfolded-three-quarter.png','v14-unfolded-three-quarter.png'),
        ('folded-three-quarter','Folded','v13-folded-three-quarter.png','v14-folded-three-quarter.png'),
        ('lens','Lens','v13-camera-sides-closeup.png','v14-lens-closeup.png')
    ]
    for name,label,old_file,new_file in shots:
        old=root/'renders/v13'/old_file
        new=renders/new_file
        sheet=pair([old,new],['V13 neutral studio  /  '+label,'V14 studio lighting  /  '+label])
        file='v13-v14-'+name+'.jpg'
        sheet.save(dest/file,quality=96,subsampling=0)
        copy2(dest/file,archive/file)
    copy2(root/'renders/v13/v13-camera-sides-closeup.png',archive/'before-v13-lens-closeup.png')
    review=Image.new('RGB',(1552,3*478),'#f1f1ed')
    for i,(name,label,_,_) in enumerate(shots):
        with Image.open(dest/('v13-v14-'+name+'.jpg')) as im:
            im.thumbnail((1552,478),Image.Resampling.LANCZOS)
            review.paste(im,(0,i*478))
    review.save(dest/'v13-v14-studio-lighting.jpg',quality=94,subsampling=0)
    copy2(dest/'v13-v14-studio-lighting.jpg',archive/'v13-v14-studio-lighting.jpg')

if version=='v14a':
    panels=[]
    for name,label in [('side-contour','Lower side contour'),('lower-cheek','Front underside'),('front-trim','Camera trim')]:
        old=archive/f'before-v14-{name}.png'
        new=renders/f'v14a-{name}.png'
        board=pair([old,new],['V14  /  '+label,'V14a  /  '+label],width=896)
        board.save(dest/f'v14-v14a-{name}.jpg',quality=95,subsampling=0)
        copy2(new,archive/('after-'+new.name))
        panels.append(board)
    summary=Image.new('RGB',(panels[0].width,3*panels[0].height+12),'#f1f1ed')
    for i,board in enumerate(panels):
        summary.paste(board,(0,i*(board.height+6)))
    summary.save(dest/'v14-v14a-edge-polish.jpg',quality=95,subsampling=0)
    copy2(dest/'v14-v14a-edge-polish.jpg',archive/'v14-v14a-edge-polish.jpg')

if version in ('v14b','v14c'):
    parts = []
    views = ([('left-wall','Left side'), ('right-wall','Right side'), ('belly','Underside')] if version=='v14b'
             else [('left-corner','Left rear corner'), ('right-corner','Right rear corner'), ('rear-return','Rear hatch')])
    for name, label in views:
        old = archive/f'{before}-{name}.png'
        new = renders/f'{version}-{name}.png'
        board = pair([old,new], [f'{before.capitalize()}  /  {label}',f'{version.capitalize()}  /  {label}'],width=960)
        board.save(dest/f'{before}-{version}-{name}.jpg',quality=94,subsampling=0)
        copy2(new, archive/('after-'+new.name))
        parts.append(board)
    sheet = Image.new('RGB',(parts[0].width,3*parts[0].height+12),'#f1f1ed')
    for i, board in enumerate(parts):
        sheet.paste(board,(0,i*(board.height+6)))
    filename = 'v14b-sidewall-review.jpg' if version=='v14b' else 'v14c-rear-corners-review.jpg'
    sheet.save(dest/filename,quality=94,subsampling=0)
    copy2(dest/filename,archive/filename)
