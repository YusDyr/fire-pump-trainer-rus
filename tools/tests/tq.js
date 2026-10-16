const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message+' '+(e.stack||'').slice(0,300)));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(500);console.log(errs);await b.close()})();
