// 全量地图 UI 审计：用 Chromium 真实渲染，像用户一样逐天切换（含「全部」总览），
// 在多个视口宽度下，只测量「当前真正可见」的标签/胶囊/日签，检测重叠与超界。
// 用法：node tools/audit_maps.mjs   （需本机 http://localhost:8000 提供 dist/）
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'http://localhost:8000/maps';
const MAPS_DIR = '/Users/bytedance/xunzhi/livemap/dist/maps';
const VIEWPORTS = process.env.VP === 'both'
  ? [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]
  : [{ width: 1920, height: 1080 }];
const files = fs.readdirSync(MAPS_DIR).filter(f => f.endsWith('.html')).sort();

// 切到某天（直接驱动真实逻辑）。'all' = 全部总览
const switchDay = (d) => { /* eslint-disable */ currentDay = String(d); filterPOIs(); };

// 测量当前可见标签/胶囊/日签的重叠与超界（按父链有效可见性，反映真实状态）
const measure = () => {
  const mapEl = document.querySelector('.leaflet-container') || document.getElementById('map');
  const mapRect = mapEl.getBoundingClientRect();
  // 有效可见：沿父链累乘 opacity，任何祖先 display:none / visibility:hidden / opacity:0 都算不可见
  const vis = (el) => {
    let n = el;
    while (n && n !== document.body) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
      n = n.parentElement;
    }
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const items = [];
  const grab = (sel, kind) => document.querySelectorAll(sel).forEach(el => {
    if (vis(el)) items.push({ kind, label: (el.textContent || '').trim().slice(0, 18) || kind, r: el.getBoundingClientRect() });
  });
  grab('.leaflet-tooltip.poi-tip', 'name'); // 单日：景点名标签
  grab('.seg-label', 'seg');                // 单日：车程胶囊
  grab('.day-flag', 'flag');                // 总览：每日日签
  const overlaps = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const a = items[i].r, b = items[j].r;
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 2 && oy > 2) overlaps.push({ a: `${items[i].kind}:${items[i].label}`, b: `${items[j].kind}:${items[j].label}`, px: Math.round(Math.min(ox, oy)) });
  }
  const clipped = items.filter(it => it.r.left < mapRect.left - 2 || it.r.right > mapRect.right + 2 || it.r.top < mapRect.top - 2 || it.r.bottom > mapRect.bottom + 2).map(it => `${it.kind}:${it.label}`);
  return { visCount: items.length, overlaps, clipped };
};

const browser = await chromium.launch();
let totalOverlap = 0, totalClip = 0, totalErr = 0;
const report = [];

for (const f of files) {
  let mapOv = 0, mapClip = 0; const lines = [];
  for (const vp of VIEWPORTS) {
    const page = await browser.newPage({ viewport: vp });
    try {
      await page.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForFunction(() => {
        try { return typeof POIs !== 'undefined' && typeof markers !== 'undefined' && typeof filterPOIs === 'function' && typeof currentDay !== 'undefined' && Object.keys(markers).length > 0; }
        catch (e) { return false; } // 词法绑定 TDZ：脚本尚未执行到声明处，继续轮询
      }, { timeout: 20000 });
      await page.waitForTimeout(300);
      const days = await page.evaluate(() => ['all', ...new Set(POIs.map(p => p.day))].sort((a, b) => (a === 'all' ? -1 : b === 'all' ? 1 : a - b)));
      for (const d of days) {
        await page.evaluate(switchDay, d);
        await page.waitForTimeout(650); // 等 fitBounds 动画 + moveend declutter
        const m = await page.evaluate(measure);
        mapOv += m.overlaps.length; mapClip += m.clipped.length;
        if (m.overlaps.length || m.clipped.length) {
          lines.push(`    [w${vp.width}] Day${d}: 可见${m.visCount}` +
            (m.overlaps.length ? ` | 重叠${m.overlaps.length}: ${m.overlaps.map(o => `${o.a}×${o.b}(${o.px})`).join(', ')}` : '') +
            (m.clipped.length ? ` | 超界: ${m.clipped.join(',')}` : ''));
        }
      }
    } catch (e) { totalErr++; lines.push(`    [w${vp.width}] ERROR: ${e.message}`); }
    await page.close();
  }
  totalOverlap += mapOv; totalClip += mapClip;
  report.push(`${(mapOv || mapClip) ? '⚠' : '✓'} ${f}  (重叠${mapOv} 超界${mapClip})`);
  lines.forEach(l => report.push(l));
}

await browser.close();
console.log(report.join('\n'));
console.log(`\n==== 汇总：${files.length} 张图 × ${VIEWPORTS.length} 视口 | 重叠对=${totalOverlap} 超界=${totalClip} 错误=${totalErr} ====`);
