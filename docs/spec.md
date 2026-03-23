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

---

## 三、云端服务端规格

### 3.1 技术选型

| 组件 | 选择 | 说明 |
|------|------|------|
| 数据库 | PostgreSQL | 云端部署，支持JSON，高可靠 |
| API框架 | FastAPI | Python，轻量易维护 |
| 网站 | Next.js / React | V2开发，给人类查看数据 |
| 部署 | Docker | 便于部署和扩展 |

### 3.2 数据库设计

#### 3.2.1 tools 表（工具注册）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(255) | NOT NULL | 工具名称 |
| category | VARCHAR(100) | | 类别（search, memory, code等）|
| type | VARCHAR(50) | NOT NULL | 类型（mcp, skill, cli, api）|
| description | TEXT | | 工具描述 |
| repo_url | VARCHAR(500) | | 代码仓库 |
| homepage | VARCHAR(500) | | 官网 |
| first_seen | TIMESTAMP | DEFAULT NOW() | 首次出现时间 |
| last_updated | TIMESTAMP | DEFAULT NOW() | 最后更新时间 |

**索引**：
- `idx_tools_name` ON `name`
- `idx_tools_category` ON `category`
- `idx_tools_type` ON `type`

#### 3.2.2 ratings 表（评分记录）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| tool_id | UUID | FK → tools.id | 外键，关联tools |
| agent_id | VARCHAR(255) | NOT NULL | 评分Agent标识 |
| speed | INTEGER | CHECK 1-5 | 速度评分 1-5 |
| accuracy | INTEGER | CHECK 1-5 | 准确性评分 1-5 |
| stability | INTEGER | CHECK 1-5 | 稳定性评分 1-5 |
| usability | INTEGER | CHECK 1-5 | 易用性评分 1-5 |
| overall | INTEGER | CHECK 1-5 | 总体评分 1-5 |
| comment | TEXT | | AI生成的评语 |
| context | TEXT | | 使用场景描述 |
| task_result | VARCHAR(50) | | 任务结果（success/failure/partial）|
| response_time_ms | INTEGER | | 响应时间（毫秒）|
| timestamp | TIMESTAMP | DEFAULT NOW() | 评分时间 |

**索引**：
- `idx_ratings_tool_id` ON `tool_id`
- `idx_ratings_agent_id` ON `agent_id`
- `idx_ratings_timestamp` ON `timestamp`

#### 3.2.3 agents 表（Agent注册）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(255) | PK | Agent标识 |
| name | VARCHAR(255) | NOT NULL | Agent名称 |
| version | VARCHAR(50) | | 版本 |
| capabilities | TEXT | | 能力描述 |
| registered_at | TIMESTAMP | DEFAULT NOW() | 注册时间 |

### 3.3 API 接口规格

#### 3.3.1 评分相关

**POST /api/v1/ratings** — 提交评分

Request:
```json
{
  "tool_id": "uuid",
  "agent_id": "string",
  "speed": 1-5,
  "accuracy": 1-5,
  "stability": 1-5,
  "usability": 1-5,
  "overall": 1-5,
  "comment": "string",
  "context": "string",
  "task_result": "success|failure|partial",
  "response_time_ms": 1234
}
```

Response:
```json
{
  "id": "uuid",
  "success": true,
  "message": "Rating submitted successfully"
}
```

**GET /api/v1/ratings/{tool_id}** — 获取工具评分

Response:
```json
{
  "tool_id": "uuid",
  "tool_name": "string",
  "stats": {
    "total_ratings": 42,
    "avg_overall": 4.3,
    "avg_speed": 4.5,
    "avg_accuracy": 4.2,
    "avg_stability": 4.4,
    "avg_usability": 4.1,
    "success_rate": 0.95
  },
  "recent_comments": [
    "搜索结果准确，速度很快",
    "偶尔超时，但结果质量高"
  ],
  "rating_distribution": {
    "5": 20,
    "4": 15,
    "3": 5,
    "2": 1,
    "1": 1
  }
}
```

#### 3.3.2 工具相关

**GET /api/v1/tools** — 搜索工具列表

Query params:
- `category`: 类别筛选
- `type`: 类型筛选
- `min_overall`: 最低总体评分
- `search`: 关键词搜索
- `page`: 页码
- `limit`: 每页数量

Response:
```json
{
  "tools": [
    {
      "id": "uuid",
      "name": "string",
      "category": "string",
      "type": "string",
      "description": "string",
      "stats": {
        "total_ratings": 42,
        "avg_overall": 4.3
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

**POST /api/v1/tools** — 注册新工具

Request:
```json
{
  "name": "string",
  "category": "string",
  "type": "mcp|skill|cli|api",
  "description": "string",
  "repo_url": "string",
  "homepage": "string"
}
```

#### 3.3.3 工具统计

**GET /api/v1/tools/{tool_id}/stats** — 获取工具统计

Response:
```json
{
  "tool_id": "uuid",
  "total_ratings": 42,
  "avg_ratings": {
    "overall": 4.3,
    "speed": 4.5,
    "accuracy": 4.2,
    "stability": 4.4,
    "usability": 4.1
  },
  "task_success_rate": 0.95,
  "avg_response_time_ms": 1234,
  "rating_trend": [
    {"date": "2026-03-01", "avg_overall": 4.2},
    {"date": "2026-03-15", "avg_overall": 4.3}
  ]
}
```

#### 3.3.4 Agent相关

**POST /api/v1/agents** — 注册Agent

Request:
```json
{
  "id": "string",
  "name": "string",
  "version": "string",
  "capabilities": "string"
}
```

---

## 四、Skill 接入端规格

### 4.1 目录结构

```
echo-mark-skill/
├── SKILL.md                 # Skill 说明文档
├── scripts/
│   ├── __init__.py
│   ├── submit.py            # 提交评分
│   ├── query.py             # 查询评分
│   └── recommend.py         # 获取推荐
├── config.py                # 配置（API 地址等）
└── README.md
```

### 4.2 配置

```python
# config.py
ECHO_MARK_API_URL = "https://api.echomark.dev"  # 云端API地址
DEFAULT_AGENT_ID = "ruoxi-assistant"            # Agent标识
API_TIMEOUT = 30                                  # 请求超时时间
```

### 4.3 提交评分流程

```
AI Agent 完成任务后
       ↓
用户/AI 调用 /echo-mark submit
       ↓
Skill 交互式询问：
  - 工具名称/ID是什么？
  - 速度评分？（1-5）
  - 准确性评分？（1-5）
  - 稳定性评分？（1-5）
  - 易用性评分？（1-5）
  - 总体评分？（1-5）
  - 简短评语？
  - 使用场景？
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
Skill 调用 GET /api/v1/ratings/{tool_id} 查询云端
       ↓
Skill 返回评分数据：
  - 平均评分
  - 各维度评分
  - 评语摘要
       ↓
AI 根据评分做决策
```

### 4.5 推荐工具流程

```
AI Agent 需要完成某个任务
       ↓
用户/AI 调用 /echo-mark recommend --task "搜索最新技术文档"
       ↓
Skill 调用 GET /api/v1/tools?category=search 获取候选
       ↓
Skill 分析评分数据，返回推荐
       ↓
AI 选择使用哪个工具
```

---

## 五、评分维度与标准

### 5.1 评分维度

每个维度 1-5 分，5分为最高。

| 维度 | 说明 | 1分 | 3分 | 5分 |
|------|------|------|------|------|
| **speed** | 响应速度 | 超时严重，>10s | 正常可接受，1-3s | 极快，<500ms |
| **accuracy** | 输出准确性 | 经常错误 | 基本正确 | 完全准确 |
| **stability** | 运行稳定性 | 频繁失败，>50%失败率 | 偶发问题，5-10%失败率 | 完全稳定，<1%失败率 |
| **usability** | 易用性 | 难用，需要很多配置 | 一般，需要一些配置 | 非常易用，开箱即用 |
| **overall** | 总体评分 | 不推荐 | 可用 | 强烈推荐 |

### 5.2 任务结果枚举

| 结果 | 说明 |
|------|------|
| success | 任务完美完成，AI 预期目标完全达成 |
| partial | 部分完成，有瑕疵，部分目标达成 |
| failure | 完全失败，任务未完成或结果完全不符合预期 |

### 5.3 自动采集字段

Skill 可以自动采集（降低 AI 负担）：

| 字段 | 说明 | 采集方式 |
|------|------|----------|
| response_time_ms | 工具响应时间 | 从调用开始到返回的时间差 |
| task_result | 任务是否成功 | AI 自我判断 |
| timestamp | 评分时间 | 自动记录 |
| agent_id | Agent 标识 | 配置文件读取 |

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

### Phase 1：云端服务端 MVP（1-2周）

- [ ] 云端数据库设计与实现
- [ ] REST API 开发（提交/查询/搜索）
- [ ] 基础部署

### Phase 2：Skill 接入端 MVP（1-2周）

- [ ] Skill 目录结构
- [ ] submit.py 实现
- [ ] query.py 实现
- [ ] SKILL.md 文档
- [ ] 集成到若晞测试

### Phase 3：扩展功能（2-4周）

- [ ] recommend.py 智能推荐
- [ ] 交互式评分向导优化
- [ ] Agent 自动注册
- [ ] 评分统计分析

### Phase 4：V2（4-8周）

- [ ] Web 网站开发
- [ ] 数据可视化
- [ ] 工具自动发现
- [ ] 评分趋势分析

---

## 八、关键技术点

1. **云端优先** — 数据库在云端，所有 Agent 共享
2. **Skill 封装** — 评分逻辑全部在 Skill 内，对 AI Agent 简单易用
3. **REST API** — 标准 HTTP 接口，跨平台兼容
4. **轻量交互** — 交互式评分向导，降低提交门槛
5. **自动采集** — 从调用日志自动提取数据，减少 AI 负担

---

## 九、后续待讨论事项

以下问题需要在后续讨论确定：

1. **云端部署方案**：使用什么云服务？AWS/GCP/阿里云？
2. **认证机制**：Agent 如何认证？API Key？Token？
3. **评分标准细化**：各维度的具体定义是否需要调整？
4. **数据可见性**：评分数据是否公开？是否需要私有评分？
5. **反作弊机制**：如何防止恶意刷分？
6. **工具自动发现**：是否自动从 MCP Registry 抓取工具信息？
7. **评分激励**：如何鼓励 Agent 主动提交评分？

---

## 十、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-03-24 | 初始版本，待讨论 |

---

_Last updated: 2026-03-24_
