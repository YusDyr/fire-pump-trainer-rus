# Фоновый рендер роликов: blender -b NCPK_potoki.blend --python render_bg.py -- [проценты] [номера сценариев]
import bpy, sys, os, time
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
pct = int(argv[0]) if argv else 100
only = [int(a) for a in argv[1:]]
sc = bpy.context.scene; r = sc.render
DIR = os.path.dirname(bpy.data.filepath); OUT = os.path.join(DIR, 'video'); os.makedirs(OUT, exist_ok=True)
try: r.image_settings.media_type = 'VIDEO'
except Exception: pass
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'
try: r.ffmpeg.constant_rate_factor = 'MEDIUM'
except Exception: pass
r.ffmpeg.gopsize = 30; r.ffmpeg.audio_codec = 'NONE'
r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, pct
r.use_file_extension = True
ms = sorted(sc.timeline_markers, key=lambda m: m.frame); FEND = sc.frame_end
log = open(os.path.join(OUT, 'render.log'), 'a', encoding='utf-8')
names = ['NCPK_vodoyom', 'NCPK_cisterna_gidrant', 'NCPK_sliv_produvka', 'NCPK_VD_pena']
for i, m in enumerate(ms):
    if only and (i + 1) not in only: continue
    a = m.frame; b = (ms[i + 1].frame - 2) if i + 1 < len(ms) else FEND
    sc.frame_start, sc.frame_end = a, b
    r.filepath = os.path.join(OUT, names[i] + '_')
    t = time.time(); log.write('%s %s %d-%d start\n' % (time.strftime('%H:%M:%S'), names[i], a, b)); log.flush()
    bpy.ops.render.render(animation=True)
    log.write('%s %s done %.0f s\n' % (time.strftime('%H:%M:%S'), names[i], time.time() - t)); log.flush()
log.write('ALL DONE\n'); log.close()
