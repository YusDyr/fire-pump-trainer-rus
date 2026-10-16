const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});
const p=await b.newPage({viewport:{width:1400,height:1000}});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/test.html');await p.waitForTimeout(600);
const res=await p.evaluate(()=>{const T=window.__T,out={};
 for(const key of Object.keys(T.LESSONS)){const n=T.LESSONS[key].steps.length;const r=[];
  // natural completion check: jump to last step, then test whether each step auto-completed (not forced)
  T.fresh(key);let forced=[];
  for(let k=0;k<n;k++){const st=T.LESSONS[key].steps[k];if(!st.ok&&!st.hold){T.S.lesson.i++;continue}
    const i0=T.S.lesson.i;let c=0;const cap=st.need?st.need*10+900:2500;while(T.S.lesson&&T.S.lesson.i===i0&&c<cap&&!T.S.dead){if(st.go)st.go();T.step(0.1);c++}
    T.S.purge=false;T.S.reel=false;
    if(T.S.dead){forced.push('DEAD@'+(k+1));break}
    if(T.S.lesson&&T.S.lesson.i===i0){forced.push(k+1);T.S.lesson.i++}}
  out[key]={n,forced:forced.join(','),score:T.S.score,pen:Object.keys(T.S.pen).join(',')};}
 return out});
console.log(JSON.stringify(res,null,1));console.log(errs);await b.close()})();
