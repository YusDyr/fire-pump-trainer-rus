# -*- coding: utf-8 -*-
"""Сцена Blender: анимация потоков воды в насосе НЦПК-40/100-4/400М-В1У.

Запуск внутри Blender (5.2): exec(open('.../water_scene.py').read()) при DIR = папка с NCPK_M_V1U.glb.
Строит один таймлайн из четырёх сценариев (маркеры S1..S4), каждый рендерится отдельным роликом.
Координаты в мм в системе модели FreeCAD (X — ось вала НД к всасыванию, Z — вверх, +Y — вправо при взгляде со
стороны всасывания); в Blender 1 мм = 0,001 (импорт glTF возвращает ту же систему).

Вода показана схематично: частицы движутся по линиям потоков, заполненные участки — полупрозрачная «водяная жила».
Последовательность действий — по РЭ насоса М-В1У (2025) и урокам эмулятора.
"""
import bpy, math, os
from mathutils import Vector as V, Matrix

DIR = globals().get('DIR', '/Users/dyr/YusDyr Vivo/NCPK_3D/blender')
FPS = 30
MM = 0.001
def P(x, y, z): return V((x * MM, y * MM, z * MM))
def f1(px, py): return ((px - 540) * 0.9, (690 - py) * 0.9)

# ------------------------------------------------------------------ сцена и импорт
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
sc = bpy.context.scene
sc.render.fps = FPS
import logging
for _n in ('glTFImporter', 'io_import_scene_gltf2', 'io_scene_gltf2'): logging.getLogger(_n).setLevel(logging.ERROR)
try: bpy.ops.import_scene.gltf(filepath=os.path.join(DIR, 'NCPK_M_V1U.glb'), loglevel=40)
except TypeError: bpy.ops.import_scene.gltf(filepath=os.path.join(DIR, 'NCPK_M_V1U.glb'))
OB = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
# импорт glTF ставит детали ступени ВД узлами со смещением на ось ВД и под общий пустой объект —
# переносим все смещения в геометрию, чтобы у каждой детали начало координат было в нуле модели
for o in OB.values():
    mw = o.matrix_world.copy(); o.parent = None
    o.data.transform(mw); o.matrix_world = Matrix.Identity(4)
def obs(prefixes): return [o for n, o in OB.items() if n.startswith(prefixes)]

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
C_EXT, C_WATER, C_HUD = coll('Внешнее'), coll('Вода'), coll('Подписи')
def link(o, c):
    for u in list(o.users_collection): u.objects.unlink(o)
    c.objects.link(o)

# ------------------------------------------------------------------ материалы
def mat(name, col, alpha=1.0, emit=0.0, rough=0.5, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Alpha'].default_value = alpha
    if emit:
        b.inputs['Emission Color'].default_value = (*col, 1)
        b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        try: m.surface_render_method = 'BLENDED'
        except Exception: m.blend_method = 'BLEND'
        try: m.use_transparency_overlap = False
        except Exception: pass
    m.diffuse_color = (*col, alpha)
    return m
M_WATER = mat('Вода: частицы', (0.10, 0.45, 1.0), emit=2.5)
M_WBODY = mat('Вода: заполнено', (0.15, 0.50, 1.0), alpha=0.42, emit=0.4, rough=0.1)
M_AIR = mat('Воздух', (0.92, 0.95, 1.0), emit=1.5)
M_FOAM = mat('Пенообразователь', (1.0, 0.78, 0.10), emit=2.0)
M_FBODY = mat('Пенообразователь: заполнено', (1.0, 0.78, 0.10), alpha=0.4, emit=0.3)
M_GLASS = mat('Трубы (прозрачные)', (0.70, 0.74, 0.78), alpha=0.22, rough=0.15)
M_HOSE = mat('Рукава', (0.30, 0.31, 0.33), alpha=0.30, rough=0.6)
M_TANK = mat('Ёмкости', (0.75, 0.80, 0.85), alpha=0.15, rough=0.2)
M_POND = mat('Водоём', (0.08, 0.30, 0.55), alpha=0.75, rough=0.05)
M_GROUND = mat('Земля', (0.72, 0.72, 0.7), rough=0.95)
M_DARK = mat('Тёмный', (0.08, 0.08, 0.09), rough=0.6)
M_RED = mat('Красный', (0.75, 0.08, 0.06), rough=0.4)
M_TXT = mat('Текст', (1, 1, 1), emit=1.0)
M_BAR = mat('Плашка', (0.02, 0.03, 0.05), alpha=0.62)
M_ON = mat('Индикатор: включено', (0.2, 1.0, 0.3), emit=1.5)
M_HOT = mat('Индикатор: муфта', (1.0, 0.45, 0.05), emit=1.5)

GLASS_PARTS = ('П Коллектор', 'П Труба вакуумирования', 'П 1 Напорный вентиль DN70 (левый): корпус', 'П 12 Напорный вентиль DN70 (правый): корпус',
               'П 10 Напорный вентиль DN80 заполнения цистерны: корпус', 'П 9 ', 'П Патрубок', 'П 32 ', 'П 31 Кран высокого давления',
               'П 16 ', 'П 5 Вакуумный затвор', 'П 41 ', 'НД 19 ', 'ВД 1 Патрубки')
# материалы «как на машине»: литой алюминий, бронзовые колёса, сталь, красные маховики; сечение — оранжевое
M_CAST = mat('Литьё (алюминий)', (0.50, 0.52, 0.55), rough=0.45, metal=0.35)
M_BRONZE = mat('Бронза', (0.70, 0.42, 0.16), rough=0.35, metal=0.5)
M_STEEL = mat('Сталь', (0.70, 0.71, 0.73), rough=0.3, metal=0.6)
M_DSTEEL = mat('Сталь тёмная', (0.22, 0.23, 0.25), rough=0.45, metal=0.5)
M_WHITE = mat('Белый', (0.88, 0.88, 0.86), rough=0.5)
M_BUK = mat('БУК-02', (0.80, 0.10, 0.08), rough=0.45)
M_SECT = mat('Сечение', (0.92, 0.42, 0.16), rough=0.6)
MAT_RULES = [
    (('НД 15', 'ВД 3 ', 'ВД 5 '), M_BRONZE),
    (('НД 22', 'ВД 9 ', 'НД 1 ', 'НД 25', 'НД 26', 'ВД 17', 'П 8 '), M_STEEL),
    (('НД 2 ', 'НД 6', 'НД 9 ', 'ВД 8 ', 'ВД 10', 'НД 3 ', 'НД 4 ', 'ВД 11', 'НД 8 ', 'НД 7 ', 'НД 17', 'Р 4', 'Р 5', 'Р 6', 'П 24', 'П 23'), M_DSTEEL),
    (('НД 10', 'НД 11', 'НД 12', 'НД 14', 'НД 18', 'ВД 7', 'ВД 12', 'ВД 13', 'ВД 14', 'ВД 15', 'НД 20', 'НД 21', 'НД 23', 'НД 24',
      'НД 5 ', 'Р 3', 'Р Кожух', 'П 28', 'П 41', 'П Кран эжектора'), M_DARK),
    (('П 11', 'П 15', 'П 22', 'П 2 ', 'П 13'), M_WHITE),
    (('П 7 ',), M_BUK),
]
for n, o in OB.items():
    m = M_CAST
    for pref, mm in MAT_RULES:
        if n.startswith(pref): m = mm
    if any(w in n for w in ('Болты', 'Шпильки', 'болты', 'Гайки', 'тарель', 'шпиндель', 'Нажимная втулка', ': шар')): m = M_STEEL
    if n.startswith(('П Трубка', 'П 27', 'П 28 Обратный', 'П 29')): m = M_BRONZE
    if n.startswith(('П 20', 'НД 7 Кабель', 'П Кабель')): m = M_DARK
    if 'Пневмораспределитель' in n or n.startswith('П 23 Рукав'): m = M_DARK
    if n.startswith('П 23 Манометр'): m = M_WHITE
    if n.startswith('П 23 Фитинги'): m = M_BRONZE
    if n.startswith(('П 2 Ручной дозатор пенообразователя: рукоятка', 'П 13 Крышка', 'П 14')): m = M_DARK
    if n.startswith('П 2 Ручной дозатор пенообразователя: колпачок'): m = M_RED
    if n.startswith('П 7 БУК-02: лицевая'): m = M_WHITE
    if n.startswith('П 7 БУК-02: кнопки'): m = M_STEEL
    if 'маховик' in n or 'Рукоятка вакуумного' in n or 'Кран высокого давления: рукоятка' in n: m = M_RED
    o.data.materials.clear(); o.data.materials.append(m)
M_PU = mat('Пневмотрубки (полиуретан)', (0.95, 0.72, 0.25), alpha=0.55, rough=0.2)
for o in obs(('П Пневмолиния',)): o.data.materials.clear(); o.data.materials.append(M_PU)
for o in obs(GLASS_PARTS):
    if o.name.endswith('рукоятка') or 'маховик' in o.name: continue
    o.data.materials.clear(); o.data.materials.append(M_GLASS)

# ------------------------------------------------------------------ разрезы (булевы, резак двигается по сценариям)
def box_obj(name, lo, hi, m=None, c=None):
    me = bpy.data.meshes.new(name)
    x0, y0, z0 = lo; x1, y1, z1 = hi
    vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata([V(v) * MM for v in vs], [], fs); me.update()
    o = bpy.data.objects.new(name, me); (c or sc.collection).objects.link(o)
    if m: o.data.materials.append(m)
    return o
CUT_ND = box_obj('Резак НД', (-200, 0, -400), (900, 700, 400))
CUT_HP = box_obj('Резак ВД', (-200, -700, -400), (900, -201, 400))
for cutter in (CUT_ND, CUT_HP):
    cutter.display_type = 'WIRE'; cutter.hide_render = True; cutter.data.materials.append(M_SECT)
def add_bool(o, cutter):
    md = o.modifiers.new('Разрез ' + cutter.name[-2:], 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cutter
    try: md.material_mode = 'TRANSFER'   # грани сечения — материалом резака
    except Exception: pass
    for s in ('EXACT', 'FLOAT', 'FAST'):
        try: md.solver = s; break
        except Exception: pass
ND_CUT_PARTS = obs(('НД 13', 'НД 14', 'НД 15', 'НД 16', 'НД 17', 'НД 18', 'НД 12', 'НД 9', 'НД 10', 'НД 11', 'НД 20', 'НД 21'))
HP_CUT_PARTS = obs(('ВД 1 ', 'ВД 2 ', 'ВД 3 ', 'ВД 4 ', 'ВД 5 ', 'ВД 6 ', 'ВД 14', 'ВД 15', 'ВД 7', 'ВД 8 ', 'ВД 10', 'ВД 12', 'ВД 13'))
for o in ND_CUT_PARTS: add_bool(o, CUT_ND)
for o in HP_CUT_PARTS: add_bool(o, CUT_HP)
# что заслоняет разрез НД со стороны камеры — прячем в кадрах с разрезом НД
FRONT = obs(('П 13 ', 'П 15 ', 'П 11 '))

# ------------------------------------------------------------------ точки вращения
def set_pivot(o, piv):
    o.data.transform(Matrix.Translation(-piv)); o.location = piv
HPA = P(0, -201, 72)
ROT_ND = obs(('НД 1 ', 'НД 8 ', 'НД 15', 'НД 22', 'НД 25', 'НД 26', 'НД 20', 'НД 21', 'НД 10', 'НД 11'))
ROT_CL = obs(('НД 3 ', 'НД 4 ', 'НД 24'))
ROT_HP = obs(('ВД 3 ', 'ВД 5 ', 'ВД 9 ', 'ВД 11', 'ВД 17'))
for o in ROT_HP: set_pivot(o, HPA)

def vanes(name, parent, x0, x1, r0, r1, n, sweep, cy=0.0, cz=0.0, th=3.0, m=None):
    """Лопатки рабочего колеса: n изогнутых пластин между радиусами r0..r1, ширина по оси x0..x1 (мм)."""
    vs, fs = [], []
    K = 8
    for i in range(n):
        a0 = 2 * math.pi * i / n
        base = len(vs)
        for k in range(K + 1):
            t = k / K; r = r0 + (r1 - r0) * t; a = a0 + sweep * t
            for dx, dr in ((x0, -th / 2), (x1, -th / 2), (x1, th / 2), (x0, th / 2)):
                aa = a + dr / max(r, 1)
                vs.append(V((dx, cy + r * math.sin(aa), cz + r * math.cos(aa))) * MM)
        for k in range(K):
            q = base + 4 * k
            for j in range(4):
                fs.append((q + j, q + (j + 1) % 4, q + 4 + (j + 1) % 4, q + 4 + j))
        fs.append((base, base + 1, base + 2, base + 3)); e = base + 4 * K; fs.append((e + 3, e + 2, e + 1, e))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    o = bpy.data.objects.new(name, me); parent.users_collection[0].objects.link(o)
    o.data.materials.append(m or parent.data.materials[0])
    o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o
def mark(name, parent, lo, hi, m):
    """Метка на вращающейся детали (шпонка, полоса) — чтобы было видно вращение."""
    o = box_obj(name, lo, hi, m, parent.users_collection[0])
    o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o
# сетка 17 на входе: купол из ячеек вместо сплошного тела
_st = OB['НД 17 Сетка']; _st.hide_render = True; _st.hide_viewport = True
bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=14, radius=0.06, location=(0.622, 0, 0))
_dome = bpy.context.active_object; _dome.name = 'НД 17 Сетка (ячейки)'
import bmesh
_bm = bmesh.new(); _bm.from_mesh(_dome.data)
bmesh.ops.delete(_bm, geom=[v for v in _bm.verts if v.co.x < 0.0], context='VERTS'); _bm.to_mesh(_dome.data); _bm.free()
_dome.scale = (0.55, 1.0, 1.0)
_w = _dome.modifiers.new('Ячейки', 'WIREFRAME'); _w.thickness = 0.0025; _w.use_replace = True
_dome.data.materials.append(mat('Сетка', (0.25, 0.26, 0.28), rough=0.4, metal=0.6))
for _c in list(_dome.users_collection): _c.objects.unlink(_dome)
_st.users_collection[0].objects.link(_dome)
add_bool(_dome, CUT_ND)
M_MARK = mat('Метка', (0.95, 0.75, 0.10), rough=0.4, emit=0.3)
IMP = OB['НД 15 Колесо рабочее']
mark('НД 22 Шпонка (метка)', OB['НД 22 Вал'], (150, -6, 22), (470, 6, 28), M_MARK)
mark('НД 1 Метка полумуфты', OB['НД 1 Полумуфта'], (2, -8, 30), (48, 8, 60), M_MARK)
mark('НД 3 Метка шкива', OB['НД 3 Шкив ведущий'], (36, -10, 50), (40, 10, 84), M_MARK)
mark('ВД 11 Метка шкива', OB['ВД 11 Шкив ведомый'], (36, -201 - 6, 72 + 15), (40, -201 + 6, 72 + 38), M_MARK)
mark('ВД 9 Шпонка (метка)', OB['ВД 9 Вал'], (60, -205, 72 + 18), (370, -197, 72 + 23), M_MARK)
# положения узлов — по фото отсека (как в cad/src_m/build_m.py, словарь PH)
yL, zL = -290, 258; yR, zR = 380, 250; yT, zT = 145, 325; yv, zv = -147, 560; ye, ze = -30, 293
XH, YH, ZK = 372, -224, 468; YFV, ZFV = -400, 520
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))   # крышки вентилей DN70 развёрнуты наружу на 30°
CTRL = {  # ключ: (объект, точка, ось, угол открытия, ход вдоль X мм)
    'v1l': ('П 1 Напорный вентиль DN70 (левый): маховик', P(447 + 65 * C30, yL - 65 * S30, zL), (C30, -S30, 0.0), 4 * math.pi, 12),
    'v1r': ('П 12 Напорный вентиль DN70 (правый): маховик', P(447 + 65 * C30, yR + 65 * S30, zR), (C30, S30, 0.0), 4 * math.pi, 12),
    'vt': ('П 10 Напорный вентиль DN80 заполнения цистерны: маховик', P(507, yT, zT), 0, 4 * math.pi, 12),
    'vac': ('П 5 Рукоятка вакуумного затвора', P(483, yv, zv + 20), 0, math.pi / 2, 0),     # вертикально — открыт, вдоль трубы — закрыт
    'kvd': ('П 31 Кран высокого давления: рукоятка', P(XH, YH - 46, ZK), 1, math.pi / 2, 0),   # вдоль трубы — открыт
    'ej': ('П Кран эжектора: рукоятка', P(560, ye, ze + 27), 2, math.pi / 2, 0),          # вдоль y — открыт
    'fv': ('П Кран магистрали пенобака: рукоятка', P(470, YFV - 20, ZFV), 1, -math.pi / 2, 0),   # поперёк трубы — закрыт
}
CTRLS = [(k,) + v for k, v in CTRL.items()]
# внутренности: тарели и шпиндели вентилей идут вместе с маховиками, шар крана ВД — с рукояткой
for k, lab, y_, z_ in (('v1l', 'П 1 Напорный вентиль DN70 (левый)', yL, zL), ('v1r', 'П 12 Напорный вентиль DN70 (правый)', yR, zR),
                       ('vt', 'П 10 Напорный вентиль DN80 заполнения цистерны', yT, zT)):
    for part in ('тарель', 'шпиндель'):
        n = lab + ': ' + part
        axv = (C30, -S30, 0.0) if k == 'v1l' else (C30, S30, 0.0) if k == 'v1r' else 0
        if n in OB: CTRLS.append((k, n, P(456, y_, z_), axv, 0.0, 20))
if 'П 31 Кран высокого давления: шар' in OB:
    CTRLS.append(('kvd', 'П 31 Кран высокого давления: шар', P(XH, YH, ZK), 1, math.pi / 2, 0))
for k, n, piv, ax, ang, lift in CTRLS: set_pivot(OB[n], piv)
CTRL_BASE = {n: OB[n].location.copy() for k, n, piv, ax, ang, lift in CTRLS}

# ------------------------------------------------------------------ внешнее: трубы, рукава, ёмкости
def poly_curve(name, pts, c, bevel=0.0, m=None, cyclic=False):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*P(*p), 1)
    sp.use_cyclic_u = cyclic
    if bevel: cu.bevel_depth = bevel * MM; cu.bevel_resolution = 3; cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); c.objects.link(o)
    if m: cu.materials.append(m)
    return o
def smooth(pts, r=40, n=5):
    """Скругляет ломаную (углы — дугами радиуса r мм) — для путей частиц."""
    if len(pts) < 3: return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = V(pts[i - 1]), V(pts[i]), V(pts[i + 1])
        d1, d2 = (a - b), (c - b)
        rr = min(r, d1.length / 2.2, d2.length / 2.2)
        if d1.length < 1e-6 or d2.length < 1e-6: continue
        p0 = b + d1.normalized() * rr; p2 = b + d2.normalized() * rr
        for k in range(n + 1):
            t = k / n; out.append(tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2))
    out.append(pts[-1]); return out

EXT = {}
def ext(key, o): EXT.setdefault(key, []).append(o); return o
# всасывающий патрубок АЦ с тройником линии из цистерны
ext('suct', poly_curve('Патрубок всасывающий DN125 (фланец)', [(654, 0, 0), (730, 0, 0)], C_EXT, 66, M_GLASS))
# вода из цистерны приходит снизу справа по большой трубе с затвором (фото отсека)
TANKL = [(-500, 350, 300), (-500, 350, 30), (640, 350, 30), (700, 350, 30), (740, 300, 20), (740, 60, 0), (700, 0, 0)]   # цистерна за насосом; труба справа, затвор у фланца (фото, метка B)
ext('tankline', poly_curve('Линия «Вода из цистерны»', smooth(TANKL, 120, 6), C_EXT, 50, M_GLASS))
ext('tankline', box_obj('Затвор «Вода из цистерны»', (630, 315, -5), (670, 385, 65), M_RED, C_EXT))
ext('tank', box_obj('Цистерна (условно, за насосом)', (-1700, -700, 300), (-350, 700, 1150), M_TANK, C_EXT))
ext('fill', poly_curve('Трубопровод заполнения цистерны', [(352, yT, zT), (250, yT, zT), (-100, yT, 700), (-350, yT, 700)], C_EXT, 40, M_GLASS))
RES_PATH = [(1520, 0, -1330), (1470, 0, -1080), (1330, 0, -400), (900, 0, -40), (730, 0, 0)]
ext('res', poly_curve('Рукав всасывающий', smooth(RES_PATH, 160, 8), C_EXT, 66, M_HOSE))
ext('res', box_obj('Сетка всасывающая', (1460, -80, -1430), (1580, 80, -1290), M_DARK, C_EXT))
ext('res', box_obj('Водоём', (1150, -700, -1600), (2600, 700, -1150), M_POND, C_EXT))
HYD_PATH = [(1900, 0, -750), (1900, 0, -350), (1600, 0, -350), (1000, 0, -60), (730, 0, 0)]
ext('hyd', poly_curve('Рукав от колонки', smooth(HYD_PATH, 150, 8), C_EXT, 40, M_HOSE))
ext('hyd', box_obj('Гидрант с колонкой', (1850, -60, -900), (1950, 60, -300), M_RED, C_EXT))
ground = box_obj('Земля', (-600, -1500, -770), (1150, 1500, -750), M_GROUND, C_EXT)
OUT_L = [(447, -520, -330), (447, -560, -450), (560, -800, -730), (1300, -1250, -740)]
OUT_R = [(447, 610, -330), (447, 650, -450), (560, 900, -730), (1300, 1400, -740)]
ext('hoseL', poly_curve('Рукав напорный (левый)', smooth(OUT_L, 140, 8), C_EXT, 38, M_HOSE))
ext('hoseR', poly_curve('Рукав напорный (правый)', smooth(OUT_R, 140, 8), C_EXT, 38, M_HOSE))
# вакуумная линия: из верхней точки коллектора к затвору 5, от затвора к агрегату 24
VAC1 = [(447, -150, 330), (460, -170, 360), (470, -195, 430), (470, -195, zv)]   # рукав от насоса к затвору (уточнить на машине)
VAC2 = [(470, -147, zv), (470, 52, zv), (420, 52, zv), (420, 52, 440), (420, -430, 440), (420, -430, -80)]   # через клапан 28 — труба к агрегату слева внизу (уточнить)
EXH = [(505, -430, -235), (505, -430, -740)]
ext('vac', poly_curve('Выхлоп под днище', [(505, -430, -330), (505, -430, -740)], C_EXT, 10, M_HOSE))
# перепуск ступени ВД во всасывающий трубопровод
BYP = [(XH, YH, 300), (XH, -300, 250), (XH, -430, 150), (700, -430, 0), (700, -60, 0)]
ext('byp', poly_curve('Байпасная линия', BYP, C_EXT, 12, M_GLASS))
HPOUT = [(XH, YH, 680), (XH - 40, YH, 760), (200, YH, 820), (-200, YH, 850)]   # рукав к катушке ВД
ext('hpout', poly_curve('Рукав высокого давления', smooth(HPOUT, 120, 8), C_EXT, 16, M_HOSE))
# пенобак и линия пенообразователя к дозатору
yd, zd = -154, 278
FOAM_L = [(-200, YFV + 150, 640), (300, YFV + 120, 660), (470, YFV + 40, 650), (470, YFV, 610), (470, YFV, zd), (470, yd, zd), (550, yd, zd)]   # пенобак → рукав → кран магистрали → дозатор
ext('foam', box_obj('Пенобак (условно, за насосом)', (-1200, -1000, 300), (-500, -650, 700), mat('Пенобак', (1.0, 0.85, 0.3), alpha=0.25), C_EXT))
ext('foam', poly_curve('Линия пенообразователя', FOAM_L, C_EXT, 20, M_GLASS))
# продувка: от пневмоострова через обратный клапан 27 в коллектор
PURGE = [(348, 300, 420), (345, 250, 330), (350, 200, 306), (372, 175, 305)]   # от пневмоострова (сзади справа над коллектором) через обратный клапан 27 в коллектор
ext('purge', poly_curve('Линия продувки', PURGE, C_EXT, 8, mat('Пневмолиния', (0.2, 0.5, 0.9), rough=0.4)))

# ------------------------------------------------------------------ потоки: Geometry Nodes
def flow_group():
    ng = bpy.data.node_groups.get('Поток')
    if ng: return ng
    ng = bpy.data.node_groups.new('Поток', 'GeometryNodeTree')
    I = ng.interface
    I.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    for n, t, d in (('Фаза', 'NodeSocketFloat', 0.0), ('Заполнение', 'NodeSocketFloat', 1.0), ('Частицы', 'NodeSocketFloat', 1.0),
                    ('Жила', 'NodeSocketFloat', 0.0), ('Количество', 'NodeSocketInt', 60), ('Радиус', 'NodeSocketFloat', 0.02),
                    ('Размер', 'NodeSocketFloat', 0.006)):
        s = I.new_socket(n, in_out='INPUT', socket_type=t); s.default_value = d
    I.new_socket('Материал частиц', in_out='INPUT', socket_type='NodeSocketMaterial')
    I.new_socket('Материал жилы', in_out='INPUT', socket_type='NodeSocketMaterial')
    I.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    def math_(op, a, b=None):
        n = N.new('ShaderNodeMath'); n.operation = op
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    # частицы
    pts = N.new('GeometryNodePoints')
    cnt_on = math_('MULTIPLY', gi.outputs['Количество'], gi.outputs['Частицы'])
    L.new(cnt_on, pts.inputs['Count'])
    idx = N.new('GeometryNodeInputIndex').outputs[0]
    fac = math_('FRACT', math_('ADD', math_('DIVIDE', idx, gi.outputs['Количество']), gi.outputs['Фаза']))
    smp = N.new('GeometryNodeSampleCurve'); smp.mode = 'FACTOR'
    L.new(gi.outputs[0], smp.inputs['Curves']); L.new(fac, smp.inputs['Factor'])
    rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT_VECTOR'
    L.new(idx, rnd.inputs['ID'])
    neg = math_('MULTIPLY', gi.outputs['Радиус'], -1.0)
    cmb_lo = N.new('ShaderNodeCombineXYZ'); cmb_hi = N.new('ShaderNodeCombineXYZ')
    for k in range(3): L.new(neg, cmb_lo.inputs[k]); L.new(gi.outputs['Радиус'], cmb_hi.inputs[k])
    L.new(cmb_lo.outputs[0], rnd.inputs['Min']); L.new(cmb_hi.outputs[0], rnd.inputs['Max'])
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
    L.new(smp.outputs['Position'], add.inputs[0]); L.new(rnd.outputs['Value'], add.inputs[1])
    L.new(add.outputs[0], pts.inputs['Position'])
    cmp = N.new('FunctionNodeCompare'); cmp.data_type = 'FLOAT'; cmp.operation = 'GREATER_THAN'
    L.new(fac, cmp.inputs['A']); L.new(gi.outputs['Заполнение'], cmp.inputs['B'])
    dele = N.new('GeometryNodeDeleteGeometry'); dele.domain = 'POINT'
    L.new(pts.outputs[0], dele.inputs['Geometry']); L.new(cmp.outputs[0], dele.inputs['Selection'])
    ico = N.new('GeometryNodeMeshIcoSphere'); ico.inputs['Subdivisions'].default_value = 1
    L.new(gi.outputs['Размер'], ico.inputs['Radius'])
    inst = N.new('GeometryNodeInstanceOnPoints')
    L.new(dele.outputs[0], inst.inputs['Points']); L.new(ico.outputs['Mesh'], inst.inputs['Instance'])
    sm1 = N.new('GeometryNodeSetMaterial'); L.new(inst.outputs[0], sm1.inputs['Geometry']); L.new(gi.outputs['Материал частиц'], sm1.inputs['Material'])
    # жила (заполненный участок)
    trim = N.new('GeometryNodeTrimCurve')
    L.new(gi.outputs[0], trim.inputs['Curve'])
    endf = math_('MULTIPLY', gi.outputs['Заполнение'], gi.outputs['Жила'])
    try: L.new(endf, trim.inputs[3])
    except Exception: L.new(endf, trim.inputs['End'])
    circ = N.new('GeometryNodeCurvePrimitiveCircle'); circ.inputs['Resolution'].default_value = 12
    L.new(math_('MULTIPLY', gi.outputs['Радиус'], 1.5), circ.inputs['Radius'])
    c2m = N.new('GeometryNodeCurveToMesh'); L.new(trim.outputs[0], c2m.inputs['Curve']); L.new(circ.outputs[0], c2m.inputs['Profile Curve'])
    sw = N.new('GeometryNodeSwitch'); sw.input_type = 'GEOMETRY'
    gt = math_('GREATER_THAN', endf, 0.002)
    L.new(gt, sw.inputs['Switch']); L.new(c2m.outputs[0], sw.inputs['True'])
    sm2 = N.new('GeometryNodeSetMaterial'); L.new(sw.outputs[0], sm2.inputs['Geometry']); L.new(gi.outputs['Материал жилы'], sm2.inputs['Material'])
    join = N.new('GeometryNodeJoinGeometry'); L.new(sm2.outputs[0], join.inputs[0]); L.new(sm1.outputs[0], join.inputs[0])
    L.new(join.outputs[0], go.inputs[0])
    return ng
FG = flow_group()
def sock(ng, name):
    for it in ng.interface.items_tree:
        if getattr(it, 'in_out', '') == 'INPUT' and it.name == name: return it.identifier
SID = {n: sock(FG, n) for n in ('Фаза', 'Заполнение', 'Частицы', 'Жила', 'Количество', 'Радиус', 'Размер', 'Материал частиц', 'Материал жилы')}

FLOWS = {}
def msock(md, name):
    sid = SID[name]
    try: return getattr(md.properties.inputs, sid)   # Blender 5.x
    except AttributeError: return None
def mset(md, name, v):
    s = msock(md, name)
    if s is not None: s.value = v
    else: md[SID[name]] = v
def flow(key, pts, r=14, n=None, size=3.6, mp=M_WATER, mb=M_WBODY, sm=40):
    pts = smooth(pts, sm, 5) if sm else pts
    o = poly_curve('Поток ' + key, pts, C_WATER)
    L = sum((V(pts[i + 1]) - V(pts[i])).length for i in range(len(pts) - 1))
    md = o.modifiers.new('Поток', 'NODES'); md.node_group = FG
    mset(md, 'Количество', n or max(10, int(L / 6.5)))
    mset(md, 'Радиус', r * MM * 0.6); mset(md, 'Размер', size * MM)
    mset(md, 'Материал частиц', mp); mset(md, 'Материал жилы', mb)
    mset(md, 'Частицы', 0.0); mset(md, 'Жила', 0.0); mset(md, 'Заполнение', 1.0)
    FLOWS[key] = dict(obj=o, md=md, len=L)
    return o

YN = 95   # напорный патрубок улитки (касательный выход справа сверху)
def polar(x, r, a, cy=0.0, cz=0.0): return (x, cy + r * math.sin(a), cz + r * math.cos(a))
# ступень НД: 6 линий — вход по оси, колесо, улитка к верху, патрубок вверх в коллектор
for i in range(6):
    a = i * math.pi / 3 + 0.3
    pts = [polar(x, 30, a) for x in (730, 660, 600, 520)]
    a1 = a - 1.6
    pts += [polar(452, 52 + 88 * t / 6, a - 1.6 * t / 6) for t in range(7)]
    dl = (a1 - math.radians(60)) % (2 * math.pi)   # по спирали против часовой (вид со входа) до горловины справа сверху
    for k in range(1, 17): pts.append(polar(447, 150 + 30 * k / 16, a1 - dl * k / 16))
    pts += [(447, YN, 110), (447, YN, 170), (447, YN, 210), (447, YN, 248)]
    flow('nd%d' % i, pts, r=10, sm=0)
# всасывающий патрубок и рукава (направление — к насосу)
flow('suct', [(730, 0, 0), (700, 0, 0)], r=55, sm=0)
flow('res', smooth(RES_PATH, 160, 8), r=50, sm=0)
flow('hyd', smooth(HYD_PATH, 150, 8), r=32, sm=0)
flow('tankdn', smooth(TANKL, 120, 6) + [(700, 0, 0)], r=40, sm=0)
# коллектор и выходы
flow('v1l', [(447, YN, 250), (447, -60, 290), (447, -150, 300), (447, yL, zL), (447, yL - 70, zL - 70), (447, yL - 230, zL - 180), (447, yL - 230, -330)] + smooth(OUT_L, 140, 8)[1:], r=26)
flow('v1r', [(447, YN, 250), (447, 120, 292), (447, 300, 302), (447, yR, zR), (447, yR + 70, zR - 70), (447, yR + 230, zR - 180), (447, yR + 230, -330)] + smooth(OUT_R, 140, 8)[1:], r=26)
flow('vt', [(447, YN, 250), (447, 100, 288), (447, yT, zT), (400, yT, zT), (352, yT, zT), (250, yT, zT), (250, yT, 900), (720, yT, 900)], r=30)
# вакуумирование: воздух из коллектора через затвор в агрегат и выхлоп
flow('vac', [(447, YN, 250), (447, -150, 300)] + VAC1 + VAC2 + EXH, r=10, mp=M_AIR)
flow('vacw', [(447, YN, 250), (447, -150, 300)] + VAC1 + [(470, -262, zv), (470, -295, zv)], r=10)   # вода доходит до датчика 8
# ступень ВД
xin, xout = 69.5 + (1795 - 1005) / 2.61, 69.5 + (1795 - 1255) / 2.61
for i in range(4):
    a = i * math.pi / 2 + 0.4
    pts = [(447, -60, 290), (420, -150, 300), (xin, -150, 300), (xin, -201, 300), (xin, -201, 222), (xin, -201, 170)]
    pts += [polar(352, 40, a, -201, 72), polar(341, 30, a, -201, 72), polar(341, 84, a - 0.8, -201, 72), polar(325, 92, a - 1.0, -201, 72),
            polar(325, 34, a - 1.4, -201, 72), polar(305, 30, a - 1.5, -201, 72), polar(305, 84, a - 2.3, -201, 72)]
    a2 = a - 2.3; dl = a2 % (2 * math.pi)
    for k in range(1, 9): pts.append(polar(286, 100, a2 - dl * k / 8, -201, 72))
    pts += [(xout, -201, 175), (xout, -201, 230), (xout, -201, 282), (XH, YH, 282)]
    flow('hp%d' % i, pts, r=7, sm=25)
flow('hpout', [(xout, -201, 282), (XH, YH, 282), (XH, YH, 680)] + smooth(HPOUT, 120, 8)[1:], r=8)
flow('byp', [(xout, -201, 282)] + BYP, r=7)
# пена: эжектор (вода из коллектора) и пенообразователь от дозатора в пеносмеситель и на вход
yp, zp = -30, 176
flow('ej', [(447, 0, 300), (527, ye, 330), (560, ye, 330), (560, ye, ze), (560, ye, zp), (560, ye, 75), (600, 0, 40), (660, 0, 10)], r=10)
flow('foam', FOAM_L + [(606, yd, zd), (560, yd, zd), (560, -140, zp), (560, ye, zp), (560, ye, 75), (600, 0, 40), (660, 0, 10)], r=9, mp=M_FOAM, mb=M_FBODY)
flow('foamnd', [(660, 0, 10), (560, 0, 0), (500, 0, 0)], r=20, mp=M_FOAM, mb=M_FBODY)
# слив: вода из корпуса НД через штуцер 19 и кран 19, из ступени ВД через краны 18/19
flow('drnd', [(447, 0, -140), (447, 0, -200), (440, -62, -240), (440, -62, -330), (440, -62, -745)], r=8)
flow('drhp1', [(263, -201, -40), (263, -201, -123), (263, -201, -745)], r=6)
flow('drhp2', [(370, -201, -40), (370, -201, -123), (370, -201, -745)], r=6)
# утечки через сальники — смазка и охлаждение набивки (≥ 20 капель/мин) — в дренажный канал и штуцер 19
flow('gland', [(432, 0, -38), (412, 0, -31), (392, 0, -31), (382, 0, -48), (374, 0, -82), (374, 0, -122), (374, 0, -745)], r=2, n=7, size=3.2, sm=8)
flow('glandhp', [(250, -201, 72 - 26), (262, -201, 72 - 30), (262, -201, 72 - 60), (262, -201, -745)], r=2, n=5, size=3.0, sm=8)
# щелевое уплотнение колеса: часть воды из улитки возвращается к входу колеса
for i in range(3):
    a_ = 0.6 + i * 2.1
    flow('ring%d' % i, [polar(500, 150, a_), polar(514, 142, a_), polar(519, 100, a_), polar(517, 64, a_), polar(506, 52, a_)], r=2, n=8, size=3.0, sm=10)
LEAKS = ['gland', 'ring0', 'ring1', 'ring2']
for i in range(6):   # вода стекает вниз из коллектора и улитки к сливному штуцеру
    a = i * math.pi / 3 + 0.3
    pts = [(447, YN, 300), (447, YN, 200), (447, YN, 110)] + [polar(447, 150, math.pi * (0.0 + (1 if i % 2 else -1) * k / 10)) for k in range(11)] + [(447, 0, -140)]
    flow('ndown%d' % i, pts, r=12, sm=20)
flow('purge', PURGE + [(447, 100, 290), (447, YN, 250), (447, YN, 110)] + [polar(447, 150, -math.pi * k / 10) for k in range(11)] + [(447, 0, -140), (447, 0, -200), (440, -62, -240), (440, -62, -400)], r=10, mp=M_AIR)
flow('purgehp', [(447, -60, 290), (420, -150, 300), (xin, -150, 300), (xin, -201, 300), (xin, -201, 170), (300, -201, 0), (263, -201, -123), (263, -201, -400)], r=8, mp=M_AIR)
flow('blow', [(440, -62, -400), (440, -62, -240), (447, 0, -200), (447, 0, -140)] + [polar(447, 150, math.pi * k / 10) for k in range(11)] + [(447, YN, 110), (447, YN, 250), (447, -150, 300)] + VAC1 + VAC2 + EXH, r=10, mp=M_AIR)

# ------------------------------------------------------------------ камера, свет, подписи
cam = bpy.data.objects.new('Камера', bpy.data.cameras.new('Камера')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35; cam.data.clip_start = 0.01
tgt = bpy.data.objects.new('Цель камеры', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
for nm, loc, en, rot in (('Ключевой', (2, 2.5, 3), 4.0, None), ('Заполняющий', (-2, -2, 2), 1.5, None)):
    L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN')); L.data.energy = en * 0.65; sc.collection.objects.link(L)
    L.rotation_euler = (V(loc).to_track_quat('Z', 'Y')).to_euler()
AL = bpy.data.objects.new('Мягкий сверху', bpy.data.lights.new('Мягкий сверху', 'AREA')); AL.data.energy = 300; AL.data.size = 2.5
AL.location = (0.6, 0.6, 2.2); sc.collection.objects.link(AL)
w = bpy.data.worlds.new('Мир'); sc.world = w; w.use_nodes = True
# фон кадра белый, а освещение от окружения прежнее (тёмное): камера видит белый, свет от мира — приглушённый
wn = w.node_tree.nodes; wl = w.node_tree.links
bg = wn['Background']; bg.inputs['Color'].default_value = (0.09, 0.10, 0.12, 1); bg.inputs['Strength'].default_value = 1.0
# яркость с запасом: после экспозиции и тонового отображения (Standard/AgX) фон остаётся чисто белым
bgw = wn.new('ShaderNodeBackground'); bgw.inputs['Color'].default_value = (1, 1, 1, 1); bgw.inputs['Strength'].default_value = 30.0
lp = wn.new('ShaderNodeLightPath'); mx = wn.new('ShaderNodeMixShader'); mxf = wn.new('ShaderNodeMath'); mxf.operation = 'MAXIMUM'
wl.new(lp.outputs['Is Camera Ray'], mxf.inputs[0]); wl.new(lp.outputs['Is Transmission Ray'], mxf.inputs[1])   # и сквозь стекло — тоже белый
wl.new(mxf.outputs[0], mx.inputs[0]); wl.new(bg.outputs[0], mx.inputs[1]); wl.new(bgw.outputs[0], mx.inputs[2])
wl.new(mx.outputs[0], wn['World Output'].inputs['Surface'])

FONT = None
for f in ('C:/Windows/Fonts/arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', '/Library/Fonts/Arial Unicode.ttf', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'):
    if os.path.exists(f): FONT = bpy.data.fonts.load(f); break
HALF_W = 18 / 35   # полуширина кадра на расстоянии 1 м при объективе 35 мм
HALF_H = HALF_W * 9 / 16
def hud_text(name, body, x, y, size, align='LEFT'):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = 'TOP'
    if FONT: cu.font = FONT
    o = bpy.data.objects.new(name, cu); C_HUD.objects.link(o); o.parent = cam; o.location = (x, y, -1.0)
    cu.materials.append(M_TXT); return o
def hud_bar(name, x0, y0, x1, y1):
    o = box_obj(name, (0, 0, 0), (1, 1, 1), M_BAR, C_HUD)
    o.parent = cam; o.location = (x0, y0, -1.002); o.scale = ((x1 - x0) / MM, (y1 - y0) / MM, 0.001 / MM)
    return o

# ------------------------------------------------------------------ анимация: дорожки значений
TR = {}   # ключ -> список (кадр, значение)
def setv(key, f, v): TR.setdefault(key, []).append((f, v))
def val_at(key, f, default=0.0):
    ks = sorted(TR.get(key, []))
    if not ks: return default
    if f <= ks[0][0]: return ks[0][1]
    for (f0, v0), (f1_, v1) in zip(ks, ks[1:]):
        if f0 <= f <= f1_: return v0 + (v1 - v0) * ((f - f0) / (f1_ - f0) if f1_ > f0 else 1)
    return ks[-1][1]
def ramp(key, f0, f1_, v1):
    """Плавно изменить значение key от текущего к v1 на кадрах f0..f1."""
    setv(key, f0, val_at(key, f0)); setv(key, f1_, v1)
def hold(key, f, v): setv(key, f - 0.01, val_at(key, f - 0.01)); setv(key, f, v)

STEPS = []   # (кадр начала, кадр конца, сценарий, заголовок, текст, табло)
SCN = []     # (имя, кадр начала, кадр конца, файл)
CAMK = []    # (кадр, положение, цель)
VIS = {}     # ключ группы -> [(кадр, видимость)]
def vis(key, f, on): VIS.setdefault(key, []).append((f, on))
def shot(f, loc, target, cut=False): CAMK.append((f, loc, target, cut))

cur = [1]
def scenario(name, fname):
    SCN.append([name, cur[0], None, fname])
def step(sec, title, text, board, fn=None):
    f0 = cur[0]; f1_ = f0 + int(sec * FPS)
    STEPS.append((f0, f1_, SCN[-1][0], title, text, board))
    if fn: fn(f0, f1_)
    cur[0] = f1_
def end_scenario():
    SCN[-1][2] = cur[0] - 1; cur[0] += 1

def flows_off(f, keys=None):
    for k in (keys or FLOWS):
        hold('P.' + k, f, 0); hold('B.' + k, f, 0)
def fl(k, f0, f1_, parts=None, body=None, fill=None, speed=None):
    if parts is not None: ramp('P.' + k, f0, f0 + 8, parts)
    if body is not None: hold('B.' + k, f0, body)
    if fill is not None: ramp('F.' + k, f0, f1_, fill)
    if speed is not None: ramp('S.' + k, f0, f0 + 15, speed)
def ND_ALL(): return ['nd%d' % i for i in range(6)]
def HP_ALL(): return ['hp%d' % i for i in range(4)]
def leaks(f0, f1_, on=1, hp=0):
    """Утечки через сальник и щелевое уплотнение — пока насос работает с водой."""
    for k in LEAKS: fl(k, f0, f1_, parts=on, speed=0.05 if k == 'gland' else 0.12)
    fl('glandhp', f0, f1_, parts=hp, speed=0.05)
def setall(keys, f0, f1_, **kw):
    for k in keys: fl(k, f0, f1_, **kw)

# --- исходное состояние каждого сценария
def reset(f):
    for k in FLOWS:
        hold('P.' + k, f, 0); hold('B.' + k, f, 0); hold('F.' + k, f, 1); hold('S.' + k, f, 0)
    for k in CTRL: hold('C.' + k, f, 0)
    hold('rpm', f, 0); hold('clutch', f, 0); hold('hp', f, 0)
    for g in list(EXT): vis(g, f, False)
    vis('front', f, True)
    for k in ('cutnd', 'cuthp'): hold(k, f, 0)
    for k in ('lamp.vac', 'lamp.full', 'lamp.drain', 'lamp.purge'): hold(k, f, 0)

ND_SHOT = ((0.88, 1.4, 0.22), (0.45, 0.0, 0.08))
WIDE_RES = ((1.0, 3.2, 0.1), (0.95, 0.0, -0.32))
VAC_SHOT = ((0.95, 1.05, 1.0), (0.38, -0.1, 0.4))
TOP_SHOT = ((1.25, 1.2, 1.25), (0.44, 0.05, 0.22))
WIDE_TANK = ((0.9, 3.0, 0.6), (0.75, 0.0, 0.15))
HP_SHOT = ((0.35, -1.35, 0.35), (0.28, -0.2, 0.08))
HP_WIDE = ((1.0, -2.0, 0.45), (0.5, -0.55, 0.0))
DRAIN_SHOT = ((1.05, 1.6, 0.05), (0.38, -0.1, -0.2))
FOAM_SHOT = ((1.7, 1.1, 0.8), (0.6, -0.1, 0.15))
WIDE_HYD = ((1.05, 3.9, 0.15), (1.0, 0.0, -0.25))

def ND_FILLED(f0, f1_, keys=None, speed=0.0):
    for k in (keys or ND_ALL()):
        fl(k, f0, f1_, body=1, parts=1, fill=1, speed=speed)

# ======================= S1. Забор из открытого водоёма =======================
scenario('Забор воды из открытого водоёма', 'NCPK_vodoyom')
def s(f0, f1_):
    reset(f0); vis('suct', f0, True); vis('res', f0, True); vis('vac', f0, True); vis('hoseL', f0, True); vis('front', f0, False)
    hold('cutnd', f0, 1)
    for k in ND_ALL() + ['suct', 'res', 'v1l', 'vacw']: hold('F.' + k, f0, 0)
    shot(f0, *WIDE_RES, cut=True)
step(4, 'Забор воды из открытого водоёма', 'Всасывающий рукав опущен в водоём, насос и рукав заполнены воздухом.\nНапорные вентили, затвор «Вода из цистерны», кран ВД и сливы закрыты.', 'Двигатель работает · БУК-02 включён', s)
def s(f0, f1_):
    ramp('rpm', f0, f0 + 30, 800); shot(f0 + 20, *ND_SHOT)
step(4, 'Включить привод насоса', '«Сцепление» на пульте АЦ — включён привод (КОМ).\nНасос без воды: дальше действуют без пауз.', 'Обороты ≈ 800 об/мин · Вход 0 · Выход 0', s)
def s(f0, f1_):
    hold('C.vac', f0, 0); ramp('C.vac', f0, f0 + 20, 1); hold('lamp.vac', f0 + 20, 1)
    fl('vac', f0 + 20, f1_, parts=1, speed=0.35); shot(f0, *VAC_SHOT)
    setall(ND_ALL(), f0 + 20, f1_, parts=0)
step(5, 'Открыть вакуумный затвор', 'Рукоятку затвора — вертикально, до упора. Датчик положения сам\nзапускает вакуумный агрегат: воздух уходит из насоса через выхлоп.', 'Агрегат работает · Вход −0,02 МПа', s)
def s(f0, f1_):
    ramp('rpm', f0, f0 + 45, 1500); shot(f0 + 10, *WIDE_RES)
    fl('res', f0, f1_, body=1, parts=1, fill=0.8, speed=0.25)
step(7, 'Поднять обороты до 1200–1800 об/мин', 'Не дожидаясь воды, плавно — до «среднего» уровня. Вода поднимается\nпо всасывающему рукаву: агрегат откачивает воздух.', 'Обороты 1500 · Вход −0,05 МПа · Агрегат работает', s)
def s(f0, f1_):
    fl('res', f0, f0 + 45, fill=1); fl('suct', f0 + 30, f0 + 75, body=1, parts=1, fill=1, speed=0.5)
    for i, k in enumerate(ND_ALL()): fl(k, f0 + 60, f1_ - 30, body=1, parts=1, fill=1, speed=0.45)
    leaks(f1_ - 60, f1_)
    fl('vacw', f1_ - 45, f1_, body=1, parts=1, fill=1, speed=0.3)
    shot(f0 + 20, *ND_SHOT)
step(7, 'Насос заполняется', 'Вода входит через сетку в колесо и улитку, поднимается в коллектор\nи в линию вакуумирования до датчика заполнения.', 'Обороты 1500 · Вход −0,06 МПа · Выход растёт', s)
def s(f0, f1_):
    hold('lamp.vac', f0, 0); hold('lamp.full', f0, 1); fl('vac', f0, f1_, parts=0); fl('vacw', f0, f1_, parts=0, speed=0)
    for k in ND_ALL() + ['suct', 'res']: fl(k, f0, f1_, speed=0.15)
    shot(f0, *VAC_SHOT)
step(5, 'Насос заполнен — агрегат остановился сам', 'Датчик заполнения дал сигнал, БУК-02 выключил агрегат.\nОбратный клапан в затворе держит воду — рукоятку можно не закрывать.', '«Насос заполнен» · Выход 0,25 МПа', s)
def s(f0, f1_):
    ramp('C.v1l', f0, f0 + 40, 1); shot(f0, *TOP_SHOT)
    fl('v1l', f0 + 20, f1_, body=1, parts=1, fill=1, speed=0.7)
    for k in ND_ALL() + ['suct', 'res']: fl(k, f0 + 20, f1_, speed=0.6)
step(6, 'Плавно открыть напорный вентиль', 'Левый напорный вентиль DN70: вода из коллектора уходит в рукав.', 'Обороты 1500 · Вход −0,05 МПа · Выход 0,4 МПа', s)
def s(f0, f1_):
    ramp('rpm', f0, f0 + 45, 2200); shot(f0, *WIDE_RES)
    for k in ND_ALL() + ['suct', 'res', 'v1l']: fl(k, f0, f1_, speed=1.0)
step(6, 'Подобрать обороты', '0,35–0,45 МПа у ствола. Следить за мановакуумметром на входе:\nразрежение глубже −0,07 МПа — признак кавитации.', 'Обороты 2200 · Вход −0,06 МПа · Выход 0,8 МПа', s)
end_scenario()

# ======================= S2. Цистерна и гидрант =======================
scenario('Работа от цистерны и от гидранта', 'NCPK_cisterna_gidrant')
def s(f0, f1_):
    reset(f0); vis('suct', f0, True); vis('tankline', f0, True); vis('tank', f0, True); vis('hoseL', f0, True); vis('hoseR', f0, True)
    vis('front', f0, False); hold('cutnd', f0, 1)
    for k in ND_ALL() + ['suct', 'tankdn', 'v1l', 'v1r']: hold('F.' + k, f0, 0)
    shot(f0, *WIDE_TANK, cut=True)
step(4, 'Подача воды из цистерны', 'Цистерна выше насоса: вода приходит в насос самотёком,\nвакуумная система не нужна.', 'Двигатель работает · БУК-02 включён', s)
def s(f0, f1_):
    fl('tankdn', f0, f0 + 45, body=1, parts=1, fill=1, speed=0.4)
    fl('suct', f0 + 35, f0 + 60, body=1, parts=1, fill=1, speed=0.4)
    for k in ND_ALL(): fl(k, f0 + 50, f1_, body=1, parts=1, fill=1, speed=0.3)
    leaks(f0 + 90, f1_)
    shot(f0 + 30, *ND_SHOT)
step(6, 'Открыть затвор «Вода из цистерны»', 'Вода из цистерны заполняет всасывающий патрубок и насос.', 'Вход +0,01 МПа · Выход +0,01 МПа', s)
def s(f0, f1_):
    ramp('rpm', f0, f0 + 30, 900); ramp('C.v1l', f0 + 30, f0 + 70, 1); ramp('C.v1r', f0 + 50, f0 + 90, 1); shot(f0 + 20, *TOP_SHOT)
    fl('v1l', f0 + 50, f1_, body=1, parts=1, fill=1, speed=0.7); fl('v1r', f0 + 70, f1_, body=1, parts=1, fill=1, speed=0.7)
    for k in ND_ALL() + ['suct', 'tankdn']: fl(k, f0 + 40, f1_, speed=0.8)
step(7, 'Сцепление, открыть напорные вентили', 'Привод включён на малых оборотах, вентили DN70 открыты:\nвода идёт в рукавные линии.', 'Обороты 900 · Выход 0,2 МПа', s)
def s(f0, f1_):
    ramp('rpm', f0, f0 + 40, 2000); shot(f0, *WIDE_TANK)
    for k in ND_ALL() + ['suct', 'tankdn', 'v1l', 'v1r']: fl(k, f0, f1_, speed=1.0)
step(5, 'Набрать рабочее давление', 'Обороты поднимают плавно, по манометру на выходе. Через сальник в дренаж\nидут капли — вода смазывает и охлаждает набивку (не менее 20 капель/мин).', 'Обороты 2000 · Выход 0,6 МПа', s)
def s(f0, f1_):
    vis('hyd', f0, True); vis('tankline', f0, False); vis('tank', f0, False); shot(f0, *WIDE_HYD)
    fl('tankdn', f0, f0 + 10, parts=0, body=0)
    fl('hyd', f0, f1_, body=1, parts=1, fill=1, speed=1.0)
    ramp('C.vt', f0 + 60, f0 + 100, 1); fl('vt', f0 + 80, f1_, body=1, parts=1, fill=1, speed=0.8)
    hold('F.vt', f0, 0)
step(8, 'От гидранта, заполнение цистерны', 'Колонка соединена с насосом рукавом — вода под давлением сети.\nВентиль DN80 подаёт воду из насоса в цистерну.', 'Вход +0,25 МПа · Выход 0,6 МПа', s)
def s(f0, f1_):
    vis('tank', f0, True); shot(f0, *WIDE_TANK)
step(4, 'Заполнение цистерны', 'Вода из коллектора через вентиль DN80 и трубопровод заполнения\nидёт в цистерну. Мановакуумметр на входе не должен уходить ниже нуля.', 'Вход +0,2 МПа · Выход 0,6 МПа', s)
end_scenario()

# ======================= S3. Слив и продувка =======================
scenario('Слив воды и продувка насоса', 'NCPK_sliv_produvka')
def s(f0, f1_):
    reset(f0); vis('purge', f0, True); vis('vac', f0, True); vis('front', f0, False); hold('cutnd', f0, 1)
    ND_FILLED(f0, f0 + 1)
    for k in ND_ALL(): hold('S.' + k, f0, 0.0)
    shot(f0, *DRAIN_SHOT, cut=True)
step(4, 'Слив воды и продувка насоса', 'Насос остановлен, напорные вентили открыты, привод выключен.\nВ насосе осталась вода — её нужно слить, особенно зимой.', 'Обороты 0 · Привод выключен', s)
def s(f0, f1_):
    hold('lamp.drain', f0, 1)
    for k in ND_ALL(): fl(k, f0, f1_, fill=0, speed=-0.25)
    for i in range(6): hold('F.ndown%d' % i, f0, 1); fl('ndown%d' % i, f0, f1_ - 30, parts=1, speed=0.35); fl('ndown%d' % i, f1_ - 30, f1_, parts=0)
    fl('drnd', f0, f1_, parts=1, body=1, speed=0.45)
    fl('drhp1', f0, f1_, parts=1, body=1, speed=0.45); fl('drhp2', f0, f1_, parts=1, body=1, speed=0.45)
step(9, 'Кнопка «СЛИВ» на БУК-02', 'Пневмоостров открывает сливной кран СНД и сливные краны СВД.\nВода стекает из улитки, коллектора и ступени ВД под машину.', 'Подсветка «СЛИВ» горит', s)
def s(f0, f1_):
    hold('lamp.purge', f0, 1); shot(f0, *DRAIN_SHOT)
    fl('purge', f0, f1_, parts=1, speed=0.9); fl('purgehp', f0, f1_, parts=1, speed=0.9)
    for k in ('drnd', 'drhp1', 'drhp2'): fl(k, f0, f1_, body=0, speed=0.6)
    hold('lamp.purge', f1_, 0)
step(7, 'Кнопка «ПРОДУВКА» — удерживать 5–10 с', 'Сжатый воздух через обратный клапан продувки входит в коллектор\nи выдувает остатки воды через открытые сливные краны.', 'Воздух подаётся, пока кнопка нажата', s)
def s(f0, f1_):
    for k in ('purge', 'purgehp', 'drnd', 'drhp1', 'drhp2'): fl(k, f0, f0 + 10, parts=0)
    shot(f0, *VAC_SHOT); ramp('C.vac', f0, f0 + 20, 1)
    for j in range(3):
        a = f0 + 25 + j * 55; hold('lamp.vac', a, 1); fl('blow', a, a + 30, parts=1, speed=1.0); hold('lamp.vac', a + 30, 0); fl('blow', a + 30, a + 40, parts=0)
step(7, '2–3 коротких включения вакуумной системы', 'Несколько секунд каждое — продуть вакуумный затвор и агрегат\nот остатков воды.', 'Агрегат: короткие включения', s)
def s(f0, f1_):
    ramp('C.vac', f0, f0 + 20, 0.5); shot(f0, *ND_SHOT)
step(4, 'Оставить краны полуоткрытыми', 'Ручные краны — в полуоткрытое положение, сливные краны СВД и СНД\nоткрыть-закрыть 2–3 раза и оставить открытыми.', 'Насос осушен', s)
end_scenario()

# ======================= S4. Ступень ВД и пена =======================
scenario('Ступень высокого давления и пена', 'NCPK_VD_pena')
def s(f0, f1_):
    reset(f0); vis('suct', f0, True); vis('tankline', f0, True); vis('hpout', f0, True); vis('byp', f0, True); vis('front', f0, True)
    hold('cuthp', f0, 1); hold('rpm', f0, 1000)
    for k in ND_ALL() + ['suct', 'tankdn']: fl(k, f0, f0 + 1, body=1, parts=1, fill=1, speed=0.5)
    leaks(f0, f0 + 1)
    for k in HP_ALL() + ['hpout', 'byp']: hold('F.' + k, f0, 0)
    shot(f0, *HP_SHOT, cut=True)
step(4, 'Ступень высокого давления', 'Насос заполнен и работает от цистерны на малых оборотах.\nСтупень ВД пока стоит: муфта выключена.', 'Обороты 1000 · Выход НД 0,3 МПа', s)
def s(f0, f1_):
    hold('clutch', f0, 1); hold('hp', f0 + 10, 1); leaks(f0 + 30, f1_, hp=1)
    for k in HP_ALL(): fl(k, f0 + 10, f1_, body=1, parts=1, fill=1, speed=0.8)
    fl('byp', f0 + 40, f1_, body=1, parts=1, fill=1, speed=0.5)
step(7, 'Кнопка «Ступень высокого давления»', 'Электромагнитная муфта притягивает диск — ведущий шкив вращается\nс валом, ремень крутит ступень ВД. Кран ВД закрыт: вода идёт через перепуск.', 'Муфта включена · Выход ВД 1,5 МПа', s)
def s(f0, f1_):
    ramp('C.kvd', f0, f0 + 20, 1); fl('hpout', f0 + 15, f1_, body=1, parts=1, fill=1, speed=1.2); shot(f0 + 10, *HP_WIDE)
    ramp('rpm', f0 + 20, f0 + 60, 1600)
    for k in HP_ALL(): fl(k, f0 + 20, f1_, speed=1.3)
step(7, 'Открыть кран высокого давления', 'Вода из ступени ВД идёт в рукав катушки высокого давления.\nОбороты выше 1800 с включённой ступенью ВД не поднимать.', 'Обороты 1600 · Выход ВД 3,5 МПа', s)
def s(f0, f1_):
    ramp('C.kvd', f0, f0 + 20, 0); fl('hpout', f0 + 10, f0 + 30, parts=0)
    hold('clutch', f0 + 30, 0); hold('hp', f0 + 30, 0); leaks(f0 + 30, f1_, hp=0)
    for k in HP_ALL() + ['byp']: fl(k, f0 + 30, f1_, speed=0, parts=0)
    vis('cuthp', f0, False); hold('cuthp', f0 + 30, 0); hold('cutnd', f0 + 30, 1); vis('front', f0 + 30, False)
    vis('foam', f0 + 30, True); vis('hoseL', f0 + 30, True); vis('hoseR', f0 + 30, True)
    ramp('C.v1l', f0 + 30, f0 + 70, 1); ramp('C.v1r', f0 + 30, f0 + 70, 1)
    for k in ('v1l', 'v1r'): hold('F.' + k, f0, 0); fl(k, f0 + 40, f1_, body=1, parts=1, fill=1, speed=0.9)
    ramp('rpm', f0 + 40, f1_, 2300); shot(f0 + 30, *FOAM_SHOT)
step(6, 'Пена: ступень ВД выключить, вентили открыть', 'Муфта выключена. Напорные вентили DN70 открыты, давление на выходе\nнасоса поднимают до 0,7–0,8 МПа.', 'Обороты 2300 · Выход 0,75 МПа', s)
def s(f0, f1_):
    ramp('C.ej', f0, f0 + 20, 1); hold('F.ej', f0, 0); fl('ej', f0 + 15, f1_, body=1, parts=1, fill=1, speed=0.8)
step(5, 'Открыть кран эжектора', 'Вода с выхода насоса проходит через пеносмеситель на вход:\nв камере эжектора возникает разрежение.', 'Разница давлений выход–вход ≥ 0,5 МПа', s)
def s(f0, f1_):
    ramp('C.fv', f0, f0 + 20, 1)
    hold('F.foam', f0, 0); fl('foam', f0, f1_ - 30, body=1, parts=1, fill=1, speed=0.5)
    hold('F.foamnd', f0, 0); fl('foamnd', f0 + 80, f1_, body=1, parts=1, fill=1, speed=0.8)
step(8, 'Кран магистрали пенобака, дозатор на подачу', 'Пенообразователь из бака через кран магистрали и дозатор подсасывается в пеносмеситель\nи вместе с водой поступает в насос — на выходе раствор.', 'Дозатор 12 л/с, 6 % · Выход 0,75 МПа', s)
end_scenario()

# ------------------------------------------------------------------ запись ключей
def kf(owner, path, f, v, idx=-1, interp='LINEAR'):
    if idx >= 0: getattr(owner, path)[idx] = v
    else: setattr(owner, path, v)
    owner.keyframe_insert(path, index=idx, frame=f)
def idkf(md, name, f, v):
    s = msock(md, name)
    if s is not None: s.value = v; s.keyframe_insert('value', frame=f)
    else: md[SID[name]] = v; md.keyframe_insert('["%s"]' % SID[name], frame=f)

FEND = SCN[-1][2]
sc.frame_start, sc.frame_end = 1, FEND
for name, a, b, fn in SCN:
    m = sc.timeline_markers.new(name, frame=a)

def integ(key, f0, f1_, scale=1.0):
    """Интеграл скорости (оборотов/с) → фаза на каждом кадре."""
    out = {}; ph = 0.0
    for f in range(f0, f1_ + 1):
        out[f] = ph; ph += val_at(key, f) * scale / FPS
    return out

# потоки
for k, d in FLOWS.items():
    md = d['md']
    for key, sid in (('P.' + k, 'Частицы'), ('B.' + k, 'Жила'), ('F.' + k, 'Заполнение')):
        for f, v in sorted(set(TR.get(key, []))): idkf(md, sid, int(f), v)
    # фаза: скорость задана в м/с «видимых», переводим в доли длины
    ph = 0.0
    for f in range(1, FEND + 1):
        if f % 2 == 1 or f == FEND: idkf(md, 'Фаза', f, ph)
        ph += val_at('S.' + k, f) / max(0.05, d['len'] * MM) / FPS
# вращение валов
VIS_RPS = 1.1 / 2700   # видимая скорость: ≈1 об/с на 2700 об/мин (реально в 45 раз быстрее — на видео не разглядеть)
ph_nd = integ('rpm', 1, FEND, VIS_RPS)
for o in ROT_ND + ROT_CL + ROT_HP: o.rotation_mode = 'XYZ'
clp = 0.0; hpp = 0.0
for f in range(1, FEND + 1):
    a = ph_nd[f] * 2 * math.pi
    on = val_at('clutch', f) > 0.5
    if on: clp += val_at('rpm', f) * VIS_RPS / FPS * 2 * math.pi; hpp += val_at('rpm', f) * VIS_RPS * 2.4 / FPS * 2 * math.pi
    if f % 2 == 1 or f == FEND:
        for o in ROT_ND: kf(o, 'rotation_euler', f, a, 0)
        for o in ROT_CL: kf(o, 'rotation_euler', f, clp, 0)
        for o in ROT_HP: kf(o, 'rotation_euler', f, hpp, 0)
# органы управления
for k, n, piv, ax, ang, lift in CTRLS:
    o = OB[n]; o.rotation_mode = 'XYZ'
    keys = sorted(set(TR.get('C.' + k, [])))
    for f, v in keys:
        f = int(f)
        e = v * v * (3 - 2 * v)
        if isinstance(ax, tuple):   # наклонная ось (вентили DN70)
            o.rotation_mode = 'AXIS_ANGLE'; o.rotation_axis_angle = (ang * e, *ax); o.keyframe_insert('rotation_axis_angle', frame=f)
            o.location = CTRL_BASE[n] + V(ax) * (lift * MM * e); o.keyframe_insert('location', frame=f)
            continue
        r = [0.0, 0.0, 0.0]
        if k in ('vac', 'ej', 'kvd'): r[ax] = -ang * (1 - e)    # модель — открытое положение
        else: r[ax] = ang * e
        o.rotation_euler = r; o.keyframe_insert('rotation_euler', frame=f)
        o.location = CTRL_BASE[n] + V((lift * MM * e, 0, 0)); o.keyframe_insert('location', frame=f)
# муфта: диск 4 притягивается, муфта 5 светится
disk = OB['НД 4 Диск прижимной']; clm = OB['НД 5 Муфта электромагнитная Э1ТМ']
for f, v in sorted(set(TR.get('clutch', []))):
    disk.location = (0.003 * v, 0, 0); disk.keyframe_insert('location', frame=int(f))
# разрезы
for f, v in sorted(set(TR.get('cutnd', []))):
    CUT_ND.location = (0, 0, 0) if v > 0.5 else (0, 2.0, 0); CUT_ND.keyframe_insert('location', frame=int(f))
for f, v in sorted(set(TR.get('cuthp', []))):
    CUT_HP.location = (0, 0, 0) if v > 0.5 else (0, -2.0, 0); CUT_HP.keyframe_insert('location', frame=int(f))
# видимость внешних групп
GROUPS = dict(EXT); GROUPS['front'] = FRONT
for g, lst in VIS.items():
    for f, on in lst:
        for o in GROUPS.get(g, []):
            o.hide_render = not on; o.hide_viewport = not on
            o.keyframe_insert('hide_render', frame=int(f)); o.keyframe_insert('hide_viewport', frame=int(f))
# камера
prev = None
for f, loc, target, cut in sorted(CAMK, key=lambda k: k[0]):
    f = int(f)
    if prev and not cut:   # плавный переезд за 1,5 с от прежнего положения
        for o, v in ((cam, prev[0]), (tgt, prev[1])): o.location = v; o.keyframe_insert('location', frame=f)
        f += int(1.5 * FPS)
    elif prev and cut:
        for o, v in ((cam, prev[0]), (tgt, prev[1])): o.location = v; o.keyframe_insert('location', frame=f - 1)
    cam.location = loc; cam.keyframe_insert('location', frame=f)
    tgt.location = target; tgt.keyframe_insert('location', frame=f)
    prev = (loc, target)

# подписи: заголовок сценария, шаг, табло; индикаторы БУК
hud_bar('Плашка сверху', -HALF_W, HALF_H - 0.095, HALF_W, HALF_H)
hud_bar('Плашка снизу', -HALF_W, -HALF_H, HALF_W, -HALF_H + 0.085)
LAMPS = {}
for i, (key, label, m) in enumerate((('lamp.vac', 'Агрегат работает', M_ON), ('lamp.full', 'Насос заполнен', M_ON),
                                    ('lamp.drain', 'СЛИВ', M_HOT), ('lamp.purge', 'ПРОДУВКА', M_HOT))):
    x = HALF_W - 0.31 + (i % 2) * 0.16; y = HALF_H - 0.028 - (i // 2) * 0.034
    lo = box_obj('Лампа ' + label, (0, 0, 0), (1, 1, 1), m, C_HUD); lo.parent = cam; lo.location = (x, y - 0.012, -0.9995); lo.scale = (12, 12, 1)
    lf = box_obj('Лампа выкл. ' + label, (0, 0, 0), (1, 1, 1), M_DARK, C_HUD); lf.parent = cam; lf.location = (x, y - 0.012, -1.0); lf.scale = (12, 12, 1)
    t = hud_text('Надпись ' + label, label, x + 0.017, y, 0.0155)
    LAMPS[key] = lo
for key, lo in LAMPS.items():
    for f, v in sorted(set(TR.get(key, []))):
        lo.hide_render = v < 0.5; lo.hide_viewport = v < 0.5
        lo.keyframe_insert('hide_render', frame=int(f)); lo.keyframe_insert('hide_viewport', frame=int(f))
def show_range(o, a, b):
    for f, h in ((1, True), (a, False), (b, True)):
        o.hide_render = h; o.hide_viewport = h
        o.keyframe_insert('hide_render', frame=f); o.keyframe_insert('hide_viewport', frame=f)
for name, a, b, fn in SCN:
    show_range(hud_text('Сценарий: ' + name, name, -HALF_W + 0.025, HALF_H - 0.018, 0.026), a, b + 1)
for i, (a, b, sname, title, text, board) in enumerate(STEPS):
    show_range(hud_text('Шаг %02d' % i, title, -HALF_W + 0.025, HALF_H - 0.055, 0.021), a, b)
    show_range(hud_text('Текст %02d' % i, text, -HALF_W + 0.025, -HALF_H + 0.074, 0.0175), a, b)
    show_range(hud_text('Табло %02d' % i, board, HALF_W - 0.025, -HALF_H + 0.074, 0.016, 'RIGHT'), a, b)
hud_text('Источник', 'По РЭ насоса НЦПК-40/100-4/400М-В1У (2025) · схематично, вращение замедлено', HALF_W - 0.025, -HALF_H + 0.024, 0.011, 'RIGHT')

# интерполяция: ключи видимости и разрезов — ступенчато
for o in bpy.data.objects:
    ad = o.animation_data
    if not ad or not ad.action: continue
    try: fcs = ad.action.fcurves
    except AttributeError:
        fcs = [fc for layer in ad.action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    for fc in fcs:
        const = fc.data_path.startswith('hide') or o in (CUT_ND, CUT_HP) or (o is disk)
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT' if const else ('BEZIER' if o in (cam, tgt) else 'LINEAR')

# рендер
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
try: sc.eevee.taa_render_samples = 16
except Exception: pass
try:
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = -0.7
    try: sc.view_settings.look = 'Medium High Contrast'
    except Exception: sc.view_settings.look = 'None'
except Exception: pass
for k, v in (('use_raytracing', True), ('use_shadows', True), ('use_gtao', True)):
    try: setattr(sc.eevee, k, v)
    except Exception: pass
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DIR, 'NCPK_potoki.blend'))
result = {'frames': FEND, 'scenarios': [(n, a, b) for n, a, b, _ in SCN], 'flows': len(FLOWS), 'steps': len(STEPS)}
