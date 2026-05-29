#!/usr/bin/env python3
"""把 maps/*.html 升级到 v0.6：① 去水彩 ② 打卡点配缩略图"""
import re
from pathlib import Path

MAPS_DIR = Path(__file__).parent.parent / "maps"

# ============ Phase A: 去水彩 ============

def remove_watercolor(html: str) -> str:
    # 1. 删水彩按钮
    html = re.sub(
        r'<button class="style-btn active" data-style="watercolor"[^>]*>[^<]*</button>\s*',
        '',
        html
    )
    # 2. clean 按钮变成 active
    html = re.sub(
        r'<button class="style-btn" data-style="clean"',
        '<button class="style-btn active" data-style="clean"',
        html
    )
    # 3. CSS 去掉默认 sepia 滤镜
    html = re.sub(
        r'\.leaflet-tile-pane\s*\{[^}]*filter:\s*sepia[^}]*\}',
        '.leaflet-tile-pane { transition: filter 0.3s ease; }',
        html
    )
    # 4. 去掉 .no-filter 规则（不再需要）
    html = re.sub(
        r'\.map-wrap\.no-filter\s*\.leaflet-tile-pane\s*\{[^}]*\}\s*',
        '',
        html
    )
    # 5. switchStyle 函数简化
    html = re.sub(
        r'wrap\.classList\.remove\([\'"]no-filter[\'"],\s*[\'"]topo[\'"]\);[\s\n]*if \(style === [\'"]topo[\'"]\) \{[^}]+\}[\s\n]*else if \(style === [\'"]clean[\'"]\) \{[^}]+\}[\s\n]*else \{[^}]+\}',
        'wrap.classList.remove(\'topo\');\n  if (style === \'topo\') { currentTile = TILES.topo.addTo(map); wrap.classList.add(\'topo\'); }\n  else { currentTile = TILES.voyager.addTo(map); }',
        html, flags=re.DOTALL
    )
    return html


# ============ Phase B: 打卡点配缩略图 ============

SPOT_CARD_CSS = """
  .spot-card { display: flex; gap: 10px; padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.5); border-left: 3px solid var(--accent, #b04060); margin-bottom: 6px; align-items: center; transition: all 0.15s; }
  .spot-card:hover { background: rgba(255,255,255,0.85); transform: translateX(2px); }
  .spot-thumb { width: 64px; height: 64px; object-fit: cover; border-radius: 6px; flex-shrink: 0; cursor: pointer; background: rgba(0,0,0,0.08); transition: transform 0.2s; }
  .spot-thumb:hover { transform: scale(1.05); }
  .spot-thumb.empty { display: flex; align-items: center; justify-content: center; font-size: 28px; }
  .spot-thumb.loading { display: flex; align-items: center; justify-content: center; }
  .spot-thumb.loading::after { content: ''; width: 16px; height: 16px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; opacity: 0.5; animation: spin 0.8s linear infinite; }
  .spot-body { flex: 1; min-width: 0; }
  .spot-text { font-size: 12.5px; line-height: 1.4; margin-bottom: 4px; font-weight: 500; }
  .spot-more { font-size: 10px; text-decoration: none; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,0.05); display: inline-block; }
  .spot-more:hover { background: rgba(0,0,0,0.12); }
"""

RENDER_PHOTO_SPOTS_JS = """
async function renderPhotoSpots(poi) {
  const container = document.getElementById('pdPhotoSpots');
  const spots = poi.photo_spots.map(s => typeof s === 'string' ? { text: s, query: null } : s);
  container.innerHTML = spots.map((s, i) => {
    const gImg = `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(s.query || (poi.en + ' ' + s.text.replace(/^📸\\s*/, '').slice(0, 25)))}`;
    return `<div class="spot-card" data-idx="${i}">
      <div class="spot-thumb loading"></div>
      <div class="spot-body"><div class="spot-text">${s.text}</div><a class="spot-more" href="${gImg}" target="_blank" onclick="event.stopPropagation();">🔍 搜更多</a></div>
    </div>`;
  }).join('');
  for (let i = 0; i < spots.length; i++) {
    const s = spots[i];
    const stripped = s.text.replace(/^📸\\s*/, '').replace(/[（(].*?[）)]/g, '').trim();
    const q = s.query || `${poi.en} ${stripped}`;
    try {
      let imgs = await fetchWikipediaImages(q, 1);
      if (!imgs.length) imgs = await fetchCommonsImages(q, 1);
      const card = container.querySelector(`[data-idx="${i}"]`);
      if (!card) continue;
      const thumbEl = card.querySelector('.spot-thumb');
      if (imgs[0]) {
        const url = imgs[0].replace(/"/g, '&quot;');
        thumbEl.outerHTML = `<img class="spot-thumb" src="${url}" loading="lazy" onclick="openLightbox('${url}'); event.stopPropagation();" onerror="this.outerHTML='<div class=\\\\'spot-thumb empty\\\\'>${poi.icon}</div>'">`;
      } else {
        thumbEl.className = 'spot-thumb empty';
        thumbEl.innerHTML = poi.icon;
      }
    } catch (e) {}
  }
}
"""


def add_photo_spots_thumbnails(html: str) -> str:
    # 1. ul → div
    html = re.sub(
        r'<ul id="pdPhotoSpots"></ul>',
        '<div id="pdPhotoSpots"></div>',
        html
    )
    # 2. 替换渲染逻辑：从 .map(s => `<li>${s}</li>`).join('') 改成 renderPhotoSpots(p)
    # 匹配各种格式（紧凑或多行）
    patterns = [
        # 多行格式
        (
            r"if \(p\.photo_spots\?\.length\) \{\s*photoSection\.style\.display = 'block';\s*document\.getElementById\('pdPhotoSpots'\)\.innerHTML = p\.photo_spots\.map\(s => `<li>\$\{s\}</li>`\)\.join\(''\);\s*\}",
            "if (p.photo_spots?.length) { photoSection.style.display = 'block'; renderPhotoSpots(p); }",
        ),
        # 单行紧凑格式
        (
            r"if \(p\.photo_spots\?\.length\) \{ photoSection\.style\.display = 'block'; document\.getElementById\('pdPhotoSpots'\)\.innerHTML = p\.photo_spots\.map\(s => `<li>\$\{s\}</li>`\)\.join\(''\); \}",
            "if (p.photo_spots?.length) { photoSection.style.display = 'block'; renderPhotoSpots(p); }",
        ),
    ]
    for pat, rep in patterns:
        html = re.sub(pat, rep, html)

    # 3. 注入 spot-card CSS（在 </style> 前）
    if "spot-card" not in html:
        html = html.replace('</style>', SPOT_CARD_CSS + '\n</style>', 1)

    # 4. 注入 renderPhotoSpots 函数（在 closeLightbox 后）
    if "renderPhotoSpots" not in html:
        marker = "window.closeLightbox = function() { document.getElementById('lightbox').classList.remove('show'); };"
        if marker in html:
            html = html.replace(marker, marker + "\n" + RENDER_PHOTO_SPOTS_JS, 1)

    return html


def migrate_file(path: Path) -> dict:
    src = path.read_text(encoding='utf-8')
    out = remove_watercolor(src)
    out = add_photo_spots_thumbnails(out)
    changed = (out != src)
    if changed:
        path.write_text(out, encoding='utf-8')
    return {
        "file": path.name,
        "changed": changed,
        "size_before_kb": len(src) // 1024,
        "size_after_kb": len(out) // 1024,
    }


if __name__ == "__main__":
    print("🔄 升级所有 maps/*.html → v0.6（去水彩 + 打卡点缩略图）\n")
    files = sorted(MAPS_DIR.glob("*.html"))
    for f in files:
        r = migrate_file(f)
        flag = "✅" if r["changed"] else "⏭️  "
        print(f"  {flag} {r['file']:30s} {r['size_before_kb']}KB → {r['size_after_kb']}KB")
    print(f"\n完成 · {len(files)} 个文件已处理")
