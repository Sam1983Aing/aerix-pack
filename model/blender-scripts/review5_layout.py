"""Draw the review plates from the approved surface survey and source measurements."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
audit = json.loads((root / "measurements/review5-approved-exterior.json").read_text())
rows = audit["shell_sections_y_xmin_xmax_zmin_zmax"]
objects = audit["objects"]
S = 2
W, H = 1560, 1160
im = Image.new("RGB", (W * S, H * S), "#f7f6f1")
d = ImageDraw.Draw(im)
ink, muted, thin = "#142e33", "#526869", "#bac6bf"
shell, skin = "#e4e9e2", "#82958c"
nav, esc, bat, core, cool, cam = "#276854", "#3b7065", "#9b582d", "#305f81", "#536571", "#69557d"
def point(p):
    return tuple(round(v * S) for v in p)
def line(pts, color=thin, width=1):
    d.line([point(p) for p in pts], fill=color, width=round(width * S), joint="curve")
def txt(x, y, s, size, color=ink, bold=False, anchor="la"):
    name = "Arial Bold" if bold else "Arial"
    font = ImageFont.truetype(f"/System/Library/Fonts/Supplemental/{name}.ttf", size * S)
    d.text(point((x, y)), s, font=font, fill=color, anchor=anchor)
def poly(pts, fill, color=skin, width=2):
    d.polygon([point(p) for p in pts], fill=fill)
    line(pts + [pts[0]], color, width)
def box(pos, fill, outline, radius=4, width=2):
    d.rounded_rectangle([point(pos[:2]), point(pos[2:])], radius * S, fill=fill,
                        outline=outline, width=width * S)
def disk(x, y, r, fill, outline=None):
    d.ellipse([point((x-r,y-r)),point((x+r,y+r))],fill=fill,outline=outline,width=2*S)
def dash(a, b, color, width=2, period=13):
    from math import hypot
    dx, dy = b[0]-a[0], b[1]-a[1]
    dist = hypot(dx,dy)
    for start in range(0, int(dist), period):
        end=min(dist,start+period*.55)
        line([(a[0]+dx*v/dist, a[1]+dy*v/dist) for v in (start,end)], color, width)
def boundary(rect, color):
    l,t,r,b=rect
    for a,z in [((l,t),(r,t)),((r,t),(r,b)),((r,b),(l,b)),((l,b),(l,t))]:
        dash(a,z,color)
def title(x,y,k,name):
    txt(x,y,k,14,muted,True)
    txt(x,y+22,name,30,ink,True)
def legend_row(x,y,code,color,head,sub):
    disk(x+12,y+15,12,color)
    txt(x+12,y+15,code,14,"#ffffff",True,"mm")
    txt(x+36,y+2,head,20,ink,True)
    txt(x+36,y+29,sub,17,muted)
def marker(x,y,code,c):
    disk(x,y,13,c)
    txt(x,y,code,15,"white",True,"mm")

scale = 5.69
X = lambda y: 102+(y+73.5)*scale
Y = lambda x: 414-x*scale
Z = lambda z: 1026-z*scale
def profile(ordinate, low, high):
    return [(X(v[0]),ordinate(v[low])) for v in rows]+[(X(v[0]),ordinate(v[high])) for v in reversed(rows)]
def plan(y0,y1,w):
    return (X(y0),Y(w/2),X(y1),Y(-w/2))
def elev(y0,y1,z0,z1):
    return (X(y0),Z(z1),X(y1),Z(z0))
def fins(x0,x1,top,bottom):
    for x in range(round(x0),round(x1),10):
        line([(x,top),(x,bottom)],"#738690",2)

txt(65,34,"RILL   /   PRODUCT STUDIES",17,muted,True)
txt(1495,34,"INTERIOR     •     REVIEW 5",17,muted,True,"ra")
txt(62,75,"Inside the airframe",58,ink,True)
txt(65,151,"Component placement inside the approved V14c exterior",23,muted)
line([(65,197),(1495,197)])
line([(952,220),(952,1056)])

txt(65,218,"TOP  /  COVER REMOVED",16,muted,True)
poly(profile(Y,1,2),shell)
# The outline of the core is largely obscured by the pack when viewed from above.
box(plan(-66,9,38.7),"#efdfcd",bat,8)
boundary(plan(-69,8,36.5),core)
for a,b,w,color,fill,code in [(-63,-30,32,esc,"#bfdbce","A"),(-29,2,30,nav,"#c9dece","B")]:
    box(plan(a,b,w),fill,color,6)
    if code=="B":
        box(plan(-23,-5,18),"#e3e8ce",color,4)
    marker(X((a+b)/2),Y(0),code,color)
marker(X(5.5),Y(-13),"C",bat)
# Dashes identify the main board beneath the pack, outside the port edge.
line([(X(-69),Y(-14)),(91,490),(69,490)],core,2)
marker(70,490,"D",core)
line([(X(31),Y(0)),(X(43),Y(0))],cam,6)
box(plan(36,45,12),"#c4b9ce",cam,4)
box(plan(44,61.3,31.1),"#d1c7d9",cam,7)
box(plan(61.3,63.3,12),"#b4a6c0",cam,4)
marker(X(52),Y(0),"F",cam)
txt(92,593,"TAIL",13,muted,True)
txt(904,593,"NOSE  →",13,muted,True,"ra")
line([(65,639),(919,639)])

txt(65,659,"SIDE  /  LONGITUDINAL PROJECTION",16,muted,True)
poly(profile(Z,3,4),shell)
box(elev(-66,9,25.66,45.26),"#efdfcd",bat,5)
for lo,hi,color,code in [(-63,-30,esc,"A"),(-29,2,nav,"B")]:
    # Heights are indicative. Keep PCB edge profiles schematic.
    box(elev(lo,hi,46.1,48),"#bdd7c6",color,3)
    if code=="B":
        box(elev(-23,-5,48,50),"#dce4c8",nav,2)
    marker(X((lo+hi)/2),Z(47.1),code,color)
box(elev(-69,8,19.5,21),"#bfd0de",core,2)
box(elev(-67,7,15.7,19.4),"#c5cdd0",cool,3)
fins(X(-40),X(4),Z(19),Z(16.0))
disk(X(-51),Z(16.7),4.5,ink)
box(elev(36,45,24,34),"#c4b9ce",cam,5)
box(elev(44,61.3,9.5,29.3),"#d1c7d9",cam,5)
box(elev(61.3,63.3,13.4,25.4),"#b4a6c0",cam,2)
marker(X(52),Z(19.5),"F",cam)
marker(X(-28),Z(35),"C",bat)
line([(X(-62),Z(20.3)),(125,916),(80,916)],core,2)
marker(82,916,"D",core)
line([(X(-15),Z(16)),(X(-15)+40,971),(X(-15)+100,971)],cool,2)
marker(X(-15)+102,971,"E",cool)
line([(X(-51),Z(16)),(X(-51),979)],ink,2)
txt(X(-51),990,"Downward optics",16,muted,False,"ma")
line([(X(-45),Z(36)),(106,Z(36))],bat,2)
line([(116,Z(36)-5),(106,Z(36)),(116,Z(36)+5)],bat,2)

title(995,217,"COMPONENT KEY","From roof to belly")
legend_row(997,289,"A",esc,"Motor-control board","Aft roof, four motor harnesses")
legend_row(997,358,"B",nav,"Navigation and inertial module","Above the bay, ceramic patch faces up")
legend_row(997,427,"C",bat,"Removable flight battery","Slides aft along the central bay")
legend_row(997,496,"D",core,"Core board","Beneath the bay, ports at the tail")
legend_row(997,565,"E",cool,"Finned heat spreader","Between core board and belly cover")
legend_row(997,634,"F",cam,"Camera and gimbal","Suspended in the nose opening")
line([(996,708),(1495,708)])
txt(996,733,"ARM ROUTING  /  UNFOLDED PLAN",14,muted,True)
# Inset uses native hinge and motor bounds for all four arms.
def centre(name):
    lo,hi=objects[name]["bounds_mm"]
    return [(a+b)/2 for a,b in zip(lo,hi)]
ix,iy,sc=1120,893,.99
P=lambda x,y:(ix+x*sc,iy-y*sc)
poly([P(v[1],v[0]) for v in rows]+[P(v[2],v[0]) for v in reversed(rows)],shell)
for key in ("FL","FR","RL","RR"):
    pivot=centre("Hinge.pin."+key)
    motor=centre("Motor."+key)
    a,b=P(*pivot[:2]),P(*motor[:2])
    line([a,b],skin,9)
    line([a,b],bat,2)
    disk(*b,7,skin)
    if key.startswith("F"):
        dash((ix,iy+15),(a[0],a[1]-4),core,2,6)
        line([(a[0],a[1]-4),(b[0],b[1]-4)],core,2)
        disk(*b,3,core)
txt(ix,797,"NOSE",12,muted,True,"ma")
txt(1250,816,"Four motors",18,ink,True)
txt(1250,845,"Three wires per arm lead",15,muted)
txt(1250,866,"to the motor-control board.",15,muted)
txt(1250,910,"Two antennas",18,ink,True)
txt(1250,939,"One in each front foot.",15,muted)
txt(1250,960,"Coax returns to the core.",15,muted)
line([(65,1059),(1495,1059)])
txt(65,1080,"Shell profiles come from the Blender mesh. Board footprints are photo-scaled. Mounting heights and routing are schematic.",18,ink)
txt(65,1112,"Battery 75 × 38.7 × 19.6 mm. Interior clearances, wall thickness and screw-boss depths remain open.",17,muted)
dest=root/"references/interior-layout.png"
im.resize((W*3//2,H*3//2),Image.Resampling.LANCZOS).save(dest,optimize=True)
