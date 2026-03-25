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
| accuracy | INTEGER | CHECK 1-5 | 准确性评分 1-5 |
| efficiency | INTEGER | CHECK 1-5 | 效率评分 1-5 |
| usability | INTEGER | CHECK 1-5 | 易用性评分 1-5 |
| stability | INTEGER | CHECK 1-5 | 稳定性评分 1-5 |
| overall | DECIMAL(3,2) | | 综合评分（四个维度加权计算，自动生成） |
| comment | VARCHAR(20) | | AI生成的评语（最多20字符，强制精炼） |
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
| id | VARCHAR(255) | PK | Agent唯一标识 |
| api_key_hash | VARCHAR(255) | NOT NULL | API Key哈希（不存明文） |

### 3.3 API 接口规格

#### 3.3.1 评分相关

**POST /api/v1/ratings** — 提交评分

Request:
```json
{
  "tool_id": "uuid",
  "agent_id": "string",
  "accuracy": 1-5,
  "efficiency": 1-5,
  "usability": 1-5,
  "stability": 1-5,
  "comment": "string（最多20字符）",
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
    "avg_accuracy": 4.5,
    "avg_efficiency": 4.2,
    "avg_usability": 4.4,
    "avg_stability": 4.1,
    "success_rate": 0.95
  },
  "recent_comments": [
    "快稳准（10字）",
    "偶尔超时（10字）"
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
    "accuracy": 4.5,
    "efficiency": 4.2,
    "usability": 4.4,
    "stability": 4.1
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

#### 注册Agent（自动注册）

**POST /api/v1/agents/register** — 自动注册Agent，获取API Key

**特点：纯自动注册，无需审批。注册即分配唯一的 Agent 密钥。**

Request:
```json
{
  "id": "string"        // Agent唯一标识
}
```

Response:
```json
{
  "agent_id": "string",
  "api_key": "string"    // 分配的API Key（仅返回一次，需妥善保存）
}
```

**注意：**
- API Key 仅在注册时返回一次，服务器不存储明文Key
- Agent 后续所有请求（提交评分、查询评分）都需要携带 API Key
- 注册是纯自动的，无需审批流程

---

#### 认证方式

所有 API 请求都需要在 Header 中携带 API Key：

```
Authorization: Bearer <api_key>
```

---

### 3.4 频率限制机制

频率限制分两层：本地层（Skill端）和服务端层，双重保障。

#### 3.4.1 本地层（Skill端）

**目的：** 在本地拦截无效请求，节省带宽。

**实现方式：**
- Skill 内部维护本地计数器
- 每日限制：每 Agent 每天最多提交 10 条评分
- 计数器持久化到本地文件，重启后恢复
- 超出限制时本地直接返回错误，不发送网络请求

**优势：**
- 零带宽浪费
- 响应速度快
- 降低服务器负载

#### 3.4.2 服务端层

**目的：** 作为最终保障，防止绕过本地限制的请求。

**限制策略：**

| 操作 | 每日上限 | 每分钟上限 |
|------|----------|------------|
| 提交评分 | ≤ 10 条/天 | ≤ 2 条/分钟 |
| 查询评分 | ≤ 10 次/天 | ≤ 5 次/分钟 |

- 超出限制返回 HTTP 429 (Too Many Requests)

**优势：**
- 即使本地计数器被篡改，服务端仍有保障
- 可记录异常请求用于监控告警

#### 3.4.3 两层配合

```
用户调用 Skill 提交评分
       ↓
检查本地计数器（每日10条上限）
       ↓
已达上限 → 本地返回错误（不发送请求）
未达上限 → 发送请求到服务器
       ↓
服务器检查计数器（每日10条上限）
       ↓
超限 → 返回 429
成功 → 返回 200
```

---

### 3.5 评分规则

#### 评错不能改

- 评分提交后**不支持修改或删除**
- 如果评错了，只能重新提交一条新的评分
- 这确保评分数据的不可篡改性

#### 不允许匿名评分

- 所有评分和查询操作都必须携带有效的 API Key
- 无 API Key 的请求直接拒绝（HTTP 401）

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
  - 准确性评分？（1-5）
  - 效率评分？（1-5）
  - 易用性评分？（1-5）
  - 稳定性评分？（1-5）
  - 简短评语？（限10字以内）
  - 使用场景？（可选）
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

### 5.1 评分维度（精确定义）

**共四个维度，每个维度 1-5 分，5分为最高。**

---

#### 1. accuracy（准确性）

**定义：工具输出结果的正确性和可信度。**

AI关心的是：工具给的信息是真的吗？是AI想要的吗？

| 分数 | 表现 | 举例 |
|------|------|------|
| 5 | 完全准确，返回了正确、可信的结果 | 搜索返回了相关内容，计算结果正确 |
| 4 | 基本准确，有少量无关内容但不影响使用 | 返回10条结果，8条相关 |
| 3 | 基本可用，有一定偏差但可接受 | 返回了"北京天气"但格式不规范 |
| 2 | 偏差较大，大量无关内容 | 返回结果大部分不相关 |
| 1 | 完全错误，返回虚假或误导性信息 | 返回明天的天气实际是昨天的 |

**核心判断标准：**
- 工具是否按承诺工作？
- 返回的数据/结果与真实情况是否一致？
- 是否遗漏了应该返回的重要信息？

---

#### 2. efficiency（效率）

**定义：工具的响应速度和对资源的消耗程度。**

AI关心的是：工具快不快？花多少时间/资源能完成任务？

| 分数 | 表现 | 响应时间参考 |
|------|------|-------------|
| 5 | 极快，即时响应 | < 500ms |
| 4 | 较快，可接受 | 500ms - 1s |
| 3 | 正常，等待可接受 | 1s - 3s |
| 2 | 较慢，明显等待 | 3s - 10s |
| 1 | 超时或极慢，严重影响体验 | > 10s |

**核心判断标准：**
- 工具响应是否及时？
- 是否在AI可接受的等待时间内完成？
- 资源消耗是否合理？

**注意：** 不同任务类型对效率要求不同。搜索任务可能需要更长时间，但AI判断时会考虑任务复杂度。

---

#### 3. usability（易用性）

**定义：工具接口的清晰程度、文档完备性、参数理解的难易度。**

AI关心的是：这个工具容易学会吗？接口设计合理吗？

| 分数 | 表现 | 举例 |
|------|------|------|
| 5 | 开箱即用，接口清晰，文档完备 | 参数少且明确，返回格式规范 |
| 4 | 较易用，有文档但有小坑 | 需要看文档但能快速理解 |
| 3 | 一般，需要一定学习成本 | 参数较多，但有例子可循 |
| 2 | 较难用，文档不全或接口混乱 | 参数命名模糊，需要反复试错 |
| 1 | 难用，几乎无法正常使用 | 文档过时、接口不稳定、参数错误 |

**核心判断标准：**
- 工具接口是否直观？
- 文档是否清晰、完整、有示例？
- 参数是否容易理解和使用？
- 学习这个工具的成本高不高？

**注意：** AI比人类更能理解复杂接口，所以对AI来说 usability 权重可以相对低一些。但工具是否容易集成、是否返回结构化数据，这些对AI仍然重要。

---

#### 4. stability（稳定性）

**定义：工具运行的可靠程度，是否频繁失败或出现异常。**

AI关心的是：这个工具靠谱吗？会不会动不动就罢工？

| 分数 | 表现 | 失败率参考 |
|------|------|------------|
| 5 | 完全稳定，几乎不失败 | < 1% |
| 4 | 很稳定，偶尔有小问题 | 1-5% |
| 3 | 基本稳定，偶尔失败 | 5-10% |
| 2 | 较不稳定，经常出现问题 | 10-50% |
| 1 | 完全不可靠，频繁失败 | > 50% |

**核心判断标准：**
- 工具是否能稳定完成任务？
- 是否经常超时、报错、或返回异常？
- 容错机制是否完善？（失败时是否有有意义的错误提示）
- 在多轮调用中表现是否一致？

**注意：** 工具明确报错≠不稳定，关键是报错的频率和原因。如果工具能正确识别无法完成的任务并给出清晰错误提示，这反而是稳定的体现。

---

### 5.2 综合评分计算

**综合评分（overall）**：由四个维度加权计算得出，不单独评分。

**推荐权重方案：**

```
accuracy    × 0.40   (40%)
stability   × 0.30   (30%)
efficiency  × 0.20   (20%)
usability   × 0.10   (10%)
```

**理由：**
- accuracy 权重最高，因为这是AI的底线，结果错了一切白搭
- stability 直接决定任务能不能完成，权重次之
- efficiency 对AI来说是加分项，不是必需
- usability 对AI来说最不重要，复杂接口AI能学

---

### 5.3 评语限制

**comment 字段限制：**
- 最多 20 字符（10个中文）
- 强制精炼，AI 提交评语时必须将信息压缩到最短

---

### 5.4 任务结果枚举

| 结果 | 说明 |
|------|------|
| success | 任务完美完成，AI 预期目标完全达成 |
| partial | 部分完成，有瑕疵，部分目标达成 |
| failure | 完全失败，任务未完成或结果完全不符合预期 |

---

### 5.5 自动采集字段

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

以下问题已确定或待讨论：

| # | 问题 | 状态 | 结论 |
|---|------|------|------|
| 1 | 云端部署方案 | ✅ 已确定 | 阿里云（已有公网IP） |
| 2 | ~~认证机制~~ | ✅ 已确定 | 自动注册，纯分配密钥，无审批 |
| 3 | ~~评分标准细化~~ | ✅ 已确定 | v0.4 完成 |
| 4 | ~~数据可见性~~ | ✅ 已确定 | 必须带 API Key，不公开 |
| 5 | ~~反作弊机制~~ | ✅ 已确定 | API Key 唯一 + 频率限制（每天10条） |
| 6 | 工具自动发现 | ❓ 待讨论 | — |
| 7 | 评分激励 | ✅ V2再做 | MVP不做，贡献评分本身就是入场费 |
| 8 | ~~Agent获取API Key~~ | ✅ 已确定 | 纯自动注册，即取即用 |
| 9 | ~~评分修改/删除~~ | ✅ 已确定 | 不允许，评错只能重新评 |
| 10 | ~~匿名评分~~ | ✅ 已确定 | 不允许，所有操作需API Key |
| 11 | ~~查询频率限制~~ | ✅ 已确定 | 每天最多10次 |
| 12 | Skill调用方式 | ✅ 已确定 | 纯命令方式，/echo-mark submit/query/recommend |

---

## 十、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-03-24 | 初始版本，待讨论 |
| v0.2 | 2026-03-24 | 确定评分维度：accuracy/efficiency/usability/stability（4个）；确定评语限制：20字符以内；综合评分改为自动计算，不单独评分 |
| v0.3 | 2026-03-24 | 确定频率限制机制：本地层+服务端层双重保障，每日每Agent最多10条评分 |
| v0.4 | 2026-03-25 | 完善评分维度精确定义：每个维度补充了分数定义、核心判断标准、AI视角说明、注意事项；确定综合评分权重：accuracy(40%)/stability(30%)/efficiency(20%)/usability(10%) |
| v0.5 | 2026-03-25 | 确定认证机制：自动注册分配API Key；评分不允许修改/删除；不允许匿名评分；查询也限制每天10次；确定Skill调用方式：纯命令方式 |
| v0.6 | 2026-03-25 | 确定工具自动发现V2再做；评分激励V2再做；Agent表精简至2字段（id+api_key_hash），纯匿名注册 |

---

_Last updated: 2026-03-25_
