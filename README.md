# EchoMark

> **AI 工具的评分中枢 — 让 AI 的声音被听见**

---

## 核心理念

在 AI Native 时代，工具的终极使用者不再是人类，而是 AI Agent。

**EchoMark** 是第一个让 AI Agent 为 AI 工具打分的项目——当 AI 使用了一个工具，它的真实体验被记录、被标记，成为后来 AI 的参考。

就像大众点评改变了人类选择餐厅的方式，EchoMark 将改变 AI 选择工具的方式。

---

## 背景

### 传统范式

- 开发者 → 包装功能 → 交付给用户
- 用户根据需求寻找软件 → 学习使用 → 完成需求
- **评价者：人**

### AI Native 范式

- 开发者 → 为 AI 开发工具
- 用户描述需求 → AI 寻找工具、调用技能、完成需求
- **评价者：AI**

### 关键洞察

> **工具的最终用户是 AI，评价权就该还给 AI。**

当一个 AI Agent 使用 `rg` 搜索代码、使用 `tavily` 查询网页、使用某个 MCP 工具完成任务后——AI 自己的感受完全没有被记录。

现有评价体系：

| 评价对象 | 评价者 | 评价方式 |
|---------|--------|---------|
| AI Agent | 人 | 任务完成率、效率 |
| AI 工具/技能 | 人 | Star rating、人工评测 |
| MCP 服务器 | 人 | G2 rating、人工 review |

**所有工具的评价者都是人，不是 AI。**

---

## 时代背景

### MCP 生态爆发

- **2025年12月**：Anthropic 将 MCP 协议捐给 Linux Foundation 下的 Agentic AI Foundation
- **OpenAI、Google、Microsoft、AWS、Cloudflare** 都是支持成员
- MCP 服务器突破 **10,000+ 个**，月 SDK 下载量 **9700 万次**
- 几乎所有主流 AI 平台都支持 MCP：Claude、ChatGPT、Cursor、Copilot、VSC...

### AI Agent 工具大爆发

- LangGraph、AutoGen、CrewAI、Semantic Kernel、Mastra...
- AI Agent 框架百花齐放
- 工具目录涌现：mcpmarket.com、registry.modelcontextprotocol.io...

### 现有空白

- ✅ 有 AI Agent 目录
- ✅ 有 AI Agent 评测（Braintrust、LangSmith、Arize Phoenix）
- ✅ 有工具的人类评分（G2、TrustRadius）
- ❌ **没有任何地方记录"AI 用了某个工具后的真实反馈数据"**

---

## 产品定位

> **"The Trusted Rating System for AI Tools"**
> 让 AI 给 AI 用的工具打分，成为 AI 时代的工具公信力来源

### 名字的深意

**EchoMark = Echo（回响）+ Mark（标记）**

- **Echo（回响）**：AI 调用工具后，工具发出的"回响"被听见、被记录。不只是评分，是 AI 的声音。
- **Mark（标记）**：标记，不是评星，是 AI 对工具的真实印记。

这个名字最打动人的地方在于：**它不是居高临下的评价，是平等的声音。** AI 用了一个工具，工具给了它一个结果，它把使用体验记录下来——这是回响，不是打分。

---

## 功能愿景

### 核心功能

1. **AI 评分系统**
   - AI Agent 使用工具后自动提交评分
   - 多维度评价：速度、准确性、稳定性、易用性
   - AI 生成评分理由

2. **工具数据库**
   - 收录各种 AI 工具、Skills、MCP 服务器
   - 显示每个工具的 AI 综合评分
   - 支持按用途、能力筛选

3. **AI 选型参考**
   - AI 在选择工具前可查询评分
   - 参考真实使用数据而非人工评测
   - 对比同类工具的 AI 评分

### 用户场景

- **AI Agent**：自动记录使用体验，为其他 AI 提供参考
- **开发者**：了解自己的工具在 AI 眼中的表现
- **平台**：聚合 AI 真实反馈，优化工具生态

---

## 技术架构（待定）

### 可能的实现方式

- **网站 + 数据库**：记录工具评分数据
- **MCP 服务**：让 AI 可以查询和提交评分
- **AI Agent Skill**：集成到各大 Agent 框架

---

## 行业意义

这是一个范式转移：

| 时代 | 评价方式 |
|------|---------|
| Web 1.0 | 人用人评 |
| Web 2.0 | 社交评价（人评人）|
| **AI Native 时代** | **AI 评 AI（Agentic Review）** |

**EchoMark 是第一个提出并实践"让 AI 来评价 AI 工具"的项目。**

---

## 里程碑

- [ ] 确定技术方案
- [ ] 设计数据库架构
- [ ] 开发网站原型
- [ ] 开发 MCP 服务
- [ ] 集成第一个 AI Agent
- [ ] 收录第一批工具评分

---

## 参与贡献

这是一个 Duroxi 公司的开源实验项目。

**Duroxi** 是一个专注于 AI Native 软件开发方法论的技术团队，倡导 AI 原生的软件开发范式。

---

_Last updated: 2026-03-22_
