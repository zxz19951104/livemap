#!/usr/bin/env python3
"""给地图里每个 POI 回填干净中文名 name_cn（火山 LLM 批量翻译）。幂等：已有 name_cn 的跳过。
用法: python add_name_cn.py yellowstone_5d.html          # 单图
      python add_name_cn.py --all                        # 全部 maps/*.html
仅在 const POIs=[..] 区间内操作，避免误伤其它 name 字段。
"""
import os, sys, re, json, glob, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPS = ROOT / "maps"

# ---- 读 .env ----
envf = Path(__file__).parent / ".env"
if envf.exists():
    for line in envf.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from openai import OpenAI
API_KEY = os.getenv("VOLC_API_KEY")
MODEL = os.getenv("VOLC_ENDPOINT_ID") or os.getenv("VOLC_MODEL", "doubao-1-5-pro-32k-250115")
BASE = os.getenv("VOLC_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
if not API_KEY:
    sys.exit("❌ 未设 VOLC_API_KEY")
client = OpenAI(api_key=API_KEY, base_url=BASE)

# 同时匹配 JS 对象式  name: '...'  和 JSON 式  "name": "..."
NAME_RE = re.compile(r"(\"name\"|name)\s*:\s*(['\"])((?:\\.|(?!\2).)*)\2")
POIS_RE = re.compile(r"const POIs\s*=\s*\[.*?\];", re.S)
DAYS_RE = re.compile(r"const DAYS\s*=\s*\{.*?\};", re.S)
# 标题：Day N · 主题   两种引号都支持
TITLE_RE = re.compile(r"(\"title\"|title)(\s*:\s*)(['\"])(Day\s*\d+\s*·\s*)((?:\\.|(?!\3).)*)(\3)")
HAS_LATIN = re.compile(r"[A-Za-z]")

def translate(names):
    listing = "\n".join(f"{i}. {n}" for i, n in enumerate(names))
    prompt = (
        "把下面的旅行景点名翻译成简洁、自然、地道的中文地名（中国游客一看就懂）。要求：\n"
        "- 纯中文，绝不保留英文单词/字母；保留必要的数字\n"
        "- 简短，尽量不超过 10 个汉字；专有地名用通行译名\n"
        "- 保持顺序，逐条对应\n"
        "只输出 JSON 对象，键是序号字符串，值是中文名，无任何前后说明。例如 {\"0\":\"西黄石镇入口\"}。\n\n"
        + listing
    )
    msgs = [
        {"role": "system", "content": "你是资深旅行翻译，只输出合法 JSON，无前后说明。"},
        {"role": "user", "content": prompt},
    ]
    for attempt in range(3):
        kw = dict(model=MODEL, max_tokens=4000, temperature=0.2, messages=msgs)
        if attempt == 0:
            kw["response_format"] = {"type": "json_object"}
        try:
            resp = client.chat.completions.create(**kw)
        except Exception as e:
            if attempt == 0 and "response_format" in str(e).lower():
                kw.pop("response_format", None); resp = client.chat.completions.create(**kw)
            else:
                raise
        txt = resp.choices[0].message.content
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            d = json.loads(m.group(0) if m else txt)
            return [str(d[str(i)]).strip() for i in range(len(names))]
        except Exception as e:
            print(f"    ⚠️ JSON 解析失败({e})，重试"); time.sleep(1)
    raise RuntimeError("翻译失败")

def esc(c):
    return c.replace("\\", "").replace("'", "\\'")

def do_names(s):
    """在 POIs 区间为含英文的 POI 名注入 name_cn（纯中文）。已注入或本就纯中文则跳过。"""
    mpo = POIS_RE.search(s)
    if not mpo: return s, 0
    block = mpo.group(0)
    todo = []
    for m in NAME_RE.finditer(block):
        val = m.group(3)
        if HAS_LATIN.search(val) and "name_cn" not in block[m.end():m.end()+40]:
            todo.append(m)
    if not todo: return s, 0
    cn = translate([m.group(3).replace("\\'", "'").replace('\\"', '"') for m in todo])
    nb = block
    for k in range(len(todo) - 1, -1, -1):
        m = todo[k]; c = cn[k]
        ins = f', "name_cn": "{c.replace(chr(34), "")}"' if m.group(2) == '"' else f", name_cn: '{esc(c)}'"
        nb = nb[:m.end()] + ins + nb[m.end():]
    return s[:mpo.start()] + nb + s[mpo.end():], len(todo)

def do_themes(s):
    """翻译 DAYS 标题里仍含英文的主题部分（保留 'Day N · ' 前缀）。两种引号都支持。"""
    md = DAYS_RE.search(s)
    if not md: return s, 0
    block = md.group(0)
    titles = [t for t in TITLE_RE.finditer(block) if HAS_LATIN.search(t.group(5))]
    if not titles: return s, 0
    cn = translate([t.group(5).replace("\\'", "'").replace('\\"', '"') for t in titles])
    nb = block
    for k in range(len(titles) - 1, -1, -1):
        t = titles[k]
        theme = cn[k].replace(chr(34), "") if t.group(3) == '"' else esc(cn[k])
        newt = f"{t.group(1)}{t.group(2)}{t.group(3)}{t.group(4)}{theme}{t.group(6)}"
        nb = nb[:t.start()] + newt + nb[t.end():]
    return s[:md.start()] + nb + s[md.end():], len(titles)

def process(path: Path):
    s = path.read_text(encoding="utf-8")
    s, n1 = do_names(s)
    s, n2 = do_themes(s)
    if n1 or n2:
        path.write_text(s, encoding="utf-8")
        print(f"  ✅ {path.name}：name_cn×{n1}  主题汉化×{n2}")
    else:
        print(f"  ⏭  {path.name}：已全中文，跳过")

def main():
    args = sys.argv[1:]
    if args == ["--all"]:
        files = sorted(MAPS.glob("*.html"))
    else:
        files = [MAPS / a for a in args]
    for f in files:
        if not f.exists(): print(f"  ⚠ 不存在 {f}"); continue
        print(f"→ {f.name}")
        process(f)

if __name__ == "__main__":
    main()
