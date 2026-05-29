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

## 方式 D · 托管完整版（Render，公网可在线生成）⭐

让分享链接「输入目的地 → 点生成 → 自动出图」，需要一个藏着 API key 的常驻后端。
现成的 `generator/server.py` 已支持托管：读 `$PORT`、绑定 `0.0.0.0`、多线程、公网模式强制走便宜模型。

**一键蓝图（仓库已含 `render.yaml`）：**
1. 注册 / 登录 [Render](https://render.com)（免费档即可）
2. **New + → Blueprint → 选本仓库 → Apply**（会自动读 `render.yaml`）
3. 部署后到该服务的 **Environment** 里，手动填入真实 `VOLC_API_KEY`（火山控制台拿，**不要写进仓库**）
4. 几分钟后访问 Render 给的 `https://livemap-xxxx.onrender.com/` —— 这就是「能在线生成」的完整版链接

**关键环境变量（render.yaml 已预设，仅 key 需手填）：**

| 变量 | 值 | 作用 |
|---|---|---|
| `PUBLIC_DEPLOY` | `1` | 公网模式：**强制火山便宜模型**，关闭贵的 Claude |
| `LLM_PROVIDER` | `volc` | 指定火山引擎 |
| `VOLC_MODEL` | `doubao-1-5-pro-32k-250115` | 豆包 · 约 ¥0.05/张 |
| `VOLC_API_KEY` | （手填） | 你的火山 key，`sync:false` 不进仓库 |

> ⚠️ 说明：
> - 公网生成接口用的是**你的 key**＝别人也能花你的 token；已强制只走便宜豆包，单张约 ¥0.05。如需进一步防刷，可再加每日额度上限（告诉我即可补）。
> - Render 免费档**磁盘是临时的**：预置的 29 张图随代码常在，但访客新生成的图在实例重启后会丢（缓存期内可正常访问）。要永久保留需接对象存储。
> - GitHub Pages 静态版（方式 A）仍可保留作只读镜像；想要在线生成就发 Render 链接。

---

## 本地完整版（开发 / 自用）

```bash
cd generator
# 在 .env 写入 VOLC_API_KEY（火山豆包，¥0.05/张）或 ANTHROPIC_API_KEY
python3 server.py
open http://localhost:5005
```

⚠️ 切勿把含真实 key 的 `.env` 提交到公开仓库。
