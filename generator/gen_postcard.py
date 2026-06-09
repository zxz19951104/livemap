#!/usr/bin/env python3
"""用火山 Ark 文生图(Doubao Seedream)生成某地点的卡通旅游明信片插画，存本地。
用法: python gen_postcard.py "Yellowstone National Park" out.png
"""
import os, sys, base64, urllib.request
from pathlib import Path
from openai import OpenAI

# 手动加载 .env（不依赖 python-dotenv）
envf = Path(__file__).parent / ".env"
if envf.exists():
    for line in envf.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
api_key = os.getenv("VOLC_API_KEY")
base_url = os.getenv("VOLC_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
if not api_key:
    print("❌ 缺 VOLC_API_KEY"); sys.exit(1)

place = sys.argv[1] if len(sys.argv) > 1 else "Yellowstone National Park"
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/livemap_qa/postcard.png"

prompt = (
    f"Flat vector cartoon travel postcard illustration of {place}. "
    "Iconic scenery and landmarks of this destination, cute minimal flat-design style, "
    "warm cheerful palette, soft shapes, layered mountains, sky with sun and clouds, "
    "vacation vibe, no text, no words, no letters, clean composition, "
    "suitable as a poster background, vertical orientation."
)

# 候选文生图模型（按可用性依次尝试）
models = [os.getenv("VOLC_T2I_MODEL", "")] + [
    "doubao-seedream-3-0-t2i-250415",
    "doubao-seedream-4-0-250828",
    "high_aes_general_v30l_zt2i",
]
models = [m for m in models if m]

client = OpenAI(api_key=api_key, base_url=base_url)
last_err = None
for model in models:
    try:
        print(f"→ 尝试模型 {model} ...")
        resp = client.images.generate(model=model, prompt=prompt, size="1024x1536", response_format="url")
        url = resp.data[0].url
        b = (resp.data[0].b64_json if getattr(resp.data[0], "b64_json", None) else None)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        if b:
            Path(out).write_bytes(base64.b64decode(b))
        else:
            urllib.request.urlretrieve(url, out)
        print(f"✅ 成功 model={model} → {out}")
        sys.exit(0)
    except Exception as e:
        last_err = f"{model}: {type(e).__name__}: {str(e)[:200]}"
        print("  ✗", last_err)

print("❌ 全部模型失败。最后错误：", last_err)
sys.exit(2)
