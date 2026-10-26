import cv2,numpy as np,sys
from scipy import ndimage as ndi
def snap(idm,img,drop=()):
    g=cv2.imread(img,0)[:idm.shape[0],:idm.shape[1]]
    for k in drop: idm=np.where(idm==k,0,idm)
    white=(g>=170).astype(np.uint8)
    n,lab=cv2.connectedComponents(white,connectivity=4)
    out=np.zeros_like(idm)
    # голосование внутри каждой области чертежа
    cnt=np.bincount(lab.ravel(),minlength=n)
    flat=lab.ravel().astype(np.int64)*256+idm.ravel().astype(np.int64)
    votes=np.bincount(flat,minlength=n*256).reshape(n,256)
    best=votes[:,1:].argmax(1)+1; bv=votes[np.arange(n),best]
    ok=(bv>=0.5*cnt)&(cnt<60000)&(cnt>0); ok[0]=False
    mapk=np.where(ok,best,0).astype(np.uint8)
    out=mapk[lab]; out[white==0]=0
    # линии чертежа: берём id ближайшего размеченного соседа (до 4 пикселей)
    lines=(white==0)
    dist,(iy,ix)=ndi.distance_transform_edt(out==0,return_indices=True)
    fill=out[iy,ix]; m=lines&(dist<=4)
    out[m]=fill[m]
    return out
if __name__=='__main__':
    for nm,img,drop in (('nd','../re_img/f2-000_r.png',(16,)),('hp','../re_img/f5-000_r.png',())):
        idm=np.load('id%s.npy'%nm); o=snap(idm,img,drop); np.save('ids%s.npy'%nm,o)
        g=cv2.imread(img,0)[:o.shape[0],:o.shape[1]];v=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
        rng=np.random.RandomState(5);pal=rng.randint(40,230,(256,3));pal[0]=0
        c=pal[o].astype(np.uint8);m=o>0;v[m]=(v[m]*0.35+c[m]*0.65).astype(np.uint8)
        for k in np.unique(o):
            if k==0: continue
            ys,xs=np.nonzero(o==k);i=len(xs)//2;cv2.putText(v,str(k),(int(np.median(xs)),int(np.median(ys))),0,1.4,(0,0,0),4)
        cv2.imwrite('snap_%s.jpg'%nm,cv2.resize(v,(v.shape[1]//2,v.shape[0]//2)))
