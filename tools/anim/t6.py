import sys;sys.path.insert(0,'anim')
from align import *
import pickle
res={}
# ejector open
r=align('215940',(1010,1300,1190,1470),margin=100);p=make_patch(r,'black',roi_keep=(1040,1340,1160,1450));preview(r,p,'anim/pv_ej.jpg');res['ej1']=p
# tank open (на себя)
for f in ['215625','215620']:
    r=align(f,(1150,1460,1760,1800),margin=100);p=make_patch(r,'red',roi_keep=(1150,1470,1760,1800),dil=15,feather=6);preview(r,p,f'anim/pv_tank_{f}.jpg');res['tank_'+f]=p
# hpv
for f in ['220113','220120']:
    r=align(f,(600,980,800,1170),margin=120);p=make_patch(r,'red',roi_keep=(600,990,760,1170));preview(r,p,f'anim/pv_hpv_{f}.jpg');res['hpv_'+f]=p
# vac
for f in ['222209','222207','222204']:
    r=align(f,(740,780,1110,990),margin=150);r=refine(r,[(745,880,1105,945),(780,790,860,880)]);p=make_patch(r,'red',roi_keep=(745,790,1105,958));preview(r,p,f'anim/pv_vac_{f}.jpg');res['vac_'+f]=p
pickle.dump(res,open('anim/patches.pkl','wb'))
