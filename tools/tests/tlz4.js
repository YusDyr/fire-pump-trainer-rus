const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1400,height:900}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(1000);
const st=async()=>p.evaluate(()=>[document.getElementById('zBadge').textContent,document.getElementById('scene').style.transform,document.getElementById('ph_loupe')?.style.display]);
await p.click('#loupeT');await p.waitForTimeout(200);console.log('loupe',await st());
await p.click('#zoomSeg [data-zoom=in]');await p.waitForTimeout(200);console.log('+',await st());
await p.click('#zoomSeg [data-zoom=in]');await p.waitForTimeout(200);console.log('+',await st());
await p.click('#zoomSeg [data-zoom=out]');await p.waitForTimeout(200);console.log('-',await st());
await p.click('#zoomSeg [data-zoom=fit]');await p.waitForTimeout(200);console.log('fit',await st());
// ctrl+wheel
const bb=await (await p.$('#scene')).boundingBox();await p.mouse.move(bb.x+bb.width*0.7,bb.y+bb.height*0.6);await p.keyboard.down('Control');await p.mouse.wheel(0,-200);await p.keyboard.up('Control');await p.waitForTimeout(200);console.log('wheel',await st());
console.log(errs);await b.close()})();
