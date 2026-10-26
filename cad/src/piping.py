# Обвязка насоса по рис. 1 РЭ (исполнение В1Т): коллекторы 3 и 22, вентили 1 и 10, патрубок 29, кран 23,
# клапан 21, кран вакуумный 25, датчик заполнения 2, панель 4 с приборами, пеносмеситель 7 по рис. 10.
# Положение снято с двух видов рис. 1: вид со стороны всасывания  px = 693 + Y·1,907, py = 1127 − Z·1,907;
# вид сбоку (со стороны ступени ВД)  px = 1660 + X·1,907, py = 1127 − Z·1,907. Точность около ±5–10 мм.
# Внутреннее устройство вентилей и пеносмесителя упрощено: показаны корпус, клапан/сопло/диффузор, маховик.
import math, Part
from FreeCAD import Vector as V

def cyl(r, p, d, h): return Part.makeCylinder(r, h, p, d)
def box(x0, x1, y0, y1, z0, z1): return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cone(r1, r2, p, d, h): return Part.makeCone(r1, r2, h, p, d)

def tube(pts, ro, ri, cap0=False, cap1=False):
    """Труба по ломаной: цилиндрические участки + сферические колена; полая."""
    P = [V(*p) for p in pts]
    outer = None; inner = None
    for a, b in zip(P, P[1:]):
        d = b - a; L = d.Length; d.normalize()
        o = cyl(ro, a, d, L); i = cyl(ri, a - d * 0.01, d, L + 0.02)
        outer = o if outer is None else outer.fuse(o); inner = i if inner is None else inner.fuse(i)
    for p in P[1:-1]:
        outer = outer.fuse(Part.makeSphere(ro, p)); inner = inner.fuse(Part.makeSphere(ri, p))
    s = outer.cut(inner)
    return s.removeSplitter()

def flange(p, d, r, t, ri, nb=4, rb=None):
    f = cyl(r, p, d, t)
    if ri > 0: f = f.cut(cyl(ri, p - d, d, t + 2))
    rb = rb or (r + ri) / 2
    # отверстия под болты
    u = d.cross(V(0, 0, 1)) if abs(d.z) < 0.9 else d.cross(V(1, 0, 0)); u.normalize(); w = d.cross(u)
    for k in range(nb):
        a = 2 * math.pi * (k + 0.5) / nb
        f = f.cut(cyl(r * 0.12 + 2, p + u * (rb * math.cos(a)) + w * (rb * math.sin(a)) - d, d, t + 2))
    return f

def handwheel(c, d, R=47, hub=12):
    """Маховик с тремя спицами и рукояткой (рис. 7), ось d."""
    u = d.cross(V(0, 0, 1)) if abs(d.z) < 0.9 else d.cross(V(1, 0, 0)); u.normalize(); w = d.cross(u)
    rim = Part.makeTorus(R, 5, c, d)
    s = rim.fuse(cyl(hub, c - d * 8, d, 16))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        e = u * math.cos(a) + w * math.sin(a)
        s = s.fuse(cyl(3.5, c + e * hub * 0.8, e, R - hub * 0.8))
    a = 0.3 + math.pi / 3
    e = u * math.cos(a) + w * math.sin(a)
    s = s.fuse(cyl(5, c + e * R, d, 45))
    return s

def gauge(c, d, R=45, t=22):
    body = cyl(R, c, d, t)
    face = cyl(R - 4, c + d * (t - 0.5), d, 1.5)
    return body, face

PARTS = []
def add(n, l, s, c):
    if not s.isValid():
        s = s.copy(); s.fix(1e-4, 1e-4, 1e-3)
    PARTS.append((n, l, s, c))

STEEL = (0.78, 0.79, 0.82); ALU = (0.68, 0.71, 0.74); RED = (0.75, 0.16, 0.13); BRASS = (0.8, 0.65, 0.3)
DARK = (0.3, 0.31, 0.34); WHITE = (0.93, 0.93, 0.9); PANEL = (0.86, 0.87, 0.85); FOAM = (0.62, 0.66, 0.7)

def build():
    # ---------- коллектор нормального давления 3 ----------
    XC, ZC = 400.0, 290.0                   # ось трубы коллектора (идёт поперёк насоса, вдоль Y)
    body = cyl(56, V(XC, -240, ZC), V(0, 1, 0), 520)
    body = body.fuse(box(XC - 55, XC + 55, 25, 135, 229, ZC))           # горловина над напорным патрубком корпуса
    body = body.fuse(box(XC - 55, XC + 45, -40, 200, ZC, 365))          # средняя камера (под пеносмесителем и панелью)
    body = body.fuse(flange(V(XC, -240, ZC), V(0, -1, 0), 70, 14, 0, 4))  # заглушка выхода на лафетный ствол 26 (торец)
    cav = cyl(48, V(XC, -232, ZC), V(0, 1, 0), 504).fuse(box(XC - 46, XC + 46, 32, 128, 222, ZC)).fuse(
          box(XC - 47, XC + 37, -32, 192, ZC - 20, 355))
    body = body.cut(cav)
    # отверстия: к вентилям 1, к вентилю 10, к пеносмесителю, к патрубку 29, к вакуумному крану, к датчику
    holes = [cyl(36, V(XC, y, ZC), V(1, 0, 0), 80) for y in (-201, 261)]
    holes += [cyl(30, V(XC, 230, ZC), V(0, 0, 1), 90),                 # к вентилю 10
              cyl(22, V(XC - 70, -140, 300), V(1, 0, 0), 40),           # патрубок 29
              cyl(13, V(XC + 15, 0, 340), V(0, 0, 1), 40),              # подвод к крану эжектора
              cyl(10, V(XC - 12, -190, 320), V(0, 0, 1), 40),           # вакуумный кран
              cyl(8, V(XC - 12, -130, 320), V(0, 0, 1), 40),            # датчик заполнения
              cyl(4, V(XC + 40, 140, 276), V(1, 0, 0), 30)]             # манометр 12
    body = body.cut(holes)
    add('P_kollektor_3', 'П 3 Коллектор нормального давления', body, ALU)

    # ---------- вентили напорные 1 (рис. 7) ----------
    for side, y, nm in ((-1, -201.0, 'левый'), (1, 261.0, 'правый')):
        p0 = V(XC + 48, y, ZC)
        b = cyl(46, p0, V(1, 0, 0), 92).cut(cyl(36, p0 - V(1, 0, 0), V(1, 0, 0), 84))
        # ромбовидный фланец корпуса (видно на рис. 1)
        sq = box(-58, 58, -58, 58, 0, 14); sq.rotate(V(0, 0, 0), V(0, 0, 1), 45); sq.rotate(V(0, 0, 0), V(0, 1, 0), 90); sq.translate(V(XC + 62, y, ZC))
        b = b.fuse(sq.cut(cyl(36, V(XC + 50, y, ZC), V(1, 0, 0), 40)))
        # выходной патрубок вниз-наружу под 45° с соединительной головкой
        d = V(0, side * 0.72, -0.69); d.normalize()
        pc = V(XC + 95, y, ZC)
        b = b.fuse(tube([(pc.x, pc.y, pc.z), (pc.x + d.x * 105, pc.y + d.y * 105, pc.z + d.z * 105)], 40, 33))
        b = b.fuse(flange(pc + d * 100, d, 52, 22, 33, 3))
        b = b.removeSplitter()
        add('P_ventil_1_' + ('l' if side < 0 else 'r'), 'П 1 Вентиль напорный нормального давления (%s)' % nm, b, ALU)
        # клапан 4 со штоком и маховиком
        valve = cyl(33, V(XC + 70, y, ZC), V(1, 0, 0), 10).fuse(cyl(9, V(XC + 70, y, ZC), V(1, 0, 0), 120))
        add('P_ventil_1_klapan_' + ('l' if side < 0 else 'r'), 'П 1 Вентиль %s: клапан и шток' % nm, valve, STEEL)
        add('P_ventil_1_mahovik_' + ('l' if side < 0 else 'r'), 'П 1 Вентиль %s: маховик' % nm, handwheel(V(XC + 190, y, ZC), V(1, 0, 0)), RED)

    # ---------- вентиль 10 подачи воды в цистерну ----------
    y10, z10 = 271.0, 465.0
    riser = tube([(XC, 230, ZC + 60), (XC, 230, 410), (XC + 30, y10, z10)], 30, 24)
    v10 = cyl(46, V(XC + 30, y10, z10), V(1, 0, 0), 92).cut(cyl(36, V(XC + 29, y10, z10), V(1, 0, 0), 84))
    sq = box(-58, 58, -58, 58, 0, 14); sq.rotate(V(0, 0, 0), V(0, 0, 1), 45); sq.rotate(V(0, 0, 0), V(0, 1, 0), 90); sq.translate(V(XC + 44, y10, z10))
    v10 = v10.fuse(sq.cut(cyl(36, V(XC + 30, y10, z10), V(1, 0, 0), 40)))
    # выход в цистерну — назад (к цистерне автомобиля), условно
    v10 = v10.fuse(tube([(XC + 30, y10, z10), (XC - 70, y10, z10)], 36, 30)).fuse(flange(V(XC - 70, y10, z10), V(-1, 0, 0), 58, 14, 30, 4))
    add('P_ventil_10', 'П 10 Вентиль напорный подачи воды в цистерну', riser.fuse(v10).removeSplitter(), ALU)
    add('P_ventil_10_mahovik', 'П 10 Вентиль в цистерну: маховик', handwheel(V(XC + 172, y10, z10), V(1, 0, 0)), RED)

    # ---------- патрубок 29: коллектор НД -> вход ступени ВД ----------
    # вход ВД: отверстие в приливе корпуса 14 (hp.py) x=173, y=-198, верх прилива z=225
    p29 = tube([(173, -198, 222), (173, -198, 300), (173, -140, 300), (XC - 52, -140, 300)], 27, 22)
    p29 = p29.fuse(flange(V(173, -198, 225), V(0, 0, 1), 48, 12, 22, 4))
    add('P_patrubok_29', 'П 29 Патрубок от коллектора НД к ступени ВД', p29.removeSplitter(), STEEL)

    # ---------- коллектор высокого давления 22, кран 23, клапан 21 ----------
    k22 = tube([(272, -198, 222), (272, -198, 470)], 20, 14).fuse(flange(V(272, -198, 225), V(0, 0, 1), 42, 12, 14, 4))
    k22 = k22.fuse(cyl(28, V(272, -198, 300), V(0, 0, 1), 50)).cut(cyl(14, V(272, -198, 290), V(0, 0, 1), 70))
    add('P_kollektor_22', 'П 22 Коллектор высокого давления', k22.removeSplitter(), STEEL)
    kr = Part.makeSphere(26, V(272, -198, 490)).fuse(cyl(16, V(272, -198, 470), V(0, 0, 1), 60))
    kr = kr.cut(cyl(9, V(272, -198, 460), V(0, 0, 1), 90))
    kr = kr.fuse(cyl(4, V(272, -198, 490), V(1, 0, 0), 40)).fuse(box(305, 312, -204, -192, 490, 560))  # рукоятка
    add('P_kran_23', 'П 23 Кран высокого давления', kr, RED)
    kl = cyl(16, V(272, -198, 325), V(0, -1, 0), 70).fuse(cyl(11, V(272, -270, 325), V(0, -1, 0), 45)).fuse(cyl(4, V(272, -315, 325), V(0, -1, 0), 25))
    add('P_klapan_21', 'П 21 Клапан перепускной', kl, BRASS)

    # ---------- кран вакуумный 25 и датчик заполнения 2 ----------
    vk = tube([(XC - 12, -190, 345), (XC - 12, -190, 420)], 14, 10).fuse(Part.makeSphere(22, V(XC - 12, -190, 440)))
    vk = vk.fuse(tube([(XC - 12, -190, 440), (XC - 12, -190, 500)], 14, 10)).fuse(box(XC - 16, XC + 50, -194, -186, 436, 444))
    add('P_kran_vakuum_25', 'П 25 Кран вакуумный', vk.removeSplitter(), BRASS)
    ds = cyl(12, V(XC - 12, -130, 345), V(0, 0, 1), 40).fuse(cyl(16, V(XC - 12, -130, 385), V(0, 0, 1), 22))
    add('P_datchik_2', 'П 2 Датчик заполнения', ds, DARK)

    # ---------- панель управления 4 с приборами ----------
    pan = box(535, 560, -70, 203, 334, 517)
    add('P_panel_4', 'П 4 Панель управления', pan, PANEL)
    for n, y, z in (('5 Рукоятка включения эжектора', 4, 402), ('8 Рукоятка дозатора', 108, 402)):
        h = cyl(18, V(560, y, z), V(1, 0, 0), 8).fuse(box(566, 574, y - 4, y + 4, z - 40, z + 8))
        add('P_ruk_' + n.split()[0], 'П ' + n, h, DARK)
    tb = box(560, 572, -40, 50, 455, 505)
    add('P_tahometr_6', 'П 6 Блок индикации тахометра', tb, DARK)
    g12, f12 = gauge(V(520, 140, 276), V(1, 0, 0))
    g12 = g12.fuse(tube([(XC + 56, 140, 276), (520, 140, 276)], 7, 4))
    add('P_manometr_12', 'П 12 Манометр нормального давления', g12, STEEL); add('P_manometr_12_s', 'П 12 Манометр: шкала', f12, WHITE)
    pl = box(540, 548, -300, -70, 60, 170)
    add('P_shitok', 'П Щиток приборов ВД (условно)', pl, PANEL)
    for n, nm, y, z in (('18', 'Манометр высокого давления', -248, 114), ('19', 'Мановакуумметр', -122, 118)):
        g, f = gauge(V(548, y, z), V(1, 0, 0), 40, 20)
        add('P_pribor_' + n, 'П %s %s' % (n, nm), g, STEEL); add('P_pribor_%s_s' % n, 'П %s %s: шкала' % (n, nm), f, WHITE)

    # ---------- пеносмеситель 7 (рис. 10) ----------
    XE, YE = 479.0, 0.0                       # ось эжектора: вертикальная, низ диффузора — в прилив крышки 12 (z 112)
    krn = box(XE - 40, XE + 40, YE - 52, YE + 52, 368, 448).cut(cyl(22, V(XE, YE, 360), V(0, 0, 1), 95)).fuse(
          tube([(XE, YE, 448), (XE, YE, 478), (XC + 15, YE, 478), (XC + 15, YE, 362)], 18, 13))     # подвод воды из коллектора
    add('PS_kran_1', 'ПС 1 Кран эжектора', krn.removeSplitter(), ALU)
    kor = cyl(32, V(XE, YE, 292), V(0, 0, 1), 76).cut(cyl(26, V(XE, YE, 290), V(0, 0, 1), 80))
    add('PS_korpus_13', 'ПС 13 Корпус пеносмесителя', kor, ALU)
    so = cone(26, 9, V(XE, YE, 372), V(0, 0, -1), 62).cut(cone(20, 5, V(XE, YE, 372.01), V(0, 0, -1), 62.02))
    add('PS_soplo_14', 'ПС 14 Сопло', so, BRASS)
    df = cone(14, 17, V(XE, YE, 292), V(0, 0, -1), 22).fuse(cone(17, 25, V(XE, YE, 270), V(0, 0, -1), 160))
    df = df.cut(cone(9, 11, V(XE, YE, 292.01), V(0, 0, -1), 22.02)).cut(cone(11, 21, V(XE, YE, 270.01), V(0, 0, -1), 160.02))
    add('PS_diffuzor_10', 'ПС 10 Диффузор', df.removeSplitter(), STEEL)
    # дозатор 2 с заслонкой 6, переводной патрубок 8, патрубок подвода пенообразователя 3 (рис. 1 поз. 11), клапан 4
    dz = box(XE - 40, XE + 40, 63, 153, 370, 450).cut(cyl(28, V(XE - 41, 108, 410), V(1, 0, 0), 82))
    add('PS_dozator_2', 'ПС 2 Дозатор', dz, ALU)
    zs = box(XE - 2, XE + 2, 82, 134, 384, 436)
    add('PS_zaslonka_6', 'ПС 6 Заслонка регулирующая', zs, BRASS)
    p8 = tube([(XE, 108, 372), (XE, 108, 335), (XE, 26, 335)], 18, 13)
    add('PS_patrubok_8', 'ПС 8 Патрубок переводной', p8.removeSplitter(), ALU)
    p3 = tube([(XE, 153, 410), (XE, 300, 410)], 25, 20).fuse(flange(V(XE, 300, 410), V(0, 1, 0), 48, 12, 20, 4))
    add('PS_patrubok_3', 'ПС 3 Патрубок подвода пенообразователя', p3.removeSplitter(), STEEL)
    kp = cyl(20, V(XE, 158, 410), V(0, 1, 0), 3)
    add('PS_klapan_4', 'ПС 4 Клапан лепестковый', kp, DARK)
    return PARTS
