const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1400,height:1000}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(800);
const r=await p.evaluate(async()=>{const T=window.__T;const out={};
 const run=(s)=>{for(let i=0;i<s*10;i++)T.step(0.1)};
 // 1. рычаг запускает агрегат
 T.fresh('reservoir');let S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true});
 document.getElementById('vacValve').click();out.leverStart=S.vacPump;
 // 2. заполнение при вращении колеса (сначала сцепление)
 T.fresh('reservoir');S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true,brake:true,kom:true,gear:'5'});
 S.clutch=true;run(8);out.rpm0=Math.round(S.pumpRpm);
 document.getElementById('vacValve').click();S.can=true;S.rpmSet=1300;
 let t=0;while(S.fill<0.98&&t<90){run(1);t++}
 out.fillT=t;out.vacAfter=S.vacPump;out.dead=!!S.dead;run(5);out.pout=+S.calc.Pout.toFixed(2);out.valveOpen=S.v.vacValve;run(20);out.agg=S.vacBroken;
 // 3. таймаут 60 с (заглушка не стоит → подсос: открыт вентиль)
 T.fresh('tank');S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true});S.v.out=[0.5,0];
 document.getElementById('vacValve').click();run(65);out.timeout=[S.vacPump,S.vacFault];
 // 4. длинное нажатие — ручной режим
 T.fresh('tank');S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true});
 const el=document.getElementById('vacStart');el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));
 await new Promise(r=>setTimeout(r,1200));out.manual=[S.vacMode,S.vacPump];run(70);out.manual70=S.vacPump;
 el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));out.released=S.vacPump;
 // короткое: пуск/стоп
 el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));out.short1=S.vacPump;
 el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0}));el.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));out.short2=S.vacPump;
 // 5. термореле
 S.vacHeat=0;for(let k=0;k<4;k++){S.vacPump=true;S.vacMode='auto';S.vacRun=0;run(50);S.vacPump=false;run(2)}
 out.therm=[S.vacFault,Math.round((S.thermUntil||0)-S.t)];
 // 6. неисправность датчика затвора
 T.fresh('reservoir');S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true});T.setFault('gate');document.getElementById('vacValve').click();out.gate=S.vacPump;
 // 7. флажок
 T.fresh('tank');S=T.S;T.setFault('flag');run(1);out.flag=[S.v.drain,T.sealed()];T.doAct&&T.doAct('flag');run(1);out.flagFix=S.v.drain;
 // 8. сухой вакуум
 T.fresh('vacdry');S=T.S;Object.assign(S,{power:true,engine:true,avsPower:true,buPower:true});
 document.getElementById('vacValve').click();t=0;while(S.vac<0.078&&t<300){run(0.1);t++};out.t75=t/10;
 document.getElementById('vacStart').click();run(1);out.dv=!!S.dv;run(245);out.dvDone=S.dv&&S.dv.done;out.drop=S.dv&&S.dv.drop;
 out.log=[...document.querySelectorAll('#log > *')].slice(0,4).map(x=>x.textContent);
 return out});
console.log(JSON.stringify(r,null,1),errs);await b.close()})();
