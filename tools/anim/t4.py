import sys;sys.path.insert(0,'anim')
from align import *
roi=(740,780,1110,990)
band=[(745,880,1105,945),(780,790,860,880)]
outs=[]
for f in ['222211','222209','222207','222204']:
    r=align(f,roi,margin=150)
    r=refine(r,[(b[0],b[1],b[2],b[3]) for b in band])
    print(f,np.round(r['W'],3).tolist())
    w=colormatch(r['warp'],r['base'],r['valid'])
    X0,Y0=r['off'];x0,y0,x1,y1=[int(v*K) for v in roi]
    outs.append(np.vstack([r['base'][y0-Y0:y1-Y0,x0-X0:x1-X0],w[y0-Y0:y1-Y0,x0-X0:x1-X0]]))
o=np.hstack(outs);o=cv2.resize(o,None,fx=0.55,fy=0.55);cv2.imwrite('anim/vac_cmp4.jpg',o)
