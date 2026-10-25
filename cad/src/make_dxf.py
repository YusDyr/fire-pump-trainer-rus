import ezdxf, parts as P, re
from ezdxf.enums import TextEntityAlignment
doc=ezdxf.new('R2010',setup=True); msp=doc.modelspace()
doc.layers.add('OS',color=1,linetype='CENTER')
def X(px): return (px-P.X0)/P.S
L=max(X(x) for _,_,_,_,poly in P.REV for x,_ in poly)
msp.add_line((-10,0),(L+30,0),dxfattribs={'layer':'OS'})
for i,(nm,label,c,tr,poly) in enumerate(P.REV):
    lay=re.sub(r'[^0-9A-Za-z_]','_',nm)
    rgb=tuple(int(v*255) for v in c)
    l=doc.layers.add(lay); l.rgb=rgb
    for sgn in (1,-1):
        pts=[(X(x),sgn*r) for x,r in poly]
        msp.add_lwpolyline(pts,close=True,dxfattribs={'layer':lay})
    m=re.match(r'(\d+)',label)
    if m:
        cx=sum(X(x) for x,_ in poly)/len(poly); cy=max(r for _,r in poly)+4
        msp.add_text(m.group(1),height=5,dxfattribs={'layer':lay}).set_placement((cx,cy),align=TextEntityAlignment.BOTTOM_CENTER)
msp.add_text('НЦПК-40/100-4/400. Ступень нормального давления. Полупрофили деталей по рис. 2 РЭ насоса, мм',height=6).set_placement((0,-185))
msp.add_text('Масштаб снят по подшипникам 309/307/7000108; точность около ±1 мм',height=4).set_placement((0,-195))
doc.saveas('out/NCPK_nasos_profili_ND.dxf'); print('dxf ok')
