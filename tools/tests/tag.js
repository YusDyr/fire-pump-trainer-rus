const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1400,height:1000}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(800);
await p.evaluate(()=>document.getElementById('scene').setAttribute('viewBox','1480 1060 140 110'));await p.waitForTimeout(300);
await (await p.$('#scene')).screenshot({path:'ag.png'});
await p.evaluate(()=>document.getElementById('scene').setAttribute('viewBox','0 0 2486 1960'));
await p.evaluate(()=>document.getElementById('gz_hps2').dispatchEvent(new MouseEvent('click',{bubbles:true})));await p.waitForTimeout(300);
console.log(await p.evaluate(()=>document.querySelector('.gzwin:not([hidden]) b, #gzTitle')?.textContent||'?'),errs);await b.close()})();
