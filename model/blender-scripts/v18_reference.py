"""Board registration in aircraft millimetres, with landmarks in original photo pixels."""
import numpy as np

def projective(pixels, targets):
    a=[];b=[]
    for (u,v),(x,y) in zip(pixels,targets):
        a.extend(((u,v,1,0,0,0,-u*x,-v*x),(0,0,0,u,v,1,-u*y,-v*y)));b.extend((x,y))
    return np.append(np.linalg.lstsq(a,b,rcond=None)[0],1).reshape(3,3)

def project(matrix, u, v):
    x,y,w=matrix @ (u,v,1)
    return float(x/w),float(y/w)

# ESC face is registered on the measured 32.5 mm transverse by 32 mm
# longitudinal envelope. The six installed contact tips remain independent datums.
esc_corners=[(222,111),(580,98),(595,439),(212,441)]
esc=projective(esc_corners,[(16.25,-26.35),(16.25,-58.35),(-16.25,-58.35),(-16.25,-26.35)])
esc_holes=[(249,268),(539,168),(549,366)]
# The reverse preserves left/right in the photo, with the white bushing now above.
esc_back_marks=[(228,228),(509,327),(500,144),(524,117),(208,89),(196,380),(478,88),(493,393)]
esc_front_marks=esc_holes+[(577,400),(215,435),(223,116),(529,436),(515,104)]
reverse_esc=projective(esc_back_marks,[project(esc,*p) for p in esc_front_marks])
gps_corners=[(181,60),(461,63),(181,241),(467,241)]
gps_datum=[(12.9,-24.),(-12.9,-24.),(12.9,-4.8),(-12.9,-4.8)]
gps=projective(gps_corners,gps_datum)
gps_back_marks=[(214,297),(489,304),(218,131),(483,137)]
reverse_gps=projective(gps_back_marks,gps_datum)
matrices={'esc':esc,'esc-back':reverse_esc,'gps':gps,'gps-back':reverse_gps}
photos=dict(zip(matrices,['wd-008.jpg','wd-009.jpg','wd-010.jpg','wd-011.jpg']))
labels={'esc':'ESC · power face','esc-back':'ESC · reverse face','gps':'GPS · antenna face','gps-back':'GPS · shield face'}
up_vectors={'esc':(1,0,0),'esc-back':(-1,0,0),'gps':(0,-1,0),'gps-back':(0,1,0)}
views={}
for i,key in enumerate(matrices):
    part=key.split('-')[0];upper='-' not in key
    views[key]=dict(title=labels[key],part=part,set=part,up=up_vectors[key],dir=(0,0,1 if upper else -1),
                    target=(0,-42.65,44.5) if part=='esc' else (0,-9.65,46.5),width=58,
                    source=f'Mini 2 internal photographs · WD filing, figure {9+i}')

esc_outline=[(222,119),(225,113),(307,111),(312,113),(342,112),(348,109),(405,108),(425,108),
 (430,104),(511,102),(516,104),(518,125),(524,128),(561,125),(568,128),(574,136),(577,198),
 (584,201),(587,205),(594,323),(590,327),(586,328),(585,336),(590,395),(587,407),(581,412),
 (530,413),(532,436),(527,440),(431,439),(423,436),(311,439),(224,441),(216,438),(212,431)]
gps_outline=[(161,45),(164,41),(199,41),(204,44),(207,51),(437,54),(442,45),(448,44),(475,45),
 (481,47),(488,256),(484,260),(430,261),(431,338),(428,342),(225,343),(222,340),(222,262),
 (164,262),(161,258)]
# Identifiable package and passive outlines, annotated in the four photographs.
upper_chips=[(229,158,262,187),(279,157,311,185),(321,156,352,184),(375,155,406,183),
 (420,153,452,182),(465,152,494,180),(226,346,260,379),(275,346,308,379),(322,345,354,377),
 (374,343,406,377),(420,342,452,375),(468,341,499,374)]
upper_passives=[(277,297,282,309),(301,301,309,314),(279,329,303,339),(256,303,265,315),
 (263,307,270,319),(327,191,337,199),(344,190,354,198),(403,196,409,206),
 (410,230,416,242),(419,230,425,244),(472,312,479,325),(490,303,511,323),(429,311,435,320),
 (270,194,279,200),(313,316,326,322),(282,262,289,270)]
lower_chips=[(278,181,322,224),(375,183,419,225),(278,251,322,293),(375,252,420,294)]
lower_passives=[(334,179,343,197),(347,179,356,197),(344,213,353,225),(340,246,357,255),(341,259,360,268),(342,273,360,282),
 (438,190,455,199),(439,202,457,211),(439,215,457,224),(243,253,260,262),(241,266,260,275),
 (263,230,273,247),(455,281,465,299),(446,286,452,300),(272,335,280,354),(367,339,377,361),
 (384,348,397,368),(232,309,242,328),(244,338,259,351),(457,254,491,273),(261,123,282,136),
 (298,121,319,133),(406,124,417,144),(432,124,453,135),(365,163,372,176),(381,145,390,161)]
gps_passives=[(395,148,403,155),(405,128,415,134),(418,129,426,137),(412,142,421,147),
 (396,157,405,164),(410,154,416,162),(380,156,386,164),(267,201,274,207),
 (264,209,272,214),(265,216,271,222),(264,88,279,106)]


texture_bounds={'esc':(202,91,603,451),'esc-back':(182,75,570,406),'gps':(150,30,500,355),'gps-back':(182,37,521,335)}
