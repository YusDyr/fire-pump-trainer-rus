# Генератор схемы водопенных коммуникаций (viewBox 900x450)
O=[]
def add(s):O.append(s)
def pipe(fid,d,cls='',w=7,fw=3):
    add(f'<path class="pipe" style="stroke-width:{w}" d="{d}"/>')
    if fid: add(f'<path class="flow {cls}" id="{fid}" d="{d}" style="stroke-width:{fw}"/>')
def T(x,y,t,cls='',a='start',fs=None,idd=None,extra=''):
    st=f' style="font-size:{fs}px"' if fs else ''
    i=f' id="{idd}"' if idd else ''
    add(f'<text x="{x}" y="{y}" text-anchor="{a}" class="{cls}"{i}{st}{extra}>{t}</text>')
def bow(x,y,vert=False):
    if vert: return f'M{x-7} {y-9} L{x+7} {y+9} L{x-7} {y+9} L{x+7} {y-9} Z'
    return f'M{x-9} {y-7} L{x+9} {y+7} L{x+9} {y-7} L{x-9} {y+7} Z'
def valve(vid,x,y,kind,lab,lx=None,ly=None,la='middle',vert=False,title=None,act_side=None):
    title=title or lab
    s=f'<g class="vsym" id="{vid}"><title>{title}</title>'
    s+=f'<path d="{bow(x,y,vert)}" class="vbody"/>'
    k='stroke="var(--ink)" stroke-width="1.4" fill="none"'
    if kind=='ball': s+=f'<circle cx="{x}" cy="{y}" r="3.2" fill="var(--ink)"/>'
    elif kind=='globe':  # вентиль с маховиком: шток и маховик
        if vert: s+=f'<path d="M{x} {y} H{x-14} M{x-14} {y-6} V{y+6}" {k}/>'
        else: s+=f'<path d="M{x} {y} V{y-14} M{x-6} {y-14} H{x+6}" {k}/>'
    elif kind=='bfly':   # затвор поворотный: диск
        s+=f'<path d="M{x} {y-9} V{y+9}" {k}/>' if not vert else f'<path d="M{x-9} {y} H{x+9}" {k}/>'
    elif kind=='lever':  # кран с рукояткой
        s+=f'<circle cx="{x}" cy="{y}" r="2.6" fill="var(--ink)"/>'+(f'<path d="M{x} {y} L{x-10} {y-12}" {k}/>' if not vert else f'<path d="M{x} {y} L{x-12} {y-10}" {k}/>')
    elif kind=='pneu':   # с пневмоприводом
        side=act_side or ('left' if vert else 'up')
        if side=='up': s+=f'<path d="M{x} {y} V{y-13}" {k}/><path d="M{x-8} {y-13} A8 8 0 0 1 {x+8} {y-13} Z" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.3"/>'
        else: s+=f'<path d="M{x} {y} H{x-13}" {k}/><path d="M{x-13} {y-8} A8 8 0 0 0 {x-13} {y+8} Z" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.3"/>'
    s+='</g>'
    add(s)
    if lab:
        if lx is None: lx,ly=x,y+20
        T(lx,ly,lab,'vlab',la);T(lx,ly+10,'','vpct',la,idd=vid+'p')
def gauge(x,y,lab,ax,ay,la='start',gid=None):
    i=f' id="{gid}"' if gid else ''
    add(f'<g class="gsym"{i}><path d="M{ax} {ay} L{x} {y}" stroke="var(--line)" stroke-width="2"/><circle cx="{x}" cy="{y}" r="8" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.2"/><path d="M{x} {y} L{x+5} {y-4}" stroke="var(--ink)" stroke-width="1.4"/><title>{lab}</title></g>')
def ground(x,y,lab=None,la='start'):
    add(f'<path d="M{x} {y} v10 M{x-5} {y+5} L{x} {y+11} L{x+5} {y+5}" stroke="#4aa3df" stroke-width="1.6" fill="none"/>')
    if lab:T(x+8,y+12,lab,'t-muted',la,9)
def sol(sid,x,y,lab,ctl,title):
    add(f'<g id="{sid}"><title>{title}</title><rect x="{x-11}" y="{y-9}" width="22" height="18" rx="2" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.3" class="solbody"/><path d="M{x-7} {y+5} L{x+7} {y-5}" stroke="var(--ink)" stroke-width="1.3"/><path d="M{x+11} {y} h5 M{x+16} {y-5} v10" stroke="var(--ink)" stroke-width="1.2"/></g>')
    T(x,y-14,lab,'vlab','middle');T(x,y+21,ctl,'t-muted','middle',8)
def arrow(x,y,dirn,cls='arr'):
    d={'r':f'M{x-4} {y-4} L{x+3} {y} L{x-4} {y+4}','l':f'M{x+4} {y-4} L{x-3} {y} L{x+4} {y+4}','u':f'M{x-4} {y+4} L{x} {y-3} L{x+4} {y+4}','d':f'M{x-4} {y-4} L{x} {y+3} L{x+4} {y-4}'}[dirn]
    add(f'<path d="{d}" class="{cls}"/>')

add('<svg viewBox="0 0 900 475" id="schem" role="img" aria-label="Схема водопенных коммуникаций: источники, насос, вентили, линии, наполнение, сливы, вакуумная система, сжатый воздух">')
# ---------- источники
add('<rect id="sTankBox" x="20" y="48" width="120" height="86" rx="6" fill="var(--plate-2)" stroke="var(--line)"/>')
add('<rect id="sTankFill" x="21" y="68" width="118" height="65" fill="var(--water-soft)"/>')
T(80,63,'Цистерна',a='middle');T(80,126,'',cls='t-muted',a='middle',idd='sTankInfo')
add('<g id="sCapOpen"><rect x="38" y="41" width="40" height="7" rx="2" fill="#2f7cf6"/><text x="36" y="36" class="t-muted" style="font-size:9px">горловина открыта</text></g>')
# слив из цистерны
pipe('fTankDr','M34 134 V178',w=6,fw=2.5)
valve('vsTankDr',34,156,'pneu','',vert=True,title='Слив воды из цистерны (кнопка на пульте АЦ)')
T(46,158,'слив цистерны','vlab');T(46,168,'','vpct',idd='vsTankDrp');ground(34,178)
add('<rect id="sSrcBox" x="20" y="200" width="120" height="58" rx="6" fill="var(--plate-2)" stroke="var(--line)"/>')
T(80,222,'Вход DN125',a='middle',idd='sSrcName');T(80,242,'',cls='t-muted',a='middle',idd='sSrcInfo')
add('<rect x="20" y="338" width="80" height="56" rx="6" fill="var(--plate-2)" stroke="var(--line)"/>')
add('<rect id="sFoamFill" x="21" y="353" width="78" height="40" fill="#f2c46b" opacity=".7"/>')
T(60,351,'Пенобак',a='middle');T(60,388,'',cls='t-muted',a='middle',idd='sFoamInfo')
# ---------- всасывающая сторона
pipe('fTank','M140 110 H250 V226')
valve('vsTank',190,110,'bfly','',title='Затвор «Вода из цистерны»');T(190,100,'затвор «Вода из цистерны»','vlab','middle');T(190,128,'','vpct','middle',idd='vsTankp')
pipe('fSrc','M140 230 H246')
pipe('fIn','M250 230 H292',w=8,fw=4)
arrow(272,230,'r');arrow(165,230,'r');arrow(222,110,'r')
gauge(226,178,'Мановакуумметр на входе',250,178)
T(226,165,'вход','t-muted','middle',9)
T(256,220,'',cls='t-muted',idd='tIn',fs=9)
# ---------- насос
add('<circle id="sPump" cx="330" cy="230" r="38" fill="var(--plate-2)" stroke="var(--ink)" stroke-width="1.6"/>')
add('<path d="M330 192 L368 230 L330 268" fill="none" stroke="var(--line)" stroke-width="1.2" opacity=".0"/>')
add('<g id="impeller"><path d="M330 230 L330 204 M330 230 L352.5 243 M330 230 L307.5 243" stroke="var(--muted)" stroke-width="4" stroke-linecap="round"/></g>')
add('<path d="M358 222 L370 230 L358 238 Z" fill="var(--ink)"/>')   # направление нагнетания
T(348,338,'НЦПК',cls='t-muted',a='middle',idd='sPumpInfo',fs=9)
add('<circle id="sFillSens" cx="357" cy="203" r="5" fill="var(--lamp-off)" stroke="var(--ink)"><title>Датчик заполнения: сигнал «Насос заполнен» на БУК</title></circle>')
T(366,198,'датчик','t-muted','start',9)
# ---------- вакуумная система
pipe('fVac','M330 192 V112',cls='vac',w=6,fw=2.5)
valve('vsVac',330,156,'lever','кран вакуумный',342,152,'start',vert=True,title='Кран вакуумный')
add('<g id="sVacUnit"><title>Вакуумный агрегат: вакуумный насос с электродвигателем, управляется с БУК-02 («ВАКУУМ»)</title><rect x="296" y="78" width="104" height="34" rx="6" fill="none" stroke="var(--line)" stroke-dasharray="4 3"/>'
    '<circle id="sVacPump" cx="330" cy="98" r="12" fill="var(--plate-2)" stroke="var(--ink)" stroke-width="1.4"/><g id="vacVanes"><path d="M330 98 L330 88 M330 98 L338.7 103 M330 98 L321.3 103" stroke="var(--muted)" stroke-width="2.4" stroke-linecap="round"/></g>'
    '<path d="M342 96 H366 M342 100 H366" stroke="var(--ink)" stroke-width="1.2"/><circle id="sVacMotor" cx="378" cy="98" r="11" fill="var(--plate-2)" stroke="var(--ink)" stroke-width="1.4"/><text x="378" y="102" text-anchor="middle" style="font-size:10px;font-weight:700">М</text></g>')
T(348,74,'вакуумный агрегат','vlab','middle')
pipe('fExh','M318 98 H276 V78',cls='air',w=5,fw=2)
T(276,72,'выхлоп','t-muted','middle',9)
# ---------- напорный коллектор
pipe(None,'M368 230 H440')
add('<path class="flow" id="fOut" d="M368 230 H440" style="stroke-width:4"/>')
pipe(None,'M440 20 V370')
gauge(462,196,'Манометр выхода НД',440,196)
T(474,199,'выход НД','t-muted',fs=9)
# наполнение цистерны
pipe('fFill','M440 230 V20 H80 V48')
valve('vsFill',250,20,'globe','вентиль подачи воды в цистерну',250,40,title='Вентиль подачи воды в цистерну')
arrow(150,20,'l');arrow(440,60,'u')
# линии
pipe('fL0','M440 150 H690')
valve('vsL0',560,150,'globe','вентиль напорный НД, левый',560,170,title='Вентиль напорный нормального давления, левый')
arrow(620,150,'r')
pipe('fL1','M440 250 H690')
valve('vsL1',560,250,'globe','вентиль напорный НД, правый',560,270,title='Вентиль напорный нормального давления, правый')
arrow(620,250,'r')
T(698,147,'Линия 1',idd='tL0');T(698,161,'',cls='t-muted',idd='tL0b',fs=10)
T(698,247,'Линия 2',idd='tL1');T(698,261,'',cls='t-muted',idd='tL1b',fs=10)
# ступень ВД
pipe('fHpS','M440 330 H492')
add('<rect x="492" y="314" width="76" height="32" rx="5" fill="var(--plate-2)" stroke="var(--line)" id="sHpBox"/>')
T(530,334,'ступень ВД',a='middle',fs=10)
pipe('fHp','M568 330 H690',cls='hp')
valve('vsHp',604,330,'ball','кран высокого давления',604,350,title='Кран высокого давления')
gauge(640,308,'Манометр высокого давления',640,330)
T(651,303,'ВД','t-muted',fs=9)
arrow(675,330,'r')
T(698,327,'Катушка ВД',idd='tHp');T(698,341,'',cls='t-muted',idd='tHpb',fs=10)
pipe('fHpDr','M530 346 V400',w=6,fw=2.5)
valve('vsHpDr',530,372,'pneu','',vert=True,title='Сливные краны ступени ВД (пневмопривод)')
T(544,370,'слив ступени ВД','vlab');T(544,380,'','vpct',idd='vsHpDrp');ground(530,400)
# слив насоса
pipe('fDrain','M330 268 V312',w=6,fw=2.5)
valve('vsDrain',330,290,'pneu','',vert=True,title='Кран слива насоса (пневмопривод)')
T(344,302,'слив насоса','vlab');T(344,312,'','vpct',idd='vsDrainp');ground(330,312)
# ---------- пеносмеситель
pipe('fFoam','M100 366 H246',cls='foam')
valve('vsFt',132,366,'lever','кран пенобака',132,386,title='Кран магистрали пенобака')
add('<circle id="vsDoz" cx="194" cy="366" r="8" fill="var(--plate)" stroke="var(--ink)"/><path d="M186 376 L202 356 M198 356 h4 v4" stroke="var(--ink)" stroke-width="1.2" fill="none"/>')
T(194,350,'дозатор','vlab','middle');T(194,388,'','vpct','middle',idd='vsDozp')
pipe('fKch','M224 430 V366',cls='foam',w=6,fw=2.5);T(230,428,'рукав КЩ','t-muted',fs=9)
add('<path d="M240 358 L262 362 L262 370 L240 374 Z" fill="var(--plate-2)" stroke="var(--ink)"/>')
T(252,396,'эжектор','vlab','middle')
pipe('fEjO','M250 358 V232',cls='foam')
pipe('fEjW','M440 370 V366 H262')
valve('vsEj',380,366,'lever','кран эжектора',380,386,title='Рукоятка включения эжектора')
arrow(300,366,'l');arrow(250,300,'u')
# ---------- сжатый воздух
add('<rect id="sAirSrc" x="772" y="56" width="116" height="30" rx="5" fill="var(--plate-2)" stroke="var(--line)"><title>Пневмосистема шасси: сжатый воздух для продувки и пневмоприводов</title></rect>')
T(830,69,'пневмосистема','vlab','middle');T(830,80,'шасси (ресивер)','vlab','middle')
pipe('fAirSup','M772 71 H520',cls='air',w=4,fw=2)
gauge(740,50,'Манометр воздуха',740,71);T(751,47,'воздух','t-muted',fs=9)
# клапан осушения -> напорный коллектор (продувка насоса и линий)
pipe('fAir','M520 71 V112 H440',cls='air',w=4,fw=2)
sol('sPurge',520,93,'клапан осушения','БУК «Продувка»','Пневмоклапан «Клапан осушения»: продувка насоса и рукавных линий сжатым воздухом. Держите «Продувка» на БУК')
# пневмоклапан «Сливные краны» -> пневмоприводы сливов
pipe(None,'M610 71 V84',w=4)
sol('sDrSol',610,93,'сливные краны','БУК «Слив»','Пневмоклапан «Сливные краны»: открывает пневмоприводы крана слива насоса и сливных кранов ступени ВД. Кнопка «Слив» на БУК')
add('<path id="fCtl" class="ctl" d="M610 102 V128 M317 290 H300 M517 372 H500" fill="none"/>')
T(614,138,'→ к пневмоприводам сливов','t-muted','start',8)
T(298,287,'от «Сливные','t-muted','end',8);T(298,296,'краны»','t-muted','end',8)
T(498,369,'от «Сливные','t-muted','end',8);T(498,378,'краны»','t-muted','end',8)
# продувка катушки ВД
add('<path class="pipe" style="stroke-width:4" d="M660 378 V330"/><path class="flow air" id="fReelAir" d="M660 378 V330" style="stroke-width:2"/>')
sol('sReelP',660,388,'','','Продувка катушки ВД сжатым воздухом: держите кнопку «продувка катушки» на пульте АЦ')
T(676,385,'продувка катушки','vlab');T(676,395,'воздух из пневмосистемы,','t-muted','start',8);T(676,404,'кнопка на пульте АЦ','t-muted','start',8)
# ---------- легенда
def lg(x,y,inner,txt):add(f'<g transform="translate({x} {y})">{inner}<text x="26" y="3" class="t-muted" style="font-size:9px">{txt}</text></g>')
lg(20,446,'<path d="M0 0 H22" stroke="var(--water)" stroke-width="3"/>','вода')
lg(80,446,'<path d="M0 0 H22" stroke="#9bbf2a" stroke-width="3"/>','раствор пенообразователя')
lg(262,446,'<path d="M0 0 H22" stroke="#e7a83a" stroke-width="3"/>','пенообразователь')
lg(400,446,'<path d="M0 0 H22" stroke="#3fb8d8" stroke-width="2" stroke-dasharray="3 4"/>','сжатый воздух')
lg(506,446,'<path d="M0 0 H22" stroke="#8b96a0" stroke-width="2" stroke-dasharray="2 3"/>','разрежение')
lg(606,446,'<path d="M0 0 H22" stroke="#3fb8d8" stroke-width="1.4" stroke-dasharray="6 3 1 3"/>','пневмоуправление')
st=lambda c:f'<path d="M2 -5 L20 5 L20 -5 L2 5 Z" class="vbody {c}"/>'
lg(20,466,st('v1'),'открыт');lg(84,466,st('vp'),'частично');lg(160,466,st('v0'),'закрыт')
k='stroke="var(--ink)" stroke-width="1.3" fill="none"'
B='<path d="M2 -5 L20 5 L20 -5 L2 5 Z" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.1"/>'
lg(226,466,B+f'<path d="M11 0 V-9 M7 -9 H15" {k}/>','вентиль')
lg(300,466,B+'<circle cx="11" cy="0" r="2.4" fill="var(--ink)"/>','шаровой кран')
lg(400,466,B+f'<path d="M11 -6 V6" {k}/>','затвор')
lg(464,466,B+f'<path d="M11 0 V-8" {k}/><path d="M6 -8 A5 5 0 0 1 16 -8 Z" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.1"/>','пневмопривод')
lg(576,466,'<rect x="3" y="-6" width="16" height="12" rx="2" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.1"/><path d="M6 4 L16 -4" stroke="var(--ink)" stroke-width="1.1"/>','пневмоклапан')
lg(676,466,'<circle cx="11" cy="0" r="6" fill="var(--plate)" stroke="var(--ink)" stroke-width="1.1"/><path d="M11 0 L15 -3" stroke="var(--ink)" stroke-width="1.2"/>','манометр')
lg(756,466,'<path d="M11 -6 v10 M7 0 L11 6 L15 0" stroke="#4aa3df" stroke-width="1.5" fill="none"/>','слив под машину')
add('</svg>')
open('schem_new.svg','w').write('\n'.join(O))
print(len(O))
