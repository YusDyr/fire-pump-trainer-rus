import sys;sys.path.insert(0,'anim')
from align import *
from w4lib import *
import math,io,base64,json
from PIL import Image
MAN={'w0':{'215810':5,'215812':-51,'215815':-114,'215817':-170,'215819':136,'215821':93,'215823':47,'215825':0,'215827':-42,'215830':-42,'215831':-99,'215833':172,'215834':143,'215835':108,'215836':70,'215838':13,'215839':-62},'w0base':-22}
def enc(rgba,q=76):
    im=Image.fromarray(cv2.cvtColor(rgba,cv2.COLOR_BGRA2RGBA));b=io.BytesIO();im.save(b,'WEBP',quality=q,method=6);return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode(),len(b.getvalue())
def wedge(shape,cx,cy,R,ang,half=10,r0=0.6,r1=1.38):
    h,w=shape;yy,xx=np.mgrid[0:h,0:w];rr=np.hypot(xx-cx,yy-cy);aa=np.degrees(np.arctan2(yy-cy,xx-cx))
    d=np.abs((aa-ang+180)%360-180);return (rr>r0*R)&(rr<r1*R)&(d<half)
def knobmask(img,cx,cy,R,ang):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    m=wedge(img.shape[:2],cx,cy,R,ang)&(hsv[...,1]<65)&(hsv[...,2]>90)
    m=cv2.morphologyEx(m.astype(np.uint8)*255,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    if n<2:return m
    i=1+np.argmax(st[1:,4]);m=((lab==i)*255).astype(np.uint8)
    return cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
out={};prevs={}
for wk in ['w1','w0']:
    items=sorted([(f,v) for (k,f),v in D.items() if k==wk and f not in SKIP])
    v0=items[0][1];cx,cy=v0['center'];R=v0['R'];BX0,BY0=v0['off'];H,W=v0['img'].shape[:2]
    bimg=B[BY0:BY0+H,BX0:BX0+W].copy()
    bh,_,bang=knob(bimg,cx,cy,R)
    if wk=='w0':bang=MAN['w0base']
    yy,xx=np.mgrid[0:H,0:W];rr=np.hypot(xx-cx,yy-cy)
    bkm=cv2.dilate(knobmask(bimg,cx,cy,R,bang),np.ones((9,9),np.uint8))
    outside=bkm&((rr>0.88*R)*255).astype(np.uint8)
    clean=cv2.inpaint(bimg,outside,9,cv2.INPAINT_TELEA)
    ca=cv2.GaussianBlur(cv2.dilate(outside,np.ones((7,7),np.uint8)),(0,0),2)
    ys,xs=np.nonzero(ca>5);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    src,n=enc(np.dstack([clean[y0:y1,x0:x1],ca[y0:y1,x0:x1]]))
    S=int(1.45*R);sx0,sy0=int(cx-S),int(cy-S)
    rec=dict(cx=round((BX0+cx)/K,1),cy=round((BY0+cy)/K,1),R=round(R/K,1),a0=round(bang,1),S=round(S/K,1),
      plate=dict(src=src,x=round((BX0+x0)/K,1),y=round((BY0+y0)/K,1),w=round((x1-x0)/K,1),h=round((y1-y0)/K,1)),frames=[])
    tot=n;pv=[]
    for f,v in items:
        img=v['img']
        if wk=='w0':ang=MAN['w0'][f];hm,_,_=knob(img,cx,cy,R)
        else:hm,_,ang=knob(img,cx,cy,R)
        hm=hm&((rr<1.1*R)*255).astype(np.uint8)
        km=knobmask(img,cx,cy,R,ang)
        a=cv2.GaussianBlur(cv2.erode(hm,np.ones((3,3),np.uint8)),(0,0),1.3)
        a=np.maximum(a,cv2.GaussianBlur(cv2.dilate(km,np.ones((3,3),np.uint8)),(0,0),1.2))
        rgba=np.dstack([img[sy0:sy0+2*S,sx0:sx0+2*S],a[sy0:sy0+2*S,sx0:sx0+2*S]])
        s,n=enc(rgba);tot+=n;rec['frames'].append(dict(a=round(float(ang),1),src=s))
        c=clean.astype(np.float32);al=a[...,None]/255.0;c=(c*(1-al)+img*al).astype(np.uint8)[sy0:sy0+2*S,sx0:sx0+2*S]
        pv.append(cv2.resize(c,(200,200)))
    rec['frames'].sort(key=lambda d:d['a'])
    print(wk,len(rec['frames']),'KB',tot//1024,'base',round(bang))
    pv.insert(0,cv2.resize(clean[sy0:sy0+2*S,sx0:sx0+2*S],(200,200)))
    rows=[np.hstack(pv[i:i+6]+[np.zeros((200,200,3),np.uint8)]*(6-len(pv[i:i+6]))) for i in range(0,len(pv),6)]
    cv2.imwrite(f'anim/{wk}_final.jpg',np.vstack(rows))
    out['sc_'+wk]=rec
json.dump(out,open('anim/wheels.json','w'))
