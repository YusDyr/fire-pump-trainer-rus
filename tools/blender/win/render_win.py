# Рендер роликов потоков воды на Windows с видеокартой NVIDIA.
# Запускается из render.bat:  blender.exe -b --python render_win.py -- <draft|final> [номера сценариев 1..4]
import bpy, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
mode = argv[0] if argv else 'draft'
only = [int(a) for a in argv[1:]]
OUT = os.path.join(HERE, 'video'); os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'render_%s.log' % mode), 'a', encoding='utf-8')
def say(*a):
    s = time.strftime('%H:%M:%S ') + ' '.join(str(x) for x in a); print(s, flush=True); log.write(s + '\n'); log.flush()

# 1. сцена из модели (скрипт тот же, что в репозитории: tools/blender/water_scene.py)
g = {'DIR': HERE, '__name__': '__main__'}
exec(open(os.path.join(HERE, 'water_scene.py'), encoding='utf-8').read(), g)
sc = bpy.context.scene; r = sc.render
say('сцена собрана:', g['result'])

# 2. режим
if mode == 'draft':
    # быстрый черновик: Workbench, 15 кадров/с, 960x540 — проверить, где и как идёт вода
    r.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_shadows = True; sh.shadow_intensity = 0.35
    sc.world.color = (1, 1, 1)   # белый фон
    for n, c in (('Вода: частицы', (0.35, 0.80, 1.0, 1)), ('Вода: заполнено', (0.25, 0.6, 1.0, 0.35)), ('Воздух', (1, 1, 1, 1)), ('Пенообразователь', (1, 0.85, 0.1, 1))):
        bpy.data.materials[n].diffuse_color = c
    for o in bpy.data.objects:
        if any(s.material and s.material.diffuse_color[3] < 1 for s in o.material_slots): o.show_transparent = True
    r.resolution_x, r.resolution_y = 960, 540; sc.frame_step = 2; r.fps = 30   # каждый второй кадр → 15 к/с при той же скорости
else:
    # финал: Cycles на видеокарте (OptiX, если нет — CUDA), стекло труб и вода с преломлением
    r.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    dev = None
    for t in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = t; prefs.get_devices()
            if any(d.type == t for d in prefs.devices): dev = t; break
        except Exception: pass
    for d in prefs.devices: d.use = (d.type == dev)
    sc.cycles.device = 'GPU' if dev else 'CPU'
    say('устройство:', dev or 'CPU', [d.name for d in prefs.devices if d.use])
    sc.cycles.samples = 64; sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPTIX' if dev == 'OPTIX' else 'OPENIMAGEDENOISE'
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 16
    def glassy(name, col, rough, ior, trans=1.0):
        m = bpy.data.materials.get(name)
        if not m: return
        b = m.node_tree.nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['IOR'].default_value = ior
        for k in ('Transmission Weight', 'Transmission'):
            if k in b.inputs: b.inputs[k].default_value = trans; break
        b.inputs['Alpha'].default_value = 1.0
    glassy('Трубы (прозрачные)', (0.92, 0.95, 0.97), 0.04, 1.45)
    glassy('Рукава', (0.55, 0.57, 0.6), 0.25, 1.4, 0.85)
    glassy('Вода: заполнено', (0.55, 0.8, 1.0), 0.02, 1.33)
    glassy('Ёмкости', (0.9, 0.94, 0.97), 0.05, 1.45)
    r.resolution_x, r.resolution_y = 1920, 1080; sc.frame_step = 1
    try: sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0
    except Exception: pass
r.resolution_percentage = 100

# 3. видео
try: r.image_settings.media_type = 'VIDEO'
except Exception: pass
r.image_settings.file_format = 'FFMPEG'; r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
try: r.ffmpeg.constant_rate_factor = 'HIGH'
except Exception: pass
r.ffmpeg.gopsize = 30; r.ffmpeg.audio_codec = 'NONE'
if mode == 'draft': r.fps = 15; sc.frame_step = 1   # см. ниже: рендерим каждый 2-й кадр вручную через frame_step

names = ['NCPK_vodoyom', 'NCPK_cisterna_gidrant', 'NCPK_sliv_produvka', 'NCPK_VD_pena']
ms = sorted(sc.timeline_markers, key=lambda m: m.frame); FEND = sc.frame_end
for i, m in enumerate(ms):
    if only and (i + 1) not in only: continue
    a = m.frame; b = (ms[i + 1].frame - 2) if i + 1 < len(ms) else FEND
    sc.frame_start, sc.frame_end = a, b
    if mode == 'draft': sc.frame_step = 2
    r.filepath = os.path.join(OUT, '%s_%s_' % (names[i], mode))
    t = time.time(); say(names[i], 'кадры', a, '-', b, 'старт')
    bpy.ops.render.render(animation=True)
    say(names[i], 'готово за %.0f с' % (time.time() - t))
say('ВСЁ ГОТОВО')
