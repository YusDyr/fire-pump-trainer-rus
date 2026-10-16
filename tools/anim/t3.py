import sys;sys.path.insert(0,'anim')
from align import *
roi=(740,780,1110,990)
band=[(700,780,1250,958)]
outs=[]
for f in ['222211','222209','222207','222204']:
    r=align3(f,roi,band)
    print(f,r['inl'],r['good'],np.round(r['H'][:2],3).tolist())
    w=colormatch(r['warp'],r['base'],r['valid'])
    outs.append(np.vstack([r['base'],w]))
o=np.hstack(outs);o=cv2.resize(o,None,fx=0.55,fy=0.55);cv2.imwrite('anim/vac_cmp3.jpg',o)
