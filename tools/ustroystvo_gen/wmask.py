import numpy as np,json,cv2
SP='/tmp/claude-0/-home-claude/0cddc8dd-a6d2-5d8e-ac30-92c3e8f58934/scratchpad/'
def masks():
    nd=np.load(SP+'cut/masks.npz')['water'].astype(bool)
    lab=np.load(SP+'cut/f5lab.npy')[:1450,:1640];S=json.load(open(SP+'cut/f5sets.json'))
    hp=np.isin(lab,S['water']); cool=np.isin(lab,S['cool'])
    return nd,hp,cool
def frac_out(pts,m):
    md=cv2.dilate(m.astype(np.uint8),np.ones((7,7),np.uint8))>0
    tot=0;out=0
    for a,b in zip(pts,pts[1:]):
        L=int(np.hypot(b[0]-a[0],b[1]-a[1]))+1
        for t in np.linspace(0,1,L):
            x=int(a[0]+(b[0]-a[0])*t);y=int(a[1]+(b[1]-a[1])*t);tot+=1
            if not (0<=y<m.shape[0] and 0<=x<m.shape[1]) or not md[y,x]: out+=1
    return out/max(tot,1)
if __name__=='__main__':
    nd,hp,cool=masks()
    R='/home/claude/fire-pump-trainer-rus/src/ustroystvo/'
    for nm,m,f in (('nd',nd,'nd_data.json'),('hp',hp,'hp_data.json')):
        D=json.load(open(R+f,encoding='utf-8'))
        for i,p in enumerate(D['paths']): print(nm,i,round(frac_out(p['pts'],m),2))
        if 'cool' in D: print(nm,'cool',round(frac_out(D['cool'],cool),2))
