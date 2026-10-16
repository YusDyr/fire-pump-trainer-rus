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
out={};
for wk in ['w1','w0']:
    items=sorted([(f,v) for (k,f),v in D.items() if k==wk and f not in SKIP])
    v0=items[0][1];cx,cy=v0['center'];R=v0['R'];BX0,BY0=v0['off'];H,W=v0['img'].shape[:2]
    bimg=B[BY0:BY0+H,BX0:BX0+W].copy()
    bh,bk,bang=knob(bimg,cx,cy,R);print(wk,'base',bang)
    tiles=[]
    def tile(img,m,km,ang,lab):
        t=img.copy();cnt,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);cv2.drawContours(t,cnt,-1,(0,255,0),1)
        if km is not None:
            cnt,_=cv2.findContours(km,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE);cv2.drawContours(t,cnt,-1,(255,255,0),1)
            cv2.line(t,(int(cx),int(cy)),(int(cx+R*1.3*math.cos(math.radians(ang))),int(cy+R*1.3*math.sin(math.radians(ang)))),(0,255,255),2)
        cv2.putText(t,lab,(4,16),0,0.5,(0,255,255),1);return cv2.resize(t,(230,230))
    tiles.append(tile(bimg,bh,bk,bang or 0,'base %.0f'%(bang or 0)))
    res=[]
    for f,v in items:
        hm,km,ang=knob(v['img'],cx,cy,R);res.append((f,ang))
        tiles.append(tile(v['img'],hm,km,ang or 0,f'{f} {ang if ang is None else round(ang)}'))
    rows=[np.hstack(tiles[i:i+6]+[np.zeros((230,230,3),np.uint8)]*(6-len(tiles[i:i+6]))) for i in range(0,len(tiles),6)]
    cv2.imwrite(f'anim/{wk}_knob.jpg',np.vstack(rows));print(res)
