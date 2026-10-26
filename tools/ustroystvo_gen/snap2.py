import cv2,numpy as np
from scipy import ndimage as ndi
def outline_regions(img,shape,r=2.0):
    g=cv2.imread(img,0)[:shape[0],:shape[1]]
    dark=g<170; dt=ndi.distance_transform_edt(dark)
    thick=ndi.binary_dilation(dt>=r,iterations=2)
    thick=cv2.morphologyEx(thick.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))>0
    n,lab=cv2.connectedComponents((~thick).astype(np.uint8),connectivity=4)
    return g,thick,n,lab
def snap2(model,img,water,maxarea=60000,r=2.0):
    g,thick,n,lab=outline_regions(img,model.shape,r)
    area=np.bincount(lab.ravel(),minlength=n)
    flat=lab.ravel().astype(np.int64)*256+model.ravel()
    votes=np.bincount(flat,minlength=n*256).reshape(n,256)
    cov=votes[:,1:].sum(1); best=votes[:,1:].argmax(1)+1; bv=votes[np.arange(n),best]
    wat=np.bincount(lab.ravel(),weights=water.ravel().astype(float),minlength=n)
    ok=(cov>=0.3*area)&(bv>=0.45*np.maximum(cov,1))&(area<maxarea)&(wat<0.5*area); ok[0]=False
    out=np.where(ok,best,0).astype(np.uint8)[lab]; out[thick]=0
    dist,(iy,ix)=ndi.distance_transform_edt(out==0,return_indices=True)
    m=thick&(dist<=5); out[m]=out[iy,ix][m]
    return out,lab,ok
