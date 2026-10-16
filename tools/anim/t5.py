import sys;sys.path.insert(0,'anim')
from align import *
def show(name,roi,fs,margin=100,ref=None,ratio=0.75):
    outs=[]
    for f in fs:
        r=align(f,roi,margin=margin,ratio=ratio)
        if ref: r=refine(r,ref)
        w=colormatch(r['warp'],r['base'],r['valid'])
        X0,Y0=r['off'];x0,y0,x1,y1=[int(v*K) for v in roi]
        print(name,f,r['inl'],r['good'])
        outs.append(np.vstack([r['base'][y0-Y0:y1-Y0,x0-X0:x1-X0],w[y0-Y0:y1-Y0,x0-X0:x1-X0]]))
    o=np.hstack(outs);s=900/o.shape[1];o=cv2.resize(o,None,fx=s,fy=s);cv2.imwrite(f'anim/{name}_cmp.jpg',o)
show('hpv',(600,980,800,1170),['215504','220108','220113','220120'],margin=120)
show('ft',(240,900,560,1120),['215950','215958','220037','220041','220001'],margin=120)
show('ej',(1010,1300,1190,1470),['215940','215944'],margin=100)
show('tank',(1150,1460,1760,1800),['215647','215620','215625'],margin=100)
