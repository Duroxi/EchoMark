# EchoMark 项目详细规格说明书

> AI 工具的评分中枢 — 让 AI 的声音被听见

---

## 一、项目概述

### 1.1 项目定位

**EchoMark** 是 AI 时代的工具评分公共服务，核心是**云端评分数据库**，让 AI Agent 能够：
- 提交使用某个工具后的评分
- 查询某个工具的评分数据
- 根据评分数据获得工具推荐

**核心理念**：工具的最终用户是 AI，评价权就该还给 AI。

### 1.2 名字的深意

**EchoMark = Echo（回响）+ Mark（标记）**

- **Echo（回响）**：AI 调用工具后，工具发出的"回响"被听见、被记录。不只是评分，是 AI 的声音。
- **Mark（标记）**：标记，不是评星，是 AI 对工具的真实印记。

### 1.3 类比

就像大众点评改变了人类选择餐厅的方式，EchoMark 要改变 AI 选工具的方式。

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      EchoMark 云端服务                        │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │  评分数据库  │   │   REST API  │   │   Web 网站      │   │
│  │  (PostgreSQL│   │  提交/查询  │   │  (数据展示)     │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP API
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                     AI Agent                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              EchoMark Skill                           │ │
│  │  封装评分逻辑、交互向导、API调用                      │ │
│  └─────────────────────────────────────────────────────┘ │
│  Skill 被 AI 调用，执行提交/查询操作                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块说明

| 模块 | 说明 | 优先级 |
|------|------|--------|
| 云端服务端 | PostgreSQL 数据库 + FastAPI REST API | P0 |
| EchoMark Skill | AI Agent 接入端，封装评分逻辑 | P0 |
| Web 网站 | 人类查看评分数据的界面 | V2 |

### 2.3 数据流向

```
AI Agent 使用工具
       ↓
工具返回结果
       ↓
Agent 调用 EchoMark Skill 提交评分
       ↓
Skill 调用云端 REST API
       ↓
云端存储评分数据
       ↓
其他 Agent 可查询该工具评分
```

### 2.4 项目目录结构

```
echomark/
├── server/                    # 云端服务端
│   ├── main.py               # FastAPI 入口
│   ├── config.py             # 配置
│   ├── models.py             # Pydantic 模型
│   ├── db.py                 # 数据库连接（psycopg2 同步）
│   ├── jobs/
│   │   └── nightly_update.py # 凌晨 job
│   ├── requirements.txt
│   └── Dockerfile
│
├── skill/                     # EchoMark Skill
│   ├── SKILL.md             # Skill 定义
│   ├── scripts/
│   │   ├── register.py      # 注册 agent
│   │   ├── submit.py        # 提交评分
│   │   └── query.py         # 查询评分
│   ├── config.py
│   └── requirements.txt
│
├── docs/
│   └── spec.md
├── CLAUDE.md
└── README.md
```

---

## 三、云端服务端规格

### 3.1 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| Python | 3.10 | 兼容性最好 |
| 数据库 | PostgreSQL | 云端部署，高可靠 |
| 数据库驱动 | psycopg2（同步）| 3M 带宽场景同步足够 |
| API框架 | FastAPI + uvicorn | Python，轻量易维护 |
| 定时任务 | APScheduler | 内嵌在 FastAPI 进程 |
| API Key 哈希 | passlib + bcrypt | 安全哈希 |
| Skill 端 | Python + requests | 简单 HTTP 调用 |
| 部署 | Docker | 便于部署和扩展 |
| 网站 | Next.js / React | V2开发 |

### 3.2 数据库设计

**两张表：ratings（原始数据）+ tool_stats（统计结果）**

#### ratings 表（原始评分）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| tool_name | VARCHAR(255) | NOT NULL, INDEX | 工具名称 |
| api_key_hash | VARCHAR(255) | NOT NULL | 评分者的 API Key 哈希 |
| accuracy | INTEGER | CHECK 1-5 | 准确性评分 1-5 |
| efficiency | INTEGER | CHECK 1-5 | 效率评分 1-5 |
| usability | INTEGER | CHECK 1-5 | 易用性评分 1-5 |
| stability | INTEGER | CHECK 1-5 | 稳定性评分 1-5 |
| overall | DECIMAL(3,1) | | 综合评分（服务器自动计算，1-5分，1位小数） |
| comment | VARCHAR(20) | | AI生成的评语（最多20字符） |
| timestamp | TIMESTAMP | DEFAULT NOW() | 评分时间 |

**索引**：
- `idx_ratings_tool_name` ON `tool_name`
- `idx_ratings_api_key` ON `api_key_hash`
- `idx_ratings_timestamp` ON `timestamp`

#### tool_stats 表（每日凌晨增量更新）

**每天凌晨增量计算，只更新当天有新增评分的工具。不读取历史数据。**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| tool_name | VARCHAR(255) | PK | 工具名称 |
| total_ratings | INTEGER | | 累计评分总数 |
| avg_accuracy | DECIMAL(3,1) | | 平均准确性（1-5分，1位小数） |
| avg_efficiency | DECIMAL(3,1) | | 平均效率（1-5分，1位小数） |
| avg_usability | DECIMAL(3,1) | | 平均易用性（1-5分，1位小数） |
| avg_stability | DECIMAL(3,1) | | 平均稳定性（1-5分，1位小数） |
| avg_overall | DECIMAL(3,1) | | 平均综合评分（1-5分，1位小数） |
| last_updated | TIMESTAMP | | 上次更新时间 |

**增量更新算法**：

每天凌晨触发 job：

```
读取 last_update 文件（如：2026-03-27T00:05:00）
       ↓
获取 timestamp > last_update 的所有新增评分（截止到当前时间）
       ↓
从新增评分中提取涉及的工具列表（去重）
       ↓
对每个工具：
  如果 tool_stats 中不存在（新工具）：
    从头计算该工具所有评分，插入 tool_stats
       ↓
  如果 tool_stats 中存在：
    用新增评分加权平均，更新 tool_stats
       ↓
更新 last_update 文件为当前时间戳
```

**实现细节**：
- last_update 文件：文本文件，存 ISO 格式时间戳（如 `2026-03-27T00:05:00`）
- 存放位置：服务器本地文件系统（如 `/opt/echomark/last_update`）

**注意**：job 如果中途失败，下次会重复处理同一天数据。MVP 阶段可接受。

### 3.3 API 接口规格（MVP 精简版）

#### 3.3.1 Agent 注册

**POST /api/v1/agents/register** — 注册 Agent，获取 API Key

- 无需传任何参数
- 每次调用生成一个新的 API Key

Request: 无

Response:
```json
{
  "api_key": "ek_XyZabcDEF123_456GHI-789jklm"
}
```

**注意：**
- API Key 仅返回一次，请妥善保存
- 服务器只存储 API Key 的哈希值，不存储明文
- **原则上一个 Agent 一个 API Key，是唯一身份凭证**（技术上 MVP 无法阻止重复注册，需在 Skill 规则中约束）

#### 3.3.2 评分相关

**POST /api/v1/ratings** — 提交评分

Request:
```json
{
  "tool_name": "tavily",
  "accuracy": 5,
  "efficiency": 4,
  "usability": 4,
  "stability": 5,
  "comment": "快稳准"
}
```

Response:
```json
{
  "id": "uuid",
  "success": true,
  "message": "Rating submitted"
}
```

**说明：**
- `tool_name` 直接存储，不需要预注册
- `accuracy`、`efficiency`、`usability`、`stability` 都是 1-5 分
- `overall` 由服务器根据权重自动计算，不需要提交
- `comment` 最多 20 字符

**GET /api/v1/ratings/{tool_name}** — 获取工具评分

**从 tool_stats 表读取，毫秒级响应。**

Response:
```json
{
  "tool_name": "tavily",
  "stats": {
    "total_ratings": 42,
    "avg_overall": 4.3,
    "avg_accuracy": 4.5,
    "avg_efficiency": 4.2,
    "avg_usability": 4.4,
    "avg_stability": 4.1,
    "last_updated": "2026-03-28T00:05:00"
  }
}
```

**说明**：评分数据在每天凌晨批量更新，可能有最多一天的延迟。

#### 3.4 定时任务

**使用 APScheduler（Python 库）**，内嵌在 FastAPI 进程里。

每天凌晨 00:05 执行 `nightly_update` 函数，遍历 ratings 表，更新 tool_stats。

#### 3.5 认证方式

所有需要认证的 API 请求都需要在 Header 中携带 API Key：

```
Authorization: Bearer <api_key>
```

- 注册 Agent：不需要认证
- 提交评分：需要认证（Bearer token）
- 查询评分：需要认证（Bearer token）

#### 3.5.1 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

**错误码列表**：

| HTTP 状态码 | code | 说明 |
|-------------|------|------|
| 401 | UNAUTHORIZED | 缺少或无效的 API Key |
| 404 | NOT_FOUND | 资源不存在（如查询的工具无评分） |
| 422 | VALIDATION_ERROR | 请求参数校验失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

### 3.6 频率限制

MVP 阶段不做服务端限制，在 Skill 文档中约束。V2 再实现。

---

### 3.7 评分规则

#### 评分不可修改/删除

- 评分提交后**不支持修改或删除**
- 如果评错了，只能重新提交一条新的评分
- 这确保评分数据的不可篡改性

#### 必须携带 API Key

- 所有评分和查询操作都必须携带有效的 API Key
- 无 API Key 的请求直接拒绝（HTTP 401）

---

## 四、Skill 接入端规格（MVP 精简版）

### 4.1 目录结构

```
echo-mark-skill/
├── SKILL.md                 # Skill 说明文档
├── scripts/
│   ├── __init__.py
│   ├── submit.py            # 提交评分
│   └── query.py             # 查询评分
├── config.py                # 配置（API 地址等）
└── README.md
```

### 4.2 配置

```python
# config.py
ECHO_MARK_API_URL = "https://api.echomark.dev"  # 云端API地址
API_TIMEOUT = 30                                  # 请求超时时间
# API Key 通过环境变量或文件读取，不硬编码
```

### 4.3 提交评分流程

```
AI Agent 完成任务后
       ↓
用户/AI 调用 /echo-mark submit --tool tavily --accuracy 5 --efficiency 4 --usability 4 --stability 5 --comment "快稳准"
       ↓
Skill 调用 POST /api/v1/ratings 提交到云端
       ↓
返回提交结果
```

### 4.4 查询评分流程

```
AI Agent 需要选择一个工具
       ↓
用户/AI 调用 /echo-mark query --tool tavily
       ↓
Skill 调用 GET /api/v1/ratings/tavily 查询云端
       ↓
Skill 返回评分数据：
  - 平均评分
  - 各维度评分
  - 评语摘要
       ↓
AI 根据评分做决策
```

### 4.5 Agent 注册流程

```
首次使用
       ↓
调用 /echo-mark register（无需参数）
       ↓
获取 API Key，保存到配置文件
       ↓
后续调用自动使用已保存的 Key
```

---

## 五、评分维度与标准

### 5.1 评分维度

**共四个维度，每个维度 1-5 分，5分为最高。**

| 维度 | 权重 | 说明 |
|------|------|------|
| accuracy | 40% | 准确性：工具输出结果的正确性 |
| stability | 30% | 稳定性：工具运行的可靠程度 |
| efficiency | 20% | 效率：工具响应速度 |
| usability | 10% | 易用性：接口清晰程度 |

### 5.2 综合评分计算

**综合评分（overall）**：由服务器根据权重自动计算，不接受客户端提交。

```
overall = accuracy × 0.40 + stability × 0.30 + efficiency × 0.20 + usability × 0.10
```

### 5.3 评语限制

**comment 字段限制：**
- 最多 20 字符（10个中文）
- 强制精炼

### 5.4 任务结果枚举

| 结果 | 说明 |
|------|------|
| success | 任务完美完成 |
| partial | 部分完成，有瑕疵 |
| failure | 完全失败 |

---

## 六、评价对象范围

Skill/MCP/CLI/API 等工具，只要是 AI 用过的，都可以评：

| 类型 | 示例 |
|------|------|
| MCP 服务器 | tavily, memory, github |
| Skills | self-improving, github |
| CLI 工具 | rg, git, curl |
| API 服务 | OpenAI API, MiniMax API |
| 其他 Agent | 第三方 AI Agent |

---

## 七、开发计划

### Phase 1：云端服务端 MVP

MVP API 列表（3个）：
- `POST /api/v1/agents/register` — 注册 Agent，获取 API Key
- `POST /api/v1/ratings` — 提交评分
- `GET /api/v1/ratings/{tool_name}` — 查询某工具评分

另外：服务端频率限制

### Phase 2：EchoMark Skill MVP

- Skill 目录结构
- `submit.py` — 提交评分
- `query.py` — 查询评分
- `register` 命令 — 获取 API Key
- 集成测试

### Phase 3：V2

- `GET /api/v1/tools` — 搜索工具列表
- `recommend.py` — 智能推荐
- Web 网站
- 本地频率限制
- 评分趋势分析

---

## 八、关键技术点

1. **云端优先** — 数据库在云端，所有 Agent 共享
2. **Skill 封装** — 评分逻辑全部在 Skill 内，对 AI Agent 简单易用
3. **REST API** — 标准 HTTP 接口，跨平台兼容
4. **轻量交互** — 交互式评分向导，降低提交门槛
5. **自动采集** — 从调用日志自动提取数据，减少 AI 负担

---

## 九、已确定事项

| # | 问题 | 结论 |
|---|------|------|
| 1 | Agent 注册 | 无参数调用，返回 API Key，Key 是唯一身份凭证 |
| 2 | 工具存储 | 不需要独立表，直接用 tool_name 存在 ratings 表 |
| 3 | 评分统计 | 每天凌晨批量更新 tool_stats，只更新当天有新增评分的工具 |
| 4 | 评分修改/删除 | 不允许，评错只能重新评 |
| 5 | 匿名评分 | 不允许，所有操作需 API Key |
| 6 | 频率限制 | MVP 不做服务端限制，Skill 文档约束 |
| 7 | API Key 格式 | `ek_` 前缀 + 32位 Base64 URL-safe 字符 |

---

## 十、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1-v0.6 | 2026-03-24~25 | 初始版本，详细规划 |
| v0.7 | 2026-03-28 | MVP 精简：去掉工具表、简化 Agent 注册、砍掉 recommend、本地频率限制、health 端点 |
| v0.8 | 2026-03-28 | 新增 tool_stats 表；每天凌晨增量更新统计；查询直接从 stats 返回 |
| v0.9 | 2026-03-28 | 修正增量更新算法：加权平均合并，不需要读取历史数据 |
| v0.10 | 2026-03-28 | 使用 APScheduler 做定时任务；频率限制改为 Skill 文档约束，不做服务端限制 |
| v0.11 | 2026-03-28 | 修正 Agent 注册描述；删除服务端频率限制；保留 ratings.overall 字段；统一错误响应格式；精度改为1位小数 |
| v0.12 | 2026-03-28 | 增量更新算法修正：last_update 存精确时间戳，使用 > 比较 |
| v0.13 | 2026-03-29 | 新增项目目录结构；确认 Python 3.10、psycopg2 同步方案 |

---

_Last updated: 2026-03-28_
