import json,re,cv2,numpy as np
SP='/tmp/claude-0/-home-claude/0cddc8dd-a6d2-5d8e-ac30-92c3e8f58934/scratchpad/'
G=json.load(open(SP+'cad/geo.json',encoding='utf-8'))
H=json.load(open(SP+'cad/hpsec.json',encoding='utf-8'))
def num(n):
    m=re.match(r'^(?:ВД )?(\d+)\s',n); return int(m.group(1)) if m else None
def build(loops,W,H_,proj):
    by={}
    for n,pts in loops:
        k=num(n)
        if k is None: continue
        P=np.array([proj(p) for p in pts],np.int32)
        if len(P)<3: continue
        by.setdefault(k,[]).append(P)
    # большие сначала, мелкие поверх
    area={k:sum(abs(cv2.contourArea(p)) for p in v) for k,v in by.items()}
    idm=np.zeros((H_,W),np.uint8)
    for k in sorted(by,key=lambda k:-area[k]):
        m=np.zeros((H_,W),np.uint8); cv2.fillPoly(m,by[k],1); idm[m>0]=k
    return idm
# рис. 2
nd=[(s['n'],s['p']) for s in G['sec'] if not s['n'].startswith(('ВД ','П'))]
idnd=build(nd,2272,1809,lambda p:(92+p[0]*3.82,954.5-p[1]*3.82))
# рис. 5: плоскость А-А через ось ВД, r — вдоль направления к оси НД
U=np.array([0,198.0,-55.0]);U/=np.linalg.norm(U);P0=np.array([0,-198.0,55.0])
hp=[(s['n'],s['p']) for s in H]
idhp=build(hp,1640,1450,lambda p:(1515+(p[0]-318)*3.9,736+np.dot(np.array(p)-P0,U)*3.9))
np.save('idnd.npy',idnd);np.save('idhp.npy',idhp)
for nm,idm,img in (('nd',idnd,'../re_img/f2-000_r.png'),('hp',idhp,'../re_img/f5-000_r.png')):
    g=cv2.imread(img,0)[:idm.shape[0],:idm.shape[1]]
    v=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
    rng=np.random.RandomState(3);pal=rng.randint(60,255,(256,3));pal[0]=0
    c=pal[idm].astype(np.uint8); m=idm>0
    v[m]=(v[m]*0.45+c[m]*0.55).astype(np.uint8)
    for k in np.unique(idm):
        if k==0: continue
        ys,xs=np.nonzero(idm==k);cv2.putText(v,str(k),(int(xs.mean()),int(ys.mean())),0,1.2,(0,0,0),3)
    cv2.imwrite('reg_%s.jpg'%nm,cv2.resize(v,(v.shape[1]//2,v.shape[0]//2)))
    print(nm,sorted(int(k) for k in np.unique(idm) if k))
