import sys;sys.path.insert(0,'anim')
from align import *
import pickle
W={'w1':dict(c=(1818,1462),r=126,fs='215732 215735 215737 215739 215741 215742 215744 215746 215748 215750 215752 215753 215755 215756 215757 215759'.split()),
   'w0':dict(c=(625,1439),r=128,fs='215809 215810 215812 215815 215817 215819 215821 215823 215825 215827 215830 215831 215833 215834 215835 215836 215838 215839'.split())}
out={}
for k,o in W.items():
    cx,cy=o['c'];R=o['r'];roi=(cx-R-40,cy-R-40,cx+R+40,cy+R+40)
    tiles=[]
    for f in o['fs']:
        r=align(f,roi,margin=170,ratio=0.75,excl=[(cx-R-15,cy-R-15,cx+R+15,cy+R+15)])
        w=colormatch(r['warp'],r['base'],r['valid'])
        X0,Y0=r['off'];x0,y0,x1,y1=[int(v*K) for v in roi]
        crop=w[y0-Y0:y1-Y0,x0-X0:x1-X0]
        out[(k,f)]=dict(img=crop,inl=r['inl'],roi=roi)
        print(k,f,r['inl'],r['good'])
        t=crop.copy();cv2.circle(t,(int((cx-roi[0])*K),int((cy-roi[1])*K)),int(R*K),(0,255,0),1);cv2.putText(t,f,(5,20),0,0.6,(0,255,255),2)
        tiles.append(cv2.resize(t,(260,260)))
    rows=[np.hstack(tiles[i:i+6]+[np.zeros((260,260,3),np.uint8)]*(6-len(tiles[i:i+6]))) for i in range(0,len(tiles),6)]
    cv2.imwrite(f'anim/{k}_tiles.jpg',np.vstack(rows))
pickle.dump(out,open('anim/wheels.pkl','wb'))
