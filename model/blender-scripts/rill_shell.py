"""Original compact RILL fuselage stations. All coordinates are millimeters."""
from mathutils import Vector

# Longitudinal stations for the top shell. Width is greatest at the forward
# hinge fairing. The shoulders then recede sharply alongside the battery.
stations = [
# y, half-breadth, crown, belly, sweep at outer corner
(-73.5,22.2,44,13,4.1),(-72.7,23.5,45.2,12.0,4.1),(-70,25.2,47.4,10.8,3.3),
(-64,27.1,48.7,10,1.7),(-60,26.9,49.5,9.5,.65),(-59.2,26.8,49.65,9.4,.45),
(-58.7,26.76,49.72,9.4,.43),(-55,26.4,50.3,9.1,0),(-49,25,51,9,0),
(-43,23.6,51.5,9.2,0),(-37,22.9,52,9.5,0),(-29,22.9,52.5,10,0),
(-12,23.2,53.3,11,0),(-6,23.6,53.6,11.8,0),(-3,24.3,53.7,12,0),
(0,26.9,53.8,12.7,0),(4,30.8,54,13.3,0),(6.5,32.9,54.1,13.7,0),
(9,33.0,54.1,14.3,0),(18,32.6,54.05,16.6,0),(28,31.75,53.7,25,0),
(34,31.15,53.3,32.5,-.3),(41,30.5,52.6,33.3,-1.4),(49,30,51.6,33.7,-4),
(57,29.7,50.4,34.2,-9.3),(62.9,29.3,49.3,35,-13.8),
(64.1,28.95,49.1,35.5,-14.6),(64.5,28.55,48.8,36.2,-14.8)]
U = [-1,-.97,-.91,-.86,-.82,-.77,-.72,-.67,-.62,-.56,-.50,-.42,-.32,-.24,-.18,-.12,0,
      .12,.18,.24,.32,.42,.50,.56,.62,.67,.72,.77,.82,.86,.91,.97,1]
T = [0,.025,.08,.16,.22,.30,.40,.50,.58,.65,.70,.74,.77,.785,.81,.88,.94,.98,1]

def ramp(a,b,x):
    f=min(1,max(0,(x-a)/(b-a)))
    return f*f*(3-2*f)

def skin(row,u,v):
    y,w,c,b,s = row
    t=abs(u)
    # Lower sidewalls draw in under the upper shoulders to give the rear arms a stow channel.
    w *= (1-.14*(1-v)**1.7-.040*v**7)
    shoulder = .67
    chine = max(0,(t-shoulder)/(1-shoulder))
    top = c-.64*t*t-5.05*chine**1.11
    bottom = b+2.6*t*t+1.15*chine
    # Form the walls of the gimbal bay directly in the underside skin.
    length = min(1,max(0,(y-18)/13),max(0,(58-y)/9))
    cheek = min(1,max(0,(t-.53)/.23))
    cheek = cheek*cheek*(3-2*cheek)
    bottom -= length*cheek*min(22,max(0,b-10.6))
    # Hold the edge of the flat crown on two longitudinal lines, while the
    # outer shoulder width follows the changing silhouette at each station.
    crest=min(18.4,.83*w)
    mapped=(crest*t/shoulder if t<=shoulder else crest+(w-crest)*(t-shoulder)/(1-shoulder))
    x=(1 if u>=0 else -1)*(w*t+(mapped-w*t)*v**3)
    yy=y+s*(.14*t*t+.86*max(0,(t-.50)/.50)**1.25)
    if y>54: yy-=(1-v)**1.7*2.6*(y-54)/10.5
    if y<-70: yy+=(1-v)*.8
    z=bottom+(top-bottom)*v
    # Mould the upper and lower stow channels into the original surface grid.
    # The upper lip retains the overhead planform above the front sleeve.
    upper=ramp(-13,1,yy)*(1-ramp(24,32,yy))*ramp(31.0,34.5,z)*(1-ramp(45.7,48.65,z))
    lower_band=ramp(-66,-55,yy)*(1-ramp(20,33,yy))*(1-ramp(23.0,30.5,z))
    inner=18.1+3.7*ramp(-36,-15,yy)
    recess=max(upper*max(0,w-23.3),lower_band*max(0,w-inner))
    x-=u*recess*t**1.6
    haunch=ramp(-55.7,-50.7,yy)*(1-ramp(-49,-35,yy))
    x+=u*t**2*haunch*5.8*ramp(22,30,z)*(1-ramp(34,40,z))
    motor_channel=ramp(-60,-53,yy)*(1-ramp(-39,-33,yy))*ramp(36,40,z)
    x-=u*t**2*motor_channel*3.3
    return Vector((x,yy,z))


