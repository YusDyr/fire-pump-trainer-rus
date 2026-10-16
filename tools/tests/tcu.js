const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1300,height:900}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(600);
await p.evaluate(()=>{window.__T.S.v.tank=true});
// режим Крупно, клик по затвору
await p.click('#cuT');
await p.evaluate(()=>document.getElementById('sc_tank').scrollIntoView({block:'center'}));await p.waitForTimeout(200);
const bb=await (await p.$('#sc_tank circle.ring')).boundingBox();await p.mouse.click(bb.x+bb.width/2,bb.y+bb.height/2);
await p.waitForTimeout(1500);await p.screenshot({path:'cu1.png'});
console.log(await p.evaluate(()=>[document.getElementById('cuTitle').textContent,document.getElementById('cuSub').textContent,window.__T.S.v.tank]));
// zoom
await p.mouse.move(650,450);for(let i=0;i<5;i++){await p.mouse.wheel(0,-200);await p.waitForTimeout(50)}
await p.waitForTimeout(300);await p.screenshot({path:'cu2.png'});
await p.keyboard.press('Escape');await p.click('#cuT');
// правая кнопка по левому маховику
await p.evaluate(()=>{window.__T.S.v.out[0]=0.3});await p.waitForTimeout(200);
await p.evaluate(()=>document.getElementById('sc_w0').scrollIntoView({block:'center'}));
const b2=await (await p.$('#sc_w0 circle.ring')).boundingBox();await p.mouse.click(b2.x+b2.width/2,b2.y+b2.height/2,{button:'right'});
await p.waitForTimeout(1500);await p.screenshot({path:'cu3.png'});
console.log(await p.evaluate(()=>[document.getElementById('cuTitle').textContent,document.getElementById('cuSub').textContent]));
console.log(errs);await b.close()})();
