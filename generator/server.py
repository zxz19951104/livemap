#!/usr/bin/env python3
"""
LiveMap 本地服务 · v0.5
========================
让 Hub 真正能"输入目的地 → 点生成 → 浏览器自动出图"。

使用：
    cd generator
    python3 server.py

然后浏览器打开：http://localhost:5005

零依赖（只用 Python stdlib）· 零暴露 API key（key 留在 .env，不出本机）。
"""

import json
import os
import sys
import http.server
import socketserver
import urllib.parse
from pathlib import Path

# 把 generator 加进 path，能 import generate.py 的函数
sys.path.insert(0, str(Path(__file__).parent))
from generate import (
    call_llm, render_html, slugify, load_env_file,
    MAPS_DIR, DATA_DIR, ROOT,
)

PORT = 5005


class LiveMapHandler(http.server.SimpleHTTPRequestHandler):
    """同时提供静态文件 + API 端点。"""

    def __init__(self, *args, **kwargs):
        # 静态文件根目录指向 livemap/
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        # 简化日志
        ts = self.log_date_time_string()
        print(f"[{ts}] {fmt % args}")

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/list":
            return self._list_maps()
        # 其他 GET 走默认静态文件
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/generate":
            return self._generate()
        self.send_error(404, "API not found")

    def _generate(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)

            destination = (data.get("destination") or "").strip()
            days = int(data.get("days") or 5)
            pref = (data.get("pref") or "").strip()
            mode = (data.get("mode") or "").strip().lower()
            if mode not in ("", "j", "p", "middle", "budget"):
                mode = ""

            if not destination:
                return self._json(400, {"error": "请输入目的地"})
            if not (1 <= days <= 14):
                return self._json(400, {"error": "天数应在 1-14 之间"})
            if not (os.getenv("VOLC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
                return self._json(500, {"error": "服务端未设 VOLC_API_KEY 或 ANTHROPIC_API_KEY"})

            # —— 存量优先：先按 slug+mode+days 查本地是否已有，命中直接返回，不调 AI ——
            base_guess = slugify(destination)
            if base_guess and base_guess != "destination":
                cached_name = f"{base_guess}_{mode}_{days}d.html" if mode else f"{base_guess}_{days}d.html"
                cached_path = MAPS_DIR / cached_name
                if cached_path.exists():
                    print(f"\n♻️  命中存量地图：{cached_name}（跳过 AI，0 token）")
                    return self._json(200, {
                        "success": True,
                        "cached": True,
                        "map_url": f"/maps/{cached_name}",
                        "destination": destination,
                        "days": days,
                        "size_kb": cached_path.stat().st_size // 1024,
                    })

            print(f"\n🤖 生成请求：{destination} · {days} 天 · 偏好={pref or '无'} · 模式={mode or '标准'}")
            ai_data = call_llm(destination, days, pref, mode)
            if mode:
                ai_data.setdefault("meta", {})["mode"] = mode
            base_slug = slugify(destination, ai_data.get("meta"))
            slug = f"{base_slug}_{mode}" if mode else base_slug

            # 保存 JSON 备份
            DATA_DIR.mkdir(exist_ok=True)
            json_path = DATA_DIR / f"{slug}.json"
            json_path.write_text(
                json.dumps(ai_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # 渲染 HTML
            html = render_html(ai_data)
            MAPS_DIR.mkdir(exist_ok=True)
            html_name = f"{slug}_{days}d.html"
            html_path = MAPS_DIR / html_name
            html_path.write_text(html, encoding="utf-8")

            print(f"✅ 完成：{html_path} ({html_path.stat().st_size // 1024} KB)")

            return self._json(200, {
                "success": True,
                "map_url": f"/maps/{html_name}",
                "json_url": f"/generator/data/{slug}.json",
                "destination": destination,
                "days": days,
                "poi_count": len(ai_data.get("pois", [])),
                "size_kb": html_path.stat().st_size // 1024,
            })

        except json.JSONDecodeError:
            return self._json(400, {"error": "JSON 解析失败（Claude 输出格式不符）"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self._json(500, {"error": f"{type(e).__name__}: {e}"})

    def _list_maps(self):
        """列出所有已生成的地图。"""
        from mapmeta import card_meta
        maps = []
        if MAPS_DIR.exists():
            for f in sorted(MAPS_DIR.glob("*.html")):
                entry = {
                    "name": f.stem,
                    "url": f"/maps/{f.name}",
                    "size_kb": f.stat().st_size // 1024,
                    "mtime": int(f.stat().st_mtime),
                }
                entry.update(card_meta(f))
                maps.append(entry)
        return self._json(200, {"maps": maps})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    load_env_file()

    # 公网托管模式：强制走便宜模型（火山豆包），避免被刷爆时用到贵的 Claude
    public = os.getenv("PUBLIC_DEPLOY", "").lower() in ("1", "true", "yes")
    if public:
        os.environ["LLM_PROVIDER"] = "volc"

    if not (os.getenv("VOLC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("❌ 未设 VOLC_API_KEY 或 ANTHROPIC_API_KEY。请检查 generator/.env 或托管平台环境变量")
        sys.exit(1)
    if public and not os.getenv("VOLC_API_KEY"):
        print("❌ PUBLIC_DEPLOY=1 需要 VOLC_API_KEY（强制使用火山便宜模型）")
        sys.exit(1)

    # 报告当前 LLM 提供商
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if not provider:
        provider = "volc" if os.getenv("VOLC_API_KEY") else "anthropic"
    if provider in ("volc", "volcengine", "ark"):
        model_info = f" · 模型 {os.getenv('VOLC_ENDPOINT_ID') or os.getenv('VOLC_MODEL', 'doubao-1-5-pro-32k-250115')}"
    else:
        model_info = f" · 模型 {os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5')}"
    print(f"  🤖 LLM 后端：{provider}{model_info}{' · 公网模式（强制便宜模型）' if public else ''}")

    # 托管平台（Render/Railway/Fly）通过 $PORT 指定端口，并需绑定 0.0.0.0
    host = "0.0.0.0" if (public or os.getenv("PORT")) else "localhost"
    port = int(os.getenv("PORT", PORT))

    # 多线程：LLM 生成耗时 ~10s，避免阻塞画廊浏览
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer((host, port), LiveMapHandler) as httpd:
        url = f"http://{host}:{port}/"
        print("=" * 60)
        print(f"  🚀 LiveMap 服务已启动")
        print(f"  📍 监听：{url}")
        print(f"  📡 API： POST /api/generate · GET /api/list")
        print(f"  ⏹  停止：Ctrl+C")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务已停止")


if __name__ == "__main__":
    main()
