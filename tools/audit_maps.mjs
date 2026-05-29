// 全量地图 UI 审计：用 Chromium 真实渲染，像用户一样逐天切换，
// 只测量「当前真正可见」的标签/胶囊，检测重叠与超界。
// 用法：node tools/audit_maps.mjs   （需本机 http://localhost:8000 提供 dist/）
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = 'http://localhost:8000/maps';
const MAPS_DIR = '/Users/bytedance/xunzhi/livemap/dist/maps';
const files = fs.readdirSync(MAPS_DIR).filter(f => f.endsWith('.html')).sort();

// 切到某天（直接驱动真实逻辑）
const switchDay = (d) => { /* eslint-disable */ currentDay = String(d); filterPOIs(); };

// 测量当前可见标签/胶囊的重叠与超界（不强制显示，反映真实状态）
const measure = () => {
  const mapEl = document.querySelector('.leaflet-container') || document.getElementById('map');
  const mapRect = mapEl.getBoundingClientRect();
  const vis = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const items = [];
  document.querySelectorAll('.leaflet-tooltip.poi-tip').forEach(el => {
    if (vis(el)) items.push({ kind: 'name', label: (el.textContent || '').trim().slice(0, 18), r: el.getBoundingClientRect() });
  });
  document.querySelectorAll('.seg-label').forEach(el => {
    if (vis(el)) items.push({ kind: 'seg', label: 'seg', r: el.getBoundingClientRect() });
  });
  const overlaps = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const a = items[i].r, b = items[j].r;
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 2 && oy > 2) overlaps.push({ a: items[i].label, b: items[j].label, px: Math.round(Math.min(ox, oy)) });
  }
  const clipped = items.filter(it => it.r.left < mapRect.left - 2 || it.r.right > mapRect.right + 2 || it.r.top < mapRect.top - 2 || it.r.bottom > mapRect.bottom + 2).map(it => it.label);
  const names = items.filter(i => i.kind === 'name').length;
  const segs = items.filter(i => i.kind === 'seg').length;
  return { names, segs, overlaps, clipped };
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
let totalOverlap = 0, totalClip = 0, totalErr = 0, totalHidden = 0;
const report = [];

for (const f of files) {
  try {
    await page.goto(`${BASE}/${f}`, { waitUntil: 'networkidle', timeout: 20000 });
    await page.waitForFunction(() => typeof POIs !== 'undefined' && typeof markers !== 'undefined' && typeof filterPOIs === 'function' && Object.keys(markers).length > 0, { timeout: 10000 }).catch(() => {});
    const days = await page.evaluate(() => [...new Set(POIs.map(p => p.day))].sort((a, b) => a - b));
    const lines = []; let mapOv = 0, mapClip = 0, mapHidden = 0;
    for (const d of days) {
      const total = await page.evaluate((dd) => POIs.filter(p => p.day === dd).length, d);
      await page.evaluate(switchDay, d);
      await page.waitForTimeout(550); // 等 fitBounds 动画 + moveend declutter
      const m = await page.evaluate(measure);
      const hidden = total - m.names;
      mapOv += m.overlaps.length; mapClip += m.clipped.length; mapHidden += Math.max(0, hidden);
      if (m.overlaps.length || m.clipped.length) {
        lines.push(`    Day${d}: 可见${m.names}/${total}名·${m.segs}胶囊` +
          (m.overlaps.length ? ` | 重叠${m.overlaps.length}: ${m.overlaps.map(o => `${o.a}×${o.b}(${o.px})`).join(', ')}` : '') +
          (m.clipped.length ? ` | 超界: ${m.clipped.join(',')}` : ''));
      }
    }
    totalOverlap += mapOv; totalClip += mapClip; totalHidden += mapHidden;
    const status = (mapOv || mapClip) ? '⚠' : '✓';
    report.push(`${status} ${f}  (重叠${mapOv} 超界${mapClip} 隐藏名${mapHidden})`);
    lines.forEach(l => report.push(l));
  } catch (e) { totalErr++; report.push(`✗ ${f}  ERROR: ${e.message}`); }
}

await browser.close();
console.log(report.join('\n'));
console.log(`\n==== 汇总：${files.length} 张图 | 重叠对=${totalOverlap} 超界=${totalClip} 隐藏名标签=${totalHidden} 错误图=${totalErr} ====`);
