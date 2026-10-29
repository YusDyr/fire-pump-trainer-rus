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
neck = box(420, -48, 150, 473, 48, 212).cut(box(428, -38, 140, 465, 38, 215))
flange = box(332, -75, 212, 553, 75, 245).cut(cyl(36, 50, V(445, 0, 200), V(0, 0, 1)))
casing = casing.fuse(neck).fuse(flange)
add('ND_13', 'НД 13 Корпус насоса', casing, BLUE, 'Ступень НД (рис. 3)')
add('ND_12', 'НД 12 Кольцо 108-115-46', tube(57.5, 54, 3, V(445, 0, 240), V(0, 0, 1)), RUBBER, 'Ступень НД (рис. 3)')
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
def face_yz(poly, x):
    w = Part.makePolygon([V(x, y, z) for y, z in poly] + [V(x, poly[0][0], poly[0][1])]); return Part.Face(w)
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
gf = face_yz(gp, XP - 62).extrude(V(4, 0, 0))
add('GUARD', 'Р Кожух ремённой передачи', gf, (0.12, 0.12, 0.13), 'Привод ступени ВД (рис. 5)', 55)

# ---------------- обвязка и органы управления (рис. 1, 2) ----------------
def f1(px, py): return ((px - 540) * 0.9, (690 - py) * 0.9)   # рис. 1, вид со стороны входа: y, z
G = 'Обвязка и органы управления (рис. 1, 2)'
# напорный коллектор над фланцем ступени НД
coll = box(370, -120, 245, 525, 175, 330).fuse(box(395, -205, 270, 500, -120, 318)).fuse(box(395, 175, 270, 500, 380, 318))
coll = coll.cut(box(380, -200, 258, 515, 370, 318))
add('COLL', 'П Коллектор напорный', coll, (0.7, 0.72, 0.75), G)
def valve(nm, label, y, z, sgn, dn):
    body = cyl(dn * 0.55, 95, V(447, y, z), V(0, sgn * 0.7, -0.7)).fuse(cyl(dn * 0.62, 30, V(447, y, z) + V(0, sgn * 0.7, -0.7) * 80, V(0, sgn * 0.7, -0.7)))
    body = body.fuse(cyl(dn * 0.5, 60, V(447, y, z), V(1, 0, 0)))
    add(nm + '_b', label + ': корпус и патрубок', body, (0.6, 0.62, 0.65), G)
    wheel = tube(55, 44, 10, V(510, y, z), V(1, 0, 0)).fuse(cyl(12, 14, V(508, y, z), V(1, 0, 0)))
    for a in range(5):
        t = a * 2 * math.pi / 5
        sp = Part.makeBox(5, 5, 44, V(511, y - 2.5, z)); sp.rotate(V(511, y, z), V(1, 0, 0), math.degrees(t)); wheel = wheel.fuse(sp)
    add(nm + '_w', label + ': маховик', wheel, RED, G)
yL, zL = f1(330, 350); yR, zR = f1(960, 350)
valve('V1L', 'П 1 Напорный вентиль DN70 (левый)', yL, zL, -1, 70)
valve('V1R', 'П 12 Напорный вентиль DN70 (правый)', yR, zR, 1, 70)
yT, zT = f1(720, 365)
tv = cyl(40, 80, V(447, yT, zT), V(-1, 0, 0)).fuse(cyl(48, 18, V(370, yT, zT), V(-1, 0, 0)))
add('VT_b', 'П 10 Напорный вентиль DN80 заполнения цистерны: корпус', tv, (0.6, 0.62, 0.65), G)
add('VT_w', 'П 10 Напорный вентиль DN80 заполнения цистерны: маховик', tube(48, 38, 10, V(505, yT, zT), V(1, 0, 0)).fuse(cyl(11, 14, V(500, yT, zT), V(1, 0, 0))), RED, G)
yF, zF = f1(640, 230)
add('LAF', 'П 9 Фланец DN80 для лафетного ствола', cyl(72, 18, V(447, yF, 338), V(0, 0, 1)).cut(cyl(40, 20, V(447, yF, 337), V(0, 0, 1))).fuse(tube(44, 38, 40, V(447, yF, 300), V(0, 0, 1))), GREY, G)
# БУК-02 и рукоятки
y0, z0 = f1(345, 295); y1_, z1_ = f1(585, 100)
buk = box(525, y0, z0, 585, y1_, z1_)
add('BUK', 'П 7 Блок управления и контроля БУК-02', buk, (0.8, 0.12, 0.12), G)
yv, zv = f1(400, 60)
add('VACV', 'П 5 Вакуумный затвор', cyl(18, 90, V(470, yv - 60, zv), V(0, 1, 0)), (0.6, 0.62, 0.65), G)
add('VACL', 'П 5 Рукоятка вакуумного затвора', box(478, yv - 10, zv, 488, yv, zv + 70), ORANGE, G)
yd, zd = f1(420, 370)
add('DOZ', 'П 2 Ручной дозатор пенообразователя', cyl(52, 14, V(585, yd, zd), V(1, 0, 0)).fuse(cyl(24, 30, V(598, yd, zd), V(1, 0, 0))), (0.95, 0.95, 0.93), G)
ye, ze = f1(540, 255)
add('EJL', 'П Кран эжектора: рукоятка', box(585, ye - 6, ze - 40, 595, ye + 6, ze + 40), (0.1, 0.1, 0.1), G)
# пеносмеситель: тройник и сопло к крышке 16
yp, zp = f1(500, 480); zp -= 8   # ниже фланца корпуса 13
mix = cyl(28, 160, V(560, yp - 80, zp), V(0, 1, 0)).fuse(cyl(22, zp - 69, V(560, yp, zp), V(0, 0, -1)))
add('MIX', 'П 16 Пеносмеситель (эжектор)', mix, (0.6, 0.62, 0.65), G)
# манометры
for nm, lab, (px, py), r in (('G_out', 'П 11 Мановакуумметр на выходе СНД', (810, 200), 55), ('G_in', 'П 15 Мановакуумметр на входе в СНД', (680, 595), 50), ('G_hp', 'П 22 Манометр на выходе СВД', (180, 560), 50)):
    y, z = f1(px, py); add(nm, lab, cyl(r, 30, V(585, y, z), V(1, 0, 0)), (0.85, 0.86, 0.88), G)
yo, zo = f1(760, 450)
add('OIL', 'П 13 Масляный бачок вакуумного агрегата', box(470, yo - 40, zo - 45, 540, yo + 40, zo + 45), (0.95, 0.95, 0.95), G)
# вакуумный агрегат сзади сверху, пневмоостров, клапаны
add('AVS', 'П 24 Агрегат вакуумный', cyl(70, 260, V(250, -170, 360), V(0, 1, 0)).fuse(box(190, -200, 300, 310, -150, 430)), (0.55, 0.56, 0.58), G)
add('AVS_ex', 'П 41 Выхлопной патрубок вакуумного агрегата', cyl(10, 175, V(250, -185, 310), V(0, -1, 0)).fuse(cyl(10, 310, V(250, -360, 310), V(0, 0, -1))), RUBBER, G)
add('PNEU', 'П 23 Пневмоостров', box(150, 120, 430, 230, 230, 520), (0.9, 0.9, 0.85), G)
add('VSENS', 'П 8 Датчик заполнения в линии вакуумирования', cyl(9, 80, V(470, yv - 140, zv + 20), V(0, 1, 0)), ORANGE, G)
# слив СНД с пневмоприводом (внизу)
yd2, zd2 = f1(470, 985)
add('DRND', 'П 19 Сливной кран СНД с пневмоприводом', box(410, yd2 - 35, zd2 - 20, 470, yd2 + 35, zd2 + 30).fuse(cyl(7, 40, V(440, yd2 + 30, zd2 - 20), V(0, 0, -1))), (0.6, 0.62, 0.65), G)
# патрубок от коллектора НД к входу СВД и коллектор ВД с краном ВД
xin = hx(1005); xout = hx(1255)
pipe = cyl(22, 100, V(xin, -150, 300), V(0, -1, 0)).fuse(cyl(22, 300 - (HPZ + 158) + 2, V(xin, HPY, HPZ + 158), V(0, 0, 1))).fuse(cyl(22, 30, V(xin, -150, 300), V(0, 0, -1)))
add('P_HPIN', 'П Патрубок от коллектора НД на вход СВД', pipe.fuse(cyl(22, 60, V(395, -150, 300), V(1, 0, 0)).common(box(395, -175, 275, xin + 22, -125, 325)) if xin > 395 else pipe), (0.7, 0.72, 0.75), G)
coll2 = cyl(20, 70, V(xout, HPY, HPZ + 158), V(0, 0, 1)).fuse(cyl(17, 90, V(xout, HPY, HPZ + 210), V(0, -1, 0)))
add('P_HPCOLL', 'П 32 Напорный коллектор СВД с перепускным штуцером', coll2, (0.75, 0.6, 0.85), G)
add('KVD', 'П 31 Кран высокого давления', cyl(16, 40, V(xout, HPY - 90, HPZ + 210), V(0, -1, 0)), (0.6, 0.62, 0.65), G)
add('KVDL', 'П 31 Кран высокого давления: рукоятка', box(xout - 4, HPY - 110, HPZ + 226, xout + 4, HPY - 102, HPZ + 300), RED, G)

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
