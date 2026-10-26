import sys,os,re,html
R=sys.argv[1];V=open(os.path.join(R,'VERSION')).read().strip()
md=open(os.path.join(R,'CHANGELOG.md'),encoding='utf-8').read()
apk=os.path.getsize(os.path.join(R,'NCPK-emulator.apk'))/1048576
def inline(t):
    t=html.escape(t);t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t);return t
out=[];inlist=False;n=0
for line in md.splitlines():
    if line.startswith('## '):
        if inlist:out.append('</ul>');inlist=False
        n+=1;out.append(('</details>' if n>1 else '')+f'<details{" open" if n<=2 else ""}><summary>{inline(line[3:])}</summary>')
    elif line.startswith('- '):
        if not inlist:out.append('<ul>');inlist=True
        out.append(f'<li>{inline(line[2:])}</li>')
if inlist:out.append('</ul>')
if n:out.append('</details>')
ch='\n'.join(out)
page=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Тренажёр насоса НЦПК-40/100</title>
<meta name="description" content="Учебный эмулятор насосной установки АЦ 1,6-40/4 (ГАЗон NEXT), ДПК «Экстремум»">
<style>
:root{{--bg:#eef0f2;--card:#fff;--ink:#172027;--muted:#5a6770;--line:#d3d8dc;--red:#c42a1d;--btn2:#e3e7ea}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14181b;--card:#1e2327;--ink:#e5e9eb;--muted:#9ba7ae;--line:#3b444b;--red:#e5503f;--btn2:#2a3035}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:16px}}
main{{max-width:760px;margin:0 auto;display:flex;flex-direction:column;gap:16px}}
.hero{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:14px}}
.brand{{display:flex;gap:14px;align-items:center}}.plate{{background:var(--red);color:#fff;font-weight:800;font-size:13px;padding:8px 10px;border-radius:4px;line-height:1.15;text-align:center}}
h1{{font-size:22px;margin:0;line-height:1.2}}.sub{{color:var(--muted);margin:2px 0 0;font-size:14px}}
.btns{{display:flex;flex-wrap:wrap;gap:10px}}.btn{{display:inline-flex;align-items:center;gap:8px;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600;color:var(--ink);background:var(--btn2);border:1px solid var(--line)}}
.btn.primary{{background:var(--red);border-color:var(--red);color:#fff}}.btn small{{font-weight:400;opacity:.8}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 20px}}h2{{font-size:17px;margin:0 0 8px}}
details{{border-top:1px solid var(--line);padding:8px 0}}details:first-of-type{{border-top:0}}summary{{cursor:pointer;font-weight:600}}ul{{margin:6px 0 0;padding-left:20px}}li{{margin:3px 0}}
.muted{{color:var(--muted);font-size:14px}}a{{color:inherit}}
</style></head><body><main>
<section class="hero">
 <div class="brand"><div class="plate">АЦ<br>1,6-40/4</div><div><h1>Тренажёр пожарного насоса НЦПК-40/100-4/400М-В1У</h1><p class="sub">Учебный эмулятор насосной установки · ГАЗон NEXT C41R33 · ДПК «Экстремум»</p></div></div>
 <div class="btns">
  <a class="btn primary" href="emulator/">▶ Открыть эмулятор <small>в браузере</small></a>
  <a class="btn" href="emulator/ustroystvo.html">⚙️ Устройство насоса <small>разрезы и 3D</small></a>
  <a class="btn" href="NCPK-emulator.apk" download>📱 Скачать для Android <small>v{V} · {apk:.0f} МБ</small></a>
  <a class="btn" href="https://github.com/YusDyr/fire-pump-trainer-rus/releases">Все версии</a>
 </div>
 <p class="muted">Приложение для Android работает без интернета. На телефоне может понадобиться разрешить установку из этого источника.</p>
</section>
<section class="card"><h2>Что нового</h2>{ch}</section>
<section class="card muted">Насосный отсек по фотографиям машины, задания и пошаговые уроки, неисправности по РЭ, режим «Лето/Зима», схема потоков. Учебное пособие, не заменяет руководство по эксплуатации и практические занятия. Исходники: <a href="https://github.com/YusDyr/fire-pump-trainer-rus">github.com/YusDyr/fire-pump-trainer-rus</a></section>
</main></body></html>'''
open(os.path.join(R,'index.html'),'w',encoding='utf-8').write(page);print('landing ok',V)
