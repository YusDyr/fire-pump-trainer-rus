import sys;sys.path.insert(0,'anim')
from align import *
import pickle
res=pickle.load(open('anim/patches.pkl','rb'))
for f in ['220108','220113','220120']:
    r=align(f,(600,980,800,1170),margin=120);p=make_patch2(r,'red',(620,1000,760,1160));preview(r,p,f'anim/pv_hpv_{f}.jpg');res['hpv_'+f]=p
# ft retry: features only on valve body/pipes, not diamond plate
for f in ['215950','215958','220037','220041']:
    r=align(f,(240,900,560,1120),margin=60,ratio=0.8,excl=[(180,840,330,1180)])
    print(f,r['inl'],r['good'])
    w=colormatch(r['warp'],r['base'],r['valid']);cv2.imwrite(f'anim/ft_{f}.jpg',np.hstack([r['base'],w]))
pickle.dump(res,open('anim/patches.pkl','wb'))
