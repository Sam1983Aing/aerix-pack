"""Make seamless physical-scale data maps for the RILL material library."""
from pathlib import Path
import numpy as np
from PIL import Image

DEST=Path(__file__).resolve().parents[1]/'blender/materials-v11'
SIZE=512
TILE_MM=12.8
freq=np.fft.fftfreq(SIZE)
x,y=np.meshgrid(freq,freq)
rng=np.random.default_rng(1107)


def noise(sx,sy):
    # A periodic Gaussian filter avoids borders on surfaces crossing a tile edge.
    white=np.fft.fft2(rng.normal(size=(SIZE,SIZE)))
    filtered=np.fft.ifft2(white*np.exp(-2*np.pi**2*(x*x*sx*sx+y*y*sy*sy))).real
    return (filtered-filtered.mean())/filtered.std()


def save(name,data):
    encoded=np.rint(np.clip(data,0,1)*255).astype(np.uint8)
    Image.fromarray(encoded).save(DEST/(name+'.png'),optimize=True)


def finish(name,height,roughness,metal):
    step=TILE_MM/SIZE
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))/(2*step)
    # PNG rows run downwards, tangent-space V points upwards.
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))/(2*step)
    norm=np.sqrt(1+dx**2+dy**2)
    save(name+'-normal',np.stack((-dx/norm,dy/norm,1/norm),axis=-1)*.5+.5)
    one=np.ones_like(height)
    save(name+'-mr',np.stack((one,roughness,one*metal),axis=-1))


if __name__=='__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    cells=np.tanh(noise(2.1,2.1)*1.3)
    fine=noise(.8,.8)
    finish('mold',.0060*cells+.0015*fine,
           .404+.014*cells+.012*noise(8,8)+.008*fine,0)
    soft=noise(3.8,3.8)
    finish('rubber',.006*soft+.0023*noise(1,1),.70+.041*np.tanh(soft)+.017*noise(9,9),0)
    turned=noise(27,.84)
    finish('turned',.0015*turned+.0005*noise(5,1.8),.335+.014*turned+.008*noise(32,4),1)
