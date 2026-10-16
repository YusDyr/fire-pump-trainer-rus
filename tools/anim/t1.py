import sys;sys.path.insert(0,'anim')
from align import *
roi=(760,880,1060,1000)  # vac valve region scene coords
for f in ['222211','222209','222207','222204','222147','222144']:
    r=align(f,roi,margin=150)
    print(f,r['inl'],r['good'])
    w=colormatch(r['warp'],r['base'],r['valid'])
    cv2.imwrite(f'anim/vac_{f}.jpg',np.vstack([r['base'],w]))
