# LiveMap · 项目状态快照

> 用于 Claude Code `/clear` 后快速恢复上下文。每次重大改动后更新本文件。

---

## 🎯 项目本质

把"目的地+天数+偏好" → **10 秒生成可交互的旅行活地图 HTML**。
- 后端：火山引擎豆包（¥0.05/张）/ Claude（免费，靠 Claude Code 直出）
- 前端：Hub 落地页 + 9 张已生成地图
- 服务：本地 `http://localhost:5005`（python3 server.py 后台跑）

---

## 📁 关键路径

```
/Users/bytedance/xunzhi/livemap/
├── index.html               Hub 落地页
├── maps/                    9 张已生成地图（全部走同一套 v0.7 模板）
│   ├── kyoto_6d.html        京都 6 天
│   ├── yellowstone_5d.html  黄石 5 天
│   ├── big_island_7d.html   大岛 7 天
│   ├── hokkaido_5d.html     北海道 5 天
│   ├── orlando_5d.html      奥兰多 5 天
│   ├── seoul_3d.html        首尔 3 天
│   ├── barcelona_4d.html    巴塞罗那 4 天
│   ├── chiangmai_3d.html    清迈 3 天
│   └── alaska_5d.html       阿拉斯加 5 天
├── generator/
│   ├── template.html        通用模板（17 个占位符）
│   ├── generate.py          CLI 生成器（3 模式：--api/--data/--mock）
│   ├── server.py            本地 HTTP（5005 端口）
│   ├── .env                 含 VOLC_API_KEY + VOLC_MODEL=doubao-1-5-pro-32k-250115
│   └── data/*.json          POI 源数据
└── PRD_LiveMap.md           完整 PRD（飞书已同步）
```

## 🚀 启动命令

```bash
# 后台启动服务
cd /Users/bytedance/xunzhi/livemap/generator
nohup python3 server.py > /tmp/livemap_server.log 2>&1 &
echo $! > /tmp/livemap_server.pid

# 停服务
kill $(cat /tmp/livemap_server.pid)

# 用 Claude API 生成（需要 ANTHROPIC_API_KEY）
python3 generate.py "巴黎" 5 --pref 美食 --open

# 用火山生成（已配 .env）
python3 generate.py "巴黎" 5 --pref 美食 --open  # 自动用 VOLC

# mock 数据测试
python3 generate.py --mock --open
```

---

## ✨ 已实现功能清单（v0.7）

### 地图本体
- Leaflet 真实地理底图（CartoDB Voyager）+ 风格切换（简洁/地形）
- 移动端适配（≤768px 单列 + Day Tab 横向滚动 + map 360px）
- POI markers 带编号 + 颜色分类
- Day 路线连线（彩色虚线，每天独立颜色）

### POI 详情面板
- **4 宫格大图**（Wikimedia + Commons 多源搜图，搜不到回退 emoji）
- **Lightbox** 全屏看图 + 左右箭头 + 底部圆点 + 键盘 ← →
- **POI 上一个/下一个导航** `‹ 3/24 ›`（键盘 ← →）
- **3 个 info-cell**：💴 门票（RMB+原币）/ ⏰ 营业 / **⏱️ 建议游玩**（智能默认）
- 描述 + 拍照点（搜图按钮）+ 美食（每行点 📍 跳 Google Maps）+ 米其林 + 避雷
- 「📍 在 Google Maps 打开导航」大按钮

### Day 视图
- POI 列表（每两点之间显示距离 + 步行/打车时间）
- Day tip + Plan B（雨天预案）
- 推荐酒店卡片（地址/价格 RMB/停车/Booking/Google Maps）

### 全部 N 天视图
- 4 段结构化 all_tip（🎯主题/🎬节奏/🗺️路线/💡实用）
  - 段标题 16px + emoji 20px + 段间虚线分隔
  - 关键词自动高亮：「引用」黄色记号笔 / Day N 灰徽章 / ¥价 橙记号笔 / 时段词 蓝记号笔
- 统计卡 4 槽：天数 / 景点 / **预计花费/人** / **交通方式**
- 🔥 独门绝技 + ⚠️ 安全提醒
- ✈️ 出行前必看（签证/电压/SIM/汇率/小费/急救）
- ⬇️ GPX 导出按钮（导入 Google My Maps / Garmin）

### Hub 落地页
- 输入框 + 偏好 chips + 生成按钮（点击调 /api/generate）
- 已生成地图 Gallery（自动 fetch /api/list 动态列出所有 maps/）
- 「工作原理」4 步说明

### 后端
- generate.py：3 模式（--api / --data / --mock）+ slug 映射
- server.py：Python stdlib http.server，端口 5005
  - `POST /api/generate` 生成新地图
  - `GET /api/list` 列出所有地图
  - 静态文件直接服务整个 livemap/ 目录
- 双 LLM：VOLC（默认）/ ANTHROPIC，自动 fallback
- 货币：JPY/USD/EUR/GBP/KRW/THB/AUD/CAD 自动换算 RMB

---

## 🐛 重要教训

**❌ 不要用 MutationObserver 监听 body 子树**
- 会和 Day Tab 切换的 innerHTML 重渲染产生竞态
- 之前的 L、M、P 升级都因为用了 observer 导致 Day Tab bug

**✅ 正确做法**
- 直接 regex patch 源码
- 或 override 函数：`const _orig = showDetail; window.showDetail = ...`

---

## 🚧 待办 / 用户提过的需求（未完成）

1. **O · 独门绝技项可点击** → 跳 POI 详情（task #33 pending）
2. **多模式系统**（J 人计划 / P 人随性 / 中产 / 穷游）
   - 影响：消费/节奏/玩法/酒店/餐厅/交通
   - 设计：每个模式独立 HTML 文件，Hub mode picker
3. **独门绝技点击展开深度介绍**（pending）

---

## 💡 当前协作模式

| 谁出 token | 场景 |
|---|---|
| **Claude（免费）** | 用户对话里"生成 XX N 天"——我直接写 JSON + 跑 `generate.py --data` 渲染 |
| **火山 API（¥0.05/张）** | 用户在 Hub 输入框点生成 |

---

## 🔑 .env 内容（在 generator/.env）

```
VOLC_API_KEY=<你的火山引擎 key>
VOLC_MODEL=doubao-1-5-pro-32k-250115
LLM_PROVIDER=volc
```

⚠️ 真实 key 只放本地 `generator/.env`（已被 .gitignore 忽略），切勿写进任何会提交的文件。

---

## 📊 关键技术决策

- **不用 React/Vue**——纯 vanilla JS，每张 HTML 独立 56KB，可微信/AirDrop 分享
- **不用 Mapbox**——CartoDB 免费瓦片够用（Stamen 水彩需 API key 已放弃）
- **图片源**：Wikipedia REST API（首图）+ Wikimedia Commons 搜索 + Google Images 跳转兜底
- **数据流**：POI JSON → template.html 占位符替换 → 静态 HTML
- **风格 5 套**：warm / sakura / ocean / snow / forest（LLM 按目的地气质选）

---

## 🆘 如果 Claude Code 重启后

1. 跑 `cat /Users/bytedance/xunzhi/livemap/PROJECT_STATE.md` 拉回上下文
2. 跑 `ls /Users/bytedance/xunzhi/livemap/maps/` 看现有地图
3. 跑 `curl -s http://localhost:5005/api/list | head` 看服务是否还活着
4. 如果服务挂了：`cd generator && nohup python3 server.py > /tmp/livemap_server.log 2>&1 &`
