const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1440,height:1000}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(300);
const r=await p.evaluate(()=>{const T=window.__T;const run=s=>{for(let i=0;i<s*20;i++)T.step(0.05)};const out={};
 // tank lesson
 T.fresh('learn-tank');let S=T.S;S.speed=0;const A=[
  ()=>S.brake=true,()=>S.kom=true,()=>S.gear='5',()=>S.power=true,()=>S.v.tank=true,()=>S.v.out[0]=0.15,()=>run(5),()=>{S.clutch=true;run(9)},()=>S.can=true,
  ()=>S.v.out=[1,1],()=>{S.rpmSet=1400;run(8)},()=>run(12),()=>{S.can=false;S.rpmSet=750;run(3)},()=>S.v.out=[0,0],()=>{S.clutch=false;run(4)},()=>{S.v.tank=false;S.v.drain=true},()=>S.v.drain=false];
 const trace=[];for(const a of A){a();run(0.2);trace.push(S.lesson.i)} out.tank=trace;
 // res lesson
 T.fresh('learn-res');S=T.S;const B=[()=>S.brake=true,()=>S.kom=true,()=>S.gear='5',()=>S.power=true,()=>{},()=>S.avsPower=true,()=>S.buPower=true,()=>S.v.vacValve=true,()=>S.vacPump=true,()=>run(30),()=>S.v.vacValve=false,()=>{S.clutch=true;run(9)},()=>{S.can=true;S.rpmSet=1500;run(6)},()=>{S.v.out[0]=1;run(3)},()=>{let best=0;for(const r of [1500,1600,1700,1800,1900,2000,2100]){S.rpmSet=r;run(5);if(S.lesson.i>14)break}},()=>{S.buPower=false;S.avsPower=false}];
 const tr2=[];for(const a of B){a();run(0.2);tr2.push(S.lesson.i)} out.res=tr2;out.resN=S.calc.Pn[0].toFixed(2);
 return out});
console.log(JSON.stringify(r),errs);
await p.evaluate(()=>{window.__T.fresh('learn-tour')});await p.click('#lNext');await p.waitForTimeout(400);
await p.screenshot({path:'shot5.png',clip:{x:0,y:0,width:1440,height:1000}});
await b.close()})();
