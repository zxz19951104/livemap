# LiveMap MVP · v0.1-0.2

> 把旅行攻略变成一张能"看"的地图

## 🚀 立刻体验

```bash
open index.html
```

或在浏览器双击 `index.html`，即可看到 Hub 落地页 + 3 张已生成的活地图。

---

## 📦 当前 MVP 内容

```
livemap/
├── index.html              ← Hub 落地页（v0.1）
├── maps/
│   ├── big_island_7d.html  ← 大岛 7 天（28 POI）
│   ├── yellowstone_5d.html ← 黄石 5 天（20 POI）
│   └── kyoto_6d.html       ← 京都 6 天（24 POI · 新增）
├── generator/
│   └── generate.py         ← AI 生成器脚本（v0.2，需 API key）
├── PRD_LiveMap.md          ← 产品 PRD
└── README.md
```

---

## ✅ v0.1 已实现（手工模板验证）

- [x] Hub 落地页，UI 美感对齐 Linear/Notion 水准
- [x] 3 个目的地手工活地图（大岛 / 黄石 / 京都）
- [x] 输入框 + 偏好 chip + 生成按钮（演示交互）
- [x] "工作原理" 4 步说明
- [x] 单文件 HTML，可微信/AirDrop 分享

## 🚧 v0.2 已搭好脚手架（待 API 接入）

- [x] `generator/generate.py` AI 生成器核心逻辑
- [x] Claude POI 生成 prompt（结构化 JSON 输出）
- [x] CLI 接口：`python3 generate.py "京都" 6 --pref 美食`
- [ ] **TODO**：抽取 `template.html`（把黄石 HTML 改成带占位符版本）
- [ ] **TODO**：接入 Claude API 测试端到端
- [ ] **TODO**：在 index.html 加 fetch 调用替代模态框

---

## 🎯 体验流程

1. **打开 `index.html`** → 看到 Hub
2. **点 3 张卡片任意一张** → 进入交互式活地图
3. **在地图里**：
   - 切换 Day Tab（看路线高亮）
   - 点 POI（看详情）
   - 看 emoji 图例
4. **回到 Hub**：在输入框输入"巴厘岛" + 选偏好 → 点生成（弹窗解释 v0.2 状态）

---

## 🛠️ 启用 v0.2 AI 生成（开发者）

```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
pip install anthropic
cd generator
python3 generate.py "冰岛" 7 --pref 自然,极光 --open
```

输出到 `../maps/<slug>_<days>d.html`，自动在浏览器打开。

---

## 📊 测试数据点

| 目的地 | 天数 | POI 数 | 文件大小 |
|---|---|---|---|
| Big Island 大岛 | 7 | 28 | 36 KB |
| Yellowstone 黄石 | 5 | 20 | 37 KB |
| Kyoto 京都 | 6 | 24 | 35 KB |

平均：~5 KB/POI，符合 PRD "≤100KB" 要求。
