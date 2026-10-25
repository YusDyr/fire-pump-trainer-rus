# Сборка модели ступени НД НЦПК-40/100-4/400 во FreeCAD 1.0 (запускать в GUI-режиме, можно offscreen)
import sys, os, math
HERE = os.environ.get('NCPK_DIR', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import FreeCAD as App, FreeCADGui as Gui, Part, Sketcher
from FreeCAD import Vector as V, Placement, Rotation
import parts as P
CUT = os.environ.get('NCPK_CUT') == '1'
OUT = os.environ.get('NCPK_OUT', os.path.join(HERE, 'out'))
os.makedirs(OUT, exist_ok=True)
LOG=open(os.path.join(OUT,'log%s.txt'%('_cut' if CUT else '')),'w',encoding='utf-8')
def print(*a):
    LOG.write(' '.join(map(str,a))+'\n'); LOG.flush()
name = 'NCPK_nasos_razrez' if CUT else 'NCPK_nasos'
doc = App.newDocument(name)
doc.Label = 'НЦПК-40/100-4/400 — ступени НД и ВД' + (' (разрез)' if CUT else '')

def xmm(px): return (px - P.X0) / P.S

grp = {}
for g in ['Проточная часть', 'Вал и опоры', 'Привод ступени ВД', 'Уплотнение вала', 'Корпусные детали', 'Тахометр', 'Ступень ВД', 'Подложка']:
    grp[g] = doc.addObject('App::DocumentObjectGroup', 'G%d' % len(grp)); grp[g].Label = g
def group_of(label):
    if label.startswith('ВД '): return 'Ступень ВД'
    n = label.split(' ')[0]
    m = {'Проточная часть': ['11','12','13','14','Напорный','Гайка'],
         'Вал и опоры': ['Вал','1','3','4','9','25','26','Гайка'],
         'Привод ступени ВД': ['5','6','8','19','Барабан'],
         'Уплотнение вала': ['10','15','17','Гильза','Нажимное'],
         'Корпусные детали': ['20','18'], 'Тахометр': ['2','24']}
    if label.startswith('Гайка крепления'): return 'Проточная часть'
    if label.startswith('Гайка конца'): return 'Вал и опоры'
    for g, keys in m.items():
        if n in keys: return g
    return 'Корпусные детали'

cutter = None
if CUT:  # вырезаем четверть: x любой, y<0, z>0 (смотрим спереди — видно внутренность)
    cutter = Part.makeBox(2000, 999.7, 1000, V(-500, -1000, 0.37))

def color(obj, c, tr=0):
    if App.GuiUp:
        obj.ViewObject.ShapeColor = c
        obj.ViewObject.Transparency = tr

def finish(obj, label, c, tr=0):
    color(obj, c, tr)
    grp[group_of(label)].addObject(obj)

def rev_body(nm, label, c, tr, poly):
    pts = [V(xmm(x), r, 0) for x, r in poly]
    if CUT:
        face = Part.Face(Part.makePolygon(pts + [pts[0]]))
        face.rotate(V(0,0,0), V(1,0,0), 90)  # плоскость XY -> XZ
        sol = face.revolve(V(0,0,0), V(1,0,0), 360).cut(cutter)
        o = doc.addObject('Part::Feature', nm); o.Label = label; o.Shape = sol
        finish(o, label, c, tr); return o
    body = doc.addObject('PartDesign::Body', nm); body.Label = label
    sk = body.newObject('Sketcher::SketchObject', nm + '_Profil'); sk.Label = label + ' — профиль'
    sk.AttachmentSupport = [(body.Origin.OriginFeatures[4], '')]  # XZ_Plane
    sk.MapMode = 'FlatFace'
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        sk.addGeometry(Part.LineSegment(V(a.x, a.y, 0), V(b.x, b.y, 0)), False)
    for i in range(n):
        sk.addConstraint(Sketcher.Constraint('Coincident', i, 2, (i + 1) % n, 1))
    rv = body.newObject('PartDesign::Revolution', nm + '_Vrashchenie'); rv.Label = label + ' — вращение'
    rv.Profile = sk; rv.ReferenceAxis = (sk, ['H_Axis']); rv.Angle = 360
    sk.Visibility = False
    finish(body, label, c, tr)
    return body

for nm, label, c, tr, poly in P.REV:
    if nm == 'Kryshka_12': continue
    rev_body(nm, label, c, tr, poly)
doc.recompute()

hpcutter = Part.makeBox(2000, 600, 600, V(-500, -600, 55.0)) if CUT else None
def feat(nm, label, shape, c, tr=0, precut=False):
    if CUT and not precut:
        shape = shape.cut(hpcutter if label.startswith('ВД ') else cutter)
        if shape.isNull() or not shape.Solids: return None
    o = doc.addObject('Part::Feature', nm); o.Label = label; o.Shape = shape
    finish(o, label, c, tr); return o

def revolve_xy(poly_mm):
    pts = [V(x, r, 0) for x, r in poly_mm]
    f = Part.Face(Part.makePolygon(pts + [pts[0]])); f.rotate(V(0,0,0), V(1,0,0), 90)
    return f.revolve(V(0,0,0), V(1,0,0), 360)

import asym
feat('Korpus_nasosa_20', '20 Корпус насоса (улитка, напорный патрубок, приливы)', asym.casing(cutter), (0.55,0.6,0.66), precut=True)
_cv = [p for p in P.REV if p[0] == 'Kryshka_12'][0]
feat('Kryshka_12', _cv[1], asym.cover_extra(revolve_xy([(xmm(x), r) for x, r in _cv[4]])), _cv[2])
_b, _s = asym.fasteners()
feat('Bolty_kryshki', 'Болты крышки M12 (8 шт.)', _b, (0.35,0.36,0.4))
feat('Shpilki_vsasyvaniya', 'Шпильки фланца всасывания M16 (6 шт.)', _s, (0.35,0.36,0.4))
feat('Kran_slivnoy_16', '16 Кран сливной', asym.drain_valve(), (0.75,0.6,0.2))
feat('Shchup', 'Щуп/сапун (условно)', Part.makeCylinder(3, 36, V(xmm(1080), 0, 64), V(0,0,1)).fuse(Part.makeCylinder(8, 5, V(xmm(1080), 0, 100), V(0,0,1))), (0.3,0.3,0.32))

# Лопатки
B = P.BLADES
tb = math.tan(math.radians(B['beta_deg']))
th_max = math.log(B['r2'] / B['r1']) / tb
def spiral(off):
    pts = []
    for i in range(41):
        th = th_max * i / 40; r = B['r1'] * math.exp(th * tb)
        # плоскость YZ (ось вала X); нормаль к спирали ~ смещение по углу
        dth = off / r
        pts.append((r, th + dth))
    return pts
side1 = spiral(B['t'] / 2); side2 = spiral(-B['t'] / 2)
x0 = xmm(1455); x1 = xmm(1720)
prof = [V(x0, r * math.cos(t), r * math.sin(t)) for r, t in side1] + [V(x0, r * math.cos(t), r * math.sin(t)) for r, t in reversed(side2)]
blade = Part.Face(Part.makePolygon(prof + [prof[0]])).extrude(V(x1 - x0, 0, 0))
chan = revolve_xy([(xmm(x), r) for x, r in B['channel']])
blade = blade.common(chan)
blades = [blade.copy() for _ in range(B['n'])]
for k, b in enumerate(blades): b.rotate(V(0,0,0), V(1,0,0), 360.0 * k / B['n'])
feat('Lopatki', '14 Колесо рабочее: лопатки (6 шт., форма условная)', Part.makeCompound(blades), (0.8,0.63,0.33))

# Сетка 13 — сферический сегмент
Sv = P.SIEVE; a = Sv['r_base']; h = xmm(Sv['x_apex']) - xmm(Sv['x_base']); R = (a*a + h*h) / (2*h)
cx = xmm(Sv['x_apex']) - R
outer = Part.makeSphere(R, V(cx, 0, 0)); inner = Part.makeSphere(R - Sv['t'], V(cx, 0, 0))
cap = outer.cut(inner).common(Part.makeBox(h + 1, 2*a + 4, 2*a + 4, V(xmm(Sv['x_base']), -a - 2, -a - 2)))
feat('Setka_13', '13 Сетка', cap, (0.3,0.32,0.35), 35)

# Пакет дисков муфты 5
Cl = P.CLUTCH; w = (xmm(Cl['x2']) - xmm(Cl['x1'])) / Cl['n']
steel, fric = [], []
for i in range(Cl['n']):
    xa = xmm(Cl['x1']) + i * w
    ri, ro = (Cl['r_in'], Cl['r_out'] - 1.5) if i % 2 else (Cl['r_in'] + 3, Cl['r_out'])
    d = Part.makeCylinder(ro, w * 0.86, V(xa, 0, 0), V(1,0,0)).cut(Part.makeCylinder(ri, w, V(xa - 0.1, 0, 0), V(1,0,0)))
    (fric if i % 2 else steel).append(d)
feat('Mufta_5_stalnye', '5 Муфта фрикционная: стальные диски', Part.makeCompound(steel), (0.75,0.76,0.8))
feat('Mufta_5_frikcionnye', '5 Муфта фрикционная: фрикционные диски', Part.makeCompound(fric), (0.85,0.42,0.12))

# Радиальные детали
for nm, label, c, xpx, r0, r1, rad, sd in P.RADIAL:
    base = V(xmm(xpx), 0, r0 * sd)
    if nm.startswith('Patrubok'):
        sh = Part.makeCylinder(rad, r1 - r0, base, V(0,0,sd)).cut(Part.makeCylinder(rad - 7, r1 - r0 + 1, base, V(0,0,sd)))
        fl = Part.makeCylinder(rad + 30, 18, V(xmm(xpx), 0, (r1 - 18) * sd), V(0,0,sd)).cut(Part.makeCylinder(rad - 7, 20, V(xmm(xpx), 0, (r1 - 19) * sd), V(0,0,sd)))
        sh = sh.fuse(fl)
    else:
        sh = Part.makeCylinder(rad, r1 - r0, base, V(0,0,sd))
    feat(nm, label, sh, c)
F = P.FORK
feat(F['name'], F['label'], Part.makeCylinder(F['r'], F['L'], V(xmm(F['x']), -55, F['z']), V(0,1,0)), F['color'])
import hp
for _n, _l, _s, _c in hp.build():
    feat(_n, _l, _s, _c)

# Подложка: рис. 2 в масштабе, в плоскости XZ, за моделью
img = os.path.join(HERE, 'ris2_stupen_ND.png')
if os.path.exists(img) and not CUT:
    ip = doc.addObject('Image::ImagePlane', 'Podlozhka_ris2'); ip.Label = 'Подложка: рис. 2 РЭ насоса (масштаб 1:1)'
    ip.ImageFile = img
    ip.XSize = 2272 / P.S; ip.YSize = 1809 / P.S
    ip.Placement = Placement(V(xmm(1136), 180, (P.AXIS_Y - 904.5) / P.S), Rotation(V(1,0,0), 90))
    grp['Подложка'].addObject(ip)
    if App.GuiUp: ip.ViewObject.Transparency = 30

doc.recompute()
fc = os.path.join(OUT, name + '.FCStd'); doc.saveAs(fc)
# экспорт STEP (с цветами) и glTF
objs = [o for o in doc.Objects if hasattr(o, 'Shape') and o.TypeId in ('PartDesign::Body', 'Part::Feature') and not o.Shape.isNull()]
try:
    import Import; Import.export(objs, os.path.join(OUT, name + '.step'))
except Exception as e: print('STEP fail', e)
try:
    import ImportGui; ImportGui.export(objs, os.path.join(OUT, name + '.glb'))
except Exception as e: print('GLB fail', e)
bb = None
for o in objs:
    b = o.Shape.BoundBox; bb = b if bb is None else bb.united(b)
print('OBJS', len(objs), 'BB', bb)
for o in objs:
    print(o.Label, round(o.Shape.Volume/1000,1), 'см3', o.Shape.isValid())
os._exit(0)
