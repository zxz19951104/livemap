# LiveMap 部署指南（静态分享版）

把 LiveMap 打包成纯静态站点，分享给任何人浏览。**画廊 + 所有已生成地图都能看**；实时 AI 生成会优雅降级为「请本地运行」提示（静态站点没有后端、不暴露 API key）。

---

## 一键本地构建 + 预览

```bash
cd generator
python3 build_static.py          # 输出到 ../dist
cd ../dist
python3 -m http.server 8000      # 浏览器开 http://localhost:8000
```

每次新增/更新地图后，重跑 `build_static.py` 即可刷新 `dist/`。

---

## 方式 A · GitHub Pages（推荐，免费且自动）

1. 把整个 `livemap/` 推到 GitHub 仓库（`main` 分支）
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**
3. 已内置 `.github/workflows/deploy.yml`：每次 push 自动构建 `dist/` 并发布
4. 几分钟后访问 `https://<用户名>.github.io/<仓库名>/`

> 已生成 `.nojekyll`，避免 GitHub 忽略下划线开头的文件。

---

## 方式 B · Netlify / Vercel

- **Build command**: `cd generator && python3 build_static.py --out ../dist`
- **Publish directory**: `dist`
- Python 运行时：Netlify/Vercel 默认带 Python3，无需额外依赖（构建脚本零依赖）

拖拽部署：本地先 `python3 build_static.py`，再把 `dist/` 文件夹直接拖到 Netlify Drop（app.netlify.com/drop）。

---

## 方式 C · 任意静态托管 / 内网

`dist/` 是纯静态文件，丢到任何能托管 HTML 的地方即可：对象存储（OSS/S3）、nginx、`python3 -m http.server`、U 盘……

---

## 完整版（含实时 AI 生成）

分享版只读浏览。要让别人也能输入任意目的地秒出新图，需要后端 + API key：

```bash
cd generator
# 在 .env 写入 VOLC_API_KEY（火山豆包，¥0.05/张）或 ANTHROPIC_API_KEY
python3 server.py
open http://localhost:5005
```

⚠️ 切勿把含真实 key 的 `.env` 提交到公开仓库。
