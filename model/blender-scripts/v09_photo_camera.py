"""Estimate the side-photo camera from the four deployed motor centres, in mm and pixels."""
from math import sin, cos, sqrt
import numpy as np

rear_y=39.7-sqrt(213**2-171.5**2)
points=np.array([[88.4,39.7,53.6],[-88.4,39.7,53.6],[83.1,rear_y,29.9],[-83.1,rear_y,29.9]])
photo=np.array([[977,154],[574,135],[125,401],[142,253]])
W,H=1200,676


def axes(p):
    az,el,roll=p[3:6]
    forward=-np.array([cos(az)*cos(el),sin(az)*cos(el),sin(el)])
    right=np.cross(forward,[0,0,1])
    right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    return right*cos(roll)+up*sin(roll), up*cos(roll)-right*sin(roll),forward


def residuals(p):
    right,up,forward=axes(p)
    delta=points-p[:3]
    uv=np.c_[delta@right,-delta@up]*p[6]/(delta@forward)[:,None]+[W/2,H/2]
    return (uv-photo).flatten()


def solve():
    # Damped least squares with numerical derivatives of the perspective projection.
    p=np.array([235.,-75.,73.,-.35,.19,0,1000.])
    steps=np.array([.005,.005,.005,1e-5,1e-5,1e-5,.01])
    for _ in range(60):
        r=residuals(p)
        J=np.column_stack([(residuals(p+e)-residuals(p-e))/(2*step) for e,step in zip(np.diag(steps),steps)])
        dp=np.linalg.lstsq(J,-r,rcond=None)[0]
        for scale in (1,.5,.25,.125,.0625,.03125):
            trial=p+dp*scale
            if trial[6]>0 and np.linalg.norm(residuals(trial))<np.linalg.norm(r):
                p=trial
                break
        else:
            break
    return p

if __name__=='__main__':
    p=solve()
    print('Camera position, angles and focal length',p)
    print('Image residuals',residuals(p))
