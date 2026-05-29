#!/usr/bin/env python3
"""Claude 直出：批量升级 8 张地图的 all_tip + hotel 数据。不调任何 API。"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAPS_DIR = ROOT / "maps"
DATA_DIR = Path(__file__).parent / "data"

# ============ 所有升级内容（Claude 直接写） ============

UPGRADES = {

# ============ KYOTO（inline）============
"kyoto_6d.html": {
    "type": "inline",
    "all_tip": "🎯 主题定调：这不是清水寺打卡式扫景，而是用 1200 年古都把「侘寂美学」完整解读——从禅意到艺伎，从茶道到匠人精神，每天有一个明确的精神主题。\n\n🎬 节奏递进：Day1 祇園夜游(到达调时差) → Day2 东山禅意线(慢) → Day3 嵐山(自然) → Day4 金阁(华丽) → Day5 伏见+宇治(神圣+茶) → Day6 锦市场(烟火气告别)。情绪曲线是「轻→深→悟→食」。\n\n🗺️ 路线设计：6 天住一个酒店(京都站或祇園)，不换基地。每天按区域切：东(Day1-2)/西(Day3)/北(Day4)/南(Day5)/中(Day6)，避免来回。Day5 伏见→宇治不回市区直接 JR 17 分钟到。\n\n💡 实用建议：京都站、祇園附近预算 ¥800-1500/晚。樱花季 3 月底-4 月初、红叶季 11 月中-12 月初最美但人最多，建议错峰 4 月中或 11 月上。早 6 点起床应对热门景点拍照是「京都的钥匙」。",
    "hotels": {
        "1": {"name_cn": "京都十字酒店", "name_en": "Cross Hotel Kyoto", "address": "375 Kamiya-cho, Nakagyo-ku, Kyoto", "price": "¥900-1300/晚", "parking": "代客泊车 ¥2000/晚", "highlights": "步行 3 分钟到河原町地铁，步行 5 分钟到锦市场"},
        "2": {"name_cn": "京都十字酒店", "name_en": "Cross Hotel Kyoto", "address": "同上（不换酒店）", "price": "¥900-1300/晚", "parking": "代客泊车 ¥2000/晚", "highlights": "Day2 东山线最近的现代酒店"},
        "3": {"name_cn": "京都十字酒店", "name_en": "Cross Hotel Kyoto", "address": "同上", "price": "¥900-1300/晚", "parking": "代客泊车 ¥2000/晚", "highlights": "嵐山往返从河原町站直达 35 分钟"},
        "4": {"name_cn": "京都十字酒店", "name_en": "Cross Hotel Kyoto", "address": "同上", "price": "¥900-1300/晚", "parking": "代客泊车 ¥2000/晚", "highlights": "金阁寺巴士线起点站附近"},
        "5": {"name_cn": "京都十字酒店", "name_en": "Cross Hotel Kyoto", "address": "同上", "price": "¥900-1300/晚", "parking": "代客泊车 ¥2000/晚", "highlights": "祇園散步距离，晚归方便"},
        "6": {"name_cn": "京都站附近", "name_en": "Hotel Granvia Kyoto", "address": "Karasuma-dori, Shiokoji-sagaru, Shimogyo-ku", "price": "¥1100-1800/晚", "parking": "¥2500/晚", "highlights": "JR 京都站直连，最后一天去关西机场最方便"},
    }
},

# ============ YELLOWSTONE（inline）============
"yellowstone_5d.html": {
    "type": "inline",
    "all_tip": "🎯 主题定调：这是一场地球内部的史诗——你站在一个超级火山的破火山口里 5 天，看 500+ 次喷泉表演、撞见 1000 头野牛迁徙、夜爬看星空下的橙色岩浆湖。不是观光，是与地球对话。\n\n🎬 节奏递进：Day1 Old Faithful(经典开场) → Day2 湖区+Hayden Valley(野牛日) → Day3 大峡谷(瀑布日) → Day4 Lamar Valley(狼群+5 大动物清晨日出) → Day5 Mammoth+Norris(温泉+离开)。能量曲线「地热震撼→生命壮阔→水石呼应→野性凝视→悠然告别」。\n\n🗺️ 路线设计：黄石是「8字形」两个 loop，分基地换酒店避免每天开 4h+ 跨园。Day1-2 西南 Old Faithful 区，Day3 中段 Canyon，Day4-5 北部 Mammoth/Gardiner。每天开车不超 2h。\n\n💡 实用建议：BZN(Bozeman) 机场进出最近 1.5h，比 Jackson JAC 省半天。门票 ¥252/车 7 天通。5-10 月主路全开，11-4 月只北线雪车通。野生动物距离强制 ≥23m，野牛/熊 ≥91m。",
    "hotels": {
        "1": {"name_cn": "Old Faithful Inn 老忠实木屋酒店", "name_en": "Old Faithful Inn", "address": "3200 Old Faithful Inn Rd, Yellowstone National Park, WY", "price": "¥2500-3600/晚", "parking": "免费", "highlights": "1904 年百年木屋，步行 2 分钟到老忠实喷泉。需提前 8 个月订", "url": "https://www.yellowstonenationalparklodges.com/lodging/old-faithful-inn/"},
        "2": {"name_cn": "Canyon Lodge 大峡谷酒店", "name_en": "Canyon Lodge & Cabins", "address": "Canyon Village, Yellowstone National Park, WY", "price": "¥2200-2900/晚", "parking": "免费", "highlights": "湖区+Hayden Valley 中点，去 Lake/Mud Volcano 都不远", "url": "https://www.yellowstonenationalparklodges.com/lodging/canyon-lodge-cabins/"},
        "3": {"name_cn": "Canyon Lodge 大峡谷酒店", "name_en": "Canyon Lodge & Cabins", "address": "同上（不换酒店）", "price": "¥2200-2900/晚", "parking": "免费", "highlights": "步行可达 Artist Point 等大峡谷观景点"},
        "4": {"name_cn": "Mammoth Hot Springs Hotel 猛犸温泉酒店", "name_en": "Mammoth Hot Springs Hotel", "address": "1 Grand Loop Rd, Mammoth, WY 82190", "price": "¥1800-3200/晚", "parking": "免费", "highlights": "北门出口附近，去 Lamar Valley 看狼群最近", "url": "https://www.yellowstonenationalparklodges.com/lodging/mammoth-hot-springs-hotel/"},
        "5": {"name_cn": "Mammoth Hot Springs Hotel", "name_en": "Mammoth Hot Springs Hotel", "address": "同上", "price": "¥1800-3200/晚", "parking": "免费", "highlights": "回程方便：Mammoth→Norris→Madison→West 出口 1.5h"},
    }
},

# ============ BIG ISLAND（inline）============
"big_island_7d.html": {
    "type": "inline",
    "all_tip": "🎯 主题定调：地球上极少数能「上天入地」的岛——一边是活火山喷出新陆地，另一边是世界最大天文台俯瞰宇宙。从 4000m 雪山顶到深海曼塔魟夜潜，一周经历 5 个气候带。\n\n🎬 节奏递进：Day1-3 西海岸 Kona(阳光+浮潜) → Day4 跨岛(从干燥到雨林) → Day5 火山公园全日(高潮) → Day6 黑沙+南端(冒险) → Day7 咖啡告别。从度假感开场，逐步升级到地球震撼，最后回到悠闲。\n\n🗺️ 路线设计：必须换酒店。Day1-3 住 Kona 西海岸(浮潜+度假村)，Day4-6 搬到 Volcano Village 或 Hilo 东海岸(雨林+火山)。航班 Kona 进 Hilo 出最省时(或反之)，可省 4h 跨岛回程。\n\n💡 实用建议：必须租车，岛太大 Uber 不实际。普通车足够(除非自驾 Mauna Kea 山顶要 4WD)。曼塔魟夜潜旺季提前 1-2 月订。Mauna Kea 观星山顶 -10°C 起，带羽绒。",
    "hotels": {
        "1": {"name_cn": "Sheraton Kona 喜来登 Kona 度假村", "name_en": "Sheraton Kona Resort & Spa", "address": "78-128 Ehukai St, Kailua-Kona, HI", "price": "¥1800-3200/晚", "parking": "¥250/晚（必要）", "highlights": "曼塔魟夜潜出海点 Keauhou Bay 步行 5 分钟，海景房直接看夜潜灯光", "url": "https://www.marriott.com/en-us/hotels/koasi-sheraton-kona-resort-and-spa-at-keauhou-bay/"},
        "2": {"name_cn": "Sheraton Kona", "name_en": "Sheraton Kona Resort & Spa", "address": "同上", "price": "¥1800-3200/晚", "parking": "¥250/晚", "highlights": "海上 Kona 行程不换酒店最方便"},
        "3": {"name_cn": "Sheraton Kona", "name_en": "Sheraton Kona Resort & Spa", "address": "同上", "price": "¥1800-3200/晚", "parking": "¥250/晚", "highlights": "Mauna Kea 观星 tour 提供来回接送，不用自驾"},
        "4": {"name_cn": "Volcano Village Lodge 火山村小屋", "name_en": "Volcano Village Lodge", "address": "19-4183 Road E, Volcano, HI 96785", "price": "¥1500-2400/晚", "parking": "免费", "highlights": "火山公园入口 5 分钟车程，Day5 夜观熔岩最近", "url": "https://volcanovillagelodge.com/"},
        "5": {"name_cn": "Volcano Village Lodge", "name_en": "Volcano Village Lodge", "address": "同上", "price": "¥1500-2400/晚", "parking": "免费", "highlights": "Day5 火山全日来回最方便，夜观熔岩 10pm 回酒店"},
        "6": {"name_cn": "Hilo Hawaiian Hotel 希洛夏威夷酒店", "name_en": "Hilo Hawaiian Hotel", "address": "71 Banyan Dr, Hilo, HI 96720", "price": "¥1000-1800/晚", "parking": "免费", "highlights": "Hilo 港口湾景，去南端黑沙滩往返出发点", "url": "https://www.castleresorts.com/properties/hilo-hawaiian-hotel/"},
        "7": {"name_cn": "Hilo Hawaiian Hotel", "name_en": "Hilo Hawaiian Hotel", "address": "同上", "price": "¥1000-1800/晚", "parking": "免费", "highlights": "Hilo 机场离港或开 Saddle Rd 回 Kona 机场都方便"},
    }
},

# ============ JSON-based maps ============
"orlando_5d.html": {
    "type": "json",
    "json_file": "orlando.json",
    "all_tip": "🎯 主题定调：这是一场五园通关的主题乐园马拉松——2 园 Universal 的哈利波特双园 + 3 园 Disney 的迪士尼三宇宙，每天换一个童话世界。你不是来观光，是来成为故事里的角色。\n\n🎬 节奏递进：Day1-2 Universal 哈利波特(浪漫开场) → Day3 Magic Kingdom(童年回忆) → Day4 EPCOT(未来与世界) → Day5 Hollywood Studios(星战压轴)。叙事弧线从地球扩展到宇宙。\n\n🗺️ 路线设计：建议住园区酒店——提前 30-60 分钟入园冲热门项目是最大特权。Universal 资产酒店还送 Express Pass(每个项目省 2h+ 排队)。Day1-2 住 Universal 区，Day3-5 搬到 Disney 区(开车 15 分钟)。\n\n💡 实用建议：MCO 机场租车 ¥430/天。Genie+ 闪电通道(¥250/人/天)早 7am 开抢。哈利波特 Hogwarts Express 需双园票才能坐。下午 1-4 点最热建议午睡。",
    "hotels": {
        "1": {"name_cn": "Loews Royal Pacific Resort 太平洋皇家度假村", "name_en": "Loews Royal Pacific Resort at Universal", "address": "6300 Hollywood Way, Orlando, FL 32819", "price": "¥3200-5000/晚", "parking": "¥200/晚（住客自停）", "highlights": "Universal 资产酒店 · 送 Unlimited Express Pass(¥1500 价值/人/天) · 园区步行/船 10 分钟", "url": "https://www.universalorlando.com/web/en/us/places-to-stay/loews-royal-pacific-resort"},
        "2": {"name_cn": "Loews Royal Pacific Resort", "name_en": "Loews Royal Pacific Resort", "address": "同上", "price": "¥3200-5000/晚", "parking": "¥200/晚", "highlights": "Day2 Universal Studios Florida 同样 Express Pass 直通"},
        "3": {"name_cn": "Disney's Polynesian Village Resort 迪士尼波利尼西亚村", "name_en": "Disney's Polynesian Village Resort", "address": "1600 Seven Seas Dr, Lake Buena Vista, FL", "price": "¥4500-8500/晚", "parking": "¥180/晚", "highlights": "Magic Kingdom 园区免费单轨电车直达 · Tiki 主题 · 私人沙滩看烟花", "url": "https://disneyworld.disney.go.com/resorts/polynesian-resort/"},
        "4": {"name_cn": "Disney's Polynesian Village Resort", "name_en": "Disney's Polynesian Village Resort", "address": "同上", "price": "¥4500-8500/晚", "parking": "¥180/晚", "highlights": "EPCOT 单轨电车 20 分钟 · 不必换酒店"},
        "5": {"name_cn": "Disney's Polynesian Village Resort", "name_en": "Disney's Polynesian Village Resort", "address": "同上", "price": "¥4500-8500/晚", "parking": "¥180/晚", "highlights": "Hollywood Studios Skyliner 缆车 15 分钟，最后一天回程方便"},
    }
},

"hokkaido_5d.html": {
    "type": "json",
    "json_file": "hokkaido.json",
    "all_tip": "🎯 主题定调：冷暖交织的旅行——从札幌的霓虹拉面摊到登别地狱谷的硫磺蒸汽，再到富良野的薰衣草海。北海道把「治愈」两个字写在每个细节里：从蟹腿到雪山，从温泉到星空。\n\n🎬 节奏递进：Day1 札幌夜景(到达调时差) → Day2 小樽(浪漫日游) → Day3 洞爷湖+登别(温泉泡澡日) → Day4 美瑛+富良野(花海/雪原) → Day5 札幌购物+回程。从城市烟火→海港浪漫→温泉疗愈→自然壮阔→悠然告别。\n\n🗺️ 路线设计：Day1-2 札幌做基地不换酒店(JR 半小时往返小樽)，Day3 搬到登别温泉旅馆(必须住一晚)，Day4 搬到富良野(美瑛之间开车 30 分钟)，Day5 早班 JR 直回新千岁。城市间 JR 北海道周游券+租车结合。\n\n💡 实用建议：12-3 月路面结冰，防滑鞋必备(便利店 ¥1500)。6-8 月薰衣草 7 月最佳。新千岁 CTS 机场进出，国内多直飞。2 月雪祭酒店翻倍。",
    "hotels": {
        "1": {"name_cn": "札幌十字酒店", "name_en": "Cross Hotel Sapporo", "address": "北海道札幌市中央区北 2 条西 2-23", "price": "¥600-1000/晚", "parking": "¥1500/晚", "highlights": "札幌站步行 7 分钟，狸小路购物街 3 分钟，顶楼免费露天浴池"},
        "2": {"name_cn": "札幌十字酒店", "name_en": "Cross Hotel Sapporo", "address": "同上", "price": "¥600-1000/晚", "parking": "¥1500/晚", "highlights": "Day2 小樽往返 JR 札幌站直达 40 分钟"},
        "3": {"name_cn": "登别第一泷本馆", "name_en": "Dai-ichi Takimotokan", "address": "北海道登别市登别温泉町 55", "price": "¥1800-4500/晚 含 2 餐", "parking": "免费", "highlights": "日本三大名汤之一，35 个温泉池露天浴池看雪景。怀石晚餐 7 道", "url": "https://takimotokan.co.jp/"},
        "4": {"name_cn": "Furano Natulux Hotel", "name_en": "Furano Natulux Hotel", "address": "北海道富良野市朝日町 1-35", "price": "¥800-1500/晚", "parking": "免费", "highlights": "JR 富良野站旁，去美瑛/青池开车 25 分钟，富田农场 20 分钟"},
        "5": {"name_cn": "回程不住", "name_en": "Departure", "address": "—", "price": "—", "parking": "—", "highlights": "富良野 7am JR 直达新千岁机场 3.5h"},
    }
},

"barcelona_4d.html": {
    "type": "json",
    "json_file": "barcelona.json",
    "all_tip": "🎯 主题定调：这是高迪的城市——他把一座地中海港口变成一个鲜活的建筑教科书。圣家堂、巴特罗之家、米拉之家、古埃尔公园，4 天看懂这位疯子如何用 50 年解构所有「直线」。\n\n🎬 节奏递进：Day1 高迪初体验(圣家堂+古埃尔) → Day2 美食日(海鲜饭+Tapas) → Day3 海滩+市场 → Day4 建筑探索(巴特罗+米拉+凯旋门)。从震撼到味蕾，到放松，再到深度品味。\n\n🗺️ 路线设计：4 天住 1 家酒店(市中心 Eixample 区最方便)，所有景点地铁+步行覆盖。建议 Hola Barcelona Card 4 天 ¥230(含机场地铁+市内无限次)。\n\n💡 实用建议：圣家堂、古埃尔公园必须提前 2 周官网订票否则只能远观。8 月本地店多歇业避开。地铁警惕扒手(很多)。中午 2-4 点本地午休，餐厅 8pm 才晚餐。",
    "hotels": {
        "1": {"name_cn": "加泰罗尼亚广场酒店", "name_en": "Hotel Catalonia Plaza Catalunya", "address": "Bergara, 11, 08002 Barcelona, Spain", "price": "€150-220/晚（¥1200-1760）", "parking": "€30/晚", "highlights": "加泰罗尼亚广场对面，地铁 1/3 号线交汇，机场地铁直达"},
        "2": {"name_cn": "加泰罗尼亚广场酒店", "name_en": "Hotel Catalonia Plaza Catalunya", "address": "同上", "price": "€150-220/晚", "parking": "€30/晚", "highlights": "兰布拉大道 3 分钟步行，美食区核心"},
        "3": {"name_cn": "加泰罗尼亚广场酒店", "name_en": "Hotel Catalonia Plaza Catalunya", "address": "同上", "price": "€150-220/晚", "parking": "€30/晚", "highlights": "去 Barceloneta 海滩地铁 4 号线 10 分钟"},
        "4": {"name_cn": "加泰罗尼亚广场酒店", "name_en": "Hotel Catalonia Plaza Catalunya", "address": "同上", "price": "€150-220/晚", "parking": "€30/晚", "highlights": "巴特罗之家、米拉之家步行 10 分钟"},
    }
},

"seoul_3d.html": {
    "type": "json",
    "json_file": "seoul.json",
    # all_tip 已经是 4 段结构（刚再生成的），不动
    "all_tip": None,
    "hotels": {
        "1": {"name_cn": "明洞 Ibis 大使酒店", "name_en": "Ibis Ambassador Myeongdong", "address": "首尔特别市中区明洞 8 街 59", "price": "₩100000-150000/晚（¥550-825）", "parking": "免费", "highlights": "明洞地铁站步行 3 分钟，明洞购物街 5 分钟，去景福宫地铁 2 站"},
        "2": {"name_cn": "明洞 Ibis 大使酒店", "name_en": "Ibis Ambassador Myeongdong", "address": "同上", "price": "₩100000-150000/晚", "parking": "免费", "highlights": "Day2 南山塔缆车站步行 15 分钟，梨泰院地铁 10 分钟"},
        "3": {"name_cn": "明洞 Ibis 大使酒店", "name_en": "Ibis Ambassador Myeongdong", "address": "同上", "price": "₩100000-150000/晚", "parking": "免费", "highlights": "去仁川机场 AREX 直达列车 60 分钟"},
    }
},

"chiangmai_3d.html": {
    "type": "json",
    "json_file": "chiangmai.json",
    # all_tip 已经是 4 段结构（刚再生成的），不动
    "all_tip": None,
    # 酒店数据保留 LLM 给的（古城酒店），不动
    "hotels": None,
},

}


def upgrade_inline(file_path: Path, upgrade: dict):
    """直接 patch HTML 里 inline 的 const META / const DAYS。"""
    src = file_path.read_text(encoding="utf-8")
    changed = False

    # 1. 替换 const ALL_TIP
    if upgrade.get("all_tip"):
        # 用 Python 把字符串转成 JSON 字符串（带引号）
        new_tip_js = json.dumps(upgrade["all_tip"], ensure_ascii=False)
        # 找 const ALL_TIP = '...';
        m = re.search(r"const ALL_TIP = ['\"`].*?['\"`];", src, re.DOTALL)
        if m:
            src = src[:m.start()] + f"const ALL_TIP = {new_tip_js};" + src[m.end():]
            changed = True

    # 2. 给每个 day 加 hotel 字段
    if upgrade.get("hotels"):
        days_match = re.search(r"const DAYS = \{(.*?)\n\};", src, re.DOTALL)
        if days_match:
            days_block = days_match.group(1)
            # 用正则找每个 day 的对象 "1": { ... },
            new_days_block = days_block
            for day_str, hotel in upgrade["hotels"].items():
                hotel_js = json.dumps(hotel, ensure_ascii=False)
                # 找该天的结束 } 然后在 } 前插入 , hotel: {...}
                pattern = rf'(["\']?{day_str}["\']?:\s*\{{[^}}]*?)(\}})'
                m = re.search(pattern, new_days_block)
                if m and '"hotel"' not in m.group(1):
                    new_days_block = new_days_block[:m.start()] + m.group(1) + f', "hotel": {hotel_js}' + m.group(2) + new_days_block[m.end():]
                    changed = True
            src = src[:days_match.start()] + "const DAYS = {" + new_days_block + "\n};" + src[days_match.end():]

    if changed:
        file_path.write_text(src, encoding="utf-8")
    return changed


def upgrade_json(json_path: Path, upgrade: dict):
    """改 JSON 然后重新渲染。"""
    if not json_path.exists():
        return False
    data = json.loads(json_path.read_text(encoding="utf-8"))
    changed = False
    if upgrade.get("all_tip"):
        data["meta"]["all_tip"] = upgrade["all_tip"]
        changed = True
    if upgrade.get("hotels"):
        for d_str, h in upgrade["hotels"].items():
            if d_str in data["days"]:
                data["days"][d_str]["hotel"] = h
                changed = True
    if changed:
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


def rerender_json(slug: str, days: int):
    """运行 generate.py --data 重新渲染。"""
    json_path = DATA_DIR / f"{slug}.json"
    out_html = MAPS_DIR / f"{slug}_{days}d.html"
    if not json_path.exists():
        return False
    cmd = ["python3", str(Path(__file__).parent / "generate.py"),
           "--data", str(json_path), "--slug", slug]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    return result.returncode == 0


def main():
    print("🎨 Claude 直出升级 · 不调任何 API\n")
    for fname, up in UPGRADES.items():
        slug = fname.replace(".html", "").rsplit("_", 1)[0]
        days = int(re.search(r"_(\d+)d", fname).group(1))
        if up["type"] == "inline":
            ok = upgrade_inline(MAPS_DIR / fname, up)
            print(f"  {'✅' if ok else '⏭️ '} {fname:30s} (inline patch)")
        else:
            json_changed = upgrade_json(DATA_DIR / up["json_file"], up)
            if json_changed:
                rerender_ok = rerender_json(slug, days)
                print(f"  {'✅' if rerender_ok else '⚠️ '} {fname:30s} (json edit + re-render)")
            else:
                print(f"  ⏭️  {fname:30s} (no changes)")


if __name__ == "__main__":
    main()
