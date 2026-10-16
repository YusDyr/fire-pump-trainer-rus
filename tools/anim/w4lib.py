import sys;sys.path.insert(0,'anim')
from align import *
import pickle,math,io,base64,json
from PIL import Image
D=pickle.load(open('anim/wheels.pkl','rb'))
SKIP={'215742','215809'}
def redfill(img,cx,cy,R):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV);h,w=img.shape[:2];yy,xx=np.mgrid[0:h,0:w];rr=np.hypot(xx-cx,yy-cy)
    red=(((hsv[...,0]<10)|(hsv[...,0]>168))&(hsv[...,1]>100)&(hsv[...,2]>40)).astype(np.uint8)*255
    red=cv2.morphologyEx(red,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    red&=((rr<1.15*R)*255).astype(np.uint8)
    n,lab,st,cen=cv2.connectedComponentsWithStats(red)
    i=lab[int(cy),int(cx)]
    if i==0:
        d=[(np.hypot(cen[j][0]-cx,cen[j][1]-cy),j) for j in range(1,n) if st[j][4]>500];i=min(d)[1]
    m=(lab==i).astype(np.uint8)*255
    ff=m.copy();mk=np.zeros((h+2,w+2),np.uint8);cv2.floodFill(ff,mk,(0,0),255);m=m|cv2.bitwise_not(ff)
    # convex hull smooths the rim
    cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);c=max(cnts,key=cv2.contourArea)
    hm=np.zeros_like(m);cv2.drawContours(hm,[cv2.convexHull(c)],-1,255,-1)
    return hm,hsv,rr
def knob(img,cx,cy,R):
    hm,hsv,rr=redfill(img,cx,cy,R)
    met=((hsv[...,1]<55)&(hsv[...,2]>120)&(rr>0.55*R)&(rr<1.4*R)).astype(np.uint8)*255
    met=cv2.morphologyEx(met,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(met)
    best=None
    for i in range(1,n):
        comp=lab==i;ins=(comp&(hm>0)).sum();tot=comp.sum()
        if ins<15 or tot>8000:continue
        sc=ins
        if best is None or sc>best[0]:best=(sc,i)
    if best is None:return hm,None,None
    km=((lab==best[1])*255).astype(np.uint8)
    # extend knob outward: include connected metallic pixels just outside disk along same angle
    ys,xs=np.nonzero(km);ang=math.degrees(math.atan2(ys.mean()-cy,xs.mean()-cx))
    km=cv2.dilate(km,np.ones((5,5),np.uint8))
    return hm,km,ang
