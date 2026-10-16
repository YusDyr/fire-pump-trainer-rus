const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1300,height:1000}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(500);
await p.evaluate(()=>{const T=__T;const run=s=>{for(let i=0;i<s*20;i++)T.step(0.05)};let S=T.S;S.speed=0;S.brake=true;S.kom=true;S.gear='5';S.power=true;S.v.tank=true;S.v.out=[0.05,0.05];run(3);S.clutch=true;run(8);S.can=true;S.v.out=[1,0.45];S.v.fill=0.3;S.rpmSet=1700;S.foamTankValve=true;S.foamValve=true;S.doz=0.3;S.purge=false;run(10);S.speed=1});
await p.click('#viewSeg button[data-view=panel]');await p.waitForTimeout(800);
await (await p.$('.schem')).screenshot({path:'s_sch.png'});console.log(errs);await b.close()})();
