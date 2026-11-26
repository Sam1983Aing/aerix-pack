"""Frame the actual service photographs around matching visible landmarks."""
import math,sys,json,os,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
revision=sys.argv[1] if len(sys.argv)>1 else 'v17'
assert revision in ('v17','v18')
if revision=='v17':
    from v17_views import views
else:
    from v18_reference import views,matrices,photos,project
root=Path(__file__).resolve().parents[1]
private=root/'references/real/interior'/revision;renders=root/'renders'/revision
web=root/'viewer/review7'/revision;shots=root/'teach/shots'/revision;size=(1220,842)
# Point pairs are in the unaltered photo pixel coordinates. Choose a matched
# camera crop and uniform scale; retain the donor's relative part proportions.
landmarks={
 'gimbal':([(16.36,51.5,19.4),(-16.36,51.5,19.4)],[(259,637),(738,647)]),
 'camera':([(9.07,48.37,25.45),(-9.03,48.37,25.52)],[(313,208),(879,201)]),
 'carrier':([(-9.6,45,45.44),(9.6,45,45.44)],[(1290,971),(2543,1265)])}
def basis(cfg):
    d=np.array(cfg['dir'],dtype=float);d/=np.linalg.norm(d)
    r=np.cross(cfg['up'],d);r/=np.linalg.norm(r)
    return r,np.cross(d,r)
def reference(name,cfg):
    im=Image.open(private/(cfg['ref']+'.jpg')).convert('RGB')
    r,u=basis(cfg);pts,pixels=landmarks[name]
    d=np.array(pts)-np.array(cfg['target'])
    place=np.stack([d@r,-d@u],axis=1)
    scale=np.linalg.norm(np.subtract(*pixels))/np.linalg.norm(np.subtract(*place))
    ctr=np.mean(pixels,axis=0)-scale*np.mean(place,axis=0)
    ref_width=scale*cfg['width'];fac=ref_width/size[0]
    a=ctr[0]-ref_width/2;b=ctr[1]-fac*size[1]/2
    # Keep the white studio surroundings if the fitted crop extends past a paper edge.
    fill=(255,255,255) if name!='carrier' else (197,198,195)
    image=im.transform(size,Image.Transform.AFFINE,(fac,0,a,0,fac,b),Image.Resampling.BICUBIC,fillcolor=fill)
    return image,{'source':cfg['ref']+'.jpg','landmark_source_pixels':pixels,'model_landmarks_mm':pts,
                  'source_pixels_per_model_mm':float(scale),'source_crop_xywh':[float(a),float(b),float(ref_width),float(fac*size[1])]}
def board_reference(key,cfg):
    # Transform the filing image into the orthographic camera plane using the
    # same registered board features used to position the new geometry.
    source=Image.open(private.parent/photos[key]).convert('RGB')
    r,u=basis(cfg)
    scale=cfg['width']/size[0]
    a=np.identity(3);a[:2,0]=r[:2]*scale;a[:2,1]=-u[:2]*scale
    a[:2,2]=np.array(cfg['target'][:2])-a[:2,0]*size[0]/2-a[:2,1]*size[1]/2
    tf=np.linalg.inv(matrices[key]) @ a;tf/=tf[2,2]
    fitted=source.transform(size,Image.Transform.PERSPECTIVE,tf.flatten()[:8],Image.Resampling.BICUBIC,fillcolor=(224,219,204))
    return fitted,{'source':photos[key],'source_pixels_to_aircraft_xy_mm':matrices[key].tolist(),
             'destination_pixels_to_source':tf.tolist(),'camera_width_mm':cfg['width']}

def link(dest,path):
    if not dest.exists():dest.symlink_to(os.path.relpath(path,dest.parent))
def font(n,bold=False):return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf',n)
report={}
labels={'gimbal':'Pitch supports aligned. The RILL lead follows its installed route.',
        'carrier':'Front damper stations aligned. The RILL carrier retains the four V16 suspension locations.',
        'camera':'Board eyelets aligned. The RILL glass, iris and optical axis retain their approved geometry.'}
if revision=='v18':
    labels={'esc':'Power face with the four groups of three motor solder joints.',
            'esc-back':'Reverse face with the four square packages and the installed battery header.',
            'gps':'Antenna face registered to the four V17 mounting holes.',
            'gps-back':'Shield face with its formed cover, pressings and ribbon socket.'}
for k,cfg in views.items():
    ref,report[k]=(board_reference if revision=='v18' else reference)(k,cfg)
    pic=private/(k+'-ref.jpg');ref.save(pic,quality=95);link(web/pic.name,pic)
    render=Image.open(renders/(k+'.png')).convert('RGBA')
    mat=Image.new('RGBA',size,'#c1c3bd');mat.alpha_composite(render)
    plate=Image.new('RGB',(1920,861),'#f0f1eb');d=ImageDraw.Draw(plate)
    d.text((40,19),cfg['title'],font=font(40,True),fill='#24342c')
    d.text((40,83),cfg['source'],font=font(21),fill='#43534d')
    d.text((980,83),'RILL '+revision.upper()+' · Blender',font=font(21),fill='#43534d')
    for x,picdata in [(40,ref),(980,mat.convert('RGB'))]:plate.paste(picdata.resize((900,621),Image.Resampling.LANCZOS),(x,130))
    d.text((40,791),labels[k],font=font(21),fill='#41514b')
    jpg=private/(k+'-comparison.jpg');plate.save(jpg,quality=94);link(web/jpg.name,jpg)
    link(web/(k+'.png'),renders/(k+'.png'));shutil.copyfile(renders/(k+'.png'),shots/(k+'.png'))
(root/'measurements'/(revision+'-photo-registration.json')).write_text(json.dumps(report,indent=2)+'\n')

