#!/usr/bin/env python3
"""Сборка веб-версии эмулятора и ассетов для APK из исходника src/emulator.html.

    python3 tools/build.py            # версия берётся из файла VERSION
    python3 tools/build.py 3.8        # явная версия

Что делает:
  * подменяет шрифты Google Fonts на локальные (android/fonts.css + android/fonts/*.woff2);
  * добавляет в заголовок ссылку «vX.Y» на CHANGELOG;
  * пишет emulator/index.html, emulator/ustroystvo.html (устройство насоса, 3D), emulator/ustroystvo-v1t.html (то же для исполнения В1Т) и emulator/fonts/ (сайт на GitHub Pages);
  * собирает android/assets/ (index.html, fonts, photos) для APK;
  * проставляет versionCode/versionName в android/AndroidManifest.xml.
"""
import os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_ustroystvo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

V = sys.argv[1] if len(sys.argv) > 1 else open(P('VERSION')).read().strip()
if not re.fullmatch(r'\d+\.\d+', V):
    sys.exit(f'Неверная версия: {V!r} (нужно вида 3.8)')
code = int(V.split('.')[0]) * 10 + int(V.split('.')[1])

css = open(P('android', 'fonts.css'), encoding='utf-8').read()


def localize(html):
    """Google Fonts -> локальные шрифты, viewport и doctype."""
    html = re.sub(r'<link rel="preconnect"[^>]*>\s*', '', html)
    html = re.sub(r'<link href="https://fonts.googleapis.com[^>]*>', lambda m: '<style>\n' + css + '</style>', html)
    if 'fonts.googleapis' in html:
        sys.exit('В HTML осталась ссылка на Google Fonts')
    if '<meta name="viewport"' not in html:
        html = html.replace('<title>', '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<title>', 1)
    if not html.lstrip().lower().startswith('<!doctype'):
        html = '<!doctype html>\n<html lang="ru">\n' + html
    return html


html = localize(open(P('src', 'emulator.html'), encoding='utf-8').read())
ust = localize(make_ustroystvo.assemble())
ust1 = localize(make_ustroystvo.assemble('ustroystvo_v1t'))
mark = 'Учебный эмулятор насосной установки · ГАЗон NEXT C41R33</p>'
if mark not in html:
    sys.exit('Не найдена строка подзаголовка для ссылки на версию')
html = html.replace(mark, mark[:-4] + ' · <a href="https://github.com/YusDyr/fire-pump-trainer-rus/blob/main/CHANGELOG.md" target="_blank" rel="noopener" title="Что нового">v' + V + '</a></p>', 1)

def put_fonts(dst):
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(P('android', 'fonts'), dst)

# сайт
os.makedirs(P('emulator'), exist_ok=True)
open(P('emulator', 'index.html'), 'w', encoding='utf-8').write(html)
open(P('emulator', 'ustroystvo.html'), 'w', encoding='utf-8').write(ust)
open(P('emulator', 'ustroystvo-v1t.html'), 'w', encoding='utf-8').write(ust1)
put_fonts(P('emulator', 'fonts'))

# ассеты APK
A = P('android', 'assets')
shutil.rmtree(A, ignore_errors=True)
os.makedirs(A)
open(os.path.join(A, 'index.html'), 'w', encoding='utf-8').write(html)
open(os.path.join(A, 'ustroystvo.html'), 'w', encoding='utf-8').write(ust)
open(os.path.join(A, 'ustroystvo-v1t.html'), 'w', encoding='utf-8').write(ust1)
put_fonts(os.path.join(A, 'fonts'))
shutil.copytree(P('emulator', 'photos'), os.path.join(A, 'photos'))
if os.path.isdir(P('emulator', 'video')):   # ролики потоков воды (Blender, tools/blender)
    shutil.copytree(P('emulator', 'video'), os.path.join(A, 'video'))

# версия в манифесте
m = P('android', 'AndroidManifest.xml')
t = open(m, encoding='utf-8').read()
t2 = re.sub(r'android:versionCode="\d+" android:versionName="[^"]+"', f'android:versionCode="{code}" android:versionName="{V}"', t)
if t2 == t and f'android:versionName="{V}"' not in t:
    sys.exit('Не удалось проставить версию в AndroidManifest.xml')
open(m, 'w', encoding='utf-8').write(t2)

print(f'build ok: v{V} (versionCode {code}), {len(html) // 1024} КБ HTML, фото: {len(os.listdir(P("emulator", "photos")))}')
