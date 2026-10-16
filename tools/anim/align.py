import cv2,numpy as np,sys,json
K=1.5
B=cv2.imread('hr/base2_full.jpg')
sift=cv2.SIFT_create(nfeatures=20000)
P='/mnt/user-data/uploads/YusDyr Vivo/IMG_20261013_'
def load(f):
    im=cv2.imread(P+f+'.jpg')  # cv2 ignores EXIF? use IMREAD with orientation (default applies)
    return im
def align(f,roi,margin=120,ratio=0.75,maxd=1800,excl=None):
    x0,y0,x1,y1=roi
    X0,Y0,X1,Y1=[int(v*K) for v in (x0-margin,y0-margin,x1+margin,y1+margin)]
    X0=max(0,X0);Y0=max(0,Y0)
    bc=B[Y0:Y1,X0:X1];gb=cv2.cvtColor(bc,cv2.COLOR_BGR2GRAY)
    im=load(f);a=maxd/max(im.shape[:2]);ims=cv2.resize(im,None,fx=a,fy=a,interpolation=cv2.INTER_AREA)
    gi=cv2.cvtColor(ims,cv2.COLOR_BGR2GRAY)
    mB=None
    if excl is not None:
        mB=np.full(gb.shape,255,np.uint8)
        for (ex0,ey0,ex1,ey1) in excl: mB[int(ey0*K)-Y0:int(ey1*K)-Y0,int(ex0*K)-X0:int(ex1*K)-X0]=0
    kA,dA=sift.detectAndCompute(gi,None);kB,dB=sift.detectAndCompute(gb,mB)
    mt=cv2.BFMatcher().knnMatch(dA,dB,k=2);good=[x for x,y in mt if x.distance<ratio*y.distance]
    src=np.float32([kA[m.queryIdx].pt for m in good]);dst=np.float32([kB[m.trainIdx].pt for m in good])
    H,inl=cv2.findHomography(src,dst,cv2.RANSAC,4.0)
    n=int(inl.sum()) if inl is not None else 0
    w=cv2.warpPerspective(ims,H,(bc.shape[1],bc.shape[0]),flags=cv2.INTER_AREA,borderMode=cv2.BORDER_CONSTANT)
    valid=cv2.warpPerspective(np.full(ims.shape[:2],255,np.uint8),H,(bc.shape[1],bc.shape[0]))
    return dict(base=bc,warp=w,valid=valid,H=H,inl=n,good=len(good),off=(X0,Y0))
def colormatch(w,b,mask):
    m=mask>0;o=w.astype(np.float32).copy()
    for c in range(3):
        ws=w[...,c][m].astype(np.float32);bs=b[...,c][m].astype(np.float32)
        o[...,c]=(o[...,c]-ws.mean())*(bs.std()/(ws.std()+1e-3))+bs.mean()
    return np.clip(o,0,255).astype(np.uint8)
def align2(f,roi,band,maxd=1800,ratio=0.78):
    """roi: output box (scene); band: list of scene boxes where base features are allowed"""
    x0,y0,x1,y1=roi
    X0,Y0,X1,Y1=[int(v*K) for v in roi]
    bc=B[Y0:Y1,X0:X1]
    # features from a larger base window restricted to bands
    bx0=min(b[0] for b in band);by0=min(b[1] for b in band);bx1=max(b[2] for b in band);by1=max(b[3] for b in band)
    WX0,WY0,WX1,WY1=[int(v*K) for v in (bx0,by0,bx1,by1)]
    gw=cv2.cvtColor(B[WY0:WY1,WX0:WX1],cv2.COLOR_BGR2GRAY);mB=np.zeros(gw.shape,np.uint8)
    for (a0,b0,a1,b1) in band: mB[int(b0*K)-WY0:int(b1*K)-WY0,int(a0*K)-WX0:int(a1*K)-WX0]=255
    im=load(f);a=maxd/max(im.shape[:2]);ims=cv2.resize(im,None,fx=a,fy=a,interpolation=cv2.INTER_AREA)
    gi=cv2.cvtColor(ims,cv2.COLOR_BGR2GRAY)
    kA,dA=sift.detectAndCompute(gi,None);kB,dB=sift.detectAndCompute(gw,mB)
    mt=cv2.BFMatcher().knnMatch(dA,dB,k=2);good=[x for x,y in mt if x.distance<ratio*y.distance]
    src=np.float32([kA[m.queryIdx].pt for m in good]);dst=np.float32([kB[m.trainIdx].pt for m in good])+np.float32([WX0-X0,WY0-Y0])
    H,inl=cv2.findHomography(src,dst,cv2.RANSAC,3.0)
    n=int(inl.sum()) if inl is not None else 0
    w=cv2.warpPerspective(ims,H,(bc.shape[1],bc.shape[0]),flags=cv2.INTER_AREA)
    valid=cv2.warpPerspective(np.full(ims.shape[:2],255,np.uint8),H,(bc.shape[1],bc.shape[0]))
    return dict(base=bc,warp=w,valid=valid,H=H,inl=n,good=len(good),off=(X0,Y0))
def align3(f,roi,band,maxd=1800,ratio=0.8,model='affine',H0=None):
    X0,Y0,X1,Y1=[int(v*K) for v in roi]
    bc=B[Y0:Y1,X0:X1]
    bx0=min(b[0] for b in band);by0=min(b[1] for b in band);bx1=max(b[2] for b in band);by1=max(b[3] for b in band)
    WX0,WY0,WX1,WY1=[int(v*K) for v in (bx0,by0,bx1,by1)]
    gw=cv2.cvtColor(B[WY0:WY1,WX0:WX1],cv2.COLOR_BGR2GRAY);mB=np.zeros(gw.shape,np.uint8)
    for (a0,b0,a1,b1) in band: mB[int(b0*K)-WY0:int(b1*K)-WY0,int(a0*K)-WX0:int(a1*K)-WX0]=255
    im=load(f);a=maxd/max(im.shape[:2]);ims=cv2.resize(im,None,fx=a,fy=a,interpolation=cv2.INTER_AREA)
    gi=cv2.cvtColor(ims,cv2.COLOR_BGR2GRAY)
    kA,dA=sift.detectAndCompute(gi,None);kB,dB=sift.detectAndCompute(gw,mB)
    mt=cv2.BFMatcher().knnMatch(dA,dB,k=2);good=[x for x,y in mt if x.distance<ratio*y.distance]
    src=np.float32([kA[m.queryIdx].pt for m in good]);dst=np.float32([kB[m.trainIdx].pt for m in good])+np.float32([WX0-X0,WY0-Y0])
    if model=='affine':
        A,inl=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=4.0,maxIters=5000)
        H=np.vstack([A,[0,0,1]])
    elif model=='affine6':
        A,inl=cv2.estimateAffine2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=4.0,maxIters=5000)
        H=np.vstack([A,[0,0,1]])
    else:
        H,inl=cv2.findHomography(src,dst,cv2.RANSAC,4.0)
    n=int(inl.sum()) if inl is not None else 0
    w=cv2.warpPerspective(ims,H,(bc.shape[1],bc.shape[0]),flags=cv2.INTER_AREA)
    valid=cv2.warpPerspective(np.full(ims.shape[:2],255,np.uint8),H,(bc.shape[1],bc.shape[0]))
    return dict(base=bc,warp=w,valid=valid,H=H,inl=n,good=len(good),off=(X0,Y0),scale=a)
def refine(r,band,motion=cv2.MOTION_AFFINE,iters=300,levels=3):
    """r from align(); band in scene coords: refine warp so that band region matches base"""
    X0,Y0=r['off'];b=cv2.cvtColor(r['base'],cv2.COLOR_BGR2GRAY).astype(np.float32);w=cv2.cvtColor(r['warp'],cv2.COLOR_BGR2GRAY).astype(np.float32)
    m=np.zeros(b.shape,np.uint8)
    for (a0,b0,a1,b1) in band: m[int(b0*K)-Y0:int(b1*K)-Y0,int(a0*K)-X0:int(a1*K)-X0]=255
    m=cv2.bitwise_and(m,r['valid'])
    W=np.eye(2,3,dtype=np.float32)
    # coarse-to-fine
    for lv in range(levels-1,-1,-1):
        s=1/2**lv
        bs=cv2.resize(b,None,fx=s,fy=s);ws=cv2.resize(w,None,fx=s,fy=s);ms=cv2.resize(m,None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST)
        Ws=W.copy();Ws[:,2]*=s
        try:
            cc,Ws=cv2.findTransformECC(bs,ws,Ws,motion,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,iters,1e-5),ms,5)
        except cv2.error as e:
            print('ecc fail',lv,e);continue
        W=Ws.copy();W[:,2]/=s
    # W maps base coords -> warp coords; apply inverse to warp
    out=cv2.warpAffine(r['warp'],W,(b.shape[1],b.shape[0]),flags=cv2.INTER_LINEAR+cv2.WARP_INVERSE_MAP)
    val=cv2.warpAffine(r['valid'],W,(b.shape[1],b.shape[0]),flags=cv2.INTER_NEAREST+cv2.WARP_INVERSE_MAP)
    r2=dict(r);r2['warp']=out;r2['valid']=val;r2['W']=W;return r2
def lever_mask(img,kind):
    hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    if kind=='red':
        m=((hsv[...,0]<10)|(hsv[...,0]>170))&(hsv[...,1]>110)&(hsv[...,2]>60)
    elif kind=='black':
        m=(hsv[...,2]<55)
    else: m=np.zeros(img.shape[:2],bool)
    return (m*255).astype(np.uint8)
def make_patch(r,kind,roi_keep=None,dil=9,feather=4,thr=None):
    """alpha = lever(base) ∪ lever(warp), dilated; restricted to roi_keep (scene box) and valid"""
    b=r['base'];w=colormatch(r['warp'],b,r['valid'])
    m=cv2.bitwise_or(lever_mask(b,kind),lever_mask(w,kind))
    if roi_keep is not None:
        X0,Y0=r['off'];k=np.zeros_like(m);x0,y0,x1,y1=[int(v*K) for v in roi_keep];k[y0-Y0:y1-Y0,x0-X0:x1-X0]=255;m=cv2.bitwise_and(m,k)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    m=cv2.dilate(m,np.ones((dil,dil),np.uint8))
    m=cv2.bitwise_and(m,cv2.erode(r['valid'],np.ones((5,5),np.uint8)))
    a=cv2.GaussianBlur(m,(0,0),feather)
    a=np.maximum(a,0)
    ys,xs=np.where(a>8)
    if len(xs)==0: return None
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    rgba=np.dstack([w[y0:y1,x0:x1],a[y0:y1,x0:x1]])
    X0,Y0=r['off']
    return dict(rgba=rgba,x=(X0+x0)/K,y=(Y0+y0)/K,w=(x1-x0)/K,h=(y1-y0)/K,comp=None)
def preview(r,p,path):
    b=r['base'].astype(np.float32).copy();X0,Y0=r['off']
    x0=int(round(p['x']*K))-X0;y0=int(round(p['y']*K))-Y0;h,w=p['rgba'].shape[:2]
    a=p['rgba'][...,3:4].astype(np.float32)/255
    b[y0:y0+h,x0:x0+w]=b[y0:y0+h,x0:x0+w]*(1-a)+p['rgba'][...,:3]*a
    cv2.imwrite(path,np.hstack([r['base'],b.astype(np.uint8)]))
def make_patch2(r,kind,roi_keep,thr=45,dil=11,feather=4):
    b=r['base'];w=colormatch(r['warp'],b,r['valid'])
    d=cv2.absdiff(cv2.GaussianBlur(b,(5,5),0),cv2.GaussianBlur(w,(5,5),0)).max(axis=2)
    m=((d>thr)*255).astype(np.uint8)
    m=cv2.bitwise_or(m,cv2.bitwise_or(lever_mask(b,kind),lever_mask(w,kind)))
    X0,Y0=r['off'];k=np.zeros_like(m);x0,y0,x1,y1=[int(v*K) for v in roi_keep];k[y0-Y0:y1-Y0,x0-X0:x1-X0]=255;m=cv2.bitwise_and(m,k)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
    m=cv2.dilate(m,np.ones((dil,dil),np.uint8));m=cv2.bitwise_and(m,cv2.erode(r['valid'],np.ones((5,5),np.uint8)))
    a=cv2.GaussianBlur(m,(0,0),feather);ys,xs=np.where(a>8)
    x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    return dict(rgba=np.dstack([w[y0:y1,x0:x1],a[y0:y1,x0:x1]]),x=(X0+x0)/K,y=(Y0+y0)/K,w=(x1-x0)/K,h=(y1-y0)/K)
def pair_align(fA,fB,roi,margin=60,maxd=1800,**kw):
    """align fB (other state) via fA (same viewpoint, aligned to base)"""
    r=align(fA,roi,margin=margin,maxd=maxd,**{k:v for k,v in kw.items() if k in('ratio','excl')})
    a=load(fA);b=load(fB)
    sa=maxd/max(a.shape[:2]);sb=maxd/max(b.shape[:2])
    A=cv2.resize(a,None,fx=sa,fy=sa,interpolation=cv2.INTER_AREA);Bm=cv2.resize(b,None,fx=sb,fy=sb,interpolation=cv2.INTER_AREA)
    kA,dA=sift.detectAndCompute(cv2.cvtColor(Bm,cv2.COLOR_BGR2GRAY),None);kB,dB=sift.detectAndCompute(cv2.cvtColor(A,cv2.COLOR_BGR2GRAY),None)
    mt=cv2.BFMatcher().knnMatch(dA,dB,k=2);good=[x for x,y in mt if x.distance<0.7*y.distance]
    src=np.float32([kA[m.queryIdx].pt for m in good]);dst=np.float32([kB[m.trainIdx].pt for m in good])
    Hp,inl=cv2.findHomography(src,dst,cv2.RANSAC,3.0);print('pair',int(inl.sum()),len(good))
    H=r['H']@Hp;bc=r['base']
    w=cv2.warpPerspective(Bm,H,(bc.shape[1],bc.shape[0]),flags=cv2.INTER_AREA)
    valid=cv2.warpPerspective(np.full(Bm.shape[:2],255,np.uint8),H,(bc.shape[1],bc.shape[0]))
    r2=dict(r);r2['warp']=w;r2['valid']=valid;r2['H']=H;return r,r2
def extend(r,src_img_name,ext,maxd=1800,H=None):
    """re-warp into a larger window: ext=(x0,y0,x1,y1) scene"""
    im=load(src_img_name);a=maxd/max(im.shape[:2]);ims=cv2.resize(im,None,fx=a,fy=a,interpolation=cv2.INTER_AREA)
    X0,Y0=r['off'];EX0,EY0,EX1,EY1=[int(v*K) for v in ext]
    T=np.array([[1,0,X0-EX0],[0,1,Y0-EY0],[0,0,1]],np.float64)
    HH=T@(H if H is not None else r['H'])
    bc=B[EY0:EY1,EX0:EX1]
    w=cv2.warpPerspective(ims,HH,(bc.shape[1],bc.shape[0]),flags=cv2.INTER_AREA)
    valid=cv2.warpPerspective(np.full(ims.shape[:2],255,np.uint8),HH,(bc.shape[1],bc.shape[0]))
    return dict(base=bc,warp=w,valid=valid,H=HH,off=(EX0,EY0))
