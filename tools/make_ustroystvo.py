#!/usr/bin/env python3
"""Сборка страницы «Устройство насоса» (разрезы рис. 2 и 5 + 3D-модель) в один HTML-файл.

    python3 tools/make_ustroystvo.py [выходной.html]

Исходники лежат в src/ustroystvo/:
  template.html          — разметка и код страницы;
  nd_*.webp, hp_*.webp   — чертёж (ink: прозрачность линий), карта деталей (parts: R = номер позиции) и маска областей
                           (R — вода, G — масло, B: 255 — вал, 120 — охлаждающая вода) для рис. 2 и рис. 5;
  nd_data.json, hp_data.json — пути частиц воды, координаты деталей на чертеже;
  model.json + model.bin — 3D-модель (cad/model/NCPK_nasos.glb, сжата: координаты uint16, нормали int8);
  vendor/                — three.js r147 (MIT) и OrbitControls.
Страница работает без сети (кроме шрифтов Google, которые build.py заменяет на локальные).
"""
import base64, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
U = lambda *a: os.path.join(ROOT, 'src', 'ustroystvo', *a)


def b64(name):
    return base64.b64encode(open(U(name), 'rb').read()).decode()


def assemble():
    t = open(U('template.html'), encoding='utf-8').read()
    three = open(U('vendor', 'three.min.js'), encoding='utf-8').read() + '\n' + open(U('vendor', 'OrbitControls.min.js'), encoding='utf-8').read()
    rep = {
        '__ND_INK__': b64('nd_ink.webp'), '__ND_MASK__': b64('nd_mask.webp'),
        '__HP_INK__': b64('hp_ink.webp'), '__HP_MASK__': b64('hp_mask.webp'),
        '__ND_PARTS__': b64('nd_parts.webp'), '__HP_PARTS__': b64('hp_parts.webp'),
        '__ND_DATA__': open(U('nd_data.json'), encoding='utf-8').read(),
        '__HP_DATA__': open(U('hp_data.json'), encoding='utf-8').read(),
        '__MODEL_JSON__': open(U('model.json'), encoding='utf-8').read(),
        '__MODEL_BIN__': b64('model.bin'),
    }
    for k, v in rep.items():
        if k not in t:
            sys.exit(f'В шаблоне нет {k}')
        t = t.replace(k, v)
    # three.js вставляем последним: в нём могут встретиться любые строки
    t = t.replace('<script>__THREE__</script>', '<script>' + three.replace('</script', '<\\/script') + '</script>', 1)
    return t


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'ustroystvo.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    h = assemble()
    open(out, 'w', encoding='utf-8').write(h)
    print(f'{out}: {len(h) // 1024} КБ')
