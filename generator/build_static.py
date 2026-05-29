#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiveMap 静态分享版构建器
========================
把 livemap/ 打包成纯静态 dist/，可直接部署到 GitHub Pages / Netlify / Vercel。
任何人都能浏览 Hub 画廊 + 所有已生成地图；AI 实时生成会优雅降级为「请本地运行」提示
（静态站点没有后端、不暴露 API key）。

用法：
    cd generator
    python3 build_static.py          # 输出到 ../dist
    python3 build_static.py --out /some/path

部署（GitHub Pages）：
    见 ../DEPLOY.md
"""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # livemap/
MAPS_DIR = ROOT / "maps"


def collect_maps():
    maps = []
    for f in sorted(MAPS_DIR.glob("*.html")):
        maps.append({
            "name": f.stem,
            "url": f"maps/{f.name}",          # 静态版用相对路径
            "size_kb": f.stat().st_size // 1024,
            "mtime": int(f.stat().st_mtime),
        })
    return maps


def build(out_dir: Path):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # 1. 拷贝地图
    shutil.copytree(MAPS_DIR, out_dir / "maps")

    # 2. 拷贝 PRD（Hub 底部有链接）
    for extra in ["PRD_LiveMap.md", "README.md"]:
        src = ROOT / extra
        if src.exists():
            shutil.copy(src, out_dir / extra)

    # 3. 处理 index.html：注入静态标志 + 地图列表
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    maps = collect_maps()
    inject = (
        "<script>window.STATIC_DEPLOY=true;window.STATIC_MAPS="
        + json.dumps(maps, ensure_ascii=False)
        + ";</script>\n"
    )
    # 注入到 </head> 之前，确保在主脚本之前执行
    if "</head>" in html:
        html = html.replace("</head>", inject + "</head>", 1)
    else:
        html = inject + html
    # 静态版的硬编码热门链接 / PRD 链接保持相对路径即可（本来就是相对的）
    (out_dir / "index.html").write_text(html, encoding="utf-8")

    # 4. GitHub Pages 不要 Jekyll 处理（否则下划线开头文件会被忽略）
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")

    print(f"✅ 静态站点已构建：{out_dir}")
    print(f"   - index.html（已注入 {len(maps)} 张地图列表）")
    print(f"   - maps/ {len(maps)} 张")
    print(f"   本地预览： cd {out_dir} && python3 -m http.server 8000")
    return maps


def main():
    ap = argparse.ArgumentParser(description="LiveMap 静态分享版构建器")
    ap.add_argument("--out", default=str(ROOT / "dist"), help="输出目录（默认 ../dist）")
    args = ap.parse_args()
    build(Path(args.out))


if __name__ == "__main__":
    main()
