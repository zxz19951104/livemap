import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1 });
const errs=[];
p.on('console', m=>{ if(m.type()==='error') errs.push(m.text()); });
await p.goto('http://localhost:8000/maps/yellowstone_5d.html', { waitUntil: 'networkidle', timeout: 30000 });
await p.waitForFunction(()=>typeof generatePoster==='function' && typeof QRCode!=='undefined' && typeof html2canvas!=='undefined', {timeout:15000});
await p.click('#posterFab');
await p.waitForSelector('#posterModal.show', {timeout:8000});
await p.waitForTimeout(1200); // 等 postcard 图 + QR
const info = await p.evaluate(()=>{
  const qr=document.querySelector('#posterQR img,#posterQR canvas');
  const bg=document.querySelector('#posterStage .ps-bg');
  return { qr: !!qr, bgStyle:(bg&&bg.getAttribute('style')||'').slice(0,60), rows:document.querySelectorAll('#posterStage .ps-row').length, spots:document.querySelectorAll('#posterStage .ps-spot').length };
});
console.log('MODAL:', JSON.stringify(info));
// 测试 html2canvas 真能出图
const dataLen = await p.evaluate(async ()=>{
  const c = await html2canvas(document.querySelector('#posterStage .ps-root'),{useCORS:true,backgroundColor:null,scale:1,width:1080,height:1440});
  return c.toDataURL('image/png').length;
});
console.log('html2canvas PNG dataURL 长度:', dataLen);
await p.screenshot({ path: '/tmp/livemap_qa/poster_modal.png' });
console.log('CONSOLE ERRORS:', errs.length, errs.slice(0,3).join(' | '));
await b.close();
