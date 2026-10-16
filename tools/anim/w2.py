import sys;sys.path.insert(0,'anim')
from align import *
import pickle,math
W={'w1':dict(c=(1818,1462),r=126,fs='215732 215735 215737 215739 215741 215742 215744 215746 215748 215750 215752 215753 215755 215756 215757 215759'.split()),
   'w0':dict(c=(625,1439),r=128,fs='215809 215810 215812 215815 215817 215819 215821 215823 215825 215827 215830 215831 215833 215834 215835 215836 215838 215839'.split())}
def disk(img):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    m=(((hsv[...,0]<10)|(hsv[...,0]>168))&(hsv[...,1]>110)&(hsv[...,2]>40)).astype(np.uint8)*255
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
    # fill holes (hub nut, highlights)
    ff=m.copy();h,w=m.shape;mk=np.zeros((h+2,w+2),np.uint8);cv2.floodFill(ff,mk,(0,0),255);m=m|cv2.bitwise_not(ff)
    d=cv2.distanceTransform(m,cv2.DIST_L2,5)
    # prefer near center
    yy,xx=np.mgrid[0:h,0:w];pen=1-0.25*np.hypot(xx-w/2,yy-h*0.45)/max(h,w)
    y,x=np.unravel_index(np.argmax(d*pen),d.shape);r=d[y,x]
    # hub: bright low-saturation blob near center
    met=((hsv[...,1]<70)&(hsv[...,2]>140)).astype(np.uint8)
    hub=met*(np.hypot(xx-x,yy-y)<0.32*r)
    if hub.sum()>20:
        ys,xs=np.nonzero(hub);x,y=xs.mean(),ys.mean()
    rr=np.hypot(xx-x,yy-y)
    area=((m>0)&(rr<1.3*r)).sum();R=np.sqrt(area/np.pi)
    return float(x),float(y),float(R),float(R)
# base disk radius in base pixels: measure from base
out={}
for k,o in W.items():
    cx,cy=o['c'];R=o['r']
    BX0,BY0=int((cx-R-60)*K),int((cy-R-60)*K);bs=int((2*R+120)*K)
    bimg=B[BY0:BY0+bs,BX0:BX0+bs]
    bx,by,brx,bry=disk(bimg);print(k,'base disk R',bx/K+cx-R-60,by/K+cy-R-60,brx/K,bry/K)
    tiles=[]
    for f in o['fs']:
        im=load(f);a=1500/max(im.shape[:2]);ims=cv2.resize(im,None,fx=a,fy=a,interpolation=cv2.INTER_AREA)
        px,py,prx,pry=disk(ims)
        sx=brx/prx;sy=bry/pry
        M=np.float32([[sx,0,bx-sx*px],[0,sy,by-sy*py]])
        w=cv2.warpAffine(ims,M,(bs,bs),flags=cv2.INTER_AREA)
        val=cv2.warpAffine(np.full(ims.shape[:2],255,np.uint8),M,(bs,bs))
        w=colormatch(w,bimg,val)
        out[(k,f)]=dict(img=w,center=(bx,by),R=(brx+bry)/2,off=(BX0,BY0))
        t=w.copy();cv2.circle(t,(int(bx),int(by)),int((brx+bry)/2),(0,255,0),1);cv2.putText(t,f,(5,20),0,0.6,(0,255,255),2)
        tiles.append(cv2.resize(t,(240,240)))
    b2=bimg.copy();cv2.circle(b2,(int(bx),int(by)),int((brx+bry)/2),(0,255,0),1);tiles.insert(0,cv2.resize(b2,(240,240)))
    rows=[np.hstack(tiles[i:i+6]+[np.zeros((240,240,3),np.uint8)]*(6-len(tiles[i:i+6]))) for i in range(0,len(tiles),6)]
    cv2.imwrite(f'anim/{k}_tiles.jpg',np.vstack(rows))
pickle.dump(out,open('anim/wheels.pkl','wb'))
