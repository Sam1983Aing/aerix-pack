"""Prepare the private Mini 2 V09 comparison and the two matched teaching close-ups."""
from pathlib import Path
from shutil import copy2
from PIL import Image,ImageDraw,ImageFont
import sys

root=Path(__file__).resolve().parents[1]
private=root/'references/real/mini-2'
renders=root/'renders/v09'
archive=root/'teach/shots/v09'
font_file='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(font_file,26)
caption=ImageFont.truetype(font_file,18)
W=840
H=473
header=68


def photo_board(version='v09'):
    board=Image.new('RGB',(2*W+4,2*(H+header)+6),'#f4f4f1')
    d=ImageDraw.Draw(board)
    for index,(src,pose,ref_note,render_note) in enumerate([
        ('open-right-gigazine.jpg','open-side','Open side · GIGAZINE photograph','Open side · aligned to four motor centres'),
        ('folded.jpg','folded','Folded three-quarter · DJI photograph','Folded three-quarter · approximate camera match')]):
        y=index*(H+header+6)
        with Image.open(private/src) as f:
            ref=f.convert('RGB')
        with Image.open(private/f'{version}-{pose}-render.png') as f:
            model=f.convert('RGBA')
        if pose=='folded':
            ref=ref.crop((273,398,978,891))
            model=model.crop(model.getchannel('A').getbbox())
        for x,img,title,note in [(0,ref,'DJI Mini 2',ref_note),(W+4,model,'RILL '+version.upper(),render_note)]:
            d.text((x+18,y+5),title,font=font,fill='#242821')
            d.text((x+18,y+40),note,font=caption,fill='#454940')
            bg=Image.new('RGB',(W,H),'white')
            if pose=='folded':
                img.thumbnail((W-40,H-34),Image.Resampling.LANCZOS)
            else:
                img=img.resize((W,H),Image.Resampling.LANCZOS)
            bg.paste(img,((W-img.width)//2,(H-img.height)//2),img if img.mode=='RGBA' else None)
            board.paste(bg,(x,y+header))
    name={'v09':'v09-landing-gear-comparison.jpg','v11':'v11-materials-comparison.jpg','v12':'v12-vents-hatch-comparison.jpg','v13':'v13-front-joints-comparison.jpg','v14':'v14-studio-lighting-comparison.jpg','v14a':'v14a-edge-polish-comparison.jpg','v14b':'v14b-sidewall-comparison.jpg','v14c':'v14c-rear-corners-comparison.jpg'}[version]
    board.save(private/name,quality=93,subsampling=0)


def closeups():
    sheet=Image.new('RGB',(2*W+4,2*(H+header)+6),'#f4f4f1')
    for i,part in enumerate(('front','rear')):
        y=i*(H+header+6)
        before=archive/f'before-v08-{part}-gear-closeup.png'
        after=renders/f'v09-{part}-gear-closeup.png'
        copy2(after,archive/('after-'+after.name))
        for x,stage,path in [(0,'V08',before),(W+4,'V09',after)]:
            ImageDraw.Draw(sheet).text((x+18,y+17),stage+(' · Front strut' if i==0 else ' · Rear foot'),font=font,fill='#242821')
            with Image.open(path) as im:
                assert im.size==(1920,1080)
                sheet.paste(im.convert('RGB').resize((W,H),Image.Resampling.LANCZOS),(x,y+header))
    dest=renders/'comparisons/v08-v09-landing-gear.jpg'
    sheet.save(dest,quality=93,subsampling=0)
    copy2(dest,archive/dest.name)

if __name__=='__main__':
    version=next((arg for arg in sys.argv[1:] if arg in ('v11','v12','v13','v14','v14a','v14b','v14c')),'v09')
    photo_board(version)
    if version=='v09' and '--photos-only' not in sys.argv:
        closeups()
