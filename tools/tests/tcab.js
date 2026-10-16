const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
for(const [w,h,n] of [[1400,900,'cab_d.png'],[390,844,'cab_m.png']]){
const p=await b.newPage({viewport:{width:w,height:h}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(700);
await p.screenshot({path:n});console.log(n,errs);await p.close()}
await b.close()})();
