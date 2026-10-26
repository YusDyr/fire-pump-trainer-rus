import numpy as np,json,cv2,io,base64
from PIL import Image
from scipy import ndimage as ndi
from snap import snap
from route import router,route_path
SP='/tmp/claude-0/-home-claude/0cddc8dd-a6d2-5d8e-ac30-92c3e8f58934/scratchpad/'
R='/home/claude/fire-pump-trainer-rus/src/ustroystvo/'
def webp(arr,path):
    Image.fromarray(arr).save(path,'WEBP',lossless=True,method=6)
# ---------- рис. 5: вода в каналах рабочих колёс ----------
lab=np.load(SP+'cut/f5lab.npy')[:1450,:1640];S=json.load(open(SP+'cut/f5sets.json'))
cnt=np.bincount(lab.ravel())
rect=np.zeros(lab.shape,bool)
for x0,x1 in ((1094,1117),(1228,1258)):
    for y0,y1 in ((405,625),(847,1067)): rect[y0:y1,x0:x1]=True
inside=np.bincount(lab[rect].ravel(),minlength=len(cnt))
add=[int(k) for k in np.nonzero((inside>0.7*cnt)&(cnt<3000))[0] if k]
water=sorted(set(S['water'])|set(add))
k5=np.ones((5,5),np.uint8)
m={n:cv2.dilate(np.isin(lab,ids).astype(np.uint8),k5) for n,ids in dict(S,water=water).items()}
H,W=lab.shape;rgb=np.zeros((H,W,3),np.uint8)
rgb[...,0]=m['water']*255;rgb[...,1]=m['oil']*255;rgb[...,2]=np.where(m['shaft']>0,255,np.where(m['cool']>0,120,0))
webp(rgb,R+'hp_mask.webp')
hpw=np.isin(lab,water)
# ---------- области деталей ----------
def manual(ids,img,polys):
    g=cv2.imread(img,0)[:ids.shape[0],:ids.shape[1]];white=(g>=170).astype(np.uint8)
    n,lb=cv2.connectedComponents(white,connectivity=4);c=np.bincount(lb.ravel())
    for k,poly in polys:
        pm=np.zeros(ids.shape,np.uint8);cv2.fillPoly(pm,[np.array(poly,np.int32)],1)
        ins=np.bincount(lb[pm>0].ravel(),minlength=n)
        ok=(ins>=0.9*c)&(c<3000);ok[0]=False
        sel=ok[lb]&(ids==0)&(white>0);ids[sel]=k
        lines=(white==0)&(pm>0)&(ids==0)
        dist,(iy,ix)=ndi.distance_transform_edt(ids!=k,return_indices=True);ids[lines&(dist<=3)]=k
    return ids
nd_ids=snap(np.load('idnd.npy'),SP+'re_img/f2-000_r.png',(16,))
nd_ids=manual(nd_ids,SP+'re_img/f2-000_r.png',[
 (20,[(1210,80),(1790,80),(1790,430),(1210,430)]),
 (20,[(1380,1200),(1700,1200),(1700,1450),(1560,1700),(1380,1700)]),
 (16,[(1600,1500),(1880,1500),(1880,1760),(1600,1760)])])
hp_ids=snap(np.load('idhp.npy'),SP+'re_img/f5-000_r.png')
hp_ids=manual(hp_ids,SP+'re_img/f5-000_r.png',[(14,[(1300,160),(1560,160),(1560,1250),(1300,1250)])])
ndw0=np.load(SP+'cut/masks.npz')['water'].astype(bool)
def fallback(ids,model,img):
    g=cv2.imread(img,0)[:ids.shape[0],:ids.shape[1]]
    white=(g>=170).astype(np.uint8);n,lb=cv2.connectedComponents(white,connectivity=4);c=np.bincount(lb.ravel())
    m=(ids==0)&(model>0)&(white>0)&(c[lb]<20000);ids[m]=model[m];return ids
nd_ids=fallback(nd_ids,np.where(np.load('idnd.npy')==16,0,np.load('idnd.npy')),SP+'re_img/f2-000_r.png')
hp_ids=fallback(hp_ids,np.load('idhp.npy'),SP+'re_img/f5-000_r.png')
def bigwater(wm,img):
    g=cv2.imread(img,0)[:wm.shape[0],:wm.shape[1]];n,lb=cv2.connectedComponents((g>=170).astype(np.uint8),connectivity=4);c=np.bincount(lb.ravel())
    return wm&(c[lb]>=3000)
nd_ids[bigwater(ndw0,SP+'re_img/f2-000_r.png')&np.isin(nd_ids,[20,12])]=0;hp_ids[(bigwater(hpw,SP+'re_img/f5-000_r.png')&np.isin(hp_ids,[14,5]))|np.isin(lab,S['cool'])]=0
# области, ограниченные контурными (толстыми) линиями чертежа: деталь закрашивается целиком, штриховка и выноски не мешают
from snap2 import snap2,outline_regions
nd_o,_,_=snap2(np.where(np.load('idnd.npy')==16,0,np.load('idnd.npy')),SP+'re_img/f2-000_r.png',ndw0)
hp_o,_,_=snap2(np.load('idhp.npy'),SP+'re_img/f5-000_r.png',hpw)
nd_ids=np.where(nd_o>0,nd_o,nd_ids);hp_ids=np.where(hp_o>0,hp_o,hp_ids)
def manual2(ids,img,polys,wm):
    g,thick,n,lb=outline_regions(img,ids.shape)
    area=np.bincount(lb.ravel(),minlength=n)
    for k,poly in polys:
        pm=np.zeros(ids.shape,np.uint8);cv2.fillPoly(pm,[np.array(poly,np.int32)],1)
        ins=np.bincount(lb[pm>0].ravel(),minlength=n);wat=np.bincount(lb.ravel(),weights=wm.ravel().astype(float),minlength=n)
        ok=(ins>=0.85*area)&(area<60000)&(wat<0.3*area);ok[0]=False
        sel=ok[lb]&(ids==0);ids[sel]=k
        dist,(iy,ix)=ndi.distance_transform_edt(ids!=k,return_indices=True);ids[thick&(pm>0)&(ids==0)&(dist<=5)]=k
    return ids
nd_ids=manual2(nd_ids,SP+'re_img/f2-000_r.png',[
 (20,[(1210,60),(1800,60),(1800,440),(1210,440)]),
 (20,[(1330,1150),(1760,1150),(1760,1480),(1560,1800),(1330,1800)]),
 (20,[(1330,380),(1460,380),(1460,1150),(1330,1150)])],ndw0)
hp_ids=manual2(hp_ids,SP+'re_img/f5-000_r.png',[(14,[(1300,160),(1560,160),(1560,1250),(1300,1250)])],hpw)
# сетка 13: сферический сегмент (дуга) у входа в крышку
yy,xx=np.mgrid[0:nd_ids.shape[0],0:nd_ids.shape[1]]
rr=np.hypot(xx-1757.7,yy-954.5);band=(np.abs(rr-408)<=9)&(xx>=2090)
nd_ids[band]=13
for nm,ids in (('nd',nd_ids),('hp',hp_ids)):
    a=np.zeros(ids.shape+(3,),np.uint8);a[...,0]=ids;webp(a,R+nm+'_parts.webp')
# ---------- пути и опорные точки ----------
ndw=np.load(SP+'cut/masks.npz')['water'].astype(bool)
g2=cv2.imread(SP+'re_img/f2-000_r.png',0);yy2,xx2=np.mgrid[0:g2.shape[0],0:g2.shape[1]]
dome=(np.hypot(xx2-1757.7,yy2-954.5)<400)&(xx2>2096)&(g2>=170)
ndw=ndw|dome
nm_=np.array(Image.open(R+'nd_mask.webp').convert('RGB'));nm_[...,0]=np.where(cv2.dilate(dome.astype(np.uint8),np.ones((5,5),np.uint8))>0,255,nm_[...,0]);webp(nm_,R+'nd_mask.webp')
D=json.load(open(R+'nd_data.json',encoding='utf-8'))
P=D['paths']
P[0]['pts']=[[2245,820],[2070,820]]+[[2070,820],[1880,830],[1720,850],[1620,820],[1545,750],[1518,640],[1515,500],[1505,425],[1482,398]]
P[2]['pts']=[[2245,1060],[2070,1060]]+[[2070,1060],[1880,1060],[1720,1070],[1620,1110],[1545,1180],[1518,1290],[1515,1430],[1500,1520],[1478,1556]]
P[1]['pts']=[[2245,900]]+P[1]['pts'];P[3]['pts']=[[2245,990]]+P[3]['pts']
rt=router(ndw)
for p in P: p['pts']=route_path(p['pts'],rt)
D5=json.load(open(R+'hp_data.json',encoding='utf-8'))
rt5=router(hpw)
D5['paths']=[
 {'pts':route_path([[1115,10],[1115,230],[1180,272],[1460,272],[1470,540],[1420,600],[1330,630],[1288,640]],rt5),'w':1},
 {'pts':[[1288,642],[1262,628],[1248,600],[1243,520],[1243,430],[1246,395],[1270,360],[1310,352],[1350,375],[1380,420],[1388,480]],'w':1},
 {'pts':[[1060,410],[1058,500],[1060,580],[1072,628],[1095,622],[1104,580],[1105,500],[1105,430],[1108,395],[1115,350],[1115,285]],'w':1},
 {'pts':[[1288,830],[1262,844],[1248,872],[1243,952],[1243,1042],[1246,1075]],'w':1},
 {'pts':[[1072,844],[1095,850],[1104,892],[1105,972],[1105,1042],[1108,1075]],'w':1}]
coolm=np.isin(lab,S['cool'])
D5['cool']=route_path(D5['cool'],router(coolm))
def anchor(D,ids):
    for n,(name,(x,y)) in D['parts'].items():
        k=int(n);m=ids==k
        if not m.any() or ids[y,x]==k: continue
        dist,(iy,ix)=ndi.distance_transform_edt(~m,return_indices=True)
        if dist[y,x]<120: D['parts'][n][1]=[int(ix[y,x]),int(iy[y,x])]
anchor(D,nd_ids);anchor(D5,hp_ids)
D['regions']=sorted(int(k) for k in np.unique(nd_ids) if k);D5['regions']=sorted(int(k) for k in np.unique(hp_ids) if k)
json.dump(D,open(R+'nd_data.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(D5,open(R+'hp_data.json','w',encoding='utf-8'),ensure_ascii=False)
from wmask import frac_out
for i,p in enumerate(D5['paths']): print('hp',i,round(frac_out(p['pts'],hpw),2))
for i,p in enumerate(D['paths']): print('nd',i,round(frac_out(p['pts'],ndw),2))
print('cool',round(frac_out(D5['cool'],coolm),2), D['regions'], D5['regions'])
# превью
for nm,ids,img,DD,wm in (('nd',nd_ids,'f2-000_r.png',D,ndw),('hp',hp_ids,'f5-000_r.png',D5,hpw)):
    g=cv2.imread(SP+'re_img/'+img,0)[:ids.shape[0],:ids.shape[1]];v=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
    v[wm]=(v[wm]*0.5+np.array([235,170,60])*0.5).astype(np.uint8)
    rng=np.random.RandomState(5);pal=rng.randint(40,230,(256,3));pal[0]=0
    c=pal[ids].astype(np.uint8);mm=ids>0;v[mm]=(v[mm]*0.45+c[mm]*0.55).astype(np.uint8)
    for p in DD['paths']: cv2.polylines(v,[np.array(p['pts'],np.int32)],False,(0,0,255),4)
    if 'cool' in DD: cv2.polylines(v,[np.array(DD['cool'],np.int32)],False,(160,0,160),3)
    for n,(name,(x,y)) in DD['parts'].items(): cv2.circle(v,(x,y),10,(0,0,0),3)
    cv2.imwrite('fin_%s.jpg'%nm,cv2.resize(v,(v.shape[1]//2,v.shape[0]//2)))
