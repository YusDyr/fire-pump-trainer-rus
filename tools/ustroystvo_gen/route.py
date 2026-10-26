import numpy as np,json,cv2
from skimage.graph import route_through_array
from scipy import ndimage as ndi
from wmask import masks,frac_out
def router(m):
    s=2; ms=cv2.resize(m.astype(np.uint8),(m.shape[1]//s,m.shape[0]//s),interpolation=cv2.INTER_NEAREST)>0
    dt=ndi.distance_transform_edt(ms)
    cost=np.where(ms,1+6/(1+dt),400.0)
    def route(a,b):
        A=(min(ms.shape[0]-1,int(a[1]//s)),min(ms.shape[1]-1,int(a[0]//s)));B=(min(ms.shape[0]-1,int(b[1]//s)),min(ms.shape[1]-1,int(b[0]//s)))
        p,_=route_through_array(cost,A,B,fully_connected=True,geometric=True)
        return [(x*s+1,y*s+1) for y,x in p]
    return route
def rdp(P,eps):
    P=np.array(P,float)
    if len(P)<3: return P.tolist()
    a,b=P[0],P[-1];v=b-a;w=P-a;d=np.abs(v[0]*w[:,1]-v[1]*w[:,0])/(np.linalg.norm(b-a)+1e-9)
    i=d.argmax()
    if d[i]>eps: return rdp(P[:i+1],eps)[:-1]+rdp(P[i:],eps)
    return [P[0].tolist(),P[-1].tolist()]
def smooth(P,k=5):
    P=np.array(P,float)
    if len(P)<k: return P
    Q=P.copy()
    for i in range(1,len(P)-1):
        lo=max(0,i-k//2);hi=min(len(P),i+k//2+1);Q[i]=P[lo:hi].mean(0)
    return Q
def route_path(wps,route):
    full=[]
    for a,b in zip(wps,wps[1:]):
        seg=route(a,b); full+=seg if not full else seg[1:]
    full=smooth(full,7)
    return [[round(x),round(y)] for x,y in rdp(full,2.5)]
if __name__=='__main__':
    nd,hp,cool=masks()
    R='/home/claude/fire-pump-trainer-rus/src/ustroystvo/'
    for nm,m,f in (('nd',nd,'nd_data.json'),('hp',hp,'hp_data.json')):
        D=json.load(open(R+f,encoding='utf-8'));rt=router(m)
        for i,p in enumerate(D['paths']):
            q=route_path(p['pts'],rt);print(nm,i,round(frac_out(p['pts'],m),2),'->',round(frac_out(q,m),2),len(q))
            p['routed']=q
        if 'cool' in D:
            q=route_path(D['cool'],router(cool));print('cool',round(frac_out(D['cool'],cool),2),'->',round(frac_out(q,cool),2));D['cool_routed']=q
        json.dump(D,open('routed_%s.json'%nm,'w'),ensure_ascii=False)
