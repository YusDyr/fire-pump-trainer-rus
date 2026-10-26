import numpy as np,json,cv2,io,base64
from PIL import Image
from scipy import ndimage as ndi
from snap import snap
from route import router,route_path
SP='/tmp/claude-0/-home-claude/0cddc8dd-a6d2-5d8e-ac30-92c3e8f58934/scratchpad/'
R='/home/claude/fire-pump-trainer-rus/src/ustroystvo/'
def webp(arr,path):
    Image.fromarray(arr).save(path,'WEBP',lossless=True,method=6)
# ---------- рис. 5: проточная часть — заливка от затравок внутри грубых рамок, по контурным линиям ----------
lab=np.load(SP+'cut/f5lab.npy')[:1450,:1640];S=json.load(open(SP+'cut/f5sets.json'))
g5=cv2.imread(SP+'re_img/f5-000_r.png',0)[:1450,:1640]
dark5=g5<170;thick5=ndi.binary_dilation(ndi.distance_transform_edt(dark5)>=2.0,iterations=1)
WSPEC=[ # затравка, рамка
 ((1052,500),[(1028,405),(1080,405),(1080,650),(1028,650)]),                         # камера перед колесом 18 (вход ступени)
 ((1108,500),[(1090,392),(1132,392),(1132,668),(1028,668),(1028,598),(1090,598)]),     # канал колеса 18
 ((1115,320),[(1088,246),(1142,246),(1142,395),(1088,395)]),                           # отвод колеса 18 вверх
 ((1250,272),[(1088,242),(1468,242),(1468,705),(1288,705),(1288,598),(1395,598),(1395,304),(1088,304)]),  # переводной канал к колесу 16
 ((1251,500),[(1226,398),(1280,398),(1280,598),(1335,598),(1335,660),(1226,660)]),     # канал колеса 16
 ((1255,365),[(1226,318),(1290,318),(1290,410),(1226,410)]),                           # отвод колеса 16
 ((1335,420),[(1286,322),(1388,322),(1388,522),(1286,522)]),                           # аппарат 15
 ((1100,960),[(1018,800),(1132,800),(1132,1100),(1090,1100),(1075,892),(1018,892)]),   # низ: колесо 18
 ((1245,960),[(1216,828),(1332,828),(1332,897),(1278,897),(1278,1102),(1216,1102)]),   # низ: колесо 16
 ((1340,1060),[(1293,958),(1392,958),(1392,1148),(1293,1148)]),                        # низ: аппарат 15
 ((1025,1050),[(998,958),(1062,958),(1062,1112),(998,1112)])]
# вода в рамке = белые участки, достаточно широкие (полосы штриховки узкие, каналы — широкие)
white5=~dark5;dtw=ndi.distance_transform_edt(white5)
hpw=np.zeros(g5.shape,bool)
for (sx,sy),roi in WSPEC:
    rm=np.zeros(g5.shape,np.uint8);cv2.fillPoly(rm,[np.array(roi,np.int32)],1)
    l,n=ndi.label(white5&(rm>0))
    mx=ndi.maximum(dtw,l,index=np.arange(n+1)) if n else np.zeros(1)
    keep=np.nonzero(np.asarray(mx)>=10)[0];keep=keep[keep>0]
    hpw|=np.isin(l,keep)
# заливаем тонкие линии лопаток и осевые линии внутри каналов
hpw=cv2.morphologyEx(hpw.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0
k5=np.ones((5,5),np.uint8)
m={n:cv2.dilate(np.isin(lab,ids).astype(np.uint8),k5) for n,ids in S.items()}
m['water']=cv2.dilate(hpw.astype(np.uint8),np.ones((3,3),np.uint8))
H,W=lab.shape;rgb=np.zeros((H,W,3),np.uint8)
rgb[...,0]=m['water']*255;rgb[...,1]=m['oil']*255;rgb[...,2]=np.where(m['shaft']>0,255,np.where(m['cool']>0,120,0))
webp(rgb,R+'hp_mask.webp')
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
# мелкие детали ступени ВД — прямоугольниками/многоугольниками по чертежу (их нет в 3D-модели)
hp_ids[hp_ids==21]=0
SMALL=[(21,[(860,650),(992,650),(992,680),(860,680)]),(21,[(860,792),(992,792),(992,822),(860,822)]),
 (6,[(805,615),(844,615),(844,657),(805,657)]),(6,[(803,813),(844,813),(844,857),(803,857)]),
 (7,[(880,578),(912,578),(912,609),(880,609)]),
 (8,[(833,578),(849,578),(849,594),(833,594)]),(8,[(885,580),(902,580),(902,594),(885,594)]),
 (20,[(833,878),(849,878),(849,894),(833,894)]),(20,[(885,878),(902,878),(902,894),(885,894)]),
 (2,[(268,535),(285,535),(285,550),(268,550)]),
 (3,[(232,506),(272,506),(272,522),(318,522),(318,560),(232,560)]),(3,[(232,966),(272,966),(272,950),(318,950),(318,912),(232,912)]),
 (10,[(1320,680),(1378,680),(1378,710),(1320,710)]),(10,[(1320,764),(1378,764),(1378,792),(1320,792)]),
 (11,[(1345,705),(1415,705),(1415,770),(1345,770)]),(12,[(1383,670),(1397,670),(1397,792),(1383,792)]),
 (9,[(1298,660),(1320,660),(1320,712),(1298,712)]),
 (13,[(1248,768),(1342,768),(1342,797),(1248,797)])]
for k,poly in SMALL:
    pm=np.zeros(hp_ids.shape,np.uint8);cv2.fillPoly(pm,[np.array(poly,np.int32)],1);hp_ids[(pm>0)]=k
# сетка 13: сферический сегмент (дуга) у входа в крышку
yy,xx=np.mgrid[0:nd_ids.shape[0],0:nd_ids.shape[1]]
rr=np.hypot(xx-1757.7,yy-954.5);band=(np.abs(rr-408)<=9)&(xx>=2090)
nd_ids[band]=13
hp_ids[hpw|np.isin(lab,S['cool'])]=0
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
D5['paths']=[  # 1-я ступень (колесо 18) → переводной канал → 2-я ступень (колесо 16) → аппарат 15; переход между ними вне плоскости разреза
 {'pts':[[1052,425],[1050,500],[1052,565],[1066,612],[1088,628],[1104,610],[1108,560],[1108,480],[1109,420],[1113,385],[1115,330]]+route_path([[1115,330],[1118,272],[1250,272],[1428,272],[1430,420],[1430,560],[1400,622],[1330,640],[1290,640]],rt5)[1:],'w':1},
 {'pts':[[1290,640],[1266,628],[1254,600],[1251,540],[1251,460],[1252,405],[1256,370],[1275,345],[1305,345],[1330,365],[1345,410],[1342,460],[1335,495]],'w':1},
 {'pts':route_path([[1040,850],[1078,860],[1100,900],[1100,980],[1100,1045],[1108,1085]],rt5),'w':1},
 {'pts':route_path([[1305,848],[1272,862],[1248,905],[1245,1000],[1248,1060],[1250,1090]],rt5),'w':1}]
D5['inlet']=[960,20];D5['outlet']=[[1300,170],[1300,30]]
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
