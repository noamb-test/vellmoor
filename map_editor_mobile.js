/* ============ Map maker: phone and tablet layout ============
   - Tools and the settings panel become slide-up sheets with a bottom bar.
   - One finger uses the current tool. Two fingers pan and pinch-zoom.
   - Buttons stand in for the keyboard: Delete, Copy, Paste, Shift, arrows, Esc. */
(function(){
'use strict';
const $=s=>document.querySelector(s);
const app=$('#app'),stage=$('#stage'),cv=$('#cv'),L=$('#left'),R=$('#right');
let pref=null;try{pref=localStorage.getItem('vme_layout')}catch(e){}
const auto=()=>innerWidth<=820||(matchMedia('(pointer:coarse)').matches&&innerWidth<=1100);
const isMob=()=>pref==='mobile'||(pref!=='desktop'&&auto());

/* ---------- styles ---------- */
const css=document.createElement('style');css.textContent=`
#stage{touch-action:none}
#mbar,#mnav{display:none}
body.mob,html:has(body.mob){height:100dvh}
body.mob #app{grid-template-columns:1fr;grid-template-rows:auto 1fr auto auto;height:100dvh;padding-top:env(safe-area-inset-top)}
body.mob #top{grid-column:1;overflow-x:auto;overflow-y:hidden;flex-wrap:nowrap;padding:6px 8px;gap:5px;scrollbar-width:none;min-height:46px}
body.mob #top::-webkit-scrollbar{display:none}
body.mob #top>*{flex:none}
body.mob #top h1{font-size:13px;margin:0 4px 0 0}
body.mob #top .sp{flex:1 0 6px}
body.mob #status{display:none}
body.mob button{padding:8px 11px;font-size:14px;border-radius:9px}
body.mob select,body.mob input,body.mob textarea{font-size:16px;padding:7px 8px}
body.mob #left,body.mob #right{position:fixed;left:0;right:0;bottom:var(--mnavh,108px);max-height:55vh;z-index:6;
  border:1px solid var(--line);border-bottom:none;border-radius:16px 16px 0 0;box-shadow:0 -10px 30px #0008;padding:6px 12px 14px;
  transform:translateY(120%);transition:transform .22s ease;overscroll-behavior:contain}
body.mob #left.open,body.mob #right.open{transform:none}
body.mob .msheetH{position:sticky;top:-6px;z-index:1;display:flex;align-items:center;gap:8px;background:var(--panel);margin:0 -12px 6px;padding:6px 12px 8px;border-bottom:1px solid var(--line)}
body.mob .msheetH b{flex:1;font-size:14px}
body.mob .msheetH i{display:block;position:absolute;left:50%;top:2px;width:38px;height:4px;margin-left:-19px;border-radius:3px;background:#4a5165}
body.mob .tools{grid-template-columns:repeat(4,1fr)}
body.mob .tools button{padding:10px 0;font-size:13px}
body.mob .kitgrid,body.mob .sw{grid-template-columns:repeat(3,1fr)}
body.mob #mbar{grid-column:1;display:flex;gap:6px;overflow-x:auto;padding:6px 8px;background:var(--panel);border-top:1px solid var(--line);scrollbar-width:none;z-index:7}
body.mob #mbar::-webkit-scrollbar{display:none}
body.mob #mbar>*{flex:none}
body.mob #mbar .gap{width:4px}
body.mob #mbar button{min-width:44px;padding:9px 10px}
body.mob #mbar button:disabled{opacity:.4}
body.mob #mnav{grid-column:1;display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:6px 8px calc(8px + env(safe-area-inset-bottom) + var(--mbot,0px));background:var(--panel);z-index:7}
body.mob #mnav button{padding:10px 4px;font-size:14px;font-weight:600}
body.mob #mnav small{display:block;font-weight:400;font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
body.mob #mnav button.on small{color:#cfe3ff}
body.mob #modal .box{width:96vw;max-height:88vh;padding:14px}
body.mob .rooms{max-height:58vh}
#mtip{position:fixed;left:50%;top:60px;transform:translateX(-50%);background:#000c;color:#fff;padding:7px 12px;border-radius:9px;font-size:13px;z-index:20;pointer-events:none;opacity:0;transition:opacity .2s;white-space:nowrap}
`;document.head.appendChild(css);
const vp=document.querySelector('meta[name=viewport]');if(vp)vp.content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover';

/* ---------- bars ---------- */
const bar=document.createElement('div');bar.id='mbar';
bar.innerHTML=`<button data-a="undo">↶ Undo</button><button data-a="redo">↷</button><span class="gap"></span>
<button data-a="shift" title="Acts like holding Shift: tap to select many, arrows stretch">⇧ Multi</button>
<button data-a="del">🗑 Delete</button><button data-a="copy">Copy</button><button data-a="paste">Paste</button><span class="gap"></span>
<button data-a="ArrowLeft">←</button><button data-a="ArrowUp">↑</button><button data-a="ArrowDown">↓</button><button data-a="ArrowRight">→</button><span class="gap"></span>
<button data-a="esc">Done</button><button data-a="fit">Fit</button><button data-a="zo">−</button><button data-a="zi">+</button>`;
const nav=document.createElement('div');nav.id='mnav';
nav.innerHTML=`<button data-s="left">Tools<small id="mTool">–</small></button><button data-s="right">Settings<small id="mSel">map</small></button><button data-s="pan">✋ Pan<small>1 finger</small></button><button data-s="more">More<small>layout</small></button>`;
app.appendChild(bar);app.appendChild(nav);
const tip=document.createElement('div');tip.id='mtip';document.body.appendChild(tip);
let tipT=0;function say(t){tip.textContent=t;tip.style.opacity=1;clearTimeout(tipT);tipT=setTimeout(()=>tip.style.opacity=0,1600)}
for(const[el,name]of[[L,'Tools'],[R,'Settings']]){const h=document.createElement('div');h.className='msheetH';h.innerHTML=`<i></i><b>${name}</b><button>Close</button>`;h.querySelector('button').onclick=()=>sheet(null);el.prepend(h)}
/* keep the sheet header when the panels redraw */
const keepHead=el=>new MutationObserver(()=>{const h=el.querySelector('.msheetH');if(h&&el.firstElementChild!==h)el.prepend(h)}).observe(el,{childList:true});
keepHead(L);keepHead(R);
/* R's content is rebuilt with innerHTML, which drops the header: put it back */
const headR=R.querySelector('.msheetH');new MutationObserver(()=>{if(!R.contains(headR))R.prepend(headR)}).observe(R,{childList:true});
const headL=L.querySelector('.msheetH');new MutationObserver(()=>{if(!L.contains(headL))L.prepend(headL)}).observe(L,{childList:true});

let open=null;
function sheet(which){open=open===which?null:which;L.classList.toggle('open',open==='left');R.classList.toggle('open',open==='right');
  nav.querySelectorAll('[data-s]').forEach(b=>b.classList.toggle('on',b.dataset.s===open||(b.dataset.s==='pan'&&panOn)))}
let panOn=false,shiftOn=false;
function setNavH(){document.documentElement.style.setProperty('--mnavh',(nav.offsetHeight+bar.offsetHeight)+'px')}

const key=(k,mods={})=>{const ev=new KeyboardEvent('keydown',Object.assign({key:k,bubbles:true,cancelable:true},mods));document.body.dispatchEvent(ev);
  document.body.dispatchEvent(new KeyboardEvent('keyup',Object.assign({key:k,bubbles:true},mods)))};
bar.onclick=e=>{const b=e.target.closest('button');if(!b)return;const a=b.dataset.a;
  if(a==='undo')return $('#bUndo').click();if(a==='redo')return $('#bRedo').click();
  if(a==='shift'){shiftOn=!shiftOn;b.classList.toggle('on',shiftOn);say(shiftOn?'Multi on: taps add to the selection, arrows stretch':'Multi off');return}
  if(a==='del')return key('Delete');
  if(a==='copy'){key('c',{ctrlKey:true});return say('Copied. Tap Paste, then tap where it goes')}
  if(a==='paste'){key('v',{ctrlKey:true});return say('Tap where you want to paste')}
  if(a.startsWith('Arrow'))return key(a,{shiftKey:shiftOn});
  if(a==='esc')return key('Escape');
  if(a==='fit')return key('0');if(a==='zi')return $('#bZi').click();if(a==='zo')return $('#bZo').click()};
nav.onclick=e=>{const b=e.target.closest('button');if(!b)return;const s=b.dataset.s;
  if(s==='pan'){panOn=!panOn;b.classList.toggle('on',panOn);say(panOn?'Drag with one finger to move the map':'Back to the tool');return}
  if(s==='more')return more();sheet(s)};
function more(){if(typeof modal!=='function')return;
  modal(`<h2>Phone layout</h2><p class="muted">Tips: two fingers move and zoom the map. Double-tap a building to go inside. “⇧ Multi” works like holding Shift.</p>
  <div class="row" style="margin-top:10px"><button id="lyM" class="${pref==='mobile'?'on':''}">Always phone</button><button id="lyA" class="${!pref?'on':''}">Automatic</button><button id="lyD" class="${pref==='desktop'?'on':''}">Always desktop</button></div>
  <div class="row" style="margin-top:12px"><button onclick="closeModal()">Close</button></div>`,box=>{
    const setP=v=>{pref=v;try{v?localStorage.setItem('vme_layout',v):localStorage.removeItem('vme_layout')}catch(e){}closeModal();apply()};
    box.querySelector('#lyM').onclick=()=>setP('mobile');box.querySelector('#lyA').onclick=()=>setP(null);box.querySelector('#lyD').onclick=()=>setP('desktop')})}
/* on desktop, a small button to switch to the phone layout */
const swb=document.createElement('button');swb.textContent='📱';swb.title='Phone layout';swb.onclick=()=>{if(isMob())more();else{pref='mobile';try{localStorage.setItem('vme_layout','mobile')}catch(e){}apply()}};
$('#top').appendChild(swb);

/* labels on the bottom bar */
function labels(){const t=document.querySelector('#tools button.on');$('#mTool').textContent=t?t.textContent.trim():'–';
  let s='map';try{const h=R.querySelector('.card h3,h3');if(h)s=h.textContent.trim()}catch(e){}$('#mSel').textContent=s}
new MutationObserver(labels).observe(L,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
new MutationObserver(labels).observe(R,{subtree:true,childList:true});

/* iPhone Safari's floating address bar covers the bottom of the page: leave room for it */
const iosSafari=/iP(hone|ad|od)/.test(navigator.userAgent)&&!navigator.standalone&&!matchMedia('(display-mode: standalone)').matches;
document.documentElement.style.setProperty('--mbot',iosSafari?'62px':'0px');
function apply(){const on=isMob();document.body.classList.toggle('mob',on);if(!on){L.classList.remove('open');R.classList.remove('open');open=null}
  setTimeout(()=>{setNavH();try{if(typeof M!=='undefined'&&M){fit();renderAll()}}catch(e){}labels()},50)}
addEventListener('resize',()=>{const was=document.body.classList.contains('mob');if(was!==isMob())apply();else setNavH()});
apply();

/* ---------- touch: 1 finger = tool, 2 fingers = pan + pinch ---------- */
const pts=new Map();let pend=null,live=null,gest=null;const HOLD=80;
const init=(e,o={})=>({bubbles:true,cancelable:true,composed:true,pointerId:e.pointerId,pointerType:'touch',isPrimary:true,clientX:e.clientX,clientY:e.clientY,screenX:e.screenX,screenY:e.screenY,
  button:0,buttons:o.up?0:1,shiftKey:shiftOn,ctrlKey:false,altKey:false,width:e.width,height:e.height,pressure:o.up?0:.5});
function fire(type,target,e,o){const ev=new PointerEvent(type,init(e,o));ev._vmeSyn=true;(target||cv).dispatchEvent(ev)}
function startTool(){if(!pend)return;const p=pend;pend=null;clearTimeout(p.t);live={id:p.id,target:p.target};
  if(panOn){gest={pan1:true,id:p.id,sx:p.e.clientX,sy:p.e.clientY,cx:camX,cy:camY};live=null;return}
  fire('pointerdown',p.target,p.e)}
function inStage(e){return stage.contains(e.target)}
function begin2(){const[a,b]=[...pts.values()];const r=stage.getBoundingClientRect();const cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top;
  gest={d0:Math.hypot(a.x-b.x,a.y-b.y)||1,z0:zoom,wx:(cx-camX)/zoom,wy:(cy-camY)/zoom}}
addEventListener('pointerdown',e=>{if(e._vmeSyn||e.pointerType!=='touch'||!inStage(e)||typeof M==='undefined'||!M)return;
  e.stopImmediatePropagation();e.preventDefault();if(open&&isMob())sheet(null);
  if(e.isPrimary){pts.clear();gest=null;if(pend){clearTimeout(pend.t);pend=null}live=null}
  pts.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pts.size===1){pend={id:e.pointerId,e,target:e.target,t:setTimeout(startTool,HOLD)};return}
  /* second finger: cancel or finish the one-finger action, then pan/zoom */
  if(pend){clearTimeout(pend.t);pend=null}
  if(live){fire('pointerup',live.target,e,{up:true});live=null}
  if(pts.size===2)begin2()},true);
addEventListener('pointermove',e=>{if(e._vmeSyn||e.pointerType!=='touch')return;if(!pts.has(e.pointerId))return;
  pts.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pend&&pend.id===e.pointerId){const dx=e.clientX-pend.e.clientX,dy=e.clientY-pend.e.clientY;e.stopImmediatePropagation();if(dx*dx+dy*dy>64)startTool();else return}
  if(gest&&gest.pan1){e.stopImmediatePropagation();camX=gest.cx+e.clientX-gest.sx;camY=gest.cy+e.clientY-gest.sy;cv.style.left=camX+'px';cv.style.top=camY+'px';return}
  if(gest&&pts.size>=2){e.stopImmediatePropagation();const[a,b]=[...pts.values()];const r=stage.getBoundingClientRect();const cx=(a.x+b.x)/2-r.left,cy=(a.y+b.y)/2-r.top;
    const z=Math.max(.5,Math.min(6,gest.z0*Math.hypot(a.x-b.x,a.y-b.y)/gest.d0));camX=cx-gest.wx*z;camY=cy-gest.wy*z;
    if(Math.abs(z-zoom)>.01){zoom=z;const zv=$('#zoomv');if(zv)zv.textContent=Math.round(zoom*100)+'%';renderAll()}else{cv.style.left=camX+'px';cv.style.top=camY+'px'}return}
  if(gest)e.stopImmediatePropagation()},true);
function end(e){if(e._vmeSyn||e.pointerType!=='touch'||!pts.has(e.pointerId))return;pts.delete(e.pointerId);
  if(pend&&pend.id===e.pointerId){startTool();live=null;/* quick tap: the real up goes on to the tool */if(gest&&gest.pan1){gest=null;e.stopImmediatePropagation()}return}
  if(gest){e.stopImmediatePropagation();if(!pts.size){gest=null;if(typeof renderAll==='function')renderAll()}else if(pts.size===1&&!gest.pan1){/* lift one of two fingers: keep waiting until both lift */}return}
  if(gest&&gest.pan1&&gest.id===e.pointerId){gest=null;e.stopImmediatePropagation();return}
  if(live&&live.id===e.pointerId)live=null}
addEventListener('pointerup',end,true);addEventListener('pointercancel',e=>{if(pts.has(e.pointerId)&&live&&live.id===e.pointerId){fire('pointerup',live.target,e,{up:true});live=null}end(e)},true);
/* stop the page itself from scrolling or zooming under the map */
stage.addEventListener('touchmove',e=>e.preventDefault(),{passive:false});
document.addEventListener('gesturestart',e=>e.preventDefault());
})();
