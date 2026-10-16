import sys;sys.path.insert(0,'anim')
from align import *
import pickle
res=pickle.load(open('anim/patches.pkl','rb'))
r,r2=pair_align('220037','220041',(240,900,560,1120),margin=60,ratio=0.8,excl=[(180,840,330,1180)])
r2=extend(r2,'220041',(180,780,620,1180),H=r2['H'])
b=r2['base'].copy();X0,Y0=r2['off'];w=colormatch(r2['warp'],b,r2['valid'])
def box(x0,y0,x1,y1):
    m=np.zeros(b.shape[:2],np.uint8);m[int(y0*K)-Y0:int(y1*K)-Y0,int(x0*K)-X0:int(x1*K)-X0]=255;return m
old=box(272,963,452,1034)
# clean plate: fill old handle area with base shifted up by 78 px scene (diamond plate texture) 
sh=int(78*K);src=np.roll(b,sh,axis=0)
comp=b.copy();oa=cv2.GaussianBlur(old,(0,0),5)[...,None]/255.0
comp=(b*(1-oa)+src*oa).astype(np.uint8)
# keep valve body untouched: restore body region x>=440
body=box(440,940,560,1100);ba=cv2.GaussianBlur(body,(0,0),3)[...,None]/255.0
comp=(comp*(1-ba)+b*ba).astype(np.uint8)
# new handle from warp
d=cv2.absdiff(cv2.GaussianBlur(b,(5,5),0),cv2.GaussianBlur(w,(5,5),0)).max(axis=2)
nm=np.zeros(b.shape[:2],np.uint8)
P=lambda x,y:(int(x*K)-X0,int(y*K)-Y0)
pts=np.array([P(361,893),P(380,926.7),P(410,968),P(422,985)],np.int32);cv2.polylines(nm,[pts],False,255,int(8*K))
nm|=box(344,790,382,897)&lever_mask(w,'red')
mech=box(398,955,442,1036)&((d>30)*255).astype(np.uint8);nm|=mech
nm=cv2.morphologyEx(nm,cv2.MORPH_OPEN,np.ones((3,3),np.uint8));nm=cv2.morphologyEx(nm,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8));nm=cv2.dilate(nm,np.ones((5,5),np.uint8))
na=cv2.GaussianBlur(nm,(0,0),2)[...,None]/255.0
comp=(comp*(1-na)+w*na).astype(np.uint8)
a=np.maximum(cv2.GaussianBlur(cv2.bitwise_or(old,nm),(0,0),4),0)
a=np.maximum(a,cv2.bitwise_or(old,nm))
ys,xs=np.where(a>8);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
p=dict(rgba=np.dstack([comp[y0:y1,x0:x1],a[y0:y1,x0:x1]]),x=(X0+x0)/K,y=(Y0+y0)/K,w=(x1-x0)/K,h=(y1-y0)/K)
preview(r2,p,'anim/pv_ft2.jpg');res['ft_open']=p
pickle.dump(res,open('anim/patches.pkl','wb'))
