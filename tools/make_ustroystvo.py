#!/usr/bin/env python3
"""Сборка страницы «Устройство насоса» (разрезы ступеней + 3D-модель) в один HTML-файл.

    python3 tools/make_ustroystvo.py [каталог] [выходной.html]

Каталоги исходников:
  src/ustroystvo/      — насос НЦПК-40/100-4/400М-В1У по РЭ 2025 г. (рис. 3, 4, 5 и 3D) → emulator/ustroystvo.html;
  src/ustroystvo_v1t/  — исполнение В1Т по РЭ КШИН.062223.015 (рис. 2, 5, 8 и 3D) → emulator/ustroystvo-v1t.html.

В каждом каталоге:
  template.html          — разметка и код страницы;
  *_ink.webp, *_parts.webp, *_mask.webp — чертёж (прозрачность линий), карта деталей (R = номер позиции)
                           и маска областей (R — вода, G — масло, B: 255 — вал, 120 — охлаждающая вода);
  *_data.json            — пути частиц воды, координаты деталей на чертеже;
  model.json + model.bin — 3D-модель (координаты uint16, нормали int8, см. tools/glb_to_model.py);
  vendor/                — three.js r147 (MIT) и OrbitControls.
Метки в шаблоне вида __ND_INK__ заменяются содержимым файла nd_ink.webp (base64), __ND_DATA__ — nd_data.json (текст),
__MODEL_JSON__ — model.json, __MODEL_BIN__ — model.bin (base64). Страница работает без сети (кроме шрифтов Google,
которые build.py заменяет на локальные).
"""
import base64, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def assemble(name='ustroystvo'):
    U = lambda *a: os.path.join(ROOT, 'src', name, *a)
    t = open(U('template.html'), encoding='utf-8').read()
    three = open(U('vendor', 'three.min.js'), encoding='utf-8').read() + '\n' + open(U('vendor', 'OrbitControls.min.js'), encoding='utf-8').read()

    def sub(m):
        a, b = m.group(1).lower(), m.group(2).lower()
        for fn, kind in ((f'{a}_{b}.webp', 'b64'), (f'{a}_{b}.png', 'b64'), (f'{a}_{b}.json', 'txt'), (f'{a}.{b}', 'b64' if b == 'bin' else 'txt')):
            if os.path.exists(U(fn)):
                d = open(U(fn), 'rb').read()
                return base64.b64encode(d).decode() if kind == 'b64' else d.decode('utf-8')
        sys.exit(f'{name}: нет файла для метки {m.group(0)}')
    t = re.sub(r'__([A-Z0-9]+)_([A-Z0-9]+)__', sub, t.replace('<script>__THREE__</script>', '<script>@@THREE@@</script>'))
    # three.js вставляем последним: в нём могут встретиться любые строки
    t = t.replace('<script>@@THREE@@</script>', '<script>' + three.replace('</script', '<\\/script') + '</script>', 1)
    return t


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'ustroystvo'
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'build', name.replace('_', '-') + '.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    h = assemble(name)
    open(out, 'w', encoding='utf-8').write(h)
    print(f'{out}: {len(h) // 1024} КБ')
