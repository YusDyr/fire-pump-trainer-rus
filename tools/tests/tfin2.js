const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:412,height:915},isMobile:true,hasTouch:true});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(500);
const r=await p.evaluate(()=>{const T=__T;const run=s=>{for(let i=0;i<s*20;i++)T.step(0.05)};let S=T.S;const out={};
 S.speed=0;S.brake=true;run(.2);S.kom=true;run(.2);S.gear='5';run(.2);S.power=true;run(.2);S.v.tank=true;S.v.out=[0.05,0.05];run(3);S.clutch=true;run(8);S.can=true;run(.3);S.v.out=[1,1];run(.5);
 for(const rpm of [1200,1400,1500,1600,1700,1800,1900,2000]){S.rpmSet=rpm;run(4);if(S.calc.Pn[0]>=0.35)break}
 out.pre=[S.stepIdx,S.steps.length,S.calc.Pn.map(x=>x.toFixed(2)).join('/'),document.querySelector('#tbSteps .cur')?.textContent];
 run(12);out.done=[S.done,S.stop.length,document.querySelector('#tbSteps .cur')?.textContent];
 S.rpmSet=750;S.can=false;run(5);S.v.out=[0,0];run(1);S.clutch=false;run(5);S.v.tank=false;run(1);S.v.drain=true;run(10);out.mid=[S.stopIdx,S.fill.toFixed(2),S.stop.map(x=>x.t.slice(0,25))];S.purge=true;run(6);S.purge=false;S.v.drain=false;run(1);S.kom=false;run(1);
 out.fin=[S.finished,S.score,S.stopIdx];return out});
await p.waitForTimeout(800);
const modal=await p.evaluate(()=>{const m=document.getElementById('finModal');return m&&!m.hidden?m.innerText.slice(0,200):null});
await p.screenshot({path:'s_fin.png'});
console.log(JSON.stringify(r),modal,errs);await b.close()})();
