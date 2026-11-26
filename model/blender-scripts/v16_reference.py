"""Register the component photographs to the retained V15 board mounting holes."""
import numpy as np

def core_xy(u, v):
    y = 11 - (u-303)*78/382
    relief = max(0, min(1, (y+63)/6, (-22-y)/4))
    return ((v-307.5)*37/183*(1-.058*relief), y)

bottom = core_xy
def lower_field(u,v):
    # Retain the V15 optical axis and rear edge while fitting the populated rear strip.
    optical_u=303+(11+48.6)*382/78
    shift=(optical_u-561)*max(0,min((u-303)/(561-303),(685-u)/(685-561)))
    return core_xy(u+shift,v)

# Align the four visible mounting-hole centres independently on both faces.
wd_holes = [(132,117),(101,349),(627,138),(639,371)]
pd_holes = [(315,393),(314,229),(660,389),(655,224)]
A, b = [], []
for (u,v),(x,y) in zip(wd_holes, [core_xy(*p) for p in pd_holes]):
    A.extend([[u,v,1,0,0,0,-u*x,-v*x], [0,0,0,u,v,1,-u*y,-v*y]])
    b.extend([x,y])
H = np.append(np.linalg.solve(A,b),1).reshape((3,3))
def top(u,v):
    x,y,w = H @ (u,v,1.)
    return (float(x/w),float(y/w))

# Traced outlines of the metal lids on the canned face, and of the two
# thermal-contact shields on the opposite face. Coordinates are source pixels.
top_lids = [
 [(118,151),(123,139),(136,131),(301,136),(312,140),(318,150),(311,334),(305,346),(239,342),(230,334),(229,316),(221,310),(110,304),(99,298),(98,288)],
 [(328,141),(333,126),(342,121),(417,123),(430,129),(431,141),(425,331),(417,345),(331,342),(322,333),(319,322)],
 [(441,167),(454,152),(463,149),(506,152),(523,163),(532,175),(532,249),(522,261),(518,267),(515,290),(505,303),(476,304),(462,298),(443,281),(440,267)]]
bottom_lids = [
 [(334,378),(337,272),(341,261),(371,259),(381,253),(398,237),(433,235),(444,239),(445,363),(441,378),(432,382),(341,385)],
 [(448,278),(459,266),(473,260),(516,261),(532,272),(536,279),(535,339),(526,348),(529,381),(523,395),(470,395),(451,380)]]
# The raised pressings on the installed metal sheets, from WD figure 7.
pressings = [[(214,143,308,198),(152,201,226,294),(244,257,302,331),(135,160,205,190)],
             [(338,174,415,194),(350,241,410,268),(337,274,407,329),(388,131,405,146)],
             [(465,211,511,254)]]

