# Несимметричные части: корпус 20 со спиральной улиткой, напорным патрубком и приливами,
# крышка 12 с приливом, кран сливной 16, крепёж. Координаты: ось вала X, верх Z,
# +Y — вправо при взгляде со стороны всасывания (рис. 1, вид слева).
import math, Part
from FreeCAD import Vector as V
import parts as P

def X(px): return (px - P.X0) / P.S

def revolve(poly):  # poly [(x_mm, r_mm)] -> тело вращения вокруг X
    pts = [V(x, r, 0) for x, r in poly]
    f = Part.Face(Part.makePolygon(pts + [pts[0]])); f.rotate(V(0,0,0), V(1,0,0), 90)
    return f.revolve(V(0,0,0), V(1,0,0), 360)

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl(r, p0, d, h): return Part.makeCylinder(r, h, p0, d)

# ---------- улитка ----------
Vo = P.VOLUTE
def R(g): return Vo['R0'] + Vo['k'] * g
def phi(g): return math.radians(Vo['tongue_phi'] - g)          # угол от +Z к +Y
def to3d(x, rho, ph): return V(x, rho * math.sin(ph), rho * math.cos(ph))  # патрубок справа вверху (вид со стороны всасывания)

def sec(g, grow=0.0, rmin=None):
    xa, xb = X(Vo['xa']) - grow, X(Vo['xb']) + grow
    r0 = (Vo['r_in'] if rmin is None else rmin)
    r1 = max(R(g) + grow, r0 + 3)
    c = min(6.0, (r1 - r0) / 3, (xb - xa) / 4)
    cb = min(c, 2.0)
    loc = [(xa + cb, r0), (xb - cb, r0), (xb, r0 + cb), (xb, r1 - c), (xb - c, r1), (xa + c, r1), (xa, r1 - c), (xa, r0 + cb)]
    ph = phi(g)
    pts = [to3d(x, r, ph) for x, r in loc]
    return Part.makePolygon(pts + [pts[0]])

def outlet_sec(z, grow=0.0):
    O = P.OUTLET; xc = (X(Vo['xa']) + X(Vo['xb'])) / 2
    hx, hy = O['in_x'] / 2 + grow, O['in_y'] / 2 + grow
    c = min(12.0, hx / 2, hy / 2)
    loc = [(xc - hx + c, O['y_c'] - hy), (xc + hx - c, O['y_c'] - hy), (xc + hx, O['y_c'] - hy + c), (xc + hx, O['y_c'] + hy - c),
           (xc + hx - c, O['y_c'] + hy), (xc - hx + c, O['y_c'] + hy), (xc - hx, O['y_c'] + hy - c), (xc - hx, O['y_c'] - hy + c)]
    pts = [V(x, y, z) for x, y in loc]
    return Part.makePolygon(pts + [pts[0]])

def volute(grow, rmin=None):
    gs = [6, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 352]
    spiral = Part.makeLoft([sec(g, grow, rmin) for g in gs], True, False)
    O = P.OUTLET
    gt = 352
    # горло -> вертикальный патрубок
    th = sec(gt, grow, rmin)
    mid = outlet_sec(168.0, grow)
    top = outlet_sec(O['z_top'] + (1 if grow == 0 else 0), grow)
    nozzle = Part.makeLoft([th, mid, top], True, False)
    return spiral.fuse(nozzle)

def casing(cutter=None):
    base = revolve([(X(x), r) for x, r in P.CASING_BASE])
    outer = volute(Vo['wall'], rmin=146.0)
    if cutter is not None:
        base = base.cut(cutter); outer = outer.cut(cutter)
    inner = volute(0.0)
    O = P.OUTLET; xc = (X(Vo['xa']) + X(Vo['xb'])) / 2
    fl = box(xc - O['fl_x']/2, xc + O['fl_x']/2, O['y_c'] - O['fl_y']/2, O['y_c'] + O['fl_y']/2, O['z_top'], O['z_top'] + O['fl_t'])
    add = [outer, fl]
    # прилив-проушина на заднем фланце вверху (рис. 2)
    lug = box(X(403), X(517), -45, 45, 55, 103 - 12).fuse(cyl(12, V(X(403), -33, 91), V(1,0,0), X(517) - X(403))).fuse(
          cyl(12, V(X(403), 33, 91), V(1,0,0), X(517) - X(403))).fuse(box(X(403), X(517), -33, 33, 91, 103))
    add.append(lug)
    # лапа под корпусом опор (рис. 2, снизу)
    add.append(box(X(527), X(801), -60, 60, -102, -60))
    # картер: нижняя стенка с уклоном к сливной пробке
    w = [V(X(517), 0, -60), V(X(1100), 0, -60), V(X(1100), 0, -82), V(X(569), 0, -70), V(X(517), 0, -70)]
    keel = Part.Face(Part.makePolygon(w + [w[0]])).extrude(V(0, 84, 0)); keel.translate(V(0, -42, 0))
    add.append(keel)
    # прилив под сливную пробку 18
    add.append(cyl(18, V(X(1068), 0, -60), V(0,0,-1), 26))
    # приливы оси вилки 8 по бокам корпуса
    add.append(cyl(21, V(X(941), 38, 49), V(0, 1, 0), 30))   # ось вилки выходит вправо, к рукоятке 13 (рис. 1)
    # прилив щупа/сапуна сверху
    add.append(cyl(10, V(X(1080), 0, 64), V(0,0,1), 16))
    # боковые лапы крепления (рис. 1)
    for s, ext in ((1, 270), (-1, 245)):
        lap = box(X(1369), X(1499), min(150*s, ext*s), max(150*s, ext*s), -104, -90)
        rib = box(X(1405), X(1463), min(120*s, ext*s), max(120*s, ext*s), -104, -50)
        add += [lap, rib]
    # прилив под кран слива 16 на дне улитки (рис. 1 поз. 15, рис. 2 — вид снизу)
    p0 = V(X(1434), 0, -150); d = V(0, 0, -1)
    add.append(cyl(15, p0, d, 28))
    sol = base
    for a in add:
        if cutter is not None:
            a = a.cut(cutter)
            if a.isNull() or not a.Solids: continue
        sol = sol.fuse(a)
    # выборки
    cav = revolve([(X(1100), 0), (X(1100), 64), (X(517), 64), (X(517), 0)]).fuse(
          revolve([(X(401), 0), (X(401), 40), (X(517), 40), (X(517), 0)])).fuse(
          revolve([(X(1100), 0), (X(1100), 50), (X(1212), 50), (X(1212), 33), (X(1330), 33), (X(1360), 40), (X(1405), 72), (X(1410), 141),
                   (X(1590), 141), (X(1592), 138), (X(1714)+1, 138), (X(1714)+1, 0)]))
    cuts = [inner, cav]
    cuts.append(cyl(12.5, V(X(941), 0, 49), V(0, 1, 0), 80))
    cuts.append(cyl(9, V(X(1068), 0, -50), V(0,0,-1), 50))
    cuts.append(cyl(4, V(X(1080), 0, 50), V(0,0,1), 40))
    cuts.append(cyl(7, p0 + V(0,0,20), d, 60))
    # отверстия во фланце патрубка и под болты фланца крышки
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(7, V(xc + sx * 60, O['y_c'] + sy * 40, O['z_top'] - 1), V(0,0,1), O['fl_t'] + 2))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        cuts.append(cyl(6.5, V(X(1640) - 1, 152 * math.sin(a), 152 * math.cos(a)), V(1,0,0), X(1714) - X(1640) + 2))
    for c in cuts: sol = sol.cut(c)
    sol = sol.removeSplitter()
    # окно под промежуточное колесо 23 ступени ВД
    w = sol.cut(cyl(66, V(83, -119.0, 33.1), V(1,0,0), 30))
    if w.isValid() and 0 < sol.Volume - w.Volume < 200000: return w
    w = sol.cut(cyl(66, V(83.3, -119.2, 33.4), V(1,0,0), 29.7))
    if w.isValid() and 0 < sol.Volume - w.Volume < 200000: return w
    return sol

def cover_extra(cover_shape):
    xc = X((1824 + 2019) / 2)
    boss = cyl(28, V(xc, 0, 90), V(0,0,1), 22)
    web = revolve([(X(1745), 100), (X(1745), 150), (X(1760), 150), (X(1830), 100)])
    s = cover_shape.fuse(boss).fuse(web)
    for k in range(8):  # карманы между рёбрами (рис. 1, вид слева)
        a0 = math.radians(45 * k - 14); a1 = math.radians(45 * k + 14)
        pts = []
        for i in range(8):
            a = a0 + (a1 - a0) * i / 7; pts.append((106 * math.sin(a), 106 * math.cos(a)))
        for i in range(8):
            a = a1 - (a1 - a0) * i / 7; pts.append((144 * math.sin(a), 144 * math.cos(a)))
        w = Part.makePolygon([V(X(1752), -y, z) for y, z in pts] + [V(X(1752), -pts[0][0], pts[0][1])])
        s = s.cut(Part.Face(w).extrude(V(X(1840) - X(1752), 0, 0)))
    s = s.cut(cyl(20, V(xc, 0, 55), V(0,0,1), 60))
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        s = s.cut(cyl(6.5, V(X(1714) - 1, 152 * math.sin(a), 152 * math.cos(a)), V(1,0,0), X(1745) - X(1714) + 2))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        s = s.cut(cyl(7, V(X(2019) - 1, 80 * math.sin(a), 80 * math.cos(a)), V(1,0,0), 30))
    return s.removeSplitter()

def hexbar(s, h, p0, d):
    import Part as Pt
    pts = [V(s / math.sqrt(3) * math.cos(math.radians(60 * i)), s / math.sqrt(3) * math.sin(math.radians(60 * i)), 0) for i in range(6)]
    f = Pt.Face(Pt.makePolygon(pts + [pts[0]])).extrude(V(0, 0, h))
    rot = V(0,0,1).cross(d)
    if rot.Length > 1e-9: f.rotate(V(0,0,0), rot, math.degrees(V(0,0,1).getAngle(d)))
    elif d.z < 0: f.rotate(V(0,0,0), V(1,0,0), 180)
    f.translate(p0); return f

def fasteners():
    bolts = []
    for k in range(8):
        a = math.radians(22.5 + 45 * k); y, z = 152 * math.sin(a), 152 * math.cos(a)
        x0 = X(1640) - 9
        b = cyl(6, V(x0, y, z), V(1,0,0), X(1745) - x0 + 14)
        b = b.fuse(hexbar(19, 8, V(x0 - 8, y, z), V(1,0,0))).fuse(hexbar(19, 10, V(X(1745), y, z), V(1,0,0)))
        bolts.append(b)
    studs = []
    for k in range(6):
        a = math.radians(30 + 60 * k); y, z = 80 * math.sin(a), 80 * math.cos(a)
        studs.append(cyl(8, V(X(2019) + 5, y, z), V(1,0,0), X(2190) - X(2019)))
    return Part.makeCompound(bolts), Part.makeCompound(studs)

def drain_valve():
    p0 = V(X(1434), 0, -150); d = V(0, 0, -1)
    a = p0 + d * 28
    body = hexbar(30, 10, a, d).fuse(Part.makeSphere(17, a + d * 22)).fuse(cyl(9, a + d * 30, d, 16))
    perp = V(0, 1, 0)
    handle = cyl(4, a + d * 34, perp, 70).fuse(box(-2, 2, 0, 0, 0, 0)) if False else cyl(4, a + d * 34, perp, 70)
    return body, handle
