# Модель насоса НЦПК-40/100-4/400М-В1У по РЭ 2025 г. (Миасс) для FreeCAD 1.0.
# Запуск: NCPK_DIR=<этот каталог> QT_QPA_PLATFORM=offscreen freecad run_m.py
#
# Источники геометрии:
#  * ступень НД — рис. 3: полупрофили деталей сняты с размеченного чертежа (profiles.json), масштаб 2,95 пикс/мм
#    по подшипнику 180309 (D 100, d 45), ось вала — x, x = 0 у торца полумуфты;
#  * ступень ВД — рис. 4: масштаб 2,61 пикс/мм по подшипнику 80308 (D 90, d 40);
#  * взаимное положение ступеней и ремень — рис. 5: масштаб 0,358 мм/пикс по длине ремня 16РК812 (812 мм),
#    ось ВД смещена от оси НД на 201 мм вбок (−y) и 72 мм вверх; шкивы в одной плоскости;
#  * обвязка, БУК-02, вакуумный агрегат, пневмоостров — по видам рис. 1 и 2 (рендеры без размеров, ±15–20 мм).
# Система координат: x — вдоль вала НД от привода ко входу, z — вверх, +y — вправо, если смотреть со стороны входа.
import sys, os, math, json
HERE = os.environ.get('NCPK_DIR', os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App, Part
from FreeCAD import Vector as V, Placement, Rotation
CUT = os.environ.get('NCPK_CUT') == '1'
OUT = os.environ.get('NCPK_OUT', os.path.join(HERE, 'out'))
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, 'log_m%s.txt' % ('_cut' if CUT else '')), 'w', encoding='utf-8')
def log(*a): LOG.write(' '.join(map(str, a)) + '\n'); LOG.flush()
PR = json.load(open(os.path.join(HERE, 'profiles.json'), encoding='utf-8'))
name = 'NCPK_M_V1U_razrez' if CUT else 'NCPK_M_V1U'
doc = App.newDocument(name)
doc.Label = 'НЦПК-40/100-4/400М-В1У' + (' (разрез)' if CUT else '')

GR = {}
def group(g):
    if g not in GR:
        o = doc.addObject('App::DocumentObjectGroup', 'G%d' % len(GR)); o.Label = g; GR[g] = o
    return GR[g]

HPY, HPZ = -201.0, 72.0          # ось ступени ВД относительно оси НД
XP = 69.5                        # плоскость ремня (середина ручьёв шкивов)
cutter = Part.makeBox(3000, 3000, 3000, V(-1500, -3000, 0.3)) if CUT else None   # разрез по вертикальной плоскости оси НД: убираем y<0... см. ниже

def add(nm, label, shape, col, g, tr=0):
    if CUT and cutter is not None:
        try:
            shape = shape.cut(cutter)
        except Exception as e:
            log('cut fail', label, e)
    if shape.isNull() or shape.Volume < 1e-3:
        log('пусто', label); return None
    o = doc.addObject('Part::Feature', nm); o.Label = label; o.Shape = shape
    if App.GuiUp:
        o.ViewObject.ShapeColor = col; o.ViewObject.Transparency = tr
    group(g).addObject(o); return o

def revolve(polys, axis_pos=V(0, 0, 0), x_off=0.0):
    sol = None
    for poly in polys:
        pts = [V(x + x_off, 0, r) for x, r in poly]
        if len(pts) < 3: continue
        try:
            w = Part.makePolygon(pts + [pts[0]]); f = Part.Face(w)
            if not f.isValid(): f.fix(1e-3, 1e-3, 1e-3)
            s = f.revolve(V(0, 0, 0), V(1, 0, 0), 360)
            s = Part.Solid(Part.Shell(s.Faces)) if s.ShapeType != 'Solid' and s.Faces else s
        except Exception as e:
            log('revolve fail', e); continue
        sol = s if sol is None else sol.fuse(s)
    if sol is None: return None
    if axis_pos != V(0, 0, 0): sol.translate(axis_pos)
    return sol

def cyl(r, h, p, d): return Part.makeCylinder(r, h, p, d)
def box(x0, y0, z0, x1, y1, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def tube(r1, r0, h, p, d): return cyl(r1, h, p, d).cut(cyl(r0, h + 2, p - d * 1, d))
def face_yz(poly, x):
    w = Part.makePolygon([V(x, y, z) for y, z in poly] + [V(x, poly[0][0], poly[0][1])]); return Part.Face(w)
def vane_solid(x0, x1, r0, r1, a0, sweep, th, cy=0.0, cz=0.0, K=10):
    """Лопатка: изогнутая пластина между радиусами r0..r1 (угол a0 → a0+sweep), ширина по оси x0..x1."""
    side1, side2 = [], []
    for k in range(K + 1):
        t = k / K; r = r0 + (r1 - r0) * t; a = a0 + sweep * t; da = th / 2 / max(r, 1)
        side1.append((cy + r * math.sin(a - da), cz + r * math.cos(a - da)))
        side2.append((cy + r * math.sin(a + da), cz + r * math.cos(a + da)))
    poly = side1 + side2[::-1]
    return face_yz(poly, x0).extrude(V(x1 - x0, 0, 0))
def vanes_solid(n, *a, **k):
    sol = None
    for i in range(n):
        v = vane_solid(a[0], a[1], a[2], a[3], 2 * math.pi * i / n + (a[4] if len(a) > 4 else 0), *a[5:], **k) if False else None
    return sol
def ring_of(n, fn):
    sol = None
    for i in range(n):
        s_ = fn(2 * math.pi * i / n)
        sol = s_ if sol is None else sol.fuse(s_)
    return sol
def hexprism(c, d, s, h):
    """Шестигранник «под ключ» s, высота h, ось d (единичный вектор по оси), основание в точке c."""
    pts = [V(s / math.sqrt(3) * math.cos(math.pi / 3 * i), s / math.sqrt(3) * math.sin(math.pi / 3 * i), 0) for i in range(6)]
    f = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(0, 0, h))
    rot = Rotation(V(0, 0, 1), d); f = f.transformGeometry(Placement(V(0, 0, 0), rot).toMatrix()); f.translate(c); return f
def bolt(c, d, M=10, L=25):
    """Болт/шпилька с гайкой: шестигранник у точки c, стержень вдоль d."""
    return hexprism(c, d, M * 1.6, M * 0.7).fuse(cyl(M / 2, L, c - d * (L - M * 0.7), d))
def pipeline(pts, r):
    sol = None
    for a, b in zip(pts, pts[1:]):
        a, b = V(*a), V(*b); L = (b - a).Length
        if L < 0.1: continue
        seg = cyl(r, L, a, (b - a).normalize())
        sol = seg if sol is None else sol.fuse(seg)
    for p in pts[1:-1]: sol = sol.fuse(Part.makeSphere(r, V(*p)))
    return sol


STEEL = (0.78, 0.79, 0.82); CAST = (0.55, 0.6, 0.66); BLUE = (0.36, 0.45, 0.72); BRG = (0.22, 0.23, 0.27)
BRONZE = (0.8, 0.63, 0.33); RUBBER = (0.08, 0.08, 0.08); RED = (0.8, 0.12, 0.1); ORANGE = (0.9, 0.48, 0.12)
MAG = (0.78, 0.25, 0.7); YEL = (0.88, 0.78, 0.2); GREY = (0.62, 0.63, 0.66); DARK = (0.3, 0.31, 0.34)

# ---------------- ступень НД (рис. 3) ----------------
ND_NAMES = {1: 'Полумуфта', 2: 'Подшипник 80108 (2 шт.)', 3: 'Шкив ведущий', 4: 'Диск прижимной',
            5: 'Муфта электромагнитная Э1ТМ', 6: 'Подшипник 180309', 8: 'Ротор датчика тахометра', 9: 'Подшипник 180309',
            10: 'Кольцо 095-100-30', 11: 'Кольцо 095-100-30', 14: 'Кольцо 275-285-58', 15: 'Колесо рабочее',
            16: 'Крышка насоса', 17: 'Сетка', 18: 'Сальниковое уплотнение вала', 20: 'Кольцо дистанционное', 21: 'Кольцо',
            22: 'Вал', 23: 'Прокладки регулировочные', 24: 'Прокладки регулировочные', 25: 'Гайка', 26: 'Шплинт'}
ND_COL = {1: DARK, 2: BRG, 3: ORANGE, 4: (0.85, 0.6, 0.3), 5: MAG, 6: BRG, 8: (0.65, 0.55, 0.3), 9: BRG, 10: RUBBER, 11: RUBBER,
          14: RUBBER, 15: BRONZE, 16: BLUE, 17: MAG, 18: (0.15, 0.15, 0.15), 20: STEEL, 21: STEEL, 22: STEEL, 23: YEL, 24: YEL,
          25: DARK, 26: STEEL}
for k, nm in ND_NAMES.items():
    s = revolve(PR['ND'][str(k)])
    if s is None: log('нет профиля НД', k); continue
    add('ND_%d' % k, 'НД %d %s' % (k, nm), s, ND_COL[k], 'Ступень НД (рис. 3)', 70 if k == 17 else 0)

# корпус 13: тело вращения по профилю (до r 178) + напорный патрубок и фланец вверх
casing = revolve(PR['ND']['13'])
low = revolve(PR['ND']['13low'])
# улитка: нижняя половина профиля шире — берём её для низа корпуса
if low is not None:
    casing = casing.fuse(low.common(box(-100, -400, -400, 800, 400, 0))) if casing else low
# напорный патрубок — касательный выход улитки вверх справа (рис. 1 РЭ: правый край корпуса прямой до фланца коллектора)
# (рис. 3 — сечение по оси — тоже показывает патрубок над колесом, поэтому патрубок широкий: от оси до правого края улитки)
YN = 95
neck = box(420, YN - 105, 60, 473, YN + 105, 212).cut(box(428, YN - 95, 50, 465, YN + 95, 215))
flange = box(405, YN - 110, 212, 475, YN + 110, 245).cut(cyl(50, 50, V(440, YN, 200), V(0, 0, 1)))
casing = casing.fuse(neck).fuse(flange)
add('ND_13', 'НД 13 Корпус насоса', casing, BLUE, 'Ступень НД (рис. 3)')
add('ND_12', 'НД 12 Кольцо 108-115-46', tube(57.5, 54, 3, V(440, YN, 240), V(0, 0, 1)), RUBBER, 'Ступень НД (рис. 3)')
# датчик тахометра 7 — радиально вверх; штуцер дренажа 19 — вниз
add('ND_7', 'НД 7 Датчик тахометра', cyl(9, 86, V(213, 0, 43), V(0, 0, 1)).fuse(cyl(13, 20, V(213, 0, 95), V(0, 0, 1))), (0.3, 0.6, 0.35), 'Ступень НД (рис. 3)')
add('ND_19', 'НД 19 Штуцер дренажного отверстия', cyl(5.5, 40, V(373.6, 0, -82), V(0, 0, -1)).fuse(cyl(8, 10, V(373.6, 0, -82), V(0, 0, -1))), BRONZE, 'Ступень НД (рис. 3)')

# ---------------- ступень ВД (рис. 4) ----------------
HP_NAMES = {1: 'Корпус насоса (со стороны входа)', 2: 'Аппарат направляющий', 3: 'Колесо рабочее (лопатки направо)',
            4: 'Аппарат направляющий', 5: 'Колесо рабочее (лопатки налево)', 6: 'Корпус насоса и опор', 7: 'Сальниковое уплотнение вала',
            8: 'Подшипник 80308', 9: 'Вал', 10: 'Подшипник 3308', 11: 'Шкив ведомый', 12: 'Кольцо 080-085-30', 13: 'Кольцо 072-078-25',
            14: 'Кольцо 200-210-46', 15: 'Кольцо 200-210-46', 17: 'Втулка'}
HP_COL = {1: MAG, 2: (0.7, 0.55, 0.9), 3: BRONZE, 4: (0.55, 0.45, 0.85), 5: BRONZE, 6: (0.8, 0.35, 0.75), 7: (0.15, 0.15, 0.15), 8: BRG,
          9: STEEL, 10: BRG, 11: ORANGE, 12: RUBBER, 13: RUBBER, 14: RUBBER, 15: RUBBER, 17: STEEL}
HPA = V(0, HPY, HPZ)
for k, nm in HP_NAMES.items():
    s = revolve(PR['HP'][str(k)], HPA, XP)
    if s is None: log('нет профиля ВД', k); continue
    if k in (1, 6):
        # по рис. 3/4/5 наружный обвод корпуса ступени ВД заходит в корпус 13 на 20–30 мм (точность снятия ±5 мм);
        # до сверки с насосом срезаем пересечение, чтобы тела не проникали друг в друга
        s = s.cut(casing)
    add('HP_%d' % k, 'ВД %d %s' % (k, nm), s, HP_COL[k], 'Ступень ВД (рис. 4)')
# фланец с патрубками входа и выхода ступени ВД (сверху)
def hx(px): return XP + (1795 - px) / 2.61
ports = box(hx(1360), HPY - 48, HPZ + 120, hx(912), HPY + 48, HPZ + 158)
for a, b in ((962, 1048), (1192, 1318)):
    ports = ports.cut(cyl(17, 60, V((hx(a) + hx(b)) / 2, HPY, HPZ + 110), V(0, 0, 1)))
neck2 = box(hx(1330), HPY - 40, HPZ + 95, hx(950), HPY + 40, HPZ + 122)
add('HP_ports', 'ВД 1 Патрубки входа и выхода', ports.fuse(neck2), MAG, 'Ступень ВД (рис. 4)')
for i, px in enumerate((1010, 1290)):
    add('HP_dr%d' % i, 'ВД %d Кран сливной' % (19 if i == 0 else 18),
        box(hx(px) - 18, HPY - 22, HPZ - 165, hx(px) + 18, HPY + 22, HPZ - 125).fuse(cyl(5, 30, V(hx(px), HPY, HPZ - 165), V(0, 0, -1))), YEL, 'Ступень ВД (рис. 4)')

# ---------------- ремённый привод (рис. 5) ----------------
s5 = 0.3577
C1 = (335, 494); C7 = (897, 294); C4 = (682, 188)
def p5(px, py): return (-(px - C1[0]) * s5, -(py - C1[1]) * s5)   # вид сзади: вправо на рисунке = −y
def tangent(c1, r1, c2, r2, s):
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; vx, vy = -uy, ux
    a = (r1 - r2) / L; b = math.sqrt(max(0, 1 - a * a)); nx, ny = a * ux + s * b * vx, a * uy + s * b * vy
    return (c1[0] + r1 * nx, c1[1] + r1 * ny), (c2[0] + r2 * nx, c2[1] + r2 * ny)
CC = [(C1[0], C1[1], 235), (C4[0], C4[1], -41), (C7[0], C7[1], 98)]
pts = []
segs = [tangent(CC[i][:2], CC[i][2], CC[(i + 1) % 3][:2], CC[(i + 1) % 3][2], -1) for i in range(3)]
for i in range(3):
    c = CC[(i + 1) % 3]; a = segs[i][1]; b = segs[(i + 1) % 3][0]; pts += [segs[i][0], a]
    a0 = math.atan2(a[1] - c[1], a[0] - c[0]); a1 = math.atan2(b[1] - c[1], b[0] - c[0]); da = a1 - a0
    if c[2] > 0:
        while da < 0: da += 2 * math.pi
    else:
        while da > 0: da -= 2 * math.pi
    for k in range(1, 24):
        t = a0 + da * k / 24; pts.append((c[0] + abs(c[2]) * math.cos(t), c[1] + abs(c[2]) * math.sin(t)))
P = [p5(*q) for q in pts]
def offpoly(P, d):
    out = []; n = len(P)
    for i in range(n):
        a = P[i - 1]; b = P[(i + 1) % n]; tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1
        out.append((P[i][0] - ty / L * d, P[i][1] + tx / L * d))
    return out
try:
    outer = face_yz(offpoly(P, 2.2), XP - 28.5).extrude(V(57, 0, 0)); inner = face_yz(offpoly(P, -2.2), XP - 29).extrude(V(58, 0, 0))
    # ориентация обхода может быть любой: тело ремня — разность большего и меньшего
    belt = outer.cut(inner) if outer.Volume > inner.Volume else inner.cut(outer)
    add('BELT', 'Р 3 Ремень поликлиновой 16РК812Lb', belt, RUBBER, 'Привод ступени ВД (рис. 5)')
except Exception as e:
    log('ремень', e)
y4, z4 = p5(*C4)
add('ROLLER', 'Р 4 Ролик натяжной', cyl(14.7, 30, V(XP - 15, y4, z4), V(1, 0, 0)).fuse(cyl(6, 62, V(XP - 46, y4, z4), V(1, 0, 0))), (0.85, 0.55, 0.2), 'Привод ступени ВД (рис. 5)')
plate = [p5(598, 92), p5(760, 88), p5(1000, 105), p5(1060, 160), p5(1080, 300), p5(1050, 420), p5(980, 470), p5(870, 500), p5(780, 470), p5(730, 420), p5(700, 330), p5(610, 250), p5(590, 200)]
pl = face_yz(plate, XP - 44).extrude(V(6, 0, 0)).cut(cyl(22, 20, V(XP - 50, HPY, HPZ), V(1, 0, 0)))
add('PLATE', 'Р 5 Пластина натяжителя', pl, YEL, 'Привод ступени ВД (рис. 5)')
y6, z6 = p5(922, 133)
add('NUT6', 'Р 6 Гайка', cyl(7, 10, V(XP - 54, y6, z6), V(1, 0, 0)), DARK, 'Привод ступени ВД (рис. 5)')
# кожух ремня (на рис. 2 — чёрный кожух сверху)
guard = []
gp = [p5(*q) for q in [(40, 300), (200, 140), (450, 95), (700, 60), (980, 70), (1100, 160), (1120, 330), (1060, 480), (920, 560), (760, 700), (560, 780), (330, 795), (130, 740), (30, 560)]]
# кожух ремня (рис. 2): П-образная дуга над ремнём и вокруг ведущего шкива
def arc_shell(x0, x1, cy, cz, r0, r1, a0, a1, K=36):
    """Цилиндрическая обечайка вокруг оси x: углы a0..a1 (y = r·sin a, z = r·cos a)."""
    o = [(cy + r1 * math.sin(a0 + (a1 - a0) * k / K), cz + r1 * math.cos(a0 + (a1 - a0) * k / K)) for k in range(K + 1)]
    n = [(cy + r0 * math.sin(a0 + (a1 - a0) * k / K), cz + r0 * math.cos(a0 + (a1 - a0) * k / K)) for k in range(K + 1)]
    return face_yz(o + n[::-1], x0).extrude(V(x1 - x0, 0, 0))
try:
    # рис. 2: кожух — широкая обечайка вокруг ведущего шкива и муфты (снаружи, со стороны, противоположной СВД,
    # почти до низа), над ремнём переходит в прямую крышку до ведомого шкива и огибает его сверху
    gf = arc_shell(28, 182, 0, 0, 128, 134, math.radians(-20), math.radians(165))
    gf = gf.fuse(arc_shell(28, 110, HPY, HPZ, 58, 64, math.radians(-110), math.radians(-5)))
    ya, za = 134 * math.sin(math.radians(-20)), 134 * math.cos(math.radians(-20))
    yb, zb = HPY + 64 * math.sin(math.radians(-5)), HPZ + 64 * math.cos(math.radians(-5))
    L_ = math.hypot(ya - yb, za - zb); ny, nz = -(za - zb) / L_ * 6, (ya - yb) / L_ * 6
    gf = gf.fuse(face_yz([(yb, zb), (ya, za), (ya + ny, za + nz), (yb + ny, zb + nz)], 28).extrude(V(82, 0, 0)))
except Exception as e:
    log('кожух', e); gf = face_yz(gp, XP - 62).extrude(V(4, 0, 0))
add('GUARD', 'Р Кожух ремённой передачи', gf, (0.12, 0.12, 0.13), 'Привод ступени ВД (рис. 5)')

# ---------------- обвязка и органы управления (рис. 1, 2) ----------------
def f1(px, py): return ((px - 540) * 0.9, (690 - py) * 0.9)   # рис. 1, вид со стороны входа: y, z
# ---- положения узлов обвязки по фото отсека (масштаб по БУК-02 и фланцу входа; y, z в мм; ±15 мм) ----
PH = dict(V1L=(-290, 258), V1R=(380, 250), VT=(145, 325), LAF=(125, 400), G11=(285, 500), G15=(115, 104), G22=(-292, 133),
          GATE=(-147, 560), DOZ=(-154, 278), EJ=(-30, 293), MIX=(-30, 176), HPV=(-224, 468), FOAMV=(-400, 520), OIL=(191, 238))
G = 'Обвязка и органы управления (рис. 1, 2)'
# напорный коллектор над фланцем ступени НД
coll = box(370, -120, 245, 525, 175, 330).fuse(box(395, -290, 270, 500, -120, 318)).fuse(box(395, 175, 270, 500, 380, 318))
coll = coll.cut(box(380, -285, 258, 515, 370, 318))
add('COLL', 'П Коллектор напорный', coll, (0.7, 0.72, 0.75), G)
VALVE_YAW = 30   # крышка и маховик напорных вентилей DN70 развёрнуты наружу (рис. 1, фото)
def valve(nm, label, y, z, sgn, dn):
    # угловой вентиль (фото): литой корпус, крышка с маховиком вперёд, выход вниз-наружу через квадратный фланец
    # в напорный трубопровод АЦ, который отводом уходит вниз к боковым напорным патрубкам
    c = V(447, y, z); d = V(0, sgn * 0.7071, -0.7071)
    bon = cyl(dn * 0.5, 63, c, V(1, 0, 0)).fuse(box(447 + 20, y - 46, z - 46, 447 + 34, y + 46, z + 46)); bon.rotate(c, V(0, 0, 1), sgn * VALVE_YAW)
    body = box(447 - 42, y - 42, z - 42, 447 + 42, y + 42, z + 42).fuse(bon)
    body = body.fuse(cyl(dn * 0.55, 85, c, d)).fuse(cyl(dn * 0.95, 14, c + d * 85, d))
    add(nm + '_b', label + ': корпус и патрубок', body, (0.6, 0.62, 0.65), G)
    add(nm + '_p', label.split(' (')[0].replace('Напорный вентиль DN70', 'Напорный трубопровод АЦ') + (' (левый)' if sgn < 0 else ' (правый)'),
        pipeline([(447, y + sgn * 70, z - 70), (447, y + sgn * 230, z - 180), (447, y + sgn * 230, -330)], dn * 0.5), (0.7, 0.72, 0.75), G)
    wheel = tube(55, 44, 10, V(510, y, z), V(1, 0, 0)).fuse(cyl(12, 14, V(508, y, z), V(1, 0, 0)))
    for a in range(7):
        t = a * 2 * math.pi / 7; wheel = wheel.fuse(Part.makeSphere(8, V(515, y + 52 * math.sin(t), z + 52 * math.cos(t))))
    for a in range(5):
        t = a * 2 * math.pi / 5
        sp = Part.makeBox(5, 5, 44, V(511, y - 2.5, z)); sp.rotate(V(511, y, z), V(1, 0, 0), math.degrees(t)); wheel = wheel.fuse(sp)
    wheel = wheel.fuse(cyl(6, 30, V(515, y + 42, z), V(1, 0, 0)))   # рукоятка на ободе
    wheel.rotate(c, V(0, 0, 1), sgn * VALVE_YAW)
    add(nm + '_w', label + ': маховик', wheel, RED, G)
yL, zL = PH['V1L']; yR, zR = PH['V1R']
valve('V1L', 'П 1 Напорный вентиль DN70 (левый)', yL, zL, -1, 70)
valve('V1R', 'П 12 Напорный вентиль DN70 (правый)', yR, zR, 1, 70)
yT, zT = PH['VT']
# вентиль DN80 заполнения цистерны: проходной корпус с квадратной крышкой на 4 болтах (рис. 1, поз. 10);
# сзади — квадратный фланец DN80 к трубопроводу заполнения цистерны (рис. 2, поз. 25)
tv = box(405, yT - 46, zT - 46, 470, yT + 46, zT + 46).fuse(cyl(40, 60, V(405, yT, zT), V(-1, 0, 0)))
tv = tv.fuse(box(352, yT - 58, zT - 58, 370, yT + 58, zT + 58).cut(cyl(40, 20, V(351, yT, zT), V(1, 0, 0))))
tv = tv.fuse(box(470, yT - 52, zT - 52, 486, yT + 52, zT + 52)).fuse(cyl(22, 16, V(486, yT, zT), V(1, 0, 0)))
for (dy, dz) in ((-40, -40), (-40, 40), (40, -40), (40, 40)):
    tv = tv.fuse(bolt(V(486, yT + dy, zT + dz), V(1, 0, 0), 12, 10)).fuse(bolt(V(352, yT + dy * 1.15, zT + dz * 1.15), V(-1, 0, 0), 12, 10))
add('VT_b', 'П 10 Напорный вентиль DN80 заполнения цистерны: корпус', tv, (0.6, 0.62, 0.65), G)
add('VT_w', 'П 10 Напорный вентиль DN80 заполнения цистерны: маховик', tube(48, 38, 10, V(505, yT, zT), V(1, 0, 0)).fuse(cyl(11, 14, V(500, yT, zT), V(1, 0, 0))), RED, G)
yF, zF = PH['LAF']
# фланец DN80 под лафетный ствол — смотрит вверх, на машине заглушен глухим фланцем на 8 шпильках (фото)
add('LAF', 'П 9 Фланец DN80 для лафетного ствола (заглушен)', cyl(80, 16, V(447, yF, zF - 16), V(0, 0, 1)).fuse(cyl(80, 10, V(447, yF, zF), V(0, 0, 1))).fuse(tube(48, 38, zF - 16 - 318, V(447, yF, 318), V(0, 0, 1))), GREY, G)
add('LAF_s', 'П 9 Шпильки глухого фланца (8 шт.)', Part.makeCompound([bolt(V(447 + 64 * math.cos(a_ * math.pi / 4 + 0.39), yF + 64 * math.sin(a_ * math.pi / 4 + 0.39), zF + 18.4), V(0, 0, -1), 12, 24) for a_ in range(8)]), STEEL, 'Детали и крепёж')
# БУК-02 и рукоятки
y0, z0 = f1(345, 295); y1_, z1_ = f1(585, 100)
buk = box(525, y0, z0, 585, y1_, z1_)
add('BUK', 'П 7 Блок управления и контроля БУК-02', buk, (0.8, 0.12, 0.12), G)
add('BUKp', 'П 7 БУК-02: лицевая панель', box(585, y0 + 8, z0 + 8, 588, y1_ - 8, z1_ - 8), (0.9, 0.9, 0.88), G)
add('BUKb', 'П 7 БУК-02: кнопки', Part.makeCompound([cyl(9, 6, V(588, y0 + 95, z1_ - 70 - 32 * i), V(1, 0, 0)) for i in range(3)]), (0.75, 0.76, 0.78), G)
add('PLATE14', 'П 14 Табличка фирменная', box(556, 150, 60, 558, 230, 110), (0.1, 0.1, 0.12), G)
yv, zv = PH['GATE']
# вакуумный затвор — шаровой кран на горизонтальной трубе над БУК-02 (рис. 1, фото): слева снизу труба из коллектора,
# справа — обратный клапан 28 и датчик заполнения 8
add('VACV', 'П 5 Вакуумный затвор', cyl(24, 64, V(470, yv - 32, zv), V(0, 1, 0)).fuse(cyl(11, 300, V(470, -262, zv), V(0, 1, 0))), (0.6, 0.62, 0.65), G)
add('VACP', 'П Рукав от вакуумного затвора к насосу (уточнить)', pipeline([(470, -195, zv), (470, -195, 430), (460, -170, 360), (447, -150, 330)], 12), (0.1, 0.1, 0.1), G)
add('VACH', 'П Труба вакуумирования к агрегату (уточнить)', pipeline([(470, 52, zv), (420, 52, zv), (420, 52, 440), (420, -430, 440), (420, -430, -80)], 11), (0.7, 0.72, 0.75), G)
add('VACL', 'П 5 Рукоятка вакуумного затвора', box(478, yv - 5, zv + 20, 488, yv + 5, zv + 150), RED, G)   # вертикально — открыт
yd, zd = PH['DOZ']
add('DOZ', 'П 2 Ручной дозатор пенообразователя: шкала', cyl(52, 10, V(585, yd, zd), V(1, 0, 0)), (0.95, 0.95, 0.93), G)
# рукоятка дозатора — чёрная «звезда» с красной серединой (фото)
add('DOZk', 'П 2 Ручной дозатор пенообразователя: рукоятка', cyl(24, 16, V(595, yd, zd), V(1, 0, 0)).fuse(Part.makeCompound([cyl(9, 16, V(595, yd + 22 * math.sin(i * math.pi / 3), zd + 22 * math.cos(i * math.pi / 3)), V(1, 0, 0)) for i in range(6)])), (0.08, 0.08, 0.09), G)
add('DOZc', 'П 2 Ручной дозатор пенообразователя: колпачок', cyl(13, 4, V(611, yd, zd), V(1, 0, 0)), RED, G)
ye, ze = PH['EJ']
add('EJV', 'П Кран эжектора', cyl(16, 44, V(560, ye, ze - 22), V(0, 0, 1)).fuse(pipeline([(560, ye, ze + 20), (560, ye, 330), (527, ye, 330)], 14)), (0.75, 0.76, 0.78), G)
add('EJL', 'П Кран эжектора: рукоятка', box(554, ye - 34, ze + 24, 566, ye + 34, ze + 30), (0.1, 0.1, 0.1), G)   # вдоль y — открыт
# пеносмеситель: тройник и сопло к крышке 16
yp, zp = PH['MIX']
mix = cyl(28, 110, V(560, yp - 110, zp), V(0, 1, 0)).fuse(cyl(22, zp - 69, V(560, yp, zp), V(0, 0, -1))).fuse(cyl(22, ze - 22 - zp, V(560, yp, zp), V(0, 0, 1)))
add('MIX', 'П 16 Пеносмеситель (эжектор)', mix, (0.6, 0.62, 0.65), G)
# манометры
for nm, lab, (y, z), r in (('G_out', 'П 11 Мановакуумметр на выходе СНД', PH['G11'], 55), ('G_in', 'П 15 Мановакуумметр на входе в СНД', PH['G15'], 50), ('G_hp', 'П 22 Манометр на выходе СВД', PH['G22'], 50)):
    add(nm, lab, cyl(r, 30, V(585, y, z), V(1, 0, 0)), (0.85, 0.86, 0.88), G)
yo, zo = PH['OIL']
# масляный бачок — небольшая полупрозрачная бутылка с чёрной крышкой под вентилем DN80 (фото)
add('OIL', 'П 13 Масляный бачок вакуумного агрегата', cyl(24, 62, V(500, yo, zo - 40), V(0, 0, 1)), (0.93, 0.9, 0.82), G)
add('OILc', 'П 13 Крышка масляного бачка', cyl(18, 16, V(500, yo, zo + 22), V(0, 0, 1)), (0.06, 0.06, 0.07), G)
# маслопровод от бачка к агрегату (масло подсасывается вакуумом), трасса — уточнить на машине
add('OILt', 'П 13 Маслопровод к вакуумному агрегату (уточнить)', pipeline([(500, yo, zo - 40), (560, yo + 30, zo - 60), (560, 230, -240), (560, -430, -240), (520, -430, -205)], 3), (0.9, 0.85, 0.6), G)
# датчик заполнения 26 в напорном коллекторе (рис. 2)
add('SENS26', 'П 26 Датчик заполнения в напорном коллекторе', cyl(12, 30, V(390, 120, 330), V(0, 0, 1)).fuse(cyl(4, 20, V(390, 120, 360), V(0, 0, 1))), (0.95, 0.95, 0.95), G)
# вакуумный агрегат сзади сверху, пневмоостров, клапаны
# вакуумный агрегат — слева от насоса, внизу (так на машине; на рис. 2 РЭ — сзади справа)
add('AVS', 'П 24 Агрегат вакуумный', cyl(62, 150, V(330, -430, -150), V(1, 0, 0)).fuse(box(470, -490, -220, 540, -370, -80)).fuse(box(330, -500, -235, 540, -360, -215)), (0.55, 0.56, 0.58), G)
add('AVS_ex', 'П 41 Выхлопной патрубок вакуумного агрегата', pipeline([(505, -430, -235), (505, -430, -330)], 10), RUBBER, G)
# пневмоостров 23 (фото отсека): на кронштейне над правым рукавом коллектора — алюминиевый блок-коллектор воздуха,
# на нём манометр воздуха 0–12 бар, спереди два пневмораспределителя («Клапан осушения» сверху, «Сливные краны» снизу),
# сбоку латунные фитинги с прозрачными трубками, сзади — подвод воздуха чёрным рукавом
add('PNEU', 'П 23 Пневмоостров: блок с кронштейном', box(360, 280, 390, 395, 322, 468).fuse(box(345, 268, 408, 360, 334, 482)), (0.72, 0.73, 0.75), G)
add('PNEU_v1', 'П 23 Пневмораспределитель «Клапан осушения»', box(395, 278, 428, 420, 324, 458), (0.06, 0.06, 0.07), G)
add('PNEU_v2', 'П 23 Пневмораспределитель «Сливные краны»', box(395, 278, 396, 420, 324, 426), (0.06, 0.06, 0.07), G)
add('PNEU_g', 'П 23 Манометр воздуха 0–12 бар', cyl(4, 22, V(378, 301, 468), V(0, 0, 1)).fuse(cyl(21, 13, V(376, 301, 508), V(1, 0, 0))), (0.9, 0.9, 0.88), G)
add('PNEU_f', 'П 23 Фитинги пневмолиний', cyl(5, 14, V(408, 324, 442), V(0, 1, 0)).fuse(cyl(5, 14, V(408, 324, 410), V(0, 1, 0))).fuse(cyl(5, 14, V(362, 300, 420), V(-1, 0, 0))), BRONZE, G)
add('PNEU_h', 'П 23 Рукав подвода воздуха', pipeline([(360, 290, 455), (320, 290, 470), (290, 320, 560), (270, 340, 650)], 7), RUBBER, G)
add('VSENS', 'П 8 Датчик заполнения в линии вакуумирования', cyl(9, 22, V(470, -284, zv), V(0, 1, 0)).fuse(cyl(2.5, 18, V(470, -302, zv), V(0, 1, 0))), (0.95, 0.95, 0.95), G)   # белый изолятор со штырём слева (фото)
# слив СНД с пневмоприводом (внизу)
yd2, zd2 = f1(470, 985)
add('DRND', 'П 19 Сливной кран СНД с пневмоприводом', cyl(16, 70, V(447, yd2 - 35, zd2), V(0, 1, 0)).fuse(box(415, yd2 - 30, zd2 - 32, 465, yd2 + 18, zd2 - 12)).fuse(cyl(9, 60, V(447, yd2 + 35, zd2), V(0, 0.7, -0.7))).fuse(cyl(6, 50, V(447, yd2 - 15, zd2 + 15), V(0, 0, 1))), (0.6, 0.62, 0.65), G)
# патрубок от коллектора НД к входу СВД и коллектор ВД с краном ВД
xin = hx(1005); xout = hx(1255)
pipe = cyl(22, 100, V(xin, -150, 300), V(0, -1, 0)).fuse(cyl(22, 300 - (HPZ + 158) + 2, V(xin, HPY, HPZ + 158), V(0, 0, 1))).fuse(cyl(22, 30, V(xin, -150, 300), V(0, 0, -1)))
add('P_HPIN', 'П Патрубок от коллектора НД на вход СВД', pipe.fuse(cyl(22, 60, V(395, -150, 300), V(1, 0, 0)).common(box(395, -175, 275, xin + 22, -125, 325)) if xin > 395 else pipe), (0.7, 0.72, 0.75), G)
# коллектор ВД: вверх из ступени, в сторону и вертикально вверх слева (рис. 1, 2 — оранжевая труба) к крану ВД
# выход ступени ВД (фото, рис. 1 — оранжевая труба): от верха ступени ВД вертикально вверх слева от БУК, кран ВД DN25 сбоку, выше — рукав к катушке
XH, YH, ZK = 372, PH['HPV'][0], PH['HPV'][1]
coll2 = cyl(20, 70, V(xout, HPY, HPZ + 158), V(0, 0, 1)).fuse(pipeline([(xout, HPY, HPZ + 210), (XH, YH, HPZ + 210), (XH, YH, ZK - 25)], 17))
add('P_HPCOLL', 'П 32 Напорный коллектор СВД с перепускным штуцером', coll2, (0.75, 0.6, 0.85), G)
add('KVD', 'П 31 Кран высокого давления', cyl(20, 50, V(XH, YH, ZK - 25), V(0, 0, 1)).fuse(cyl(9, 26, V(XH, YH - 20, ZK), V(0, -1, 0))), (0.78, 0.7, 0.45), G)
add('KVDL', 'П 31 Кран высокого давления: рукоятка', box(XH - 4, YH - 50, ZK, XH + 4, YH - 42, ZK + 95), RED, G)   # вдоль трубы (вертикально) — открыт
add('REEL', 'П 30 Рукав к катушке высокого давления', pipeline([(XH, YH, ZK + 25), (XH, YH, 680), (XH - 40, YH, 760), (200, YH, 820)], 14), RUBBER, G)

# ======================= детали (рис. 1–5 и фото отсека; размеры на глаз, ±5–20 мм) =======================
GD = 'Детали и крепёж'
# -- ступень НД: лопатки колеса, спираль улитки с языком, сальник, лапы, рёбра
add('ND_15v', 'НД 15 Лопатки колеса (6 шт.)', ring_of(6, lambda a: vane_solid(447, 492, 42, 136, a, -1.15, 5)), BRONZE, 'Ступень НД (рис. 3)')
spiral_o, spiral_i = [], []
TONGUE = math.radians(70)          # язык улитки — справа сверху; спираль растёт против часовой (вид со входа), выход вверх
for k in range(73):
    t = k / 72; a = TONGUE - 2 * math.pi * t
    ro = 158 + 26 * t; spiral_o.append((ro * math.sin(a), ro * math.cos(a))); spiral_i.append(((ro - 9) * math.sin(a), (ro - 9) * math.cos(a)))
try:
    sp = face_yz(spiral_o + spiral_i[::-1], 428).extrude(V(38, 0, 0))
    add('ND_13s', 'НД 13 Улитка: стенка спирального канала и язык', sp.fuse(vane_solid(428, 466, 136, 160, TONGUE - 0.02, 0.05, 10)), CAST, 'Ступень НД (рис. 3)')
except Exception as e: log('улитка', e)
add('ND_18n', 'НД 18 Нажимная втулка сальника', tube(48, 25, 9, V(381, 0, 0), V(1, 0, 0)).fuse(ring_of(2, lambda a: bolt(V(381, 40 * math.sin(a + 1.57), 40 * math.cos(a + 1.57)), V(-1, 0, 0), 8, 30))), STEEL, 'Ступень НД (рис. 3)')
# опорные лапы корпуса (рис. 1, 2 РЭ): по бокам улитки примерно на 110 мм ниже оси, улитка свисает ниже лап;
# косынки от корпуса к лапам
ZFt, ZFb = -104, -122
feet = box(290, 150, ZFb, 480, 268, ZFt).fuse(box(290, -268, ZFb, 480, -150, ZFt))
for sg in (1, -1):
    feet = feet.fuse(vane_solid(372, 398, 140, 205, math.radians(sg * 112), 0.0, 26))
    for xx in (300, 470):
        w = Part.makePolygon([V(xx, sg * 150, ZFt), V(xx, sg * 150, -20), V(xx, sg * 262, ZFt), V(xx, sg * 150, ZFt)])
        feet = feet.fuse(Part.Face(w).extrude(V(-10 if xx > 400 else 10, 0, 0)))
add('ND_13f', 'НД 13 Опорные лапы корпуса', feet.fuse(Part.makeCompound([bolt(V(x_, y_, ZFt), V(0, 0, 1), 14, 26) for x_ in (318, 452) for y_ in (-235, 235)])), CAST, 'Ступень НД (рис. 3)')
# наружная стенка улитки — спираль (видна снаружи как литой спиральный корпус)
try:
    so, si = [], []
    for k in range(73):
        t = k / 72; a = math.radians(70) - 2 * math.pi * t; ro = 186 + 34 * t
        so.append((ro * math.sin(a), ro * math.cos(a))); si.append((150 * math.sin(a), 150 * math.cos(a)))
    vol = face_yz(so + si[::-1], 418).extrude(V(56, 0, 0))
    add('ND_13v', 'НД 13 Улитка: наружная спиральная стенка', vol.cut(box(380, YN - 95, 60, 520, YN + 95, 260)), CAST, 'Ступень НД (рис. 3)')
except Exception as e: log('улитка наружная', e)
add('ND_13r', 'НД 13 Рёбра опоры подшипников', ring_of(4, lambda a: vane_solid(200, 335, 52, 112, a + math.pi / 4, 0.0, 8)), CAST, 'Ступень НД (рис. 3)')
add('ND_16b', 'НД 16 Болты крышки (12 шт.)', ring_of(12, lambda a: bolt(V(522, 166 * math.sin(a), 166 * math.cos(a)), V(1, 0, 0), 10, 28)), STEEL, GD)
add('ND_16f', 'НД 16 Шпильки фланца всасывания DN125 (8 шт.)', ring_of(8, lambda a: bolt(V(645, 100 * math.sin(a + 0.39), 100 * math.cos(a + 0.39)), V(1, 0, 0), 14, 30)), STEEL, GD)
add('ND_13n', 'НД 13 Шпильки напорного фланца (6 шт.)', Part.makeCompound([bolt(V(x_, YN + y_, 252), V(0, 0, 1), 12, 35) for x_ in (412, 468) for y_ in (-100, 0, 100)]), STEEL, GD)
add('ND_7c', 'НД 7 Кабель датчика тахометра', pipeline([(213, 0, 129), (213, 0, 190), (300, 120, 360), (520, 30, 400)], 3), RUBBER, GD)

# -- ступень ВД: лопатки колёс, направляющие аппараты, сальник, лапа, стяжные болты
HA = lambda x, r, a: V(x, HPY + r * math.sin(a), HPZ + r * math.cos(a))
add('HP_3v', 'ВД 3 Лопатки колеса (6 шт.)', ring_of(6, lambda a: vane_solid(332, 352, 32, 82, a, -1.0, 4, HPY, HPZ)), BRONZE, 'Ступень ВД (рис. 4)')
add('HP_5v', 'ВД 5 Лопатки колеса (6 шт.)', ring_of(6, lambda a: vane_solid(295, 315, 32, 82, a, 1.0, 4, HPY, HPZ)), BRONZE, 'Ступень ВД (рис. 4)')
add('HP_2v', 'ВД 2 Лопатки направляющего аппарата (8 шт.)', ring_of(8, lambda a: vane_solid(351, 359, 86, 98, a, -0.5, 4, HPY, HPZ)), (0.7, 0.55, 0.9), 'Ступень ВД (рис. 4)')
add('HP_4v', 'ВД 4 Лопатки направляющего аппарата (8 шт.)', ring_of(8, lambda a: vane_solid(318, 332, 40, 100, a, 1.2, 4, HPY, HPZ)), (0.55, 0.45, 0.85), 'Ступень ВД (рис. 4)')
add('HP_7n', 'ВД 7 Нажимная втулка сальника', tube(38, 21, 7, V(243, HPY, HPZ), V(1, 0, 0)), STEEL, 'Ступень ВД (рис. 4)')
add('HP_6f', 'ВД 6 Лапа крепления ступени ВД', box(120, -270, -75, 300, -135, -62).fuse(box(150, -215, -66, 270, -190, -30)), CAST, 'Ступень ВД (рис. 4)')
add('HP_1b', 'ВД 1 Стяжные болты корпуса (8 шт.)', ring_of(8, lambda a: bolt(HA(410, 122, a), V(1, 0, 0), 10, 100)), STEEL, GD)
add('HP_1c', 'ВД 1 Передняя крышка ступени ВД', cyl(132, 14, V(408, HPY, HPZ), V(1, 0, 0)).fuse(cyl(60, 18, V(422, HPY, HPZ), V(1, 0, 0))).fuse(ring_of(4, lambda a: vane_solid(422, 432, 60, 128, a + 0.4, 0.0, 10, HPY, HPZ))), CAST, 'Ступень ВД (рис. 4)')

# -- обвязка: трубки манометров, пневмолинии, кабели, обратные клапаны, соединительная головка
yG11, zG11 = PH['G11']; yG15, zG15 = PH['G15']; yG22, zG22 = PH['G22']
add('L_g11', 'П Трубка манометра 11', pipeline([(600, yG11, zG11 - 55), (600, yG11, 335), (530, 200, 322)], 4), BRONZE, G)
add('L_g15', 'П Трубка мановакуумметра 15', pipeline([(600, yG15, zG15 - 50), (600, yG15, 5), (600, 70, 5)], 4), BRONZE, G)
add('L_g22', 'П Трубка манометра 22', pipeline([(600, yG22, zG22 - 50), (600, yG22, 30), (420, -300, 60), (300, -301, 300)], 4), BRONZE, G)
add('P20', 'П 20 Пневмопривод сливных кранов СВД', box(470, -280, -60, 540, -180, 40), (0.75, 0.8, 0.8), G)
add('L_pn1', 'П Пневмолиния к сливному крану СНД', pipeline([(408, 338, 410), (412, 395, 390), (412, 395, -235), (450, 120, -262), (445, -30, -262)], 3), (0.85, 0.7, 0.3), G)
add('L_pn2', 'П Пневмолиния к сливным кранам СВД', pipeline([(408, 338, 442), (418, 400, 420), (418, 400, -290), (505, -150, -290), (505, -230, -60)], 3), (0.85, 0.7, 0.3), G)
add('L_pn3', 'П Пневмолиния продувки', pipeline([(348, 300, 420), (345, 250, 330), (350, 200, 306), (360, 175, 305)], 3), (0.85, 0.7, 0.3), G)
add('CV27', 'П 27 Обратный клапан продувки', cyl(12, 30, V(372, 175, 305), V(-1, 0, 0)).fuse(hexprism(V(369, 175, 305), V(-1, 0, 0), 22, 8)), BRONZE, G)
add('CV28', 'П 28 Обратный клапан в линии вакуумирования', cyl(15, 36, V(470, 10, zv), V(0, 1, 0)), BRONZE, G)
add('CV29', 'П 29 Обратный клапан магистрали пенообразователя', cyl(18, 45, V(505, yd, zd), V(1, 0, 0)), BRONZE, G)
add('L_c8', 'П Кабель датчика заполнения', pipeline([(470, 100, zv), (500, 120, zv - 20), (555, 30, 531)], 3), RUBBER, G)

add('MIXn', 'П 16 Гайки и муфты пеносмесителя 1¼″', hexprism(V(560, yp - 60, zp), V(0, 1, 0), 52, 14).fuse(hexprism(V(560, yp, zp - 40), V(0, 0, -1), 46, 14)), STEEL, G)
YFV, ZFV = PH['FOAMV']
add('FOAMP', 'П Линия пенобака', pipeline([(510, yd, zd), (470, yd, zd), (470, YFV, zd), (470, YFV, 610)], 16), (0.78, 0.79, 0.81), G)
add('FOAMV', 'П Кран магистрали пенобака', cyl(22, 50, V(470, YFV, ZFV - 25), V(0, 0, 1)).fuse(cyl(9, 24, V(470, YFV - 20, ZFV), V(0, -1, 0))), (0.78, 0.7, 0.45), G)
add('FOAMVL', 'П Кран магистрали пенобака: рукоятка', box(470 - 4, YFV - 140, ZFV - 4, 470 + 4, YFV - 40, ZFV + 4), RED, G)
add('FOAMH', 'П Рукав к пенобаку', pipeline([(470, YFV, 610), (470, YFV + 40, 650), (300, YFV + 120, 660), (-200, YFV + 150, 640)], 22), RUBBER, G)
add('FOAMG', 'П Головка подсоса пенообразователя из сторонней ёмкости', pipeline([(470, YFV, 417), (540, YFV - 40, 417)], 12).fuse(cyl(34, 30, V(540, YFV - 40, 417), V(1, -0.5, 0).normalize())).fuse(cyl(30, 10, V(567, YFV - 53, 417), V(1, -0.5, 0).normalize())), (0.8, 0.8, 0.82), G)

# -- вентили и кран ВД в разрезе: тарель на шпинделе, шар с проходом
for key, lab, y_, z_, rr in (('V1L', 'П 1 Напорный вентиль DN70 (левый)', yL, zL, 24), ('V1R', 'П 12 Напорный вентиль DN70 (правый)', yR, zR, 24),
                             ('VT', 'П 10 Напорный вентиль DN80 заполнения цистерны', yT, zT, 27)):
    td = cyl(rr, 9, V(452, y_, z_), V(1, 0, 0)).fuse(cyl(rr - 6, 4, V(448, y_, z_), V(1, 0, 0))); ts = cyl(6, 48, V(461, y_, z_), V(1, 0, 0))
    if key != 'VT':
        for sh in (td, ts): sh.rotate(V(447, y_, z_), V(0, 0, 1), (-1 if key == 'V1L' else 1) * VALVE_YAW)
    add(key + '_d', lab + ': тарель', td, STEEL, G)
    add(key + '_s', lab + ': шпиндель', ts, STEEL, G)
add('KVD_b', 'П 31 Кран высокого давления: шар', Part.makeSphere(15, V(XH, YH, ZK)).cut(cyl(6, 40, V(XH, YH, ZK - 20), V(0, 0, 1))), STEEL, G)

doc.recompute()
fc = os.path.join(OUT, name + '.FCStd'); doc.saveAs(fc)
objs = [o for o in doc.Objects if o.TypeId == 'Part::Feature']
try:
    import Import; Import.export(objs, os.path.join(OUT, name + '.step'))
except Exception as e: log('STEP fail', e)
try:
    import ImportGui; ImportGui.export(objs, os.path.join(OUT, name + '.glb'))
except Exception as e: log('GLB fail', e)
log('объектов', len(objs))
