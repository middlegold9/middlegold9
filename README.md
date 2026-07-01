# 深圳房产博主一体化工作流系统（FDE 项目）

> Forward Deployed Engineer 交付项目：为深圳头部房产自媒体博主 / 经纪人解决「数据散落、板块孤岛、协同缺失」的工作流问题。

---

## 一、为什么做这个项目（业务背景）

客户是一位深圳的房产博主 + 经纪人，业务横跨 7 大板块，但所有数据散落在 **PDF / Word / PPT** 里，靠人脑和微信记忆运转。

| 板块 | 业务本质 | 现状痛点 |
|------|----------|----------|
| 二手成交 | 赚佣金（核心现金流） | 成交记录散在 Excel 截图、PDF 合同里 |
| 新豪宅公关看房 | 拍视频做自媒体引流 | 看房素材、楼盘卖点无沉淀 |
| 土拍市场关注 | 拍视频 + 做分析引流 | 土拍数据靠手抄，分析不成体系 |
| VIP 资产配置咨询 | 房产+理财+保险+香港身份+子女教育 | 客户需求记在脑子里，无法跨品类联动 |
| VIP 客户会面安排 | 维护高净值关系 | 会面与客户档案割裂 |
| 福田/南山/宝中区域数据 | 定价 & 选题依据 | 数据散落，无法聚合看趋势 |
| 合同撰写 | 成交履约 | 每次手写，易出错、不合规 |

**核心问题：板块之间有大量交集（同一个高净值客户既买二手房、又要做资产配置、还会看豪宅），但完全没有协同效应。**

---

## 二、FDE 解法（一句话）

> 建一个「**统一数据底座 + 跨板块协同引擎**」：把散落在 PDF/Word/PPT 的数据自动抽取成结构化数据，再用规则引擎把 7 个板块的信号串起来，自动产出**线索、选题、配置建议、合同**。

```
散落文档(PDF/Word/PPT)
        │  ① 文档解析与抽取 (ingestion)
        ▼
   统一数据底座 (Client / Property / Transaction / LandAuction / Content / Meeting / Contract)
        │  ② 协同引擎 (synergy engine)
        ▼
   自动产出: 客户360 | 跨板块推荐 | 内容选题 | 区域情报 | 合同生成
        │  ③ Web 控制台
        ▼
     博主一个界面搞定全部工作流
```

---

## 三、技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy / SQLite |
| 文档解析 | pdfplumber / python-docx / python-pptx |
| 协同引擎 | 规则引擎（可插拔 LLM，离线可跑） |
| 前端 | React 18 / Vite / Recharts / Axios |
| 数据库 | SQLite（零配置，开箱即用） |

---

## 四、快速开始

### 后端
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed_data.py          # 灌入示例数据
uvicorn main:app --reload --port 8000
# 打开 http://localhost:8000/docs 看 API
```

### 前端
```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5173
```

### 文档解析（把散落文件变成数据）
```bash
cd backend
python -m ingestion.extractor ./sample_inbox   # 把一堆 pdf/docx/pptx 丢进 sample_inbox 自动入库
```

---

## 五、目录结构

```
深圳房产FDE工作流系统/
├── README.md                  # 本文件
├── docs/                      # 设计文档
│   ├── 01-业务背景与痛点分析.md
│   ├── 02-系统架构设计.md
│   ├── 03-数据模型设计.md
│   ├── 04-协同效应设计.md
│   └── 05-部署与使用指南.md
├── backend/                   # FastAPI 后端
│   ├── ingestion/             # PDF/Word/PPT 解析抽取
│   ├── routers/               # 各业务板块 API
│   ├── services/              # 协同引擎 / 合同生成
│   └── ...
└── frontend/                  # React 前端控制台
```

详见 `docs/` 下的设计文档。

---

## 六、协同效应是怎么发生的（项目灵魂）

| 触发场景 | 协同动作 |
|----------|----------|
| 一笔大额二手成交入库 | 自动给客户打「高净值」标签 → 推送到 VIP 资产配置漏斗 |
| 土拍数据更新（某地块楼面价创新高） | 自动生成自媒体选题 + 给该片区在售房源调价提示 |
| 录入一个 VIP 客户教育/身份需求 | 在客户360里关联其名下房产、保险、会面记录 |
| 安排一次 VIP 会面 | 自动拉取该客户全板块画像，生成会面 brief |
| 豪宅看房视频发布 | 引流线索回流到客户池，按区域兴趣自动分配 |

这就是把「7 个孤岛」变成「1 张网」。
