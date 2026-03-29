# EchoMark MVP 测试与部署计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 充分测试 EchoMark MVP 并准备上线部署

**Architecture:** 服务端使用 Docker 部署在阿里云，数据库使用 PostgreSQL，Skill 端通过 HTTP 调用云端 API

**Tech Stack:** Python 3.10, PostgreSQL, FastAPI, Docker, psycopg2

---

## 测试计划

### Task 1: 服务端 - 数据库初始化测试

**Files:**
- Test: `server/migrations/init.sql` 执行验证

- [ ] **Step 1: 在内网服务器创建数据库**

```bash
psql -U postgres -c "CREATE DATABASE echomark;"
```

- [ ] **Step 2: 执行数据库迁移**

```bash
psql -U postgres -d echomark -f server/migrations/init.sql
```

- [ ] **Step 3: 验证表结构**

```bash
psql -U postgres -d echomark -c "\d ratings"
psql -U postgres -d echomark -c "\d tool_stats"
```

Expected: 显示正确的表结构（id, tool_name, api_key_hash, accuracy, efficiency, usability, stability, overall, comment, timestamp）

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/
git commit -m "docs: add MVP test and deployment plan"
```

---

### Task 2: 服务端 - 启动 API 服务

**Files:**
- Server: `server/main.py`, `server/config.py`

- [ ] **Step 1: 配置环境变量**

创建 `.env` 文件：
```
DATABASE_URL=postgresql://user:password@localhost:5432/echomark
LAST_UPDATE_FILE=/opt/echomark/last_update
```

- [ ] **Step 2: 构建 Docker 镜像（如使用 Docker）**

```bash
cd server && docker build -t echomark-api .
```

或直接启动：
```bash
cd server && uvicorn main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 3: 验证服务启动**

```bash
curl http://localhost:8000/docs
```

Expected: 返回 FastAPI Swagger UI HTML

- [ ] **Step 4: Commit**

```bash
git add server/
git commit -m "chore: update server config for deployment"
```

---

### Task 3: 服务端 - Agent 注册 API 测试

**Files:**
- Test: `tests/test_api.py` 扩展

- [ ] **Step 1: 测试注册接口（无认证）**

```bash
curl -X POST http://localhost:8000/api/v1/agents/register
```

Expected Response:
```json
{
  "api_key": "ek_xxx..."
}
```

- [ ] **Step 2: 验证 API Key 格式**

确认返回的 API Key 以 `ek_` 开头，长度正确

- [ ] **Step 3: 多次注册验证**

连续调用 3 次，确认每次返回不同的 API Key

- [ ] **Step 4: Commit**

```bash
git commit -m "test: verify agent registration API"
```

---

### Task 4: 服务端 - 提交评分 API 测试

**Files:**
- Test: 手动 curl 测试

- [ ] **Step 1: 无认证提交评分（应返回 401）**

```bash
curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"test-tool","accuracy":5,"efficiency":4,"usability":4,"stability":5,"comment":"测试"}'
```

Expected: `401 Unauthorized`

- [ ] **Step 2: 带无效 Bearer token 提交（应返回 401）**

```bash
curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid_token" \
  -d '{"tool_name":"test-tool","accuracy":5,"efficiency":4,"usability":4,"stability":5,"comment":"测试"}'
```

Expected: `401 Unauthorized`

- [ ] **Step 3: 带有效 API Key 提交评分**

```bash
curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{"tool_name":"tavily","accuracy":5,"efficiency":4,"usability":4,"stability":5,"comment":"快稳准"}'
```

Expected Response:
```json
{
  "id": "uuid",
  "success": true,
  "message": "Rating submitted"
}
```

- [ ] **Step 4: 提交无效数据（应返回 422）**

```bash
curl -X POST http://localhost:8000/api/v1/ratings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -d '{"tool_name":"tavily","accuracy":6,"efficiency":4,"usability":4,"stability":5}'
```

Expected: `422 Validation Error`

- [ ] **Step 5: Commit**

```bash
git commit -m "test: verify rating submission API"
```

---

### Task 5: 服务端 - 查询评分 API 测试

**Files:**
- Test: 手动 curl 测试

- [ ] **Step 1: 查询无评分的工具（应返回 404）**

```bash
curl http://localhost:8000/api/v1/ratings/nonexistent-tool \
  -H "Authorization: Bearer <YOUR_API_KEY>"
```

Expected: `404 Not Found`

- [ ] **Step 2: 查询已有评分的工具**

```bash
curl http://localhost:8000/api/v1/ratings/tavily \
  -H "Authorization: Bearer <YOUR_API_KEY>"
```

Expected Response (在 nightly update 之前可能为空):
```json
{
  "tool_name": "tavily",
  "stats": null
}
```

- [ ] **Step 3: 测试 APScheduler 定时任务**

等待凌晨 00:05 或手动触发 `nightly_update`

验证 `tool_stats` 表有数据

- [ ] **Step 4: Commit**

```bash
git commit -m "test: verify rating query API and nightly update"
```

---

### Task 6: Skill 端 - 完整流程测试

**Files:**
- Skill: `echomark-skill/scripts/`

- [ ] **Step 1: 配置 API URL**

```bash
export ECHO_MARK_API_URL=http://<SERVER_IP>:8000
```

- [ ] **Step 2: 测试 register**

```bash
cd echomark-skill
python -m scripts.register
```

Expected: 显示成功消息，API Key 保存到 `~/.echomark/api_key`

- [ ] **Step 3: 测试 submit**

```bash
python -m scripts.submit --tool tavily --accuracy 5 --efficiency 4 --usability 4 --stability 5 --comment "快稳准"
```

Expected: 显示提交成功和 rating ID

- [ ] **Step 4: 测试 query**

```bash
python -m scripts.query --tool tavily
```

Expected: 显示该工具的评分统计（等待 nightly update 后才有数据）

- [ ] **Step 5: 测试错误处理**

1. 删除 `~/.echomark/api_key`，运行 `query` → 应提示先注册
2. 用错误参数运行 `submit` → 应显示参数错误

- [ ] **Step 6: Commit**

```bash
git commit -m "test: verify skill integration with server"
```

---

### Task 7: 部署检查清单

**Files:**
- Server: `server/Dockerfile`, `server/requirements.txt`

- [ ] **Step 1: 验证 Dockerfile 可构建**

```bash
cd server && docker build -t echomark-api:latest .
docker run -d -p 8000:8000 --name echomark echomark-api:latest
```

- [ ] **Step 2: 验证环境变量配置**

确认 `DATABASE_URL` 和 `LAST_UPDATE_FILE` 正确配置

- [ ] **Step 3: 验证进程管理**

使用 systemd 或 supervisor 管理 uvicorn 进程

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: verify deployment configuration"
```

---

## 部署后检查清单

| 检查项 | 预期结果 |
|--------|---------|
| 服务启动 | `curl http://localhost:8000/docs` 返回 HTML |
| Agent 注册 | 返回 `{"api_key": "ek_..."}` |
| 提交评分 | 返回 `{"id": "uuid", "success": true}` |
| 查询评分 | 返回评分统计（夜间更新后） |
| Skill register | API Key 保存到文件 |
| Skill submit | 评分提交成功 |
| Skill query | 显示工具评分 |

---

## 已知限制

1. **评分数据延迟**：新提交的评分需要等到凌晨 00:05 批量更新后才能在查询中看到
2. **评分不可删除**：测试时产生的评分会保留在数据库中
