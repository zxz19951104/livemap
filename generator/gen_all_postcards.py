#!/usr/bin/env python3
"""批量为每张地图生成 AI 卡通明信片底图 → assets/postcards/<slug>.png。
变体图（×4 模式）复用同一张，省 token。已存在的跳过。"""
import os, sys, subprocess, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "postcards"
OUT.mkdir(parents=True, exist_ok=True)

# (slug, 英文场景描述, [复用到这些 slug])
JOBS = [
    ("acadia_3d", "Acadia National Park Maine, rugged Atlantic granite coastline, red-roofed lighthouse, lobster boats, autumn maple forest, Cadillac Mountain sunrise", []),
    ("alaska_5d", "Alaska wilderness, snow-capped Denali mountain range, blue glaciers, moose and grizzly bear, spruce forest, northern lights", ["alaska_loop_7d", "alaska_loop_budget_7d", "alaska_loop_j_7d", "alaska_loop_middle_7d"]),
    ("barcelona_4d", "Barcelona Spain, Sagrada Familia cathedral, colorful Gaudi mosaic, Park Guell, Mediterranean beach, sunny", []),
    ("big_island_7d", "Hawaii Big Island, erupting volcano with glowing lava, black sand beach, palm trees, turquoise ocean, tropical", []),
    ("california_desert_4d", "California desert, Joshua trees, Death Valley sand dunes, cactus, red rock formations, starry desert sky", []),
    ("chiangmai_3d", "Chiang Mai Thailand, golden Buddhist temples, floating lanterns festival, elephants, misty mountains, tropical", []),
    ("glacier_4d", "Glacier National Park Montana, turquoise alpine lakes, jagged snowy peaks, mountain goat, pine forest", []),
    ("great_smoky_3d", "Great Smoky Mountains, misty blue layered ridges, dense forest, black bear, waterfalls, autumn colors", []),
    ("hokkaido_5d", "Hokkaido Japan, purple lavender fields, snowy mountains, Sapporo clock tower, Otaru canal at dusk", []),
    ("kyoto_6d", "Kyoto Japan, red torii gate tunnel, bamboo grove, golden pavilion temple, geisha, cherry blossom", ["kyoto_budget_5d"]),
    ("orlando_5d", "Orlando theme park, fairytale castle, roller coaster, palm trees, fireworks at night, fun", []),
    ("osaka_budget_3d", "Osaka Japan, Dotonbori neon signs, street food takoyaki, Osaka castle, lively night", []),
    ("pacific_northwest_7d", "Pacific Northwest USA, Mount Rainier, Seattle Space Needle, evergreen forest, rugged coastline", []),
    ("rocky_mountain_3d", "Rocky Mountain National Park Colorado, snowy peaks, elk, alpine lake, aspen trees, mountain road", []),
    ("seoul_3d", "Seoul Korea, Gyeongbokgung palace, N Seoul Tower, cherry blossoms, street food, modern skyline", []),
    ("sierra_nevada_5d", "Yosemite Sierra Nevada California, granite cliffs El Capitan, waterfalls, giant sequoia trees, valley", []),
    ("southwest_8d", "American Southwest, Zion red cliffs, Bryce Canyon hoodoos, Monument Valley buttes, desert highway, sunset", ["southwest_budget_8d", "southwest_j_8d", "southwest_middle_8d"]),
    ("usnp_top20_5d", "American National Parks, erupting geyser, grand canyon, granite peaks, bison, desert arch, scenic montage", []),
    ("yellowstone_teton_6d", "Grand Teton and Yellowstone, jagged Teton peaks reflected in lake, bison, geyser, evergreen forest", []),
    ("lassen_volcanic_3d", "Lassen Volcanic National Park California, volcanic peak, steaming sulphur fumaroles, alpine lake, pine forest, wildflowers", []),
    # yellowstone_5d 已有 → 仅复用
    ("yellowstone_5d", None, ["yellowstone_j_5d"]),
]

ok, skip, fail = [], [], []
for slug, prompt, aliases in JOBS:
    dst = OUT / f"{slug}.png"
    if prompt is not None:
        if dst.exists():
            skip.append(slug)
        else:
            print(f"🎨 生成 {slug} ...")
            r = subprocess.run([sys.executable, str(HERE / "gen_postcard.py"), prompt, str(dst)],
                               capture_output=True, text=True)
            if dst.exists():
                ok.append(slug)
            else:
                fail.append(slug); print(f"   ✗ {slug}: {r.stdout.strip()[-200:]} {r.stderr.strip()[-200:]}")
                continue
    # 复用到变体
    for al in aliases:
        ad = OUT / f"{al}.png"
        if dst.exists() and not ad.exists():
            shutil.copy(dst, ad); print(f"   ↳ 复用 {slug} → {al}")

print(f"\n✅ 生成 {len(ok)} | 跳过(已存在) {len(skip)} | 失败 {len(fail)}")
if fail: print("   失败:", fail)
