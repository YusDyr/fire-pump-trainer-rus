import sys;sys.path.insert(0,'anim')
from align import *
import pickle,math,io,base64,json
from PIL import Image
D=pickle.load(open('anim/wheels.pkl','rb'))
SKIP={'215742','215809'}
def knob_mask(img,cx,cy,R):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV);h,w=img.shape[:2]
    yy,xx=np.mgrid[0:h,0:w];rr=np.hypot(xx-cx,yy-cy)
    red=((hsv[...,0]<10)|(hsv[...,0]>168))&(hsv[...,1]>90)
    met=(~red)&(hsv[...,1]<90)&(hsv[...,2]>110)&(rr>0.55*R)&(rr<1.45*R)
    met=cv2.morphologyEx(met.astype(np.uint8)*255,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(met)
    best=None
    for i in range(1,n):
        comp=lab==i
        inside=(comp&(rr<0.98*R)).sum();outer=(comp&(rr>0.9*R)&(rr<1.45*R)).sum()
        if inside<10 or outer<40:continue
        if best is None or outer>best[0]:best=(outer,i)
    if best is None:return None,None
    km=(lab==best[1])&(rr<1.42*R)
    km=cv2.morphologyEx(km.astype(np.uint8)*255,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    ys,xs=np.nonzero(km&(rr<1.2*R)[...,None].squeeze() if False else km)
    ang=math.degrees(math.atan2(ys.mean()-cy,xs.mean()-cx))  # screen angle, y down
    return km,ang
out={}
for wk in ['w1','w0']:
    items=[(f,v) for (k,f),v in D.items() if k==wk and f not in SKIP]
    v0=items[0][1];cx,cy=v0['center'];R=v0['R'];BX0,BY0=v0['off']
    S=int(1.42*R)
    bimg=B[BY0:BY0+v0['img'].shape[0],BX0:BX0+v0['img'].shape[1]].copy()
    h,w=bimg.shape[:2];yy,xx=np.mgrid[0:h,0:w];rr=np.hypot(xx-cx,yy-cy)
    disk=(rr<R*0.995).astype(np.float32);disk=cv2.GaussianBlur(disk,(0,0),1.5)
    # base knob -> clean plate outside disk
    bk,bang=knob_mask(bimg,cx,cy,R);print(wk,'base knob angle',bang)
    outside=cv2.dilate(bk,np.ones((9,9),np.uint8))&((rr>0.9*R)*255).astype(np.uint8)
    clean=cv2.inpaint(bimg,outside,7,cv2.INPAINT_TELEA)
    ca=cv2.GaussianBlur(cv2.dilate(outside,np.ones((5,5),np.uint8)),(0,0),2)
    ys,xs=np.nonzero(ca>5);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    def enc(rgba):
        im=Image.fromarray(cv2.cvtColor(rgba,cv2.COLOR_BGRA2RGBA));b=io.BytesIO();im.save(b,'WEBP',quality=78,method=6);return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode(),len(b.getvalue())
    src,n=enc(np.dstack([clean[y0:y1,x0:x1],ca[y0:y1,x0:x1]]))
    rec=dict(cx=round((BX0+cx)/K,1),cy=round((BY0+cy)/K,1),R=round(R/K,1),a0=round(bang,1),
             plate=dict(src=src,x=round((BX0+x0)/K,1),y=round((BY0+y0)/K,1),w=round((x1-x0)/K,1),h=round((y1-y0)/K,1)),frames=[])
    tot=n;prev=[]
    for f,v in sorted(items):
        img=v['img'];km,ang=knob_mask(img,cx,cy,R)
        if km is None:print('no knob',f);continue
        a=np.maximum(disk*255,cv2.GaussianBlur(cv2.dilate(km,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),1.2)).astype(np.uint8)
        sx0,sy0=int(cx-S),int(cy-S)
        rgba=np.dstack([img[sy0:sy0+2*S,sx0:sx0+2*S],a[sy0:sy0+2*S,sx0:sx0+2*S]])
        s,n=enc(rgba);tot+=n
        rec['frames'].append(dict(a=round(ang,1),src=s,f=f))
        # preview: frame over clean base
        pv=clean.astype(np.float32);al=a[...,None]/255.0;pv=pv*(1-al)+img*al
        pv=pv[sy0:sy0+2*S,sx0:sx0+2*S].astype(np.uint8);cv2.putText(pv,f'{f} {ang:.0f}',(4,16),0,0.5,(0,255,255),1)
        prev.append(cv2.resize(pv,(220,220)))
    rec['frames'].sort(key=lambda d:d['a'])
    print(wk,'frames',len(rec['frames']),'KB',tot//1024,[d['a'] for d in rec['frames']])
    bp=bimg[sy0:sy0+2*S,sx0:sx0+2*S];prev.insert(0,cv2.resize(bp,(220,220)))
    rows=[np.hstack(prev[i:i+6]+[np.zeros((220,220,3),np.uint8)]*(6-len(prev[i:i+6]))) for i in range(0,len(prev),6)]
    cv2.imwrite(f'anim/{wk}_pv.jpg',np.vstack(rows))
    out['sc_'+wk]=rec
json.dump(out,open('anim/wheels.json','w'))
