import sys;sys.path.insert(0,'anim')
from align import *
r,r2=pair_align('220037','220041',(240,900,560,1120),margin=60,ratio=0.8,excl=[(180,840,330,1180)])
w=colormatch(r2['warp'],r2['base'],r2['valid'])
X0,Y0=r2['off']
P=lambda x,y:(int(x*K)-X0,int(y*K)-Y0)
v=w.copy();cv2.line(v,P(361,874),P(408,968),(0,255,0),1)
cv2.imwrite('anim/dbg.jpg',v)
