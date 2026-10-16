import sys;sys.path.insert(0,'anim')
from align import *
import pickle
res=pickle.load(open('anim/patches.pkl','rb'))
for f in ['220113','220120']:
    r=align(f,(600,980,800,1170),margin=120);p=make_patch2(r,'red',(626,1000,712,1115),thr=60);preview(r,p,f'anim/pv_hpv_{f}.jpg');res['hpv_'+f]=p
for A,Bf in [('220037','220041'),('215950','215958')]:
    r,r2=pair_align(A,Bf,(240,900,560,1120),margin=60,ratio=0.8,excl=[(180,840,330,1180)])
    p=make_patch2(r2,'red',(250,880,560,1100),thr=60,dil=15);preview(r2,p,f'anim/pv_ft_{Bf}.jpg');res['ft_'+Bf]=p
pickle.dump(res,open('anim/patches.pkl','wb'))
